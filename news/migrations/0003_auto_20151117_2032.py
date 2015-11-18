# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_auto_20151117_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingstory',
            name='version',
            field=models.SmallIntegerField(default=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='version',
            field=models.SmallIntegerField(default=2),
            preserve_default=True,
        ),
    ]
