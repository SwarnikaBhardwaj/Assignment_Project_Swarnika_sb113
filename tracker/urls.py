from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path("transactions/raw/", views.TransactionListGenericView.as_view(), name="transactions_raw"),
    path("transactions/render/", views.TransactionListBaseView.as_view(), name="transactions_render"),
    path("goals/<int:pk>/", views.TransactionDetailView.as_view(), name="goal_detail"),
    path("insights/", views.TransactionInsightsView.as_view(), name="transaction_insights"),
]
