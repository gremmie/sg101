# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='ip_address',
            field=models.GenericIPAddressField(verbose_name='IP Address'),
        ),
    ]
