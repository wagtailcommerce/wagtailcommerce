from .utils import get_store


class StoreMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.store = get_store(request)
        response = self.get_response(request)

        return response
