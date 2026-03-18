from django.contrib import admin
from .models import College


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ['name', 'apply_status', 'location', 'app_platform', 'acceptance_rate']
    list_filter = ['apply_status', 'app_platform']
    search_fields = ['name', 'location']
    list_editable = ['apply_status']
