from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
def home(request): return HttpResponse("FinTrack is running 🪙")

from django.http import HttpResponse
from django.views import View
from django.template import loader
from django.shortcuts import render

from django.views.generic import DetailView
from .models import Transaction, Category
from django.views.generic import ListView
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal


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

# this is going to be my base CBV
class TransactionListBaseView(View):
    def get(self, request):
        qs = Transaction.objects.filter(user=request.user).order_by('-date', '-id') if request.user.is_authenticated else Transaction.objects.none()
        context = {'transactions': qs, 'title': 'Transactions Base CBV'}
        return render(request, 'tracker/transaction_list_base.html', context)

class TransactionListGenericView(ListView):
    model = Transaction
    template_name = 'tracker/transaction_list_generic.html'
    context_object_name = 'transactions'
    ordering = ['-date', '-id']
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Transaction.objects.filter(user=self.request.user).order_by('-date', '-id')
        return Transaction.objects.none()


class TransactionDetailView(DetailView):
    model = Transaction
    template_name = 'tracker/transaction_detail.html'
    context_object_name = 'transaction'


class TransactionInsightsView(ListView):
    model = Transaction
    template_name = 'tracker/transaction_insights.html'
    context_object_name = 'transactions'
    paginate_by = 50

    def get_queryset(self):
        queryset = Transaction.objects.select_related('category', 'user').all()
        search_query = self.request.GET.get('q', '')
        category_filter = self.request.GET.get('category', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        min_amount = self.request.GET.get('min_amount', '')
        max_amount = self.request.GET.get('max_amount', '')
        if search_query:
            queryset = queryset.filter(
                Q(merchant__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        if category_filter:
            queryset = queryset.filter(category__id=category_filter)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if min_amount:
            queryset = queryset.filter(amount__gte=Decimal(min_amount))
        if max_amount:
            queryset = queryset.filter(amount__lte=Decimal(max_amount))
        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['min_amount'] = self.request.GET.get('min_amount', '')
        context['max_amount'] = self.request.GET.get('max_amount', '')
        context['categories'] = Category.objects.all()
        has_filters = any([
            context['search_query'],
            context['category_filter'],
            context['date_from'],
            context['date_to'],
            context['min_amount'],
            context['max_amount'],
        ])
        context['has_filters'] = has_filters
        filtered_qs = self.get_queryset()
        totals = filtered_qs.aggregate(
            total_transactions=Count('id'),
            total_spent=Sum('amount'),
            average_transaction=Avg('amount'),
        )
        context['total_transactions'] = totals['total_transactions'] or 0
        context['total_spent'] = totals['total_spent'] or Decimal('0.00')
        context['average_transaction'] = totals['average_transaction'] or Decimal('0.00')
        category_breakdown = filtered_qs.values(
            'category__name',
            'category__type'
        ).annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-total')
        context['category_breakdown'] = category_breakdown
        top_merchants = filtered_qs.filter(
            merchant__isnull=False
        ).exclude(
            merchant=''
        ).values('merchant').annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_spent')[:10]
        context['top_merchants'] = top_merchants
        monthly_spending = filtered_qs.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-month')[:6]
        context['monthly_spending'] = monthly_spending
        total_for_percentage = context['total_spent']
        if total_for_percentage > 0:
            for item in category_breakdown:
                item['percentage'] = (item['total'] / total_for_percentage) * 100
        return context