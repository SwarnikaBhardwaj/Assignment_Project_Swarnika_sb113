from django.contrib import admin
from .models import Category, Transaction, Goal


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user']
    list_filter = ['type', 'user']
    search_fields = ['name']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['amount', 'category', 'date', 'merchant', 'user']
    list_filter = ['category', 'date', 'user']
    search_fields = ['merchant', 'notes']
    date_hierarchy = 'date'


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_amount', 'current_amount', 'deadline', 'user', 'progress_display']
    list_filter = ['user', 'deadline']
    search_fields = ['name']
    def progress_display(self, obj):
        return f"{obj.progress():.1f}%"

    progress_display.short_description = 'Progress'

from django.contrib import admin

# Register your models here.
