from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField

from django.contrib.auth import get_user_model


class Address(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='addresses', blank=True, null=True)
    deleted = models.BooleanField(_('Deleted'), default=False)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    modified = models.DateTimeField(_('Modified'), auto_now=True)
    default_shipping_address = models.BooleanField(_('Default shipping address'), default=False)
    default_billing_address = models.BooleanField(_('Default billing address'), default=False)

    name = models.CharField(_('Name'), max_length=255, blank=True)
    last_name = models.CharField(_('Last name'), max_length=255, blank=True)
    street_address_1 = models.CharField(_('Address (line 1)'), max_length=255, blank=True)
    street_address_2 = models.CharField(_('Address (line 2)'), max_length=255, blank=True)
    street_number = models.CharField(_('Street number'), max_length=255, blank=True)
    floor = models.CharField(_('Floor'), max_length=255, blank=True)
    apartment_number = models.CharField(_('Apartment number'), max_length=255, blank=True)
    city = models.CharField(_('City / Town'), max_length=255, blank=True)
    district = models.CharField(_('District / Neighborhood'), max_length=255, blank=True)
    country_area = models.CharField(_('State / Province / Region'), max_length=255, blank=True)
    country = CountryField(_('Country'), blank=True)
    postal_code = models.CharField(_('Postal code'), max_length=64, blank=True)
    phone = models.CharField(_('Phone number'), max_length=30, blank=True)
    security_access_code = models.CharField(_('Security access code'), max_length=150, blank=True)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return '{} {}'.format(self.name, self.last_name)

    @property
    def full_street(self):
        street = '{} {}'.format(self.street_address_1, self.street_number)

        if self.floor:
            street = '{} {} {}'.format(street, self.floor, self.apartment_number)

        return street

    class Meta:
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ('-default_shipping_address', '-default_billing_address', '-created', )
