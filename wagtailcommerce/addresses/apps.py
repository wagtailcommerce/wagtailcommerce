from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AddressesAppConfig(AppConfig):
    name = 'wagtailcommerce.addresses'
    label = 'wagtailcommerce_addresses'
    verbose_name = _('Wagtail Commerce Addresses')
