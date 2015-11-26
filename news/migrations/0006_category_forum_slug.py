# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_auto_20151121_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='forum_slug',
            field=models.CharField(default=b'', help_text=b'Identifies the forum to create comment threads in for stories in this category', max_length=80, blank=True),
            preserve_default=True,
        ),
    ]
