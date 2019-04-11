from __future__ import absolute_import, unicode_literals

import graphene
from django.utils.translation import ugettext_lazy as _

from wagtailcommerce.carts.exceptions import CartException
from wagtailcommerce.carts.object_types import CartType
from wagtailcommerce.carts.utils import can_purchase_variant, get_cart_from_request
from wagtailcommerce.promotions.utils import apply_coupon, remove_coupon


class ModifyCartLine(graphene.Mutation):
    class Arguments:
        variant_pk = graphene.String()
        quantity = graphene.Int()

    success = graphene.Boolean()
    cart = graphene.Field(lambda: CartType)
    deleted = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, variant_pk, quantity, *args):
        from wagtailcommerce.carts.utils import modify_cart_line
        from wagtailcommerce.products.models import ProductVariant

        try:
            variant = ProductVariant.objects.get(pk=variant_pk, product__store=info.context.store)

            try:
                cart_line = modify_cart_line(info.context, variant, quantity)
            except CartException:
                return ModifyCartLine(success=False)

            if cart_line is not None:
                return ModifyCartLine(
                    success=True,
                    cart=get_cart_from_request(info.context)
                )
            else:
                return ModifyCartLine(
                    success=True,
                    deleted=True,
                    cart=get_cart_from_request(info.context)
                )

        except ProductVariant.DoesNotExist:
            return ModifyCartLine(success=False, errors=[_('Product variant not found')])


class AddToCart(graphene.Mutation):
    class Arguments:
        variant_pk = graphene.String()

    success = graphene.Boolean()
    cart = graphene.Field(lambda: CartType)
    errors = graphene.List(graphene.String)
    disableVariant = graphene.Boolean()

    def mutate(self, info, variant_pk, *args):
        from wagtailcommerce.carts.utils import add_to_cart
        from wagtailcommerce.products.models import ProductVariant

        try:
            variant = ProductVariant.objects.get(pk=variant_pk, product__store=info.context.store)

            if not can_purchase_variant(info.context.user, variant):
                return AddToCart(success=False, errors=[_('No more products available for the selected size.')], disableVariant=True)
            else:
                add_to_cart(info.context, variant)

                return AddToCart(
                    success=True,
                    cart=get_cart_from_request(info.context)
                )

        except ProductVariant.DoesNotExist:
            return AddToCart(success=False, errors=[_('Product variant not found')])


class UpdateCartCoupon(graphene.Mutation):
    class Arguments:
        delete = graphene.Boolean(required=False)
        new_coupon_code = graphene.String(required=False)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, delete=False, new_coupon_code=None, *args):
        cart = get_cart_from_request(info.context)
        if delete:
            remove_coupon(cart)
            return UpdateCartCoupon(success=True)
        elif new_coupon_code:
            result = apply_coupon(new_coupon_code, cart)

            if result:
                return UpdateCartCoupon(success=True)
            return UpdateCartCoupon(success=False)
