from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AnalyticsAppConfig(AppConfig):
    name = 'wagtailcommerce.analytics'
    label = 'wagtailcommerce_analytics'
    verbose_name = _('Wagtail Commerce Analytics')
