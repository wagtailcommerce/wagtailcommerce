import graphene

from wagtailcommerce.accounts.schema import UserQuery
from wagtailcommerce.addresses.mutations import DeleteAddress, EditAddress
from wagtailcommerce.carts.schema import CartQuery
from wagtailcommerce.carts.mutations import AddToCart, ModifyCartLine, UpdateCartCoupon
from wagtailcommerce.products.schema import CategoriesQuery
from wagtailcommerce.orders.schema import OrdersQuery
from wagtailcommerce.orders.mutations import PlaceOrder
from wagtailcommerce.shipping.schema import ShippingQuery


class WagtailCommerceMutations(graphene.ObjectType):
    add_to_cart = AddToCart.Field()
    edit_address = EditAddress.Field()
    delete_address = DeleteAddress.Field()
    place_order = PlaceOrder.Field()
    modify_cart_line = ModifyCartLine.Field()
    update_cart_coupon = UpdateCartCoupon.Field()


class WagtailCommerceQueries(CategoriesQuery, CartQuery, OrdersQuery, UserQuery, ShippingQuery, graphene.ObjectType):
    pass
