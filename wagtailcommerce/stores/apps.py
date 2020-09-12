from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class StoreAppConfig(AppConfig):
    name = 'wagtailcommerce.stores'
    label = 'wagtailcommerce_stores'
    verbose_name = _('Wagtail Commerce Stores')
