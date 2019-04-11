from wagtailcommerce.stores.utils import get_store


def store(request):
    store = getattr(request, 'store', None)

    return {
        'store': store,
        'store_currency': store.currency if store else ''
    }
