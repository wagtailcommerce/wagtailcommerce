from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import translation

from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

from wagtailcommerce.shipping.models import ShippingMethod


def get_shipping_cost(cart, shipping_address, shipping_method):
    return shipping_method.get_shipping_cost(cart, shipping_address)


def generate_standard_shipping_label(order, shipping_method):
    font_config = FontConfiguration()
    with translation.override(order.language_code):
        html = HTML(
            string=render_to_string('shipping/standard_shipping_label.html', {
                'order': order,
                'shipping_method': shipping_method,
                'MEDIA_URL': settings.MEDIA_URL,
                'font_family': getattr(settings, 'WAGTAILCOMMERCE_SIMPLE_SHIPPING_LABEL_FONT_FAMILY')
            }),
            url_fetcher=django_url_fetcher
        )

    return ContentFile(html.write_pdf(font_config=font_config))
