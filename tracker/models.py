from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


class Category(models.Model):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TYPE_CHOICES = [(EXPENSE, "Expense"), (INCOME, "Income")]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        help_text="Null = global category; non-null = user-specific category."
    )
    name = models.CharField(max_length=64)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default=EXPENSE)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "type"],
                condition=Q(user__isnull=False),
                name="uniq_user_name_type_scoped"
            ),
            models.UniqueConstraint(
                fields=["name", "type"],
                condition=Q(user__isnull=True),
                name="uniq_name_type_global"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "type"], name="idx_category_user_type"),
        ]
        ordering = ["type", "name"]

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    kind = models.CharField(max_length=7, choices=Category.TYPE_CHOICES)  # EXPENSE or INCOME
    date = models.DateField(default=timezone.localdate)  # avoids datetime->date coercion
    merchant = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "kind", "date"]),
        ]

    def clean(self):
        if self.category and self.kind and (self.kind != self.category.type):
            raise ValidationError({
                "kind": "Transaction kind must match the linked Category type (e.g., EXPENSE or INCOME)."
            })
        if self.amount is not None and self.amount <= 0:
            raise ValidationError('Amount must be greater than zero')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    def progress(self):
        return (self.current_amount / self.target_amount) * 100 if self.target_amount else 0
    def __str__(self):
        return f"{self.name} ({self.progress():.0f}% complete)"

from django.db import models

