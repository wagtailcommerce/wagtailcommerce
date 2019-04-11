from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.db.models.query import BaseIterable

from wagtailcommerce.utils.query import SpecificIterable


class ShipmentQuerySet(QuerySet):
    def specific(self):
        """
        This efficiently gets all the specific objects for the queryset, using
        the minimum number of queries.
        """
        clone = self._clone()
        clone._iterable_class = SpecificIterable
        return clone
