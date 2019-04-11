from __future__ import absolute_import, unicode_literals

from wagtailcommerce.shipping.models import ShippingMethod


def get_shipping_cost(cart, address=None):
    shipping_method = ShippingMethod.objects.first().specific

    return shipping_method.calculate_cost(cart, address)
