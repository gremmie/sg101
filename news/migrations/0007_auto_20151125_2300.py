# -*- coding: utf-8 -*-

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '__first__'),
        ('news', '0006_category_forum_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='forums_topic',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='forums.Topic', help_text='Forum topic used for comments', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='forum_slug',
            field=models.CharField(default='', help_text='Identifies the forum to create comment threads in for stories in this category. If blank, no comment threads will be created for stories in this category.', max_length=80, blank=True),
            preserve_default=True,
        ),
    ]
