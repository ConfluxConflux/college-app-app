from django.contrib import admin
from .models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry


@admin.register(UCEntry)
class UCEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'core_activity']
    list_filter = ['category']
    search_fields = ['name', 'description']
    list_editable = ['order']


@admin.register(CommonAppActivity)
class CommonAppActivityAdmin(admin.ModelAdmin):
    list_display = ['organization', 'position', 'activity_type', 'order', 'core_activity']
    list_filter = ['activity_type']
    search_fields = ['organization', 'position', 'description']
    list_editable = ['order']


@admin.register(CommonAppHonor)
class CommonAppHonorAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'core_activity']
    search_fields = ['title']
    list_editable = ['order']


@admin.register(MITEntry)
class MITEntryAdmin(admin.ModelAdmin):
    list_display = ['org_name', 'category', 'role_award', 'order', 'core_activity']
    list_filter = ['category']
    search_fields = ['org_name', 'role_award', 'description']
    list_editable = ['order']
