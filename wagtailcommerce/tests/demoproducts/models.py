from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Orderable

from wagtailcommerce.products.models import Product, ProductVariant


class CustomShoe(Product):
    allowed_variants = [
        'demoproducts.CustomShoeVariant'
    ]

    class Meta:
        verbose_name = _('shoe')
        verbose_name_plural = _('shoes')


class ShoeColor(models.Model):
    name = models.CharField(_('name'), max_length=30)

    class Meta:
        verbose_name = _('shoe color')
        verbose_name_plural = _('shoe colors')


class ShoeSize(models.Model):
    us_size = models.CharField(_('us size'), max_length=10)

    class Meta:
        verbose_name = _('shoe size')
        verbose_name_plural = _('shoe sizes')


class CustomShoeVariant(ProductVariant):
    size = models.ForeignKey(ShoeSize, related_name='shoe_variants')
    color = models.ForeignKey(ShoeColor, related_name='shoe_variants')
    main_image = models.ForeignKey('wagtailimages.Image', verbose_name=_('image'), null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='+')

    class Meta:
        verbose_name = _('shoe variant')
        verbose_name_plural = _('shoe variants')


class ShoeVariantImage(Orderable):
    variant = ParentalKey('wagtailcommerce_tests_demoproducts.CustomShoeVariant', related_name='images')
    image = models.ForeignKey('wagtailimages.Image', verbose_name=_('image'), null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='+')

    class Meta:
        verbose_name = _('shoe variant image')
        verbose_name_plural = _('shoe variant images')
