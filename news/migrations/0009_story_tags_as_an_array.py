"""Move story tags from a space-separated string plus a join table onto an
array column on the story itself.

The old column is renamed rather than dropped: it is the only copy of what an
author actually typed, and it costs nothing to keep until the tagging tables it
was kept in step with are dropped too.

"""
import django.contrib.postgres.fields
import django.contrib.postgres.indexes
from django.db import migrations, models

import news.models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0008_auto_20151126_2319'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pendingstory',
            old_name='tags',
            new_name='tags_legacy',
        ),
        migrations.RenameField(
            model_name='story',
            old_name='tags',
            new_name='tags_legacy',
        ),
        migrations.AddField(
            model_name='pendingstory',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                help_text='Separate tags with commas, e.g. surf, reverb, twang.',
                size=None,
                validators=[news.models.validate_tags]),
        ),
        migrations.AddField(
            model_name='story',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                help_text='Separate tags with commas, e.g. surf, reverb, twang.',
                size=None,
                validators=[news.models.validate_tags]),
        ),
        migrations.AddIndex(
            model_name='pendingstory',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['tags'], name='news_pendingstory_tags_gin'),
        ),
        migrations.AddIndex(
            model_name='story',
            index=django.contrib.postgres.indexes.GinIndex(
                fields=['tags'], name='news_story_tags_gin'),
        ),
    ]
