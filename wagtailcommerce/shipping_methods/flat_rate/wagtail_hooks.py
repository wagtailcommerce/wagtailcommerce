from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.options import ModelAdmin

from wagtailcommerce.shipping_methods.flat_rate.models import FlatRateShippingMethod

class FlatRateShippingMethodAdmin(ModelAdmin):
    model = FlatRateShippingMethod
    menu_label = _('Flat rate shipping')
    menu_icon = 'fa-truck'
    list_display = (
        'id', 'title', 'display_title', 'shipping_rate', 'free_shipping_above_amount',
        'enabled', 'enabled_for_administrators'
    )
    search_fields = ('order__identifier', )
