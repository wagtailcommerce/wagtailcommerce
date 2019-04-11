from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel


class Currency(models.Model):
    name = models.CharField(_("name"), max_length=128)
    code = models.CharField(_("code"), max_length=3, help_text=_("ISO 4217 3 letter code"))
    symbol = models.CharField(_("symbol"), max_length=30, help_text=_("As displayed on frontend"))

    panels = [
        FieldPanel('name'),
        FieldPanel('code'),
        FieldPanel('symbol')
    ]

    def __str__(self):
        return "{} ({})".format(self.name, self.code)

    class Meta:
        verbose_name = _("currency")
        verbose_name_plural = _("currencies")


class Store(models.Model):
    name = models.CharField(_("name"), max_length=128)
    site = models.OneToOneField('wagtailcore.Site', blank=True, null=True,
                                on_delete=models.SET_NULL, related_name="store")
    # Options
    checkout_enabled = models.BooleanField(_('checkout enabled'), default=True)

    # TODO: allow multiple/dynamic tax rates
    tax_rate = models.DecimalField(_("tax rate (percentage)"), decimal_places=2, max_digits=5,
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])

    # TODO: allow multiple currencies
    currency = models.ForeignKey(Currency, related_name="stores")

    panels = [
        FieldPanel('name'),
        FieldPanel('site'),
        FieldPanel('checkout_enabled'),
        FieldPanel('currency'),
        FieldPanel('tax_rate'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("store")
        verbose_name_plural = _("stores")
