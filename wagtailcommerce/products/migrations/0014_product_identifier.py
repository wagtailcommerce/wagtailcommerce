# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import shortuuid

from django.db import migrations, models


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Product = apps.get_model('wagtailcommerce_products', 'Product')
    db_alias = schema_editor.connection.alias

    for product in Product.objects.using(db_alias).all():
        shortuuid.set_alphabet('abcdefghijklmnopqrstuvwxyz1234567890')

        while True:
            uuid = shortuuid.uuid()[:8]
            if not Product.objects.filter(identifier=uuid).exists():
                break

        product.identifier = uuid
        product.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcommerce_products', '0013_product_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='identifier',
            field=models.CharField(db_index=True, default='', max_length=8, verbose_name='identifier'),
            preserve_default=False,
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]
