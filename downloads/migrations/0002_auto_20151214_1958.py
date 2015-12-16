# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('downloads', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='download',
            name='ip_address',
            field=models.GenericIPAddressField(verbose_name=b'IP Address'),
        ),
        migrations.AlterField(
            model_name='pendingdownload',
            name='ip_address',
            field=models.GenericIPAddressField(verbose_name=b'IP Address'),
        ),
    ]
