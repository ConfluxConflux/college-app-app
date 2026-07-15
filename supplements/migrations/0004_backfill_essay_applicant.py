from django.db import migrations


def backfill_applicant(apps, schema_editor):
    """Adopt the owning college's applicant for essays that have none.

    Essays created by the import/seed commands never set applicant. Once the
    views filter on applicant, an essay without one becomes unreachable.
    """
    SupplementEssay = apps.get_model('supplements', 'SupplementEssay')
    for essay in SupplementEssay.objects.filter(applicant__isnull=True).select_related('college'):
        if essay.college and essay.college.applicant_id:
            essay.applicant_id = essay.college.applicant_id
            essay.save(update_fields=['applicant'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('supplements', '0003_add_uc_piq_common_essay'),
    ]

    operations = [
        migrations.RunPython(backfill_applicant, noop),
    ]
