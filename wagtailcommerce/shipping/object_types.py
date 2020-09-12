from graphene_django.types import DjangoObjectType

from wagtailcommerce.shipping.models import ShippingMethod


class ShippingMethodObjectType(DjangoObjectType):

    class Meta:
        model = ShippingMethod
