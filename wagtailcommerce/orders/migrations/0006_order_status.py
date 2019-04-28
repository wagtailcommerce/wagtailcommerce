# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-23 20:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcommerce_orders', '0005_order_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('payment_pending', 'Payment pending'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='payment_pending', max_length=30, verbose_name='status'),
        ),
    ]