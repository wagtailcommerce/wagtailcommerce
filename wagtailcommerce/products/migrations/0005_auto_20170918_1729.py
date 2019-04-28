# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-18 20:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcommerce_products', '0004_auto_20170918_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='products', to='wagtailcommerce_products.Category'),
        ),
    ]