from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0003_college_sat_avg_college_undergrad_enrollment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='college',
            name='apply_status',
            field=models.CharField(
                choices=[
                    ('applying', 'Applying'), ('likely', 'Likely'),
                    ('considering', 'Considering'), ('unlikely', 'Unlikely'),
                    ('not_applying', 'Not Applying'), ('applied', 'Submitted'),
                    ('accepted', 'Accepted'), ('deferred', 'Deferred'),
                    ('waitlisted', 'Waitlisted'), ('rejected', 'Rejected'),
                    ('enrolled', 'Enrolled'),
                ],
                default='not_applying',
                max_length=20,
            ),
        ),
    ]
