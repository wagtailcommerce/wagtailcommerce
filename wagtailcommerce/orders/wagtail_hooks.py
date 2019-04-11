from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from wagtailcommerce.orders.models import Order, OrderLine


class OrderAdmin(ModelAdmin):
    model = Order
    menu_icon = 'fa-money'
    menu_order = 1000
    # list_display = ('ident', 'code', 'symbol')
