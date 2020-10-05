from __future__ import absolute_import, unicode_literals

import shortuuid
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel, ObjectList,
    TabbedInterface)

from wagtailcommerce.orders.signals import order_paid_signal, order_shipment_generation_failure_signal
from wagtailcommerce.promotions.models import Coupon
from wagtailcommerce.utils.edit_handlers import ReadOnlyPanel


class Order(ClusterableModel):
    PAYMENT_PENDING = 'payment_pending'
    AWAITING_PAYMENT_CONFIRMATION = 'awaiting_payment_confirmation'
    AWAITING_PAYMENT_AUTHORIZATION = 'awaiting_payment_authorization'
    PAID = 'paid'
    SHIPMENT_GENERATED = 'shipment_generated'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancellled'

    ORDER_STATUS_OPTIONS = (
        (PAYMENT_PENDING, _('Payment pending')),
        (AWAITING_PAYMENT_CONFIRMATION, _('Awaiting payment confirmation')),
        (AWAITING_PAYMENT_AUTHORIZATION, _('Awaiting payment authorization')),
        (PAID, _('Paid')),
        (SHIPMENT_GENERATED, _('Shipment generated')),
        (SHIPPED, _('Shipped')),
        (DELIVERED, _('Delivered')),
        (CANCELLED, _('Cancelled')),
    )

    identifier = models.CharField(_('identifier'), max_length=8, db_index=True, unique=True)

    status = models.CharField(_('status'), max_length=30, choices=ORDER_STATUS_OPTIONS,
                              default='payment_pending')

    cart = models.ForeignKey('wagtailcommerce_carts.Cart', related_name='orders', verbose_name=_('cart'),
                             blank=True, null=True, on_delete=models.SET_NULL)
    store = models.ForeignKey('wagtailcommerce_stores.Store', related_name='orders', verbose_name=_('store'), on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', verbose_name=_('user'), on_delete=models.PROTECT)
    billing_address = models.ForeignKey(
        'wagtailcommerce_addresses.Address', blank=True, null=True,
        related_name='orders_by_billing_address', on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        'wagtailcommerce_addresses.Address', blank=True, null=True,
        related_name='orders_by_shipping_address', on_delete=models.SET_NULL)

    # Financial information
    subtotal = models.DecimalField(_('product sub total'), decimal_places=2, max_digits=12)
    product_discount = models.DecimalField(_('product discount'), decimal_places=2, max_digits=12)
    product_tax = models.DecimalField(_('product tax'), decimal_places=2, max_digits=12)
    shipping_cost = models.DecimalField(_('shipping cost'), decimal_places=2, max_digits=12)
    shipping_cost_discount = models.DecimalField(_('shipping cost discount'), decimal_places=2, max_digits=12)
    shipping_cost_total = models.DecimalField(_('shipping cost total'), decimal_places=2, max_digits=12)
    total = models.DecimalField(_('order total'), decimal_places=2, max_digits=12)
    total_inc_tax = models.DecimalField(_('order total (inc. tax)'), decimal_places=2, max_digits=12)

    # Shipping
    # TODO: persist the shipping method information on the order itself in case it's modified or deleted
    shipping_method = models.ForeignKey(
        'wagtailcommerce_shipping.ShippingMethod', related_name='orders',
        verbose_name=_('shipping method'), blank=True, null=True, on_delete=models.SET_NULL)

    # TODO: multi-currency support. Now a single store can only have one currency.
    # currency = models.ForeignKey('stores.Currency', related_name='orders', verbose_name=_('currency'))

    # Coupon information
    coupon = models.ForeignKey(
        'wagtailcommerce_promotions.Coupon', verbose_name=_('coupon'), blank=True, null=True,
        related_name='orders', on_delete=models.SET_NULL)
    coupon_type = models.CharField(_('coupon type'), max_length=20, choices=Coupon.COUPON_TYPE_CHOICES, blank=True)
    coupon_mode = models.CharField(_('coupon mode'), max_length=20, choices=Coupon.COUPON_MODE_CHOICES, blank=True)
    coupon_amount = models.DecimalField(_('coupon amount'), decimal_places=2, max_digits=12, blank=True, null=True)
    coupon_code = models.CharField(_('coupon code'), max_length=40, blank=True)

    language_code = models.CharField(_('language code'), max_length=40)
    date_placed = models.DateTimeField(_('date placed'), db_index=True, auto_now_add=True)
    date_paid = models.DateTimeField(_('date paid'), db_index=True, blank=True, null=True)

    edit_handler = TabbedInterface([
        ObjectList([
            MultiFieldPanel([
                FieldRowPanel([
                    ReadOnlyPanel('identifier', heading=_('Identifier')),
                    FieldPanel('status'),
                ])
            ], heading=_('Order details')),
            MultiFieldPanel([
                FieldRowPanel([
                    ReadOnlyPanel('coupon_code', heading=_('Coupon code')),
                ]),
                FieldRowPanel([
                    ReadOnlyPanel('get_coupon_type_display', heading=_('Coupon type')),
                    ReadOnlyPanel('get_coupon_mode_display', heading=_('Coupon mode')),
                    ReadOnlyPanel('coupon_amount', heading=_('Coupon amount')),
                ])
            ], heading=_('Discount')),
            MultiFieldPanel([
                FieldRowPanel([
                    ReadOnlyPanel('shipping_cost', heading=_('Shipping cost')),
                    ReadOnlyPanel('shipping_cost_discount', heading=_('Shipping cost discount')),
                    ReadOnlyPanel('shipping_cost_total', heading=_('Shipping cost total')),
                ]),
                FieldRowPanel([
                    ReadOnlyPanel('subtotal', heading=_('Subtotal')),
                    ReadOnlyPanel('product_discount', heading=_('Product discount')),
                    ReadOnlyPanel('product_tax', heading=_('Product tax')),
                ]),
                FieldRowPanel([
                    ReadOnlyPanel('total_inc_tax', heading=_('Total')),
                ]),
            ], heading=_('Totals'))
        ], heading=_('Basic info')),
        ObjectList([
            InlinePanel('lines'),
        ], heading=_('Products')),
        ObjectList([
            InlinePanel('shipments'),
        ], heading=_('Shipments')),
    ])

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = self.generate_identifier()

        try:
            previous_state = Order.objects.get(pk=self.pk)

            if previous_state.status != 'paid' and self.status == 'paid':
                # Order has been paid, reduce product stock and trigger event
                for line in self.lines.all():
                    variant = line.product_variant
                    variant.stock = variant.stock - line.quantity
                    variant.save(update_fields=['stock'])

                # Update coupon amount
                if self.coupon:
                    Coupon.objects.filter(pk=self.coupon.pk).update(times_used=models.F('times_used') + 1)

                order_paid_signal.send(Order, order=self)

                # If the order has shipping, generate shipment
                if self.shipping_method:
                    shipment_generation_result = self.shipping_method.specific.generate_shipment(self)

                    if not shipment_generation_result:
                        order_shipment_generation_failure_signal.send(self)

        except Order.DoesNotExist:
            pass

        super().save(*args, **kwargs)

    def generate_identifier(self):
        shortuuid.set_alphabet('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')

        while True:
            uuid = shortuuid.uuid()[:8]
            if not Order.objects.filter(identifier=uuid).exists():
                break

        return uuid

    def product_count(self):
        o = Order.objects.filter(pk=self.pk).annotate(
            product_count=Sum('lines__quantity')
        )

        return o[0].product_count

    def __str__(self):
        return '{}'.format(self.identifier if self.identifier else self.pk)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ('-date_placed', )


class OrderLine(models.Model):
    order = ParentalKey(Order, related_name='lines')
    sku = models.CharField(_('SKU'), max_length=128)
    product_thumbnail = models.ImageField(_('product thumbnail'), blank=True, null=True)
    product_variant = models.ForeignKey('wagtailcommerce_products.ProductVariant', related_name='lines',
                                        null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    item_unit_price = models.DecimalField(_('unit price'), decimal_places=2, max_digits=12)
    item_unit_regular_price = models.DecimalField(_('unit regular price'), decimal_places=2, max_digits=12)
    item_unit_sale_price = models.DecimalField(
        _('unit sale price'), decimal_places=2, max_digits=12, blank=True, null=True)
    item_percentage_discount = models.DecimalField(
        _('percentage discount'), decimal_places=2, max_digits=12, blank=True, null=True)
    item_unit_promotions_discount = models.DecimalField(
        _('per unit discount unit based on promotions'), decimal_places=2, max_digits=12)
    item_unit_price_with_promotions_discount = models.DecimalField(
        _('unit price with promotions discount'), decimal_places=2, max_digits=12)
    line_total = models.DecimalField(_('subtotal'), decimal_places=2, max_digits=12)

    # Persistent fields. If the linked Product Variant is deleted, the SKU, product name and variant desc. persist.
    product_name = models.CharField(_('product name'), max_length=255)
    product_variant_description = models.CharField(_('product variant description'), max_length=255)

    # Dimensions
    weight = models.DecimalField(_('weight'), max_digits=12, decimal_places=2, help_text=_('value stored in grams'), blank=True, null=True)
    width = models.DecimalField(_('width'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)
    height = models.DecimalField(_('height'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)
    depth = models.DecimalField(_('depth'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)

    # Stores serialized custom product information
    product_details = JSONField()

    panels = [
        FieldRowPanel([
            ReadOnlyPanel('sku', heading=_('SKU')),
            ReadOnlyPanel('product_variant_description', _('Variant'))
        ]),
        FieldRowPanel([
            ReadOnlyPanel('quantity', heading=_('quantity')),
            ReadOnlyPanel('item_unit_price', _('unit price')),
        ]),
        FieldRowPanel([
            ReadOnlyPanel('item_unit_regular_price', _('unit regular price')),
            ReadOnlyPanel('item_unit_sale_price', _('unit sale price')),
        ]),
        FieldRowPanel([
            ReadOnlyPanel('item_percentage_discount', _('percentage discount')),
        ]),
        FieldRowPanel([
            ReadOnlyPanel('item_unit_promotions_discount', _('per unit discount unit based on promotions')),
            ReadOnlyPanel('item_unit_price_with_promotions_discount', _('unit price with promotions discount')),
        ]),
        FieldRowPanel([
            ReadOnlyPanel('quantity', heading=_('quantity')),
            ReadOnlyPanel('line_total', _('subtotal'))
        ])
    ]

    def __str__(self):
        return "{} ({})".format(self.product_name, self.quantity)

    @property
    def volume(self, unit=None):
        return self.width * self.height * self.depth

    @property
    def volume_m3(self):
        return self.volume / (1000000000)

    def weight_kg(self):
        if self.weight:
            return self.weight / 1000

    @property
    def width_cm(self):
        if self.width:
            return self.width / 10

    @property
    def height_cm(self):
        if self.height:
            return self.height / 10

    @property
    def depth_cm(self):
        if self.depth:
            return self.depth / 10
        return ''

    class Meta:
        verbose_name = _('order line')
        verbose_name_plural = _('order lines')
