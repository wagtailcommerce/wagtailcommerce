from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CartsAppConfig(AppConfig):
    name = 'wagtailcommerce.carts'
    label = 'wagtailcommerce_carts'
    verbose_name = _('Wagtail Commerce Carts')
