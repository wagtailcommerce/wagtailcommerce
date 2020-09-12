from __future__ import absolute_import, unicode_literals
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from django_countries.fields import CountryField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.fields import RichTextField
from wagtail.core.models import Orderable
from wagtail.images.edit_handlers import ImageChooserPanel

from wagtailcommerce.shipping.query import ShipmentQuerySet

SHIPPING_METHOD_MODEL_CLASSES = []
SHIPMENT_MODEL_CLASSES = []


def get_default_shipping_method_content_type():
    """
    Returns the content type to use as a default for shipping methods whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(ShippingMethod)


def get_default_shipment_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(Shipment)


class ShippingMethodQueryset(models.QuerySet):
    pass


class BaseShippingMethodManager(models.Manager):
    def get_queryset(self):
        return ShippingMethodQueryset(self.model)

    def for_user(self, user):
        """
        Returns shipping methods available a particular user
        """
        if user.is_superuser:
            return self.filter(models.Q(enabled_for_administrators=True) | models.Q(enabled=True))

        return self.filter(enabled=True)

    def for_shipping_address(self, shipping_address, user):
        """
        Returns shipping methods available for a shipping address and user
        """
        included_shipping_method_pks = []

        for shipping_method in self.for_user(user):
            if shipping_method.is_available(shipping_address, user):
                included_shipping_method_pks.append(shipping_method.pk)

        return self.filter(pk__in=included_shipping_method_pks)


ShippingMethodManager = BaseShippingMethodManager.from_queryset(ShippingMethodQueryset)


class ShippingMethodBase(models.base.ModelBase):
    """
    Metaclass for Shipping Method
    """
    ordering = ['sort_order']

    def __init__(cls, name, bases, dct):
        super(ShippingMethodBase, cls).__init__(name, bases, dct)

        if not cls._meta.abstract:
            # register this type in the list of page content types
            SHIPPING_METHOD_MODEL_CLASSES.append(cls)


class AbstractShippingMethod(models.Model):
    """
    Abstract superclass for Page. According to Django's inheritance rules, managers set on
    abstract models are inherited by subclasses, but managers set on concrete models that are extended
    via multi-table inheritance are not. We therefore need to attach PageManager to an abstract
    superclass to ensure that it is retained by subclasses of Page.
    """
    objects = ShippingMethodManager()

    class Meta:
        abstract = True


class ShippingMethod(AbstractShippingMethod, ClusterableModel, metaclass=ShippingMethodBase):
    title = models.CharField(_('title'), max_length=200)
    display_title = models.CharField(
        _('display title'), max_length=200, blank=True,
        help_text=_('Displayed on frontends instead of the title field'))
    description = models.CharField(_('description'), max_length=200, blank=True)
    free_shipping_above_amount = models.DecimalField(
        _('free shipping above amount'), decimal_places=2, max_digits=12, null=True, blank=True,
        help_text=_('If the cart total is above this amount, shipping will be free')
    )
    enabled = models.BooleanField(_('enabled'))
    enabled_for_administrators = models.BooleanField(
        _('enabled for administrators'),
        help_text=_('It will be available for admin users even if it\'s not enabled for the general public')
    )
    store = models.ForeignKey('wagtailcommerce_stores.Store', related_name='shipping_methods', on_delete=models.PROTECT)
    sort_order = models.PositiveIntegerField(
        _('sort order'),
        help_text=_('Shipping methods with a higher sort order will appear closer to the end on listings')
    )

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='shipping_methods',
        on_delete=models.SET(get_default_shipping_method_content_type)
    )

    panels = [
        FieldPanel('store'),
        FieldPanel('title'),
        FieldPanel('display_title'),
        FieldPanel('description'),
        FieldPanel('sort_order'),
        FieldPanel('free_shipping_above_amount'),
        FieldPanel('enabled'),
        FieldPanel('enabled_for_administrators'),
        InlinePanel('shipping_regions', heading=_('shipping regions'))
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;

            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

    def __str__(self):
        return self.title


    def is_available(self, shipping_address, user):
        """
        Determines if it should be available for a specified shipping address
        """
        if not self.enabled and not (self.enabled_for_administrators and user and user.is_superuser):
            return False

        has_regions = self.shipping_regions.exists()

        if has_regions:
            if not shipping_address:
                return False

            if not self.shipping_regions.filter(
                postal_codes__regex=r'(:?^|,)({0})(:?$|,|\s)'.format(shipping_address.postal_code)
            ).exists():
                return False

        return True


    def get_shipping_cost(self, cart, shipping_address):
        """
        Return the shipping cost for a specified shipping address
        """
        shipping_cost = self.calculate_shipping_cost(cart, shipping_address)

        if self.free_shipping_above_amount:
            cart_total = cart.get_total()

            if cart_total > self.free_shipping_above_amount:
                shipping_cost['discount'] = shipping_cost['cost']
                shipping_cost['total'] = Decimal('0')

        return shipping_cost


    def calculate_shipping_cost(self, cart, shipping_address):
        """
        Should be replaced by each shipping method. Does the actual method-specific calculation.
        """
        raise NotImplementedError

    def generate_shipment(self, order):
        """
        Generate the actual shipment order
        """
        raise NotImplementedError

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


class ShippingRegion(Orderable, models.Model):
    shipping_method = ParentalKey(ShippingMethod, on_delete=models.CASCADE, related_name='shipping_regions')
    country = CountryField(_('Country'), blank=True)
    postal_codes = models.TextField(
        _('postal codes'), blank=True,
        help_text=_('Enter postal codes separated by commas, e.g. "3547,7894,45 545,as 51 d"')
    )

    class Meta(Orderable.Meta):
        verbose_name = _('shipping region')
        verbose_name_plural = _('shipping regions')


class BaseShipmentManager(models.Manager):
    def get_queryset(self):
        return ShipmentQuerySet(self.model)


ShipmentManager = BaseShipmentManager.from_queryset(ShipmentQuerySet)


class ShipmentBase(models.base.ModelBase):
    """
    Metaclass for Shipment
    """
    def __init__(cls, name, bases, dct):
        super(ShipmentBase, cls).__init__(name, bases, dct)

        if not cls._meta.abstract:
            # register this type in the list of product content types
            SHIPMENT_MODEL_CLASSES.append(cls)


class AbstractShipment(models.Model):
    objects = ShipmentManager()

    class Meta:
        abstract = True


class Shipment(AbstractShipment, ClusterableModel, metaclass=ShipmentBase):
    order = ParentalKey('wagtailcommerce_orders.Order', related_name='shipments')
    shipping_method = models.ForeignKey(ShippingMethod, related_name='shipments', on_delete=models.PROTECT)
    tracking_code = models.CharField(_('tracking code'), max_length=255, blank=True)
    tracking_link = models.CharField(_('tracking link'), max_length=255, blank=True)
    shipping_label = models.FileField(verbose_name=_('shipping label'), upload_to='shipping_labels/', blank=True)

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='shipments',
        on_delete=models.SET(get_default_shipment_content_type)
    )

    created = models.DateTimeField(_('created on'), auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            # this model is being newly created
            # rather than retrieved from the db;
            if not self.content_type_id:
                # set content type to correctly represent the model class
                # that this was created as
                self.content_type = ContentType.objects.get_for_model(self)

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

        if isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    class Meta:
        verbose_name = _('shipment')
        verbose_name_plural = _('shipments')


class WithStandardLabelGeneration(models.Model):
    generate_shipping_label = models.BooleanField(_('generate shipping label'))
    label_logo = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_('label logo'),
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='wagtailcommerce_images'
    )
    label_heading = RichTextField(verbose_name=_('label heading'))

    panels = [
        FieldPanel('generate_shipping_label'),
        ImageChooserPanel('label_logo'),
        FieldPanel('label_heading'),
    ]

    class Meta:
        abstract = True
