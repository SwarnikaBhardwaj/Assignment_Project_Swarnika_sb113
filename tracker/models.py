from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Category(models.Model):
    """This is for the spending/income category, optionally user-scoped so users can define their own."""
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
            # this helps prevent duplicate category names per user and type (globals are user=None)
            models.UniqueConstraint(fields=["user", "name", "type"], name="uniq_user_name_type"),
        ]
        ordering = ["type", "name"]  # this lists nicely in admin

    def __str__(self):
        scope = self.user.username if self.user_id else "global"
        return f"{self.name} ({self.type.lower()}) · {scope}"


class Transaction(models.Model):
    """Single money movement."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,  # protect history so cannot delete a used category
        related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    # Store direction in 'kind' so amount stays positive
    kind = models.CharField(max_length=7, choices=Category.TYPE_CHOICES)  # EXPENSE or INCOME
    date = models.DateField(default=timezone.now)
    merchant = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "kind", "date"]),
        ]

    def __str__(self):
        sign = "-" if self.kind == Category.EXPENSE else "+"
        return f"{self.date} {sign}${self.amount} · {self.category.name}"


class Goal(models.Model):
    """Savings goal tracking."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "title"], name="uniq_goal_per_user_title")
        ]
        ordering = ["deadline", "title"]

    def __str__(self):
        return f"{self.title} (${self.current_amount}/{self.target_amount})"
from django.db import models

# Create your models here.
