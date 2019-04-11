from __future__ import absolute_import, unicode_literals

from wagtailcommerce.carts.exceptions import CartException
from wagtailcommerce.carts.models import CartLine
from wagtailcommerce.promotions.models import Coupon
from wagtailcommerce.promotions.utils import apply_coupon

SESSION_KEY_NAME = 'cart_token'


def set_cart_cookie(cart, request):
    """
    Save a cart token in the session
    """
    # FIXME: check why session is not used in Saleor
    request.session[SESSION_KEY_NAME] = '{}'.format(cart.token)


def get_anonymous_cart_from_token(store, token):
    """
    Return an open anonymous cart for a given token
    """
    from wagtailcommerce.carts.models import Cart

    return Cart.objects.open().from_store(store).for_token(token=token).first()


def get_user_cart(store, user):
    """
    Fetch an open cart for user
    """
    from wagtailcommerce.carts.models import Cart

    return Cart.objects.open().from_store(store).for_user(user).first()


def can_purchase_variant(user, variant):
    if (variant.stock <= 0 or not variant.product.purchasing_enabled or (
            variant.active is False or variant.product.active is False) and not (user.is_staff and variant.product.preview_enabled)):
        return False
    return True


def get_cart_from_request(request):
    """
    Retrieve cart from DB or create a new one
    """
    from wagtailcommerce.carts.models import Cart

    if request.user.is_authenticated:
        cart = get_user_cart(request.store, request.user)
        user = request.user
    else:
        token = request.session.get(SESSION_KEY_NAME, None)
        cart = get_anonymous_cart_from_token(request.store, token)
        user = None

    if cart is not None:

        if not cart.coupon:
            # Look for auto-assignment coupons
            try:
                coupon = Coupon.objects.active().filter(auto_assign_to_new_users=True).latest('created')

                apply_coupon(coupon.code, cart)

            except Coupon.DoesNotExist:
                pass

        return cart

    return Cart(user=user, store=request.store)


def merge_carts(user, request):
    from wagtailcommerce.carts.models import Cart

    try:
        db_cart = Cart.objects.from_store(request.store).for_user(user).open().latest('created')
    except Cart.DoesNotExist:
        db_cart = None

    session_cart = None
    token = request.session.get(SESSION_KEY_NAME, None)

    if token:
        session_cart = get_anonymous_cart_from_token(token=token, store=request.store)

    final_cart = None

    if db_cart:
        final_cart = db_cart

    if session_cart and db_cart:
        # Copy session cart lines to db cart

        session_cart.status = Cart.REPLACED
        session_cart.save()

        for line in session_cart.lines.all():
            if line.has_stock():
                # Only copy if in stock
                try:
                    existing_cart_variant = db_cart.lines.get(variant=line.variant)
                except CartLine.DoesNotExist:
                    existing_cart_variant = None

                if existing_cart_variant and line.quantity > existing_cart_variant.quantity:
                    # Modify quantity if greater in session cart
                    existing_cart_variant.quantity = line.quantity
                    existing_cart_variant.save()

                if not existing_cart_variant:
                    # Duplicate
                    line.pk = None
                    line.cart = db_cart
                    line.save()

    elif session_cart:
        final_cart = session_cart

        session_cart.user = user
        session_cart.save()

        for line in session_cart.lines.all():
            if not line.has_stock:
                line.delete()

    close_queryset = Cart.objects.from_store(request.store).open().for_user(user)

    if final_cart:
        close_queryset = close_queryset.exclude(pk=final_cart.pk)

    close_queryset.update(status=Cart.CANCELED)


def add_to_cart(request, variant):
    """
    Add one unit of variant to the request's cart
    """
    from wagtailcommerce.carts.models import CartLine

    cart = get_cart_from_request(request)

    if not getattr(cart, 'pk', None):
        cart.save()

    try:
        cart_line = cart.lines.get(variant=variant)
        cart_line.quantity = cart_line.quantity + 1
        cart_line.save()
    except CartLine.DoesNotExist:
        cart_line = CartLine.objects.create(cart=cart, variant=variant, quantity=1)

    if not request.user.is_authenticated:
        set_cart_cookie(cart, request)

    return cart_line


def modify_cart_line(request, variant, quantity):
    """
    Find a cart line matching the variant and modify its quantity
    """
    from wagtailcommerce.carts.models import CartLine

    cart = get_cart_from_request(request)

    if not getattr(cart, 'pk', None) or quantity < 0:
        # Generic error to be displayed on UI
        # Should't happen on any normal scenario
        raise CartException()

    try:
        cart_line = cart.lines.get(variant=variant)

        if quantity == 0:
            cart_line.delete()
            return None

        cart_line.quantity = quantity
        cart_line.save()
        return cart_line
    except CartLine.DoesNotExist:
        raise CartException()


def modify_cart_status(cart, next_status):
    """
    Modify cart status
    """
    cart.status = next_status
    cart.save()


def cart_awaiting_payment(cart):
    if cart.status != cart.OPEN:
        return

    modify_cart_status(cart, cart.AWAITING_PAYMENT)


def cart_paid(cart):
    if cart.status in [cart.CANCELED, cart.PAID]:
        return

    modify_cart_status(cart, cart.PAID)


def reopen_cart(cart):
    from wagtailcommerce.carts.models import Cart

    open_cart_exists = Cart.objects.filter(user=cart.user, store=cart.store, status=Cart.OPEN).exists()

    if not open_cart_exists:
        modify_cart_status(cart, Cart.OPEN)


def verify_cart_lines_stock(user, cart):
    no_stock_variants = []

    for line in cart.lines.all():
        if not can_purchase_variant(user, line.variant):
            no_stock_variants.append(line.variant)

            line.delete()

    return no_stock_variants
