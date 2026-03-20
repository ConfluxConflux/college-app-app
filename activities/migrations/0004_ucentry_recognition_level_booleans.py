from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0003_alter_commonappactivity_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ucentry',
            name='recognition_level',
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_school',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_city',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_state',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_regional',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_national',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ucentry',
            name='level_international',
            field=models.BooleanField(default=False),
        ),
    ]
