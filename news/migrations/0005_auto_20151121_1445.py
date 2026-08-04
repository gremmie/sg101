# -*- coding: utf-8 -*-

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_auto_20151120_2228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingstory',
            name='short_text',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='story',
            name='short_text',
            field=models.TextField(default='', blank=True),
            preserve_default=True,
        ),
    ]
