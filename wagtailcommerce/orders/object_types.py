import graphene
from graphene_django.types import DjangoObjectType
from graphene.types.generic import GenericScalar

from wagtailcommerce.orders.models import Order, OrderLine


class OrderObjectType(DjangoObjectType):
    display_day_placed = graphene.Field(graphene.String)
    display_time_placed = graphene.Field(graphene.String)
    product_count = graphene.Field(graphene.Int)
    status_verbose = graphene.Field(graphene.String)

    def resolve_display_day_placed(self, info, **kwargs):
        return self.date_placed.strftime('%d/%m/%Y')

    def resolve_display_time_placed(self, info, **kwargs):
        return self.date_placed.strftime('%H:%M')

    def resolve_status_verbose(self, info, **kwargs):
        return self.get_status_display()

    def resolve_product_count(self, info, **kwargs):
        return self.product_count()

    class Meta:
        model = Order


class OrderLineObjectType(DjangoObjectType):
    product_thumbnail_url = graphene.Field(graphene.String)
    product_details = GenericScalar()
    
    def resolve_product_thumbnail_url(self, info, **kwargs):
        if self.product_thumbnail:
            return self.product_thumbnail.url
        return ''

    class Meta:
        model = OrderLine
