from django.conf import settings
from django.views.generic import TemplateView
from django.urls import path

urlpatterns = [
    path(
        'standard-shipping-label-demo/',
        TemplateView.as_view(
            template_name='shipping/standard_shipping_label.html',
            extra_context={
                'order': {
                    'identifier': 'E4PK2CAD',
                    'user': {
                        'get_full_name': 'Jane Doe'
                    },
                    'shipping_address': {
                        'street_address_1': 'North street',
                        'street_address_2': 'Between East and West streets',
                        'floor': '7',
                        'apartment_number': 'B',
                        'city': 'One city',
                        'street_number': '1234',
                        'phone': '+999 123-456-789',
                        'postal_code': '7755',
                        'security_access_code': '123456',
                        'district': 'District',
                        'get_country_area': 'Country Area',
                        'country': 'Country'
                    }
                },
                'shipping_method': {
                    'label_heading': '<p>Shipping method <i>label heading</i></p>'
                },
                'test_logo': settings.STATIC_URL + 'img/simple_shipping_label_test_logo.png',
                'font_family': getattr(settings, 'WAGTAILCOMMERCE_SIMPLE_SHIPPING_LABEL_FONT_FAMILY')
            }
        )
    )
]
