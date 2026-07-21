# Django stopped forcing blank=True on BooleanField, so the field's explicit
# blank=True now serializes and the state needs to catch up. blank is
# validation-only: on MySQL this emits no SQL at all. SQLite still rebuilds the
# table, because its schema editor does that for any AlterField.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0002_auto_20151214_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='locked',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='topic',
            name='sticky',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
