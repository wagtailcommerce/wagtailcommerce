import graphene

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from wagtailcommerce.addresses.models import Address
from wagtailcommerce.carts.utils import get_cart_from_request
from wagtailcommerce.shipping.exceptions import ShippingCostCalculationException
from wagtailcommerce.shipping.object_types import ShippingMethodObjectType
from wagtailcommerce.shipping.models import ShippingMethod


class ShippingQuery(graphene.ObjectType):
    shipping_cost = graphene.Float(
        address_pk=graphene.String(),
        shipping_method_code=graphene.String()
    )
    shipping_methods = graphene.List(ShippingMethodObjectType, shipping_address_pk=graphene.String())

    def resolve_shipping_cost(self, info, address_pk, shipping_method_code, **kwargs):
        # TODO: fix or remove
        try:
            address = info.context.user.addresses.get(deleted=False, pk=address_pk)
            return get_cart_from_request(info.context).get_shipping_cost(address)

        except Address.DoesNotExist:
            raise ShippingCostCalculationException(_('Address not found'))

    def resolve_shipping_methods(self, info, shipping_address_pk, **kwargs):
        try:
            shipping_address = info.context.user.addresses.get(deleted=False, pk=shipping_address_pk)

            if info.context.user.is_superuser:
                return ShippingMethod.objects.for_shipping_address(shipping_address, info.context.user)

            return ShippingMethod.objects.for_shipping_address(shipping_address, info.context.user)

        except Address.DoesNotExist:
            raise ShippingCostCalculationException(_('Address not found'))

