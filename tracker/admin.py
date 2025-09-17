from django.contrib import admin
from .models import Category, Transaction, Goal


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "user")
    list_filter = ("type", "user")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "kind", "category", "amount", "merchant")
    list_filter = ("kind", "category", "date")
    search_fields = ("merchant", "notes")
    date_hierarchy = "date"


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "current_amount", "target_amount", "deadline")
    list_filter = ("deadline",)
    search_fields = ("title",)
from django.contrib import admin

# Register your models here.
