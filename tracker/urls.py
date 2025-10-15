from django.urls import path
from . import views

from django.urls import path
from . import views

urlpatterns = [
    path("transactions/raw/", views.TransactionDetailView.as_view(), name="transactions_raw"),
    path("transactions/render/", views.TransactionListGenericView.as_view(), name="transactions_render"),
    path("goals/<int:pk>/", views.DetailView.as_view(), name="goal_detail"),
    path("insights/", views.TransactionInsightsView.as_view(), name="transaction_insights"),
    path("charts/", views.ChartsOverviewView.as_view(), name="charts_overview"),
    path("charts/monthly-spending.png", views.MonthlySpendingChartView.as_view(), name="chart_monthly_spending"),
    path("charts/category-pie.png", views.CategoryPieChartView.as_view(), name="chart_category_pie"),
]
