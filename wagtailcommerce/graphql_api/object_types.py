import graphene
from graphene_django.types import DjangoObjectType

from wagtailcommerce.utils.images import get_image_model
from wagtailcommerce.products.models import Image, ImageSet

from wagtail.images.models import Rendition


WagtailImage = get_image_model(require_ready=False)


class RenditionType(DjangoObjectType):
    class Meta:
        model = Rendition


class WagtailImageType(DjangoObjectType):
    renditions = graphene.List(RenditionType, filter_specs=graphene.Argument(graphene.List(graphene.String)))

    def resolve_renditions(self, info, filter_specs=[]):
        params = {}

        if filter_specs:
            params['filter_spec__in'] = filter_specs

        rend = self.renditions.filter(**params)
        return rend

    class Meta:
        model = WagtailImage
        exclude_fields = ('tags', )


class ImageType(DjangoObjectType):
    image = graphene.Field(WagtailImageType)

    def resolve_image(self, info):
        return self.image

    class Meta:
        model = Image


class ImageSetType(DjangoObjectType):
    images = graphene.List(ImageType, limit=graphene.Argument(graphene.Int))
    object_id = graphene.String(required=False)

    def resolve_object_id(self, info, limit=None):
        if self.object_id:
            return str(self.object_id)

        return self.object_id

    def resolve_images(self, info, limit=None):
        images = self.images.all()

        if limit:
            return images[:limit]

        return images

    class Meta:
        model = ImageSet
