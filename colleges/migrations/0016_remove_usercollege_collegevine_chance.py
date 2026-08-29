from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0015_seed_relevance_and_gender'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usercollege',
            name='collegevine_chance',
        ),
    ]
