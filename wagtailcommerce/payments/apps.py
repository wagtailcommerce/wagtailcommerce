from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class PaymentsAppConfig(AppConfig):
    name = 'wagtailcommerce.payments'
    label = 'wagtailcommerce_payments'
    verbose_name = _('Wagtail Commerce Payments')
