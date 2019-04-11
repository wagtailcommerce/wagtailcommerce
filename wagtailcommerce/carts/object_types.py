import graphene
from graphene_django.types import DjangoObjectType

from wagtailcommerce.carts.models import Cart, CartLine
from wagtailcommerce.graphql_api.object_types import WagtailImageType
from products.schema import ProductUnion, ProductVariantUnion


class CartLineType(DjangoObjectType):
    main_image = graphene.Field(WagtailImageType)
    product = graphene.Field(ProductUnion)
    variant = graphene.Field(ProductVariantUnion)
    item_price = graphene.Float()
    item_discount = graphene.Float()
    item_price_with_discount = graphene.Float()
    total = graphene.Float()

    def resolve_product(self, info, **kwargs):
        return self.variant.product.specific

    def resolve_main_image(self, info, **kwargs):
        return self.get_image()

    def resolve_item_price(self, info, **kwargs):
        return self.get_item_price()

    def resolve_item_discount(self, info, **kwargs):
        return self.get_item_discount()

    def resolve_item_price_with_discount(self, info, **kwargs):
        return self.get_item_price_with_discount()

    def resolve_total(self, info, **kwargs):
        return float(self.get_total())

    def resolve_variant(self, info, **kwargs):
        return self.variant.specific

    class Meta:
        model = CartLine


class CartType(DjangoObjectType):
    discount = graphene.Field(graphene.Float)
    total = graphene.Field(graphene.Float)
    lines = graphene.List(CartLineType)
    item_count = graphene.Int()

    def resolve_total(self, info, address_pk=None, **kwargs):
        return float(self.get_total())

    def resolve_discount(self, info, **kwargs):
        return float(self.get_discount())

    def resolve_lines(self, info, **kwargs):
        return self.lines.all()

    def resolve_item_count(self, info, **kwargs):
        return self.get_item_count()

    class Meta:
        model = Cart


class CartTotalsObjectType(graphene.ObjectType):
    coupon_code = graphene.Field(graphene.String)
    coupon_auto_assigned = graphene.Field(graphene.Boolean)
    discount = graphene.Field(graphene.Float)
    shipping_cost = graphene.Float()
    shipping_cost_discount = graphene.Float()
    shipping_cost_total = graphene.Float()
    subtotal = graphene.Field(graphene.Float)
    total = graphene.Field(graphene.Float)


class CartReplyObjectType(graphene.ObjectType):
    cart = graphene.Field(lambda: CartType)
    coupon_removed = graphene.Field(graphene.String)
    coupon_auto_assigned = graphene.Field(graphene.Boolean)
