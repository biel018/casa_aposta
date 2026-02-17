from django import forms
from decimal import Decimal


class PlaceBetForm(forms.Form):
    odd_id = forms.IntegerField(widget=forms.HiddenInput())
    amount = forms.DecimalField(
        label='Valor da Aposta',
        min_value=Decimal('1.00'),
        max_value=Decimal('10000.00'),
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'R$ 0,00',
            'step': '0.01',
            'min': '1.00',
        })
    )
