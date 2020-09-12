from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TestsAppConfig(AppConfig):
    name = 'wagtailcommerce.tests'
    label = 'wagtailcommerce_tests'
    verbose_name = _('Wagtail Commerce Tests')
