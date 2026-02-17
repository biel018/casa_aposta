"""
Views para depósitos em criptomoeda.
Simulação de depósito crypto com verificação de TX hash.
"""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Wallet, CryptoDeposit

# Preços simulados de crypto (em um sistema real, usar API CoinGecko/Binance)
CRYPTO_PRICES = {
    'ETH': Decimal('3200.00'),
    'USDT': Decimal('1.00'),
    'USDC': Decimal('1.00'),
    'BTC': Decimal('97000.00'),
    'MATIC': Decimal('0.85'),
}

# Endereço de depósito da plataforma (simulado)
PLATFORM_ADDRESSES = {
    'ethereum': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18',
    'polygon': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18',
    'bsc': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18',
    'arbitrum': '0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18',
}


@login_required
def crypto_deposit_view(request):
    """Página de depósito crypto."""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    deposits = CryptoDeposit.objects.filter(wallet=wallet)[:20]

    return render(request, 'wallet/crypto_deposit.html', {
        'wallet': wallet,
        'deposits': deposits,
        'crypto_prices': CRYPTO_PRICES,
        'platform_addresses': PLATFORM_ADDRESSES,
    })


@require_GET
@login_required
def crypto_prices_api(request):
    """Retorna preços atuais das criptos."""
    return JsonResponse({
        'prices': {k: str(v) for k, v in CRYPTO_PRICES.items()},
        'addresses': PLATFORM_ADDRESSES,
    })


@csrf_exempt
@require_POST
@login_required
def crypto_deposit_confirm(request):
    """
    Confirma um depósito crypto.
    Em produção, isso verificaria a blockchain via Web3/Etherscan API.
    Por ora, simula a confirmação.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    tx_hash = data.get('tx_hash', '')
    crypto = data.get('crypto', '')
    network = data.get('network', 'ethereum')
    amount = data.get('amount', 0)
    from_address = data.get('from_address', '')

    if not all([tx_hash, crypto, amount, from_address]):
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    if crypto not in CRYPTO_PRICES:
        return JsonResponse({'error': 'Criptomoeda não suportada'}, status=400)

    # Verificar se TX já foi processada
    if CryptoDeposit.objects.filter(tx_hash=tx_hash).exists():
        return JsonResponse({'error': 'Esta transação já foi processada'}, status=400)

    amount_crypto = Decimal(str(amount))
    amount_usd = amount_crypto * CRYPTO_PRICES[crypto]

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    to_address = PLATFORM_ADDRESSES.get(network, PLATFORM_ADDRESSES['ethereum'])

    # Criar registro do depósito
    deposit = CryptoDeposit.objects.create(
        wallet=wallet,
        crypto=crypto,
        network=network,
        amount_crypto=amount_crypto,
        amount_usd=amount_usd,
        tx_hash=tx_hash,
        from_address=from_address,
        to_address=to_address,
        status='completed',  # Simulando confirmação instantânea
        confirmations=12,
    )

    # Creditar na carteira
    wallet.deposit(
        amount_usd,
        f'Depósito Crypto: {amount_crypto} {crypto} (TX: {tx_hash[:10]}...)'
    )

    return JsonResponse({
        'success': True,
        'message': f'Depósito de {amount_crypto} {crypto} (~${amount_usd:.2f}) confirmado!',
        'deposit': {
            'id': deposit.pk,
            'crypto': crypto,
            'amount_crypto': str(amount_crypto),
            'amount_usd': str(amount_usd),
            'tx_hash': tx_hash,
            'status': 'completed',
        }
    })


@csrf_exempt
@require_POST
@login_required
def crypto_send_tx(request):
    """
    Recebe uma transação feita via MetaMask.
    O frontend envia a TX depois que o usuário confirma no MetaMask.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    tx_hash = data.get('tx_hash', '')
    crypto = data.get('crypto', 'ETH')
    amount = data.get('amount', 0)
    from_address = data.get('from_address', '')
    network = data.get('network', 'ethereum')

    if not tx_hash or not from_address:
        return JsonResponse({'error': 'TX hash e endereço são obrigatórios'}, status=400)

    amount_crypto = Decimal(str(amount))
    amount_usd = amount_crypto * CRYPTO_PRICES.get(crypto, Decimal('0'))

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    # Registrar o depósito como pendente
    deposit = CryptoDeposit.objects.create(
        wallet=wallet,
        crypto=crypto,
        network=network,
        amount_crypto=amount_crypto,
        amount_usd=amount_usd,
        tx_hash=tx_hash,
        from_address=from_address,
        to_address=PLATFORM_ADDRESSES.get(network, ''),
        status='confirming',
    )

    # Em produção: agendar task para verificar confirmações na blockchain
    # Por enquanto, confirmar automaticamente
    deposit.status = 'completed'
    deposit.confirmations = 12
    deposit.save()

    wallet.deposit(
        amount_usd,
        f'Depósito MetaMask: {amount_crypto} {crypto}'
    )

    return JsonResponse({
        'success': True,
        'message': f'Depósito recebido! {amount_crypto} {crypto} (~R$ {amount_usd:.2f})',
        'deposit_id': deposit.pk,
    })
