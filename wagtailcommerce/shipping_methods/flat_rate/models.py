from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel

from wagtailcommerce.orders.utils import order_shipment_generated
from wagtailcommerce.shipping.models import Shipment, ShippingMethod, WithStandardLabelGeneration
from wagtailcommerce.shipping.utils import generate_standard_shipping_label


class FlatRateShippingMethod(WithStandardLabelGeneration, ShippingMethod):
    shipping_rate = models.DecimalField(_('shipping rate'), max_digits=12, decimal_places=2)

    panels = ShippingMethod.panels + [
        FieldPanel('shipping_rate')
    ] + WithStandardLabelGeneration.panels

    def calculate_shipping_cost(self, cart, shipping_address):
        return {
            'cost': self.shipping_rate,
            'discount': Decimal('0'),
            'total': self.shipping_rate
        }

    def generate_shipment(self, order):
        shipment = FlatRateShipment.objects.create(shipping_method=self, shipping_rate=self.shipping_rate, order=order)

        if self.generate_shipping_label:
            shipment.shipping_label.save(
                'Order_{}_shipping_label.pdf'.format(order.identifier),
                generate_standard_shipping_label(order, self)
            )

        # Mark order as shipped
        order_shipment_generated(order)

        # Success
        return True

    class Meta:
        verbose_name = _('flat rate shipping method')
        verbose_name_plural = _('flat rate shipping methods')


class FlatRateShipment(Shipment):
    shipping_rate = models.CharField(
        _('shipping rate'), max_length=100, blank=True,
        help_text=_('Shipping rate at the moment the shipment was generated'))

    class Meta:
        verbose_name = _('flat rate shipment')
        verbose_name_plural = 'flat rate shipments'
