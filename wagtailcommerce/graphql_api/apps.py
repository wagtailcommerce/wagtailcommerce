from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GraphQLAPIAppConfig(AppConfig):
    name = 'wagtailcommerce.graphql_api'
    label = 'wagtailcommerce_graphql_api'
    verbose_name = _('Wagtail Commerce GraphQL API')
