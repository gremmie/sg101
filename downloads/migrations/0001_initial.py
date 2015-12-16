# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import downloads.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extension', models.CharField(help_text=b'e.g. .txt', max_length=8)),
            ],
            options={
                'ordering': ('extension',),
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64)),
                ('description', models.TextField(blank=True)),
                ('count', models.IntegerField(default=0, blank=True)),
            ],
            options={
                'ordering': ('title',),
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Download',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('html', models.TextField(blank=True)),
                ('file', models.FileField(upload_to=downloads.models.download_path)),
                ('date_added', models.DateTimeField(db_index=True)),
                ('ip_address', models.IPAddressField(verbose_name=b'IP Address')),
                ('update_date', models.DateTimeField(db_index=True, blank=True)),
                ('hits', models.IntegerField(default=0)),
                ('average_score', models.FloatField(default=0.0)),
                ('total_votes', models.IntegerField(default=0)),
                ('is_public', models.BooleanField(default=False, db_index=True)),
                ('category', models.ForeignKey(to='downloads.Category')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PendingDownload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('html', models.TextField(blank=True)),
                ('file', models.FileField(upload_to=downloads.models.download_path)),
                ('date_added', models.DateTimeField(db_index=True)),
                ('ip_address', models.IPAddressField(verbose_name=b'IP Address')),
                ('update_date', models.DateTimeField(db_index=True, blank=True)),
                ('category', models.ForeignKey(to='downloads.Category')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('date_added',),
            },
        ),
        migrations.CreateModel(
            name='VoteRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vote_date', models.DateTimeField(auto_now_add=True)),
                ('download', models.ForeignKey(to='downloads.Download')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-vote_date',),
            },
        ),
    ]
