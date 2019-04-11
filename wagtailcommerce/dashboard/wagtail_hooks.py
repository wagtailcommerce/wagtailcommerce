from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from wagtailcommerce.products.models import Product
from wagtailcommerce.stores.models import Currency, Store


class CurrencyAdmin(ModelAdmin):
    model = Currency
    menu_icon = 'fa-money'
    menu_order = 1000
    list_display = ('name', 'code', 'symbol')


class ProductAdmin(ModelAdmin):
    model = Product
    menu_icon = 'fa-file'
    menu_order = 0
    list_display = ('name', 'active')


class StoreAdmin(ModelAdmin):
    model = Store
    menu_icon = 'date'
    menu_order = 100
    list_display = ('site', )


class WagtailCommerceGroup(ModelAdminGroup):
    menu_label = 'Commerce'
    menu_icon = 'fa-shopping-cart'
    menu_order = 500
    items = [CurrencyAdmin, ProductAdmin, StoreAdmin]


modeladmin_register(WagtailCommerceGroup)
