from django.shortcuts import render

# Create your views here.
def home(request): return HttpResponse("FinTrack is running 🪙")
from django.template import loader

from django.views.generic import DetailView
from .models import Transaction, Category
from django.views.generic import ListView
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal
import threading
import requests

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TransactionCreateForm
from django.views.generic import FormView
from django.urls import reverse_lazy


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


matplotlib_lock = threading.Lock()


class MonthlySpendingChartView(View):
    def get(self, request):
        with matplotlib_lock:
            plt.close('all')
            monthly_data = Transaction.objects.annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-month')[:6]
            fig = plt.figure(figsize=(10, 5))
            ax = fig.add_subplot(111)
            try:
                if not monthly_data:
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)
                    ax.axis('off')
                else:
                    months = [item['month'].strftime('%b %Y') for item in reversed(list(monthly_data))]
                    totals = [float(item['total']) for item in reversed(list(monthly_data))]
                    bars = ax.bar(months, totals, color='#667eea', edgecolor='#764ba2', linewidth=1.5)
                    ax.set_ylabel('Total Amount ($)', fontsize=11, fontweight='600')
                    ax.set_title('Monthly Spending Trends', fontsize=13, fontweight='bold', pad=15)

                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width() / 2., height,
                                    f'${height:,.0f}',
                                    ha='center', va='bottom', fontsize=9, fontweight='600')
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.grid(axis='y', alpha=0.3, linestyle='--')
                    ax.tick_params(axis='x', rotation=45, labelsize=9)
                    ax.tick_params(axis='y', labelsize=9)
                    fig.tight_layout()
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                image_data = buffer.getvalue()
                return HttpResponse(image_data, content_type='image/png')
            finally:
                plt.close(fig)


class CategoryPieChartView(View):
    def get(self, request):
        with matplotlib_lock:
            plt.close('all')
            category_data = Transaction.objects.filter(
                category__type='EXPENSE'
            ).values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')[:6]
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111)
            try:
                if not category_data:
                    ax.text(0.5, 0.5, 'No expense data available', ha='center', va='center', fontsize=14)
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)
                    ax.axis('off')
                else:
                    labels = [item['category__name'] for item in category_data]
                    sizes = [float(item['total']) for item in category_data]
                    colors = ['#667eea', '#764ba2', '#9b59b6', '#8b5cf6', '#a78bfa', '#c4b5fd']
                    wedges, texts, autotexts = ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        textprops={'fontsize': 10, 'fontweight': '600'}
                    )
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        autotext.set_fontsize(9)
                    ax.set_title('Expense Breakdown by Category', fontsize=13, fontweight='bold', pad=15)
                fig.tight_layout()
                buffer = BytesIO()
                fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight', facecolor='white')
                buffer.seek(0)
                image_data = buffer.getvalue()
                return HttpResponse(image_data, content_type='image/png')
            finally:
                plt.close(fig)


class ChartsOverviewView(TemplateView):
    template_name = 'tracker/charts_overview.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Transaction.objects.aggregate(
            total_transactions=Count('id'),
            total_spent=Sum('amount'),
            average_transaction=Avg('amount')
        )
        context['total_transactions'] = stats['total_transactions'] or 0
        context['total_spent'] = stats['total_spent'] or 0
        context['average_transaction'] = stats['average_transaction'] or 0
        category_breakdown = Transaction.objects.values(
            'category__name',
            'category__type'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        context['category_breakdown'] = category_breakdown
        return context


def transaction_create_fbv(request):
    if request.method == 'POST':
        form = TransactionCreateForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction created successfully. Reminder to stay within your budget :)')
            return redirect('transactions_render')
        else:
            messages.error(request, 'Please fix the errors below :(')
    else:
        form = TransactionCreateForm()
    return render(request, 'tracker/create_fbv.html', {
        'form': form
    })


class TransactionCreateCBV(FormView):
    form_class = TransactionCreateForm
    template_name = 'tracker/create_cbv.html'
    success_url = reverse_lazy('transactions_render')
    def form_valid(self, form):
        transaction = form.save(commit=False)
        transaction.user = self.request.user
        transaction.save()
        messages.success(self.request, 'Transaction created successfully. Reminder to stay within your budget :)')
        return super().form_valid(form)
    def form_invalid(self, form):
        messages.error(self.request, 'Please fix the errors below :(')
        return super().form_invalid(form)


