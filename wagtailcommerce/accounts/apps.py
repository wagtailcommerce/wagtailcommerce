from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AccountsAppConfig(AppConfig):
    name = 'wagtailcommerce.accounts'
    label = 'wagtailcommerce_accounts'
    verbose_name = 'Wagtail Commerce Accounts'
