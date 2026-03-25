from django import forms
from .models import UserCollege


class CollegeForm(forms.ModelForm):
    class Meta:
        model = UserCollege
        fields = [
            'display_name', 'apply_status', 'tier', 'acceptance_rate_override', 'collegevine_chance',
            'location', 'app_platform_override', 'academic_calendar_override',
            'cost_of_attendance_override', 'estimated_financial_aid', 'estimated_net_cost',
            'financial_aid_deadline_override', 'fafsa_required_override', 'css_profile_required_override',
            'requirements_style', 'intended_major', 'second_choice_major', 'third_choice_major',
            'restrictive_ea_override', 'ea_deadline_override', 'ed1_deadline_override', 'ed2_deadline_override',
            'rd_deadline_override', 'other_deadline_override',
            'self_report_sat_override', 'interview_override',
            'known_students', 'known_faculty',
            'toured', 'portal_info',
            'applicant_notes', 'parent_notes', 'random_notes',
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'input'}),
            'apply_status': forms.Select(attrs={'class': 'select'}),
            'tier': forms.TextInput(attrs={'class': 'input is-small', 'size': 4}),
            'acceptance_rate_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'collegevine_chance': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'location': forms.TextInput(attrs={'class': 'input'}),
            'app_platform_override': forms.TextInput(attrs={'class': 'input is-small'}),
            'academic_calendar_override': forms.TextInput(attrs={'class': 'input is-small'}),
            'cost_of_attendance_override': forms.TextInput(attrs={'class': 'input is-small'}),
            'estimated_financial_aid': forms.TextInput(attrs={'class': 'input is-small'}),
            'estimated_net_cost': forms.TextInput(attrs={'class': 'input is-small'}),
            'financial_aid_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'requirements_style': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'intended_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'second_choice_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'third_choice_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'restrictive_ea_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 3}),
            'ea_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'ed1_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'ed2_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'rd_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'other_deadline_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'self_report_sat_override': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'interview_override': forms.TextInput(attrs={'class': 'input is-small'}),
            'known_students': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
            'known_faculty': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
            'toured': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'portal_info': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
            'applicant_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
            'parent_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
            'random_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
        }


class CollegeQuickEditForm(forms.ModelForm):
    """Minimal form for inline cell editing."""
    class Meta:
        model = UserCollege
        fields = '__all__'
        exclude = ['order', 'latitude_override', 'longitude_override']
