from __future__ import absolute_import, unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtailcommerce.payments.query import PaymentMethodQuerySet


PAYMENT_METHOD_MODEL_CLASSES = []


def get_default_payment_method_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    return ContentType.objects.get_for_model(PaymentMethod)


class BasePaymentMethodManager(models.Manager):
    def get_queryset(self):
        return PaymentMethodQuerySet(self.model)


PaymentMethodManager = BasePaymentMethodManager.from_queryset(PaymentMethodQuerySet)


class PaymentMethodBase(models.base.ModelBase):
    """
    Metaclass for PaymentMethod
    """
    def __init__(cls, name, bases, dct):
        super(PaymentMethodBase, cls).__init__(name, bases, dct)

        if not cls._meta.abstract:
            # register this type in the list of product content types
            PAYMENT_METHOD_MODEL_CLASSES.append(cls)


class AbstractPaymentMethod(models.Model):
    """
    Payment Method abstract base
    """
    objects = PaymentMethodManager()

    class Meta:
        abstract = True
        verbose_name = _('Payment method')
        verbose_name_plural = _('Payment methods')


class PaymentMethod(AbstractPaymentMethod, ClusterableModel, metaclass=PaymentMethodBase):
    """
    Payment Method root model
    """
    identifier = models.CharField(
        _('Identifier'), max_length=255,
        help_text=_('Internal name to uniquely identify this payment method'))
    display_name = models.CharField(
        _('Display name'), max_length=255, blank=True,
        help_text=_('How the payment method will be displayed on the frontend. If empty, identifier will be used instead'))
    active = models.BooleanField(_('Active'), default=True)

    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name=_('content type'),
        related_name='payment_methods',
        on_delete=models.SET(get_default_payment_method_content_type)
    )

    created = models.DateTimeField(_('created on'), auto_now_add=True)
    modified = models.DateTimeField(_('modified on'), auto_now=True)

    def __str__(self):
        return self.identifier

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
        elif isinstance(self, model_class):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)
