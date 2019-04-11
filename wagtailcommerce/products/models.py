import shortuuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from wagtailcommerce.products.query import ProductQuerySet, ProductVariantQuerySet
from wagtailcommerce.utils.images import get_image_model

CATEGORY_MODEL_CLASSES = []
PRODUCT_MODEL_CLASSES = []
PRODUCT_VARIANT_MODEL_CLASSES = []


def get_default_product_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(Product)


def get_default_product_variant_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(ProductVariant)


class Category(MP_Node):
    store = models.ForeignKey('wagtailcommerce_stores.Store', related_name='categories')
    name = models.CharField(_('name'), max_length=150)
    slug = models.SlugField(_('slug'), max_length=50)
    description = models.TextField(_('description'), blank=True)

    def category_path(self):
        return list(self.get_ancestors().values_list('name', flat=True)) + [self.name]

    def __str__(self):
        return ' » '.join(self.category_path())

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class BaseProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model)


ProductManager = BaseProductManager.from_queryset(ProductQuerySet)


class ProductBase(models.base.ModelBase):
    """
    Metaclass for Product
    """
    def __init__(cls, name, bases, dct):
        super(ProductBase, cls).__init__(name, bases, dct)

        if not cls._meta.abstract:
            # register this type in the list of product content types
            PRODUCT_MODEL_CLASSES.append(cls)


class AbstractProduct(models.Model):
    objects = ProductManager()

    class Meta:
        abstract = True


