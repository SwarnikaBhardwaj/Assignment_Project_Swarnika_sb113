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
    path('demo/text/', views.demo_text_response, name='demo_text'),
    path('demo/json/', views.demo_json_response, name='demo_json'),
    path('charts/api-demo/', views.api_chart_demo_page, name='api_chart_demo_page'),
    path('api/charts/transactions.png', views.transaction_chart_from_api, name='api_transaction_chart'),
    path('external/currency/', views.CurrencyConverterView.as_view(), name='currency_api'),
    path('external/currency/page/', views.currency_converter_page, name='currency_converter_page'),
    path('reports/', views.reports_page, name='reports'),
    path('export/transactions.csv', views.export_transactions_csv, name='export_transactions_csv'),
    path('export/transactions.json', views.export_transactions_json, name='export_transactions_json'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]
