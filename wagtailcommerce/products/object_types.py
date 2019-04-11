import graphene
from graphene_django.types import DjangoObjectType

from wagtailcommerce.products.models import Category, Product, ProductVariant


class CategoryType(DjangoObjectType):
    children = graphene.List('wagtailcommerce.products.object_types.CategoryType')

    class Meta:
        model = Category


class ProductType(graphene.ObjectType):
    name = graphene.String()


class ProductVariantType(DjangoObjectType):
    product = graphene.Field(ProductType)

    class Meta:
        model = ProductVariant