from .forms import TransactionSearchForm
def transaction_search(request):
    form = TransactionSearchForm(request.GET)
    transactions = Transaction.objects.all()
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        min_amount = form.cleaned_data.get('min_amount')
        category = form.cleaned_data.get('category')
        if search_query:
            from django.db.models import Q
            transactions = transactions.filter(
                Q(merchant__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        if min_amount:
            transactions = transactions.filter(amount__gte=min_amount)
        if category:
            transactions = transactions.filter(category=category)
    return render(request, 'tracker/search_transaction.html', {
        'form': form,
        'transactions': transactions
    })


from django.http import JsonResponse
from datetime import datetime, timedelta
import urllib.request
import json

def api_transaction_summary(request):
    total_transactions = Transaction.objects.count()
    total_amount = Transaction.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_count = Transaction.objects.filter(date__gte=thirty_days_ago).count()
    data = {
        'total_transactions': total_transactions,
        'total_amount': float(total_amount),
        'recent_transactions_30_days': recent_count,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return JsonResponse(data)


class APITransactionsByCategory(View):
    def get(self, request):
        category_data = Transaction.objects.values('category__name').annotate(
            total_spent=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_spent')
        results = []
        for item in category_data:
            results.append({
                'category': item['category__name'],
                'total_spent': float(item['total_spent']),
                'count': item['transaction_count']
            })
        response_data = {
            'count': len(results),
            'results': results
        }
        return JsonResponse(response_data)


def transaction_chart_from_api(request):
    api_url = request.build_absolute_uri('/api/transactions/by-category/')
    with urllib.request.urlopen(api_url) as response:
        data = json.loads(response.read().decode())
    categories = data['results']
    category_names = [item['category'] for item in categories]
    amounts = [item['total_spent'] for item in categories]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(category_names, amounts, color='#667eea', edgecolor='#764ba2', linewidth=2)
    ax.set_ylabel('Total Spent ($)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax.set_title('Spending by Category (From API Data)', fontsize=14, fontweight='bold')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'${height:.2f}',
                ha='center', va='bottom', fontsize=10)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def demo_text_response(request):
    data = {
        'message': 'This is plain text',
        'count': 42,
        'items': ['Idli', 'Dosa', 'Sambar']
    }
    json_string = json.dumps(data)
    return HttpResponse(json_string, content_type='text/plain')

def demo_json_response(request):
    data = {
        'message': 'This is proper JSON',
        'count': 42,
        'items': ['Idli', 'Dosa', 'Sambar']
    }
    return JsonResponse(data)

def api_chart_demo_page(request):
    return render(request, 'tracker/api_chart_demo.html')

def home_view(request):
    return redirect('transaction_insights')


class CurrencyConverterView(View):
    def get(self, request):
        amount = request.GET.get('amount', '100')
        target_currency = request.GET.get('to', 'EUR')
        try:
            amount = float(amount)
        except ValueError:
            return JsonResponse({
                'ok': False,
                'error': 'Amount must be a valid number'
            }, status=400)
        api_url = 'https://api.exchangerate-api.com/v4/latest/USD'
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            base_currency = data.get('base', 'USD')
            rates = data.get('rates', {})
            if target_currency not in rates:
                return JsonResponse({
                    'ok': False,
                    'error': f'Currency {target_currency} not found'
                }, status=404)
            exchange_rate = rates[target_currency]
            converted_amount = amount * exchange_rate
            result = {
                'ok': True,
                'original_amount': amount,
                'original_currency': base_currency,
                'target_currency': target_currency,
                'exchange_rate': exchange_rate,
                'converted_amount': round(converted_amount, 2),
                'last_updated': data.get('date', 'Unknown')
            }
            return JsonResponse(result)
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'ok': False,
                'error': 'Could not connect to exchange rate API'
            }, status=502)


def currency_converter_page(request):
    result = None
    error = None
    if request.GET.get('amount'):
        amount = request.GET.get('amount', '100')
        target_currency = request.GET.get('to', 'EUR')
        api_url = request.build_absolute_uri(
            f'/external/currency/?amount={amount}&to={target_currency}'
        )
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        result = response.json()
        if not result.get('ok'):
            error = result.get('error', 'Unknown error')
            result = None
    popular_currencies = [
        'EUR', 'GBP', 'JPY', 'CAD', 'AUD',
        'CHF', 'CNY', 'INR', 'MXN', 'BRL'
    ]
    return render(request, 'tracker/currency_converter.html', {
        'result': result,
        'error': error,
        'currencies': popular_currencies,
        'selected_amount': request.GET.get('amount', '100'),
        'selected_currency': request.GET.get('to', 'EUR')
    })

