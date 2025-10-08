from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path("transactions/raw/", views.TransactionRawView.as_view(), name="transactions_raw"),
    path("transactions/render/", views.TransactionGenericCBV.as_view(), name="transactions_render"),
    path("goals/<int:pk>/", views.GoalDetailView.as_view(), name="goal_detail"),
    path("insights/", views.TransactionInsightsView.as_view(), name="transaction_insights"),
]
