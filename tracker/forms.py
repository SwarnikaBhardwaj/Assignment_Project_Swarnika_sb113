from django import forms
from .models import Transaction, Category
from decimal import Decimal

class TransactionSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by merchant or notes...',
            'class': 'form-control'
        })
    )
    min_amount = forms.DecimalField(
        required=False,
        label='Min Amount',
        widget=forms.NumberInput(attrs={
            'placeholder': '0.00',
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class TransactionCreateForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['merchant', 'amount', 'category', 'kind','date', 'notes']
        widgets = {
            'merchant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where did you spend? (e.g., Starbucks, Amazon)'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes about this transaction',
                'rows': 3
            })
        }
        labels = {
            'merchant': 'Merchant/Store',
            'amount': 'Amount ($)',
            'category': 'Category',
            'kind': 'Type',
            'date': 'Transaction Date',
            'notes': 'Notes (Optional)'
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError('Amount is required')
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount