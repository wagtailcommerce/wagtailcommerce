from django.db.models import QuerySet

from wagtailcommerce.utils.query import SpecificIterable


class PaymentMethodQuerySet(QuerySet):
    def specific(self):
        """
        This efficiently gets all the specific objects for the queryset, using
        the minimum number of queries.
        """
        clone = self._clone()
        clone._iterable_class = SpecificIterable
        return clone
