from django.db import migrations


def seed_test_applicant(apps, schema_editor):
    Applicant = apps.get_model('core', 'Applicant')
    applicant = Applicant.objects.create(
        first_name='Jacob',
        last_name='Cohen',
        email='chromaticconflux@gmail.com',
        profile_picture='img/profile.jpeg',
    )

    # Backfill all existing rows to belong to the test applicant
    for model_label in [
        ('core', 'CoreActivity'),
        ('colleges', 'College'),
        ('activities', 'UCEntry'),
        ('activities', 'CommonAppActivity'),
        ('activities', 'CommonAppHonor'),
        ('activities', 'MITEntry'),
        ('supplements', 'SupplementEssay'),
    ]:
        Model = apps.get_model(*model_label)
        Model.objects.filter(applicant=None).update(applicant=applicant)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_applicant_coreactivity_applicant'),
        ('colleges', '0002_college_applicant'),
        ('activities', '0002_commonappactivity_applicant_commonapphonor_applicant_and_more'),
        ('supplements', '0002_supplementessay_applicant'),
    ]

    operations = [
        migrations.RunPython(seed_test_applicant, migrations.RunPython.noop),
    ]
