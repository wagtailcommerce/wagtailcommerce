from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ShippingAppConfig(AppConfig):
    name = 'wagtailcommerce.shipping'
    label = 'wagtailcommerce_shipping'
    verbose_name = _('Wagtail Commerce Shipping')
