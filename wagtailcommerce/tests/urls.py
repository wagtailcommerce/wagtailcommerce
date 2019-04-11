from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url

from graphene_django.views import GraphQLView

from wagtail.contrib.wagtailsitemaps import views as sitemaps_views
from wagtail.contrib.wagtailsitemaps import Sitemap
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailimages import urls as wagtailimages_urls
from wagtail.wagtailsearch import urls as wagtailsearch_urls


urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search/', include(wagtailsearch_urls)),
    url(r'^images/', include(wagtailimages_urls)),

    url(r'^graphql', GraphQLView.as_view(graphiql=True)),

    url(r'^sitemap\.xml$', sitemaps_views.sitemap),

    url(r'^sitemap-index\.xml$', sitemaps_views.index, {
        'sitemaps': {'pages': Sitemap},
        'sitemap_url_name': 'sitemap',
    }),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemaps_views.sitemap, name='sitemap'),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
]
