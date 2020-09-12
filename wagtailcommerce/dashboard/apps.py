from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DashboardAppConfig(AppConfig):
    name = 'wagtailcommerce.dashboard'
    label = 'wagtailcommerce_dashboard'
    verbose_name = _('Wagtail Commerce Dashboard')
