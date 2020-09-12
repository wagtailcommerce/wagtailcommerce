from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class OrdersAppConfig(AppConfig):
    name = 'wagtailcommerce.orders'
    label = 'wagtailcommerce_orders'
    verbose_name = _('Wagtail Commerce Orders')
