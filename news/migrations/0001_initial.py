# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64)),
                ('icon', models.ImageField(upload_to=b'news/categories/', blank=True)),
            ],
            options={
                'ordering': ('title',),
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PendingStory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('short_text', models.TextField()),
                ('long_text', models.TextField(blank=True)),
                ('date_submitted', models.DateTimeField(db_index=True)),
                ('allow_comments', models.BooleanField(default=True)),
                ('tags', tagging.fields.TagField(max_length=255, blank=True)),
                ('front_page_expiration', models.DateField(null=True, blank=True)),
                ('update_date', models.DateTimeField(db_index=True, blank=True)),
                ('priority', models.IntegerField(default=0, db_index=True, blank=True)),
                ('meta_description', models.TextField(blank=True)),
                ('category', models.ForeignKey(to='news.Category')),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-date_submitted',),
                'verbose_name_plural': 'Pending Stories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('short_text', models.TextField()),
                ('long_text', models.TextField(blank=True)),
                ('date_submitted', models.DateTimeField(db_index=True)),
                ('allow_comments', models.BooleanField(default=True)),
                ('tags', tagging.fields.TagField(max_length=255, blank=True)),
                ('front_page_expiration', models.DateField(null=True, blank=True)),
                ('update_date', models.DateTimeField(db_index=True, blank=True)),
                ('priority', models.IntegerField(default=0, db_index=True, blank=True)),
                ('meta_description', models.TextField(blank=True)),
                ('category', models.ForeignKey(to='news.Category')),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-date_submitted',),
                'verbose_name': 'news story',
                'verbose_name_plural': 'news stories',
            },
            bases=(models.Model,),
        ),
    ]
