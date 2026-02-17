from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, Transaction
from .forms import DepositForm, WithdrawForm


@login_required
def wallet_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:20]
    return render(request, 'wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
    })


@login_required
def deposit_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                wallet.deposit(amount, f'Depósito via {form.cleaned_data["payment_method"].upper()}')
                messages.success(request, f'Depósito de R$ {amount:.2f} realizado com sucesso!')
                return redirect('wallet:wallet')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = DepositForm()
    return render(request, 'wallet/deposit.html', {'form': form, 'wallet': wallet})


@login_required
def withdraw_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            try:
                wallet.withdraw(amount, f'Saque via PIX - {form.cleaned_data["pix_key"]}')
                messages.success(request, f'Saque de R$ {amount:.2f} solicitado com sucesso!')
                return redirect('wallet:wallet')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = WithdrawForm()
    return render(request, 'wallet/withdraw.html', {'form': form, 'wallet': wallet})


@login_required
def transaction_history_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    tx_type = request.GET.get('type', '')
    transactions = wallet.transactions.all()
    if tx_type:
        transactions = transactions.filter(type=tx_type)
    return render(request, 'wallet/history.html', {
        'wallet': wallet,
        'transactions': transactions,
        'current_type': tx_type,
    })
