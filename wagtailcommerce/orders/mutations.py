from __future__ import absolute_import, unicode_literals

import graphene
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from wagtailcommerce.addresses.models import Address
from wagtailcommerce.carts.utils import get_cart_from_request, verify_cart_lines_stock
from wagtailcommerce.orders.object_types import OrderObjectType
from wagtailcommerce.orders.utils import create_order
from wagtailcommerce.payments.models import PaymentMethod
from wagtailcommerce.promotions.utils import remove_coupon, verify_coupon
from wagtailcommerce.shipping.models import ShippingMethod


class PlaceOrder(graphene.Mutation):
    class Arguments:
        shipping_address_pk = graphene.String()
        billing_address_pk = graphene.String()
        shipping_method_pk = graphene.String()

    payment_redirect_url = graphene.String()
    success = graphene.Boolean()
    order = graphene.Field(lambda: OrderObjectType)
    error = graphene.String()

    @transaction.atomic
    def mutate(self, info, shipping_address_pk, billing_address_pk, shipping_method_pk, *args):
        try:
            shipping_address = Address.objects.get(user=info.context.user, pk=shipping_address_pk)
        except Address.DoesNotExist:
            raise Exception

        try:
            billing_address = Address.objects.get(user=info.context.user, pk=billing_address_pk)
        except Address.DoesNotExist:
            raise Exception

        try:
            shipping_method = ShippingMethod.objects.for_shipping_address(
                shipping_address, info.context.user).get(pk=shipping_method_pk).specific
        except ShippingMethod.DoesNotExist:
            raise Exception

        cart = get_cart_from_request(info.context)

        place_order_error = ''

        if cart.coupon and not verify_coupon(cart.coupon):
            coupon_code = cart.coupon.code
            remove_coupon(cart)
            place_order_error = _(
                'The coupon "{}" you were currently using is no longer valid. It may have expired or reached its maximum uses.'
            ).format(coupon_code)

        removed_variant_data = verify_cart_lines_stock(info.context.user, cart)

        for variant_data in removed_variant_data:
            if place_order_error:
                place_order_error += ' '

            place_order_error += variant_data['removal_reason_message']

        if place_order_error:
            return PlaceOrder(error=place_order_error, success=False)

        method = PaymentMethod.objects.specific().filter(active=True).first()

        order = create_order(info.context, shipping_address, billing_address, shipping_method)

        payment_redirect_url = method.generate_payment_redirect_url(order, info.context.site.root_url)

        return PlaceOrder(success=True, order=order, payment_redirect_url=payment_redirect_url)
