import graphene

from django.utils.translation import ugettext_lazy as _

from wagtailcommerce.addresses.models import Address
from wagtailcommerce.carts.utils import get_cart_from_request
from wagtailcommerce.shipping.exceptions import ShippingCostCalculationException


class ShippingQuery(graphene.ObjectType):
    shipping_cost = graphene.Float(
        address_pk=graphene.String(),
        shipping_method_code=graphene.String()
    )

    def resolve_shipping_cost(self, info, address_pk, shipping_method_code, **kwargs):
        try:
            address = info.context.user.addresses.get(deleted=False, pk=address_pk)
            return get_cart_from_request(info.context).get_shipping_cost(address)

        except Address.DoesNotExist:
            raise ShippingCostCalculationException(_('Address not found'))
