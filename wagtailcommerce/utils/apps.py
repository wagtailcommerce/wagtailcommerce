from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UtilsAppConfig(AppConfig):
    name = 'wagtailcommerce.utils'
    label = 'wagtailcommerce_utils'
    verbose_name = _('Wagtail Commerce Utils')
