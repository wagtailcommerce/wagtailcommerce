from __future__ import absolute_import, unicode_literals

import os
import sys
import traceback
from decimal import Decimal

from django.core.files.base import ContentFile

from wagtailcommerce.carts.utils import (
    cart_awaiting_payment, cart_paid, get_cart_from_request)
from wagtailcommerce.orders.models import Order, OrderLine
from wagtailcommerce.orders.signals import order_shipment_generated_signal


def create_order(request, shipping_address, billing_address, shipping_method, cart=None):
    if not cart:
        cart = get_cart_from_request(request)

    order_shipping_address = shipping_address
    order_shipping_address.pk = None
    order_shipping_address.user = None
    order_shipping_address.save()

    order_billing_address = billing_address
    order_billing_address.pk = None
    order_billing_address.user = None
    order_billing_address.save()

    totals = cart.get_totals_with_shipping(shipping_address, shipping_method)

    order = Order.objects.create(
        cart=cart,
        coupon=cart.coupon if cart.coupon else None,
        coupon_code=cart.coupon.code if cart.coupon else '',
        coupon_type=cart.coupon.coupon_type if cart.coupon else '',
        coupon_mode=cart.coupon.coupon_mode if cart.coupon else '',
        coupon_amount=cart.coupon.coupon_amount if cart.coupon else None,
        store=request.store,
        user=request.user,
        shipping_address=order_shipping_address,
        billing_address=order_billing_address,
        subtotal=totals['subtotal'],
        product_discount=totals['discount'],
        product_tax=Decimal('0'),
        shipping_cost=totals['shipping_cost'],
        shipping_cost_discount=totals['shipping_cost_discount'],
        shipping_cost_total=totals['shipping_cost_total'],
        shipping_method=shipping_method,
        total=totals['total'],
        total_inc_tax=totals['total'],
        language_code=request.LANGUAGE_CODE
    )

    order_lines = []

    for line in cart.lines.select_related('variant', 'variant__product').all():
        variant = line.variant.specific
        product = variant.product

        order_line = OrderLine(
            order=order,
            sku=variant.sku,
            product_variant=variant,
            quantity=line.quantity,
            item_unit_price=line.get_item_unit_price(),
            item_unit_regular_price=line.get_item_unit_regular_price(),
            item_unit_sale_price=line.get_item_unit_sale_price(),
            item_percentage_discount=product.percentage_discount,
            item_unit_promotions_discount=line.get_item_unit_promotions_discount(),
            item_unit_price_with_promotions_discount=line.get_item_unit_price_with_promotions_discount(),
            line_total=line.get_total(),
            product_name=product.name,
            product_variant_description=variant.__str__(),
            product_details=variant.get_details(),
            weight=variant.weight,
            width=variant.width,
            height=variant.height,
            depth=variant.depth
        )

        image = line.get_image()

        if image:
            source_file = image.get_rendition('max-400x400|format-jpeg|bgcolor-ffffff')
            if source_file.file:
                try:
                    file_content = ContentFile(source_file.file.read())
                    file_name = os.path.split(source_file.file.name)[-1]

                    order_line.product_thumbnail.save(file_name, file_content, save=False)

                    source_file.file.close()

                except FileNotFoundError:
                    pass

        order_lines.append(order_line)

    OrderLine.objects.bulk_create(order_lines)

    return order


def modify_order_status(order, next_status):
    """
    Modify order status
    """
    order.status = next_status
    order.save()


def order_awaiting_payment_authorization(order):
    if order.status not in [Order.AWAITING_PAYMENT_AUTHORIZATION, Order.PAID]:
        modify_order_status(order, Order.AWAITING_PAYMENT_AUTHORIZATION)

    cart = getattr(order, 'cart', None)

    if cart:
        cart_awaiting_payment(cart)


def order_awaiting_payment_confirmation(order):
    if order.status not in [Order.AWAITING_PAYMENT_CONFIRMATION, Order.PAID]:
        modify_order_status(order, Order.AWAITING_PAYMENT_CONFIRMATION)

    cart = getattr(order, 'cart', None)

    if cart:
        cart_awaiting_payment(cart)


def order_paid(order):
    if order.status in [Order.PAYMENT_PENDING, Order.AWAITING_PAYMENT_AUTHORIZATION, Order.AWAITING_PAYMENT_CONFIRMATION]:
        modify_order_status(order, Order.PAID)

        cart = getattr(order, 'cart', None)

        if cart:
            cart_paid(cart)


def order_shipment_generated(order):
    if order.status != Order.SHIPMENT_GENERATED:
        modify_order_status(order, Order.SHIPMENT_GENERATED)

    order_shipment_generated_signal.send(order.shipping_method.__class__, order=order)


def order_cancelled(order):
    modify_order_status(order, Order.CANCELLED)
