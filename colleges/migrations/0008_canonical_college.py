"""
Phase 1 migration: introduce canonical College model, rename old College → UserCollege,
rename fields that become override fields, and link all UserCollege rows to their
canonical College.
"""
from django.db import migrations, models
import django.db.models.deletion


def create_canonical_colleges(apps, schema_editor):
    """
    For each unique school name, create one canonical College row,
    then link all UserCollege rows to it.  Clear display_name where
    it already matches the canonical name (no need to store it twice).
    """
    UserCollege = apps.get_model('colleges', 'UserCollege')
    College = apps.get_model('colleges', 'College')

    # Known duplicates: two display_name variants that refer to the same school.
    # Map lowercased display_name → canonical name to use.
    DEDUP = {
        'mit': 'Massachusetts Institute of Technology (MIT)',
        'massachusetts institute of technology (mit)': 'Massachusetts Institute of Technology (MIT)',
        'uc irvine': 'UC Irvine (UCI)',
        'uc irvine (uci)': 'UC Irvine (UCI)',
        'csu fort collins': 'Colorado State',
        'colorado state': 'Colorado State',
    }

    canonical_map = {}  # canonical_name → College instance
    for uc in UserCollege.objects.all():
        raw = (uc.display_name or '').strip()
        canonical_name = DEDUP.get(raw.lower(), raw)
        if not canonical_name:
            canonical_name = '(unnamed)'
        if canonical_name not in canonical_map:
            canonical_map[canonical_name] = College.objects.create(name=canonical_name, unitid=None)

    for uc in UserCollege.objects.all():
        raw = (uc.display_name or '').strip()
        canonical_name = DEDUP.get(raw.lower(), raw) or '(unnamed)'
        uc.college = canonical_map[canonical_name]
        # Clear display_name when it matches canonical (redundant to store)
        if raw.lower() == canonical_name.lower():
            uc.display_name = ''
        uc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0007_add_difficulty_field'),
    ]

    operations = [
        # 1. Rename the old College model to UserCollege
        migrations.RenameModel('College', 'UserCollege'),

        # 2. Rename name → display_name (becomes per-user label)
        migrations.RenameField('UserCollege', 'name', 'display_name'),

        # 3. Rename fields that become overrides of canonical data
        migrations.RenameField('UserCollege', 'acceptance_rate',     'acceptance_rate_override'),
        migrations.RenameField('UserCollege', 'latitude',            'latitude_override'),
        migrations.RenameField('UserCollege', 'longitude',           'longitude_override'),
        migrations.RenameField('UserCollege', 'app_platform',        'app_platform_override'),
        migrations.RenameField('UserCollege', 'terms',               'academic_calendar_override'),
        migrations.RenameField('UserCollege', 'fafsa_required',      'fafsa_required_override'),
        migrations.RenameField('UserCollege', 'css_profile_required','css_profile_required_override'),
        migrations.RenameField('UserCollege', 'sat_avg',             'sat_avg_override'),
        migrations.RenameField('UserCollege', 'undergrad_enrollment','undergrad_enrollment_override'),
        migrations.RenameField('UserCollege', 'restrictive_ea',      'restrictive_ea_override'),
        migrations.RenameField('UserCollege', 'ea_deadline',         'ea_deadline_override'),
        migrations.RenameField('UserCollege', 'ed1_deadline',        'ed1_deadline_override'),
        migrations.RenameField('UserCollege', 'ed2_deadline',        'ed2_deadline_override'),
        migrations.RenameField('UserCollege', 'rd_deadline',         'rd_deadline_override'),
        migrations.RenameField('UserCollege', 'other_deadline',      'other_deadline_override'),
        migrations.RenameField('UserCollege', 'financial_aid_deadline', 'financial_aid_deadline_override'),
        migrations.RenameField('UserCollege', 'cost_of_attendance',  'cost_of_attendance_override'),
        migrations.RenameField('UserCollege', 'interview',           'interview_override'),
        migrations.RenameField('UserCollege', 'self_report_sat',     'self_report_sat_override'),

        # 4. Create the new canonical College model
        migrations.CreateModel(
            name='College',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unitid', models.CharField(blank=True, null=True, max_length=20, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('city', models.CharField(blank=True, max_length=200)),
                ('state', models.CharField(blank=True, max_length=10)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('tuition_instate', models.IntegerField(blank=True, null=True)),
                ('fees_instate', models.IntegerField(blank=True, null=True)),
                ('tuition_outofstate', models.IntegerField(blank=True, null=True)),
                ('fees_outofstate', models.IntegerField(blank=True, null=True)),
                ('room', models.IntegerField(blank=True, null=True)),
                ('board', models.IntegerField(blank=True, null=True)),
                ('total_cost', models.IntegerField(blank=True, null=True)),
                ('avg_grant_aid', models.IntegerField(blank=True, null=True)),
                ('academic_calendar', models.CharField(blank=True, max_length=50)),
                ('acceptance_rate', models.CharField(blank=True, max_length=20)),
                ('sat_avg', models.IntegerField(blank=True, null=True)),
                ('undergrad_enrollment', models.IntegerField(blank=True, null=True)),
                ('app_platform', models.CharField(blank=True, max_length=50)),
                ('fafsa_required', models.BooleanField(blank=True, null=True)),
                ('css_profile_required', models.BooleanField(blank=True, null=True)),
                ('proof_acceptances', models.IntegerField(default=0)),
                ('restrictive_ea', models.CharField(blank=True, max_length=5)),
                ('ea_deadline', models.CharField(blank=True, max_length=20)),
                ('ed1_deadline', models.CharField(blank=True, max_length=20)),
                ('ed2_deadline', models.CharField(blank=True, max_length=20)),
                ('rd_deadline', models.CharField(blank=True, max_length=20)),
                ('other_deadline', models.CharField(blank=True, max_length=20)),
                ('financial_aid_deadline', models.CharField(blank=True, max_length=20)),
                ('cost_of_attendance', models.CharField(blank=True, max_length=100)),
                ('interview', models.CharField(blank=True, max_length=50)),
                ('self_report_sat', models.CharField(blank=True, max_length=20)),
            ],
            options={'ordering': ['name']},
        ),

        # 5. Add FK from UserCollege to canonical College
        migrations.AddField(
            model_name='UserCollege',
            name='college',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='user_colleges',
                to='colleges.college',
            ),
        ),

        # 6. Add new override fields that have no old equivalent
        migrations.AddField('UserCollege', 'city_override',
            models.CharField(blank=True, max_length=200)),
        migrations.AddField('UserCollege', 'state_override',
            models.CharField(blank=True, max_length=10)),
        migrations.AddField('UserCollege', 'country_override',
            models.CharField(blank=True, max_length=100)),
        migrations.AddField('UserCollege', 'tuition_instate_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'fees_instate_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'tuition_outofstate_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'fees_outofstate_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'room_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'board_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'total_cost_override',
            models.IntegerField(blank=True, null=True)),
        migrations.AddField('UserCollege', 'avg_grant_aid_override',
            models.IntegerField(blank=True, null=True)),

        # 6b. Fix ordering now that 'name' field was renamed to 'display_name'
        migrations.AlterModelOptions(
            name='UserCollege',
            options={'ordering': ['order', 'display_name']},
        ),

        # 7. Data migration: create canonical College rows and link UserCollege rows
        migrations.RunPython(create_canonical_colleges, migrations.RunPython.noop),
    ]
