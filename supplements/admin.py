from django.contrib import admin
from .models import EssayCategory, SupplementEssay


@admin.register(EssayCategory)
class EssayCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_order']
    list_editable = ['sort_order']


@admin.register(SupplementEssay)
class SupplementEssayAdmin(admin.ModelAdmin):
    list_display = ['college', 'category', 'status', 'word_count']
    list_filter = ['status', 'category', 'college']
    search_fields = ['prompt', 'response']
