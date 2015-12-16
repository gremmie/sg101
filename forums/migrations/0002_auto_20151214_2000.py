# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='groups',
            field=models.ManyToManyField(help_text=b'If groups are assigned to this category, only members of those groups can view this category.', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='forum',
            name='moderators',
            field=models.ManyToManyField(to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='user_ip',
            field=models.GenericIPAddressField(default=b'', null=True, blank=True),
        ),
    ]
