from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ProductsAppConfig(AppConfig):
    name = 'wagtailcommerce.products'
    label = 'wagtailcommerce_products'
    verbose_name = _('Wagtail Commerce Products')
