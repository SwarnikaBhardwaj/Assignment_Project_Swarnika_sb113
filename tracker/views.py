from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
def home(request): return HttpResponse("FinTrack is running 🪙")

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from .models import Transaction


def transactions_httpresponse(request):
    """
    Style 1: Manual template loading + HttpResponse.
    Exactly what the spec asks for.
    """
    qs = Transaction.objects.filter(user=request.user).order_by("-date", "-id") if request.user.is_authenticated else Transaction.objects.none()
    template = loader.get_template("tracker/transaction_list.html")
    context = {"transactions": qs, "title": "Transactions (HttpResponse)"}
    html = template.render(context, request)
    return HttpResponse(html)


def transactions_render(request):
    """
    Style 2: Shortcut render()
    Same template, same context key — shows that templates don't care how data arrives.
    """
    qs = Transaction.objects.filter(user=request.user).order_by("-date", "-id") if request.user.is_authenticated else Transaction.objects.none()
    if request.GET.get("empty") == "1":
        qs = qs.none()

    return render(request, "tracker/transaction_list.html", {
        "transactions": qs,
        "title": "Transactions (render)"
    })

