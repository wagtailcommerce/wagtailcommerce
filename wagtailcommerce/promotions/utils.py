from django.db.models import F
from django.utils import timezone

from wagtailcommerce.promotions.models import Coupon


def verify_coupon(coupon):
    """
    Check if the coupon is still valid.
    """
    try:
        Coupon.objects.active().get(pk=coupon.pk)
    except Coupon.DoesNotExist:
        return False

    return True


def apply_coupon(coupon_code, cart):
    try:
        coupon = Coupon.objects.get(code__iexact=coupon_code.strip(), active=True, auto_generated=False)

        if not verify_coupon(coupon):
            return False

        cart.coupon = coupon
        cart.save()

        Coupon.objects.filter(pk=coupon.pk).update(times_added_to_cart=F('times_added_to_cart') + 1)

        return True

    except Coupon.DoesNotExist:
        return False


def remove_coupon(cart):
    if cart.coupon:
        cart.coupon = None
        cart.save()

    return True
