# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20151117_2032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingstory',
            name='long_text',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='long_text',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
    ]
