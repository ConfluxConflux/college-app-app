from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0004_ucentry_recognition_level_booleans'),
    ]

    operations = [
        migrations.AddField(
            model_name='ucentry',
            name='estimator_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
