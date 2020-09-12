from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PromotionsAppConfig(AppConfig):
    name = 'wagtailcommerce.promotions'
    label = 'wagtailcommerce_promotions'
    verbose_name = _('Wagtail Commerce Promotions')
