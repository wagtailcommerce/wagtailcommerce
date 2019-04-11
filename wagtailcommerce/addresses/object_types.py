import graphene
from graphene_django.types import DjangoObjectType

from wagtailcommerce.addresses.models import Address


class AddressInput(graphene.InputObjectType):
    pk = graphene.String(required=False)
    name = graphene.String(required=False)
    last_name = graphene.String(required=False)
    street_address_1 = graphene.String(required=False)
    street_address_2 = graphene.String(required=False)
    street_number = graphene.String(required=False)
    floor = graphene.String(required=False)
    apartment_number = graphene.String(required=False)
    city = graphene.String(required=False)
    district = graphene.String(required=False)
    country_area = graphene.String(required=False)
    country = graphene.String(required=False)
    postal_code = graphene.String(required=False)
    phone = graphene.String(required=False)
    security_access_code = graphene.String(required=False)

    default_shipping_address = graphene.Boolean(required=False)
    default_billing_address = graphene.Boolean(required=False)


class AddressObjectType(DjangoObjectType):
    country_name = graphene.Field(graphene.String)
    full_street = graphene.Field(graphene.String)

    def resolve_country_name(self, info):
        return self.get_country_display()

    def resolve_full_street(self, info):
        return self.full_street

    class Meta:
        model = Address
