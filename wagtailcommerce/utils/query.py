from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models.query import BaseIterable


def specific_iterator(qs):
    """
    This efficiently iterates all the specific pages in a queryset, using
    the minimum number of queries.
    This should be called from ``PageQuerySet.specific``
    """
    pks_and_types = qs.values_list('pk', 'content_type')
    pks_by_type = defaultdict(list)
    for pk, content_type in pks_and_types:
        pks_by_type[content_type].append(pk)

    # Content types are cached by ID, so this will not run any queries.
    content_types = {pk: ContentType.objects.get_for_id(pk)
                     for _, pk in pks_and_types}

    # Get the specific instances of all pages, one model class at a time.
    objects_by_type = {}
    for content_type, pks in pks_by_type.items():
        # look up model class for this content type, falling back on the original
        # model (i.e. Page) if the more specific one is missing
        model = content_types[content_type].model_class() or qs.model
        objects = model.objects.filter(pk__in=pks)
        objects_by_type[content_type] = {obj.pk: obj for obj in objects}

    # Yield all of the pages, in the order they occurred in the original query.
    for pk, content_type in pks_and_types:
        yield objects_by_type[content_type][pk]


class SpecificIterable(BaseIterable):
    def __iter__(self):
        return specific_iterator(self.queryset)
