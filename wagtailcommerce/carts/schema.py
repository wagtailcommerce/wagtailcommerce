from django.utils.translation import ugettext_lazy as _

import graphene

from wagtailcommerce.addresses.models import Address
from wagtailcommerce.carts.object_types import CartReplyObjectType, CartTotalsObjectType
from wagtailcommerce.carts.utils import get_cart_from_request
from wagtailcommerce.promotions.utils import remove_coupon, verify_coupon
from wagtailcommerce.shipping.exceptions import ShippingCostCalculationException
from wagtailcommerce.shipping.models import ShippingMethod


class CartQuery(graphene.ObjectType):
    cart = graphene.Field(CartReplyObjectType)

    cart_totals = graphene.Field(
        lambda: CartTotalsObjectType,
        shipping_address_pk=graphene.String(required=False),
        shipping_method_pk=graphene.String(required=False)
    )

    def resolve_cart_totals(self, info, shipping_address_pk=None, shipping_method_pk=None, **kwargs):
        cart = get_cart_from_request(info.context)

        if shipping_address_pk and shipping_method_pk:
            try:
                shipping_address = info.context.user.addresses.get(deleted=False, pk=shipping_address_pk)
                shipping_method = ShippingMethod.objects.for_shipping_address(
                    shipping_address, info.context.user
                ).get(pk=shipping_method_pk).specific

                totals = cart.get_totals_with_shipping(shipping_address, shipping_method)
            except Address.DoesNotExist:
                raise ShippingCostCalculationException(_('Address not found'))
            except ShippingMethod.DoesNotExist:
                raise ShippingCostCalculationException(_('Shipping method not found'))

        else:
            totals = cart.get_totals()

        totals.update({
            'coupon_code': cart.coupon.code if cart.coupon else None,
            'coupon_auto_assigned': cart.coupon.auto_assign_to_new_users if cart.coupon else False
        })

        return CartTotalsObjectType(**totals)

    def resolve_cart(self, info, **kwargs):
        from wagtailcommerce.carts.utils import get_cart_from_request

        cart = get_cart_from_request(info.context)

        coupon_removed = None
        coupon_auto_assigned = False

        if cart.coupon:
            if cart.coupon.auto_assign_to_new_users:
                coupon_auto_assigned = True

            if not verify_coupon(cart.coupon):
                coupon_removed = cart.coupon.code
                remove_coupon(cart)

        return CartReplyObjectType(cart=cart, coupon_removed=coupon_removed, coupon_auto_assigned=coupon_auto_assigned)