class Product(AbstractProduct, index.Indexed, ClusterableModel, metaclass=ProductBase):
    store = models.ForeignKey('wagtailcommerce_stores.Store', related_name='products')
    name = models.CharField(_('name'), max_length=150)
    slug = models.SlugField(
        verbose_name=_('slug'),
        allow_unicode=True,
        max_length=255,
        help_text=_('The name of the product as it will appear in URLs e.g http://domain.com/store/[product-slug]/'))

    categories = models.ManyToManyField(Category, blank=True, related_name='products')
    single_price = models.BooleanField(_('single price'), default=True, help_text=_('same price for all variants'))
    price = models.DecimalField(_('price'), max_digits=12, decimal_places=2, blank=True, null=True)

    identifier = models.CharField(_('identifier'), max_length=8, db_index=True, unique=True)

    active = models.BooleanField(_('active'))
    purchasing_enabled = models.BooleanField(_('purchasing enabled'), default=True)
    presale = models.BooleanField(_('presale'), default=False)
    preview_enabled = models.BooleanField(_('preview enabled'), default=False)
    available_on = models.DateTimeField(_('available on'), blank=True, null=True)
    featured = models.BooleanField(_('featured'), default=False)

    seo_title = models.CharField(
        verbose_name=_("page title"),
        max_length=255,
        blank=True,
        help_text=_("Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")
    )
    search_description = models.TextField(verbose_name=_('search description'), blank=True)

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='products',
        on_delete=models.SET(get_default_product_content_type)
    )

    created = models.DateTimeField(_('created on'), auto_now_add=True)
    modified = models.DateTimeField(_('modified on'), auto_now=True)

    search_fields = [
        index.SearchField('name', boost=2),
        index.FilterField('price'),
        index.FilterField('active'),
        index.FilterField('available_on'),
        index.FilterField('featured'),
        index.FilterField('created'),
    ]

    # panels = [
    #     FieldPanel('store'),
    #     FieldPanel('name'),
    #     FieldPanel('slug'),
    #     FieldPanel('active'),
    #     FieldPanel('available_on'),
    #     FieldPanel('categories'),
    #     FieldPanel('single_price'),
    #     FieldPanel('price'),
    # ]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    @classmethod
    def get_verbose_name(cls):
        """
        Returns the human-readable "verbose name" of this product model e.g "Clothing product".
        """
        # This is similar to doing cls._meta.verbose_name.title()
        # except this doesn't convert any characters to lowercase
        return capfirst(cls._meta.verbose_name)

    def save(self, *args, **kwargs):
        if not self.identifier:
            self.identifier = self.generate_identifier()

        super().save(*args, **kwargs)

    def generate_identifier(self):
        shortuuid.set_alphabet('abcdefghijklmnopqrstuvwxyz1234567890')

        while True:
            uuid = shortuuid.uuid()[:8]
            if not Product.objects.filter(identifier=uuid).exists():
                break

        return uuid

    @cached_property
    def specific(self):
        """
        Return this product variant in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            # Cannot locate a model class for this content type. This might happen
            # if the codebase and database are out of sync (e.g. the model exists
            # on a different git branch and we haven't rolled back migrations before
            # switching branches); if so, the best we can do is return the page
            # unchanged.
            return self
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @cached_property
    def url(self):
        raise NotImplementedError(_('Your child Product model must implement the url() method'))


class ImageSet(ClusterableModel):
    product = ParentalKey(Product, related_name='image_sets')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    filtering_relation = GenericForeignKey('content_type', 'object_id')

    panels = [
        InlinePanel('images', label=_('images'))
    ]

    def __str__(self):
        return "{}".format(self.filtering_relation)

    class Meta:
        verbose_name = _('image set')
        verbose_name_plural = _('image sets')
        unique_together = ('content_type', 'object_id', )


class Image(Orderable):
    image_set = ParentalKey(ImageSet, related_name='images')
    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_('image'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='wagtailcommerce_images'
    )

    panels = [
        ImageChooserPanel('image')
    ]

    class Meta(Orderable.Meta):
        verbose_name = _('image')
        verbose_name_plural = _('images')


class BaseProductVariantManager(models.Manager):
    def get_queryset(self):
        return ProductVariantQuerySet(self.model)


ProductVariantManager = BaseProductVariantManager.from_queryset(ProductVariantQuerySet)


class AbstractProductVariant(models.Model):
    objects = ProductVariantManager()

    class Meta:
        abstract = True


class ProductVariantBase(models.base.ModelBase):
    """
    Metaclass for Product Variant
    """
    def __init__(cls, name, bases, dct):
        super(ProductVariantBase, cls).__init__(name, bases, dct)

        if not cls._meta.abstract:
            # register this type in the list of product content types
            PRODUCT_VARIANT_MODEL_CLASSES.append(cls)


class ProductVariant(AbstractProductVariant, ClusterableModel, metaclass=ProductVariantBase):
    product = ParentalKey(Product, related_name='variants')
    sku = models.CharField(_('SKU'), max_length=32, unique=True)
    name = models.CharField(_('name'), max_length=100, blank=True)
    price = models.DecimalField(_('price'), max_digits=12, decimal_places=2, blank=True, null=True)
    active = models.BooleanField(_('active'), default=True)

    weight = models.DecimalField(_('weight'), max_digits=12, decimal_places=2, help_text=_('value stored in grams'), blank=True, null=True)
    width = models.DecimalField(_('width'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)
    height = models.DecimalField(_('height'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)
    depth = models.DecimalField(_('depth'), max_digits=12, decimal_places=2, help_text=_('value stored in millimeters'), blank=True, null=True)

    stock = models.IntegerField(_('stock'), default=0)
    active = models.BooleanField(_('active'))

    created = models.DateTimeField(_('created on'), auto_now_add=True)
    modified = models.DateTimeField(_('modified on'), auto_now=True)

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='product_variants',
        on_delete=models.SET(get_default_product_variant_content_type)
    )

    panels = [
        FieldPanel('product'),
        FieldPanel('sku'),
        FieldPanel('name'),
        FieldPanel('price'),
        FieldPanel('stock')
    ]

    def get_details(self):
        """
        Should be overwritten on each specific task.
        """
        return {}

    @cached_property
    def specific(self):
        """
        Return this product variant in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = content_type.model_class()
        if model_class is None:
            # Cannot locate a model class for this content type. This might happen
            # if the codebase and database are out of sync (e.g. the model exists
            # on a different git branch and we haven't rolled back migrations before
            # switching branches); if so, the best we can do is return the page
            # unchanged.
            return self
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    def __init__(self, *args, **kwargs):
        super(ProductVariant, self).__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return self.specific.__str__()


if getattr(settings, 'WAGTAILCOMMERCE_ASYNC_THUMBNAILS', False):
    from wagtailcommerce.products.images import generate_renditions

    @receiver(models.signals.post_save, sender=Image)
    def image_post_save(sender, instance, created, **kwargs):
        # Generate renditions when Image Set image is saved.
        generate_renditions.delay(instance)

    WagtailImageModel = get_image_model(require_ready=False)

    @receiver(models.signals.post_save, sender=WagtailImageModel)
    def wagtail_image_post_save(sender, instance, created, **kwargs):
        # Generate renditions for product images when Wagtail image is saved
        for wagtailcommerce_image in instance.wagtailcommerce_images.all():
            generate_renditions.delay(wagtailcommerce_image)
