from django.contrib import admin
from .models import College, UserCollege


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'acceptance_rate', 'undergrad_enrollment']
    search_fields = ['name', 'city', 'state']


@admin.register(UserCollege)
class UserCollegeAdmin(admin.ModelAdmin):
    list_display = ['name', 'apply_status', 'location', 'app_platform', 'acceptance_rate']
    list_filter = ['apply_status']
    search_fields = ['display_name', 'college__name']
    list_editable = ['apply_status']
