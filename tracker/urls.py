from django.urls import path
from . import views

urlpatterns = [
    path('transactions/base/', views.TransactionListBaseView.as_view(), name='transactions_base'),
    path('transactions/generic/', views.TransactionListGenericView.as_view(), name='transactions_generic'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
]
