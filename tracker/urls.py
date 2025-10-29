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
    path('transaction/create/fbv/', views.transaction_create_fbv, name='transaction_create_fbv'),
    path('transaction/create/cbv/', views.TransactionCreateCBV.as_view(), name='transaction_create_cbv'),
    path('transaction/search/', views.transaction_search, name='transaction_search'),
    path('api/transactions/summary/', views.api_transaction_summary, name='api_transaction_summary'),
    path('api/transactions/by-category/', views.APITransactionsByCategory.as_view(), name='api_transactions_by_category'),
]
