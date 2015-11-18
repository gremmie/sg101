# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pendingstory',
            options={'ordering': ['-date_submitted'], 'verbose_name_plural': 'Pending Stories'},
        ),
        migrations.AlterModelOptions(
            name='story',
            options={'ordering': ['-date_submitted'], 'verbose_name': 'news story', 'verbose_name_plural': 'news stories'},
        ),
        migrations.AddField(
            model_name='pendingstory',
            name='admin_content',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pendingstory',
            name='long_markup',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pendingstory',
            name='short_markup',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pendingstory',
            name='version',
            field=models.SmallIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='story',
            name='admin_content',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='long_markup',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='short_markup',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='version',
            field=models.SmallIntegerField(default=0),
            preserve_default=False,
        ),
    ]
