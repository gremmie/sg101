# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('oembed', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('embed', models.ForeignKey(to='oembed.Oembed',
                                            on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('slug', models.SlugField(max_length=80)),
                ('position', models.IntegerField(default=0, blank=True)),
                ('groups', models.ManyToManyField(help_text=b'If groups are assigned to this category, only members of those groups can view this category.', to='auth.Group', null=True, blank=True)),
            ],
            options={
                'ordering': ('position',),
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='FlaggedPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flag_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('flag_date',),
            },
        ),
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('slug', models.SlugField(max_length=80)),
                ('description', models.TextField(default=b'', blank=True)),
                ('position', models.IntegerField(default=0, blank=True)),
                ('topic_count', models.IntegerField(default=0, blank=True)),
                ('post_count', models.IntegerField(default=0, blank=True)),
                ('category', models.ForeignKey(related_name='forums',
                                               to='forums.Category',
                                               on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='ForumLastVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('begin_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('forum', models.ForeignKey(to='forums.Forum',
                                            on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-end_date',),
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(db_index=True)),
                ('update_date', models.DateTimeField(db_index=True)),
                ('body', models.TextField()),
                ('html', models.TextField()),
                ('user_ip', models.IPAddressField(default=b'', null=True, blank=True)),
                ('attachments', models.ManyToManyField(to='oembed.Oembed', through='forums.Attachment')),
            ],
            options={
                'ordering': ('creation_date',),
                'get_latest_by': 'creation_date',
                'verbose_name': 'forum post',
                'verbose_name_plural': 'forum posts',
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('creation_date', models.DateTimeField(db_index=True)),
                ('view_count', models.IntegerField(default=0, blank=True)),
                ('sticky', models.BooleanField(default=False)),
                ('locked', models.BooleanField(default=False)),
                ('post_count', models.IntegerField(default=0, blank=True)),
                ('update_date', models.DateTimeField(db_index=True)),
                ('bookmarkers', models.ManyToManyField(related_name='favorite_topics', verbose_name=b'bookmarkers', to=settings.AUTH_USER_MODEL, blank=True)),
                ('forum', models.ForeignKey(related_name='topics',
                                            to='forums.Forum',
                                            on_delete=models.CASCADE)),
                ('last_post', models.OneToOneField(related_name='parent_topic',
                                                   null=True, blank=True,
                                                   to='forums.Post',
                                                   on_delete=models.CASCADE)),
                ('subscribers', models.ManyToManyField(related_name='subscriptions', verbose_name=b'subscribers', to=settings.AUTH_USER_MODEL, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-sticky', '-update_date'),
            },
        ),
        migrations.CreateModel(
            name='TopicLastVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('last_visit', models.DateTimeField(db_index=True)),
                ('topic', models.ForeignKey(to='forums.Topic',
                                            on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-last_visit',),
            },
        ),
        migrations.AddField(
            model_name='post',
            name='topic',
            field=models.ForeignKey(related_name='posts', to='forums.Topic',
                                    on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(related_name='posts',
                                    to=settings.AUTH_USER_MODEL,
                                    on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='forum',
            name='last_post',
            field=models.OneToOneField(related_name='parent_forum', null=True,
                                       blank=True, to='forums.Post',
                                       on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='forum',
            name='moderators',
            field=models.ManyToManyField(to='auth.Group', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='flaggedpost',
            name='post',
            field=models.ForeignKey(to='forums.Post', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='flaggedpost',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                    on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='attachment',
            name='post',
            field=models.ForeignKey(to='forums.Post', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='topiclastvisit',
            unique_together=set([('user', 'topic')]),
        ),
        migrations.AlterUniqueTogether(
            name='forumlastvisit',
            unique_together=set([('user', 'forum')]),
        ),
    ]
