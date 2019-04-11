from django.core.paginator import Paginator
import graphene

from django.db.models import Q

from wagtailcommerce.products.models import Category, Product
from wagtailcommerce.products.object_types import CategoryType, ProductType


def process_category(category):
    if 'data' in category:
        cat = {
            'id': category['id'],
            'name': category['data']['name'],
            'slug': category['data']['slug'],
        }

        cat = Category(**cat)

        if 'children' in category.keys():
            cat.children = [process_category(c) for c in category['children']]

        return cat


class CategoriesQuery(graphene.ObjectType):
    categories = graphene.List(CategoryType)

    def resolve_categories(self, info, **kwargs):
        categories = []

        for category in Category.dump_bulk():
            categories.append(process_category(category))

        return categories


class BaseProductSearchResult(graphene.ObjectType):
    num_pages = graphene.Int()
    page_number = graphene.Int()


class BaseProductsQuery(graphene.ObjectType):

    def get_products_queryset(cls, info, *args, **kwargs):
        if info.context.user.is_staff:
            products = Product.objects.specific().all().filter(Q(active=True) | Q(preview_enabled=True))
        else:
            products = Product.objects.specific().all().filter(active=True)

        params = kwargs.keys()
        if 'parent_categories' in params and kwargs['parent_categories']:
            products = products.filter(categories__pk__in=kwargs['parent_categories'])

        return products

    @classmethod
    def resolve_product_search(cls, info, *args, **kwargs):
        products = cls.get_products_queryset(cls, info, *args, **kwargs).order_by('-featured', '-created')

        params = kwargs.keys()

        if 'product_pks' in params:
            clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(kwargs['product_pks'])])
            ordering = 'CASE %s END' % clauses

            products = products.filter(pk__in=kwargs['product_pks']).extra(
                select={
                    'ordering': ordering
                },
                order_by=('ordering', )
            )

        if 'related_to' in params:
            products = products.order_by('?')

        if 'page_number' in params:
            if 'page_size' in params:
                page_size = kwargs['page_size']

            page_number = kwargs['page_number']
        else:
            page_number = 1
            page_size = 10

        paginator = Paginator(products, page_size)
        return cls.get_search_result_class(cls)(products=paginator.page(page_number), num_pages=paginator.num_pages, page_number=page_number)
