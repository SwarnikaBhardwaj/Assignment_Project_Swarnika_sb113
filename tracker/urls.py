from django.urls import path
from . import views

urlpatterns = [
    path("transactions/raw/", views.transactions_httpresponse, name="tx_raw"),
    path("transactions/", views.transactions_render, name="tx_render"),
]
