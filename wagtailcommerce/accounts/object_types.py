import graphene
from graphene_django.types import DjangoObjectType

from django.contrib.auth import get_user_model
from wagtailcommerce.addresses.object_types import AddressObjectType


class UserObjectType(DjangoObjectType):
    addresses = graphene.List(AddressObjectType)
    gender_verbose = graphene.Field(graphene.String)

    def resolve_addresses(self, info, **kwargs):
        return self.addresses.filter(deleted=False)

    def resolve_gender_verbose(self, info, **kwargs):
        return self.get_gender_display()

    class Meta:
        model = get_user_model()
