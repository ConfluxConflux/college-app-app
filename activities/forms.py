from django import forms
from .models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from core.models import CoreActivity


class UCEntryForm(forms.ModelForm):
    class Meta:
        model = UCEntry
        exclude = ['order']
        widgets = {
            'core_activity': forms.Select(attrs={'class': 'select is-small'}),
            'category': forms.Select(attrs={'class': 'select'}),
            'name': forms.TextInput(attrs={'class': 'input'}),
            'background': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 3,
                'x-model': 'background',
                'maxlength': 250,
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 4,
                'x-model': 'description',
                'maxlength': 350,
            }),
            'hours_per_week': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'weeks_per_year': forms.TextInput(attrs={'class': 'input is-small', 'size': 6}),
            'recognition_level': forms.TextInput(attrs={'class': 'input is-small'}),
            'earnings_usage': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2, 'maxlength': 250}),
            'personal_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['core_activity'].queryset = CoreActivity.objects.all()
        self.fields['core_activity'].required = False
        self.fields['core_activity'].empty_label = '— Link to activity hub —'


class CommonAppActivityForm(forms.ModelForm):
    class Meta:
        model = CommonAppActivity
        exclude = ['order']
        widgets = {
            'core_activity': forms.Select(attrs={'class': 'select is-small'}),
            'activity_type': forms.Select(attrs={'class': 'select'}),
            'position': forms.TextInput(attrs={
                'class': 'input', 'maxlength': 50,
                'x-model': 'position',
            }),
            'organization': forms.TextInput(attrs={
                'class': 'input', 'maxlength': 100,
                'x-model': 'organization',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 3, 'maxlength': 150,
                'x-model': 'description',
            }),
            'hours_per_week': forms.NumberInput(attrs={'class': 'input is-small', 'style': 'width:80px'}),
            'weeks_per_year': forms.NumberInput(attrs={'class': 'input is-small', 'style': 'width:80px'}),
            'personal_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['core_activity'].queryset = CoreActivity.objects.all()
        self.fields['core_activity'].required = False
        self.fields['core_activity'].empty_label = '— Link to activity hub —'


class CommonAppHonorForm(forms.ModelForm):
    class Meta:
        model = CommonAppHonor
        exclude = ['order']
        widgets = {
            'core_activity': forms.Select(attrs={'class': 'select is-small'}),
            'title': forms.TextInput(attrs={'class': 'input'}),
            'personal_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['core_activity'].queryset = CoreActivity.objects.all()
        self.fields['core_activity'].required = False
        self.fields['core_activity'].empty_label = '— Link to activity hub —'


class MITEntryForm(forms.ModelForm):
    class Meta:
        model = MITEntry
        exclude = ['order']
        widgets = {
            'core_activity': forms.Select(attrs={'class': 'select is-small'}),
            'category': forms.Select(attrs={'class': 'select'}),
            'org_name': forms.TextInput(attrs={'class': 'input'}),
            'role_award': forms.TextInput(attrs={'class': 'input'}),
            'participation_period': forms.TextInput(attrs={'class': 'input is-small'}),
            'hours_per_week': forms.NumberInput(attrs={'class': 'input is-small', 'style': 'width:80px'}),
            'weeks_per_year': forms.NumberInput(attrs={'class': 'input is-small', 'style': 'width:80px'}),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 3,
                'x-model': 'description',
            }),
            'personal_notes': forms.Textarea(attrs={'class': 'textarea is-small', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['core_activity'].queryset = CoreActivity.objects.all()
        self.fields['core_activity'].required = False
        self.fields['core_activity'].empty_label = '— Link to activity hub —'
