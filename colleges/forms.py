from django import forms
from .models import College


class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = [
            'name', 'apply_status', 'tier', 'acceptance_rate', 'collegevine_chance',
            'location', 'app_platform', 'terms',
            'cost_of_attendance', 'estimated_financial_aid', 'estimated_net_cost',
            'financial_aid_deadline', 'fafsa_required', 'css_profile_required',
            'requirements_style', 'intended_major', 'second_choice_major', 'third_choice_major',
            'restrictive_ea', 'ea_deadline', 'ed1_deadline', 'ed2_deadline',
            'rd_deadline', 'other_deadline',
            'self_report_sat', 'interview',
            'known_students', 'known_faculty',
            'toured', 'portal_info',
            'applicant_notes', 'parent_notes', 'random_notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'apply_status': forms.Select(attrs={'class': 'select'}),
            'tier': forms.TextInput(attrs={'class': 'input is-small', 'size': 4}),
            'acceptance_rate': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'collegevine_chance': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'location': forms.TextInput(attrs={'class': 'input'}),
            'app_platform': forms.TextInput(attrs={'class': 'input is-small'}),
            'terms': forms.TextInput(attrs={'class': 'input is-small'}),
            'cost_of_attendance': forms.TextInput(attrs={'class': 'input is-small'}),
            'estimated_financial_aid': forms.TextInput(attrs={'class': 'input is-small'}),
            'estimated_net_cost': forms.TextInput(attrs={'class': 'input is-small'}),
            'financial_aid_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'requirements_style': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'intended_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'second_choice_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'third_choice_major': forms.TextInput(attrs={'class': 'input is-small'}),
            'restrictive_ea': forms.TextInput(attrs={'class': 'input is-small', 'size': 3}),
            'ea_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'ed1_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'ed2_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'rd_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'other_deadline': forms.TextInput(attrs={'class': 'input is-small', 'size': 8}),
            'self_report_sat': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'interview': forms.TextInput(attrs={'class': 'input is-small'}),
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
        model = College
        fields = '__all__'
        exclude = ['order', 'latitude', 'longitude']
