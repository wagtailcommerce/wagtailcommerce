from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from wagtail.contrib.modeladmin.options import ModelAdmin

from wagtailcommerce.products.models import Category, Product
from wagtailcommerce.products.modeladmin.views import ProductEditView


class CategoryAdmin(TreeAdmin):
    fields = ('store', 'name', 'slug', '_position', '_ref_node_id',)
    form = movenodeform_factory(Category)
    prepopulated_fields = {
        'slug': ('name', )
    }


admin.site.register(Category, CategoryAdmin)


class ProductAdmin(ModelAdmin):
    model = Product
    menu_order = 10
    list_display = ('name', 'active', 'available_on', 'display_type', )
    edit_view_class = ProductEditView
    # search_fields = ('name', )

    def display_type(self, obj):
        return obj.content_type.model_class().get_verbose_name()
