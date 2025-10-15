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
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from decimal import Decimal

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

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


class MonthlySpendingChartView(View):
    def get(self, request):
        from django.db.models.functions import TruncMonth
        from django.db.models import Sum, Count

        monthly_data = Transaction.objects.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')[:6]

        months = [item['month'].strftime('%b %Y') for item in monthly_data]
        totals = [float(item['total']) for item in monthly_data]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(months, totals, color='#6366f1', alpha=0.8, edgecolor='#4f46e5', linewidth=2)

        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Total Spending ($)', fontsize=12, fontweight='bold')
        ax.set_title('Monthly Spending Trends', fontsize=14, fontweight='bold', pad=20)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height, f'${height:,.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)

        return HttpResponse(buffer, content_type='image/png')


class CategoryPieChartView(View):
    def get(self, request):
        from django.db.models import Sum

        category_data = Transaction.objects.values(
            'category__name',
            'category__type'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')[:6]

        labels = [item['category__name'] for item in category_data]
        sizes = [float(item['total']) for item in category_data]
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6']

        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, explode=[0.05] * len(sizes)
        )

        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax.set_title('Spending by Category', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)

        return HttpResponse(buffer, content_type='image/png')


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