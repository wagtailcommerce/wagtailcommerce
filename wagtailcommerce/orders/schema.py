import graphene

from wagtailcommerce.orders.models import Order
from wagtailcommerce.orders.object_types import OrderObjectType


class OrdersQuery(graphene.ObjectType):
    orders = graphene.List(OrderObjectType)
    order = graphene.Field(OrderObjectType, pk=graphene.String())

    def resolve_orders(self, info, **kwargs):
        return info.context.user.orders.filter(status__in=[
            Order.PAID, Order.SHIPMENT_GENERATED, Order.SHIPPED, Order.DELIVERED,
            Order.AWAITING_PAYMENT_CONFIRMATION, Order.AWAITING_PAYMENT_AUTHORIZATION
        ])

    def resolve_order(self, info, pk, **kwargs):
        return info.context.user.orders.get(pk=pk)
