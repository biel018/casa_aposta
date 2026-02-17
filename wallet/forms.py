from django import forms
from decimal import Decimal


class DepositForm(forms.Form):
    amount = forms.DecimalField(
        label='Valor do Depósito',
        min_value=Decimal('10.00'),
        max_value=Decimal('50000.00'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0,00',
            'step': '0.01',
            'min': '10.00',
        })
    )
    payment_method = forms.ChoiceField(
        label='Método de Pagamento',
        choices=[
            ('pix', 'PIX'),
            ('credit_card', 'Cartão de Crédito'),
            ('bank_transfer', 'Transferência Bancária'),
        ],
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )


class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        label='Valor do Saque',
        min_value=Decimal('20.00'),
        max_value=Decimal('50000.00'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0,00',
            'step': '0.01',
            'min': '20.00',
        })
    )
    pix_key = forms.CharField(
        label='Chave PIX',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'CPF, E-mail, Telefone ou Chave Aleatória'
        })
    )
