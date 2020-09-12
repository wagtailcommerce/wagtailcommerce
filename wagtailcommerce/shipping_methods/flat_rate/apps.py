from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FlatRateShippingAppConfig(AppConfig):
    name = 'wagtailcommerce.shipping_methods.flat_rate'
    label = 'wagtailcommerce_flat_rate_shipping'
    verbose_name = _('Flat rate shipping method')
