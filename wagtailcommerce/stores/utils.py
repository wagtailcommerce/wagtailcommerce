from wagtailcommerce.stores.models import Store


def get_store(request):
    site = getattr(request, 'site')

    if site:
        try:
            return Store.objects.get(site=site)
        except Store.DoesNotExist:
            pass

    return None
