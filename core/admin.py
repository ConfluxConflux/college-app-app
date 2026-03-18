from django.contrib import admin
from .models import CoreActivity


@admin.register(CoreActivity)
class CoreActivityAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    search_fields = ['name', 'full_description']
    list_editable = ['order']
