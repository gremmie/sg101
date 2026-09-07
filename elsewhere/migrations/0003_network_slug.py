"""Give a network a stable key of its own.

A network used to be identified by slugify(name), recomputed every time the
lookup dict was built, so renaming one in the admin silently moved its key and
orphaned every profile row pointing at the old value. The slug is written down
once here and never derived again.

"""
from django.db import migrations, models
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    """Freeze each network's current derived key as its stored one."""
    for model_name in ('SocialNetwork', 'InstantMessenger'):
        model = apps.get_model('elsewhere', model_name)
        for network in model.objects.all():
            network.slug = slugify(network.name)
            network.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('elsewhere', '0002_alter_instantmessengerprofile_date_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetwork',
            name='slug',
            # db_index=False here: SlugField's default index and the
            # unique one added below are the same index on PostgreSQL.
            field=models.SlugField(db_index=False, default='', max_length=16),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='instantmessenger',
            name='slug',
            # db_index=False here: SlugField's default index and the
            # unique one added below are the same index on PostgreSQL.
            field=models.SlugField(db_index=False, default='', max_length=16),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='socialnetwork',
            name='slug',
            field=models.SlugField(max_length=16, unique=True),
        ),
        migrations.AlterField(
            model_name='instantmessenger',
            name='slug',
            field=models.SlugField(max_length=16, unique=True),
        ),
    ]
