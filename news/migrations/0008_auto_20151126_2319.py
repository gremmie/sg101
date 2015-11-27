# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0007_auto_20151125_2300'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingstory',
            name='short_markup',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='short_markup',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
