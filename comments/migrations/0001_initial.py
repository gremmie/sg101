# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('comment', models.TextField(max_length=3000)),
                ('html', models.TextField(blank=True)),
                ('creation_date', models.DateTimeField()),
                ('ip_address', models.IPAddressField(verbose_name='IP Address')),
                ('is_public', models.BooleanField(default=True, help_text='Uncheck this field to make the comment invisible.')),
                ('is_removed', models.BooleanField(default=False, help_text='Check this field to replace the comment with a "This comment has been removed" message')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('creation_date',),
            },
        ),
        migrations.CreateModel(
            name='CommentFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('flag_date', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(to='comments.Comment',
                                              on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('flag_date',),
            },
        ),
    ]
