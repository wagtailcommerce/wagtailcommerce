# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-30 01:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcommerce_promotions', '0003_auto_20180129_2233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='valid_until',
            field=models.DateTimeField(blank=True, null=True, verbose_name='valid until'),
        ),
    ]