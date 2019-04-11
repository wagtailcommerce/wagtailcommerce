import graphene
from django.utils.translation import ugettext_lazy as _

from wagtailcommerce.addresses.forms import AddressForm
from wagtailcommerce.addresses.models import Address
from wagtailcommerce.addresses.object_types import AddressObjectType, AddressInput
from wagtailcommerce.accounts.object_types import UserObjectType


class DeleteAddress(graphene.Mutation):
    class Arguments:
        address_pk = graphene.Int(required=True)

    success = graphene.Boolean()
    user = graphene.Field(lambda: UserObjectType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, address_pk, *args):
        try:
            address_instance = Address.objects.filter(user=info.context.user).get(pk=address_pk)
            address_instance.delete()
        except Address.DoesNotExist:
            return EditAddress(
                success=False,
                errors=[_('Error while deleting address. Please reload the page and try again.')]
            )

        return EditAddress(success=True, user=info.context.user)


class EditAddress(graphene.Mutation):
    class Arguments:
        address = AddressInput(required=True)

    success = graphene.Boolean()
    user = graphene.Field(lambda: UserObjectType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, address=None, *args):
        if address.pk:
            try:
                address_instance = Address.objects.filter(user=info.context.user).get(pk=address.pk)
            except Address.DoesNotExist:
                return EditAddress(
                    success=False,
                    errors=[_('Error while editing address. Please reload the page and try again.')]
                )
        else:
            address_instance = Address(user=info.context.user)

        for k, v in address.items():
            setattr(address_instance, k, v)

        address_instance.save()

        if address_instance.default_shipping_address:
            info.context.user.addresses.exclude(pk=address_instance.pk).filter(
                default_shipping_address=True).update(default_shipping_address=False)

        if address_instance.default_billing_address:
            info.context.user.addresses.exclude(pk=address_instance.pk).filter(
                default_billing_address=True).update(default_billing_address=False)

        return EditAddress(success=True, user=info.context.user)
