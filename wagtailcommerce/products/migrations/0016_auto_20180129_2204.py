# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-30 01:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcommerce_products', '0015_auto_20180110_1657'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='image',
            options={'ordering': ['sort_order'], 'verbose_name': 'image', 'verbose_name_plural': 'images'},
        ),
    ]
