"""
Views para autenticação Web3 com MetaMask.
Fluxo:
1. Frontend solicita nonce para o endereço da wallet
2. Usuário assina o nonce com MetaMask
3. Backend verifica a assinatura e faz login/registro
"""
import secrets
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth import login
from eth_account.messages import encode_defunct
from web3 import Web3
from .models import User


def generate_nonce():
    return f'Bem-vindo à Casa de Apostas!\n\nAssine esta mensagem para autenticar.\n\nNonce: {secrets.token_hex(16)}'


@require_GET
def web3_nonce(request):
    """Retorna um nonce para o endereço da wallet assinar."""
    address = request.GET.get('address', '').lower()

    if not address or not Web3.is_address(address):
        return JsonResponse({'error': 'Endereço inválido'}, status=400)

    address = Web3.to_checksum_address(address)

    try:
        user = User.objects.get(wallet_address__iexact=address)
        user.nonce = generate_nonce()
        user.save(update_fields=['nonce'])
    except User.DoesNotExist:
        user = None
        nonce = generate_nonce()
        # Guardar temporariamente na sessão
        request.session[f'web3_nonce_{address}'] = nonce

    nonce = user.nonce if user else request.session.get(f'web3_nonce_{address}')

    return JsonResponse({
        'nonce': nonce,
        'address': address,
        'exists': user is not None,
    })


@csrf_exempt
@require_POST
def web3_verify(request):
    """Verifica a assinatura e faz login/registro."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    address = data.get('address', '').lower()
    signature = data.get('signature', '')

    if not address or not signature:
        return JsonResponse({'error': 'Endereço e assinatura são obrigatórios'}, status=400)

    address = Web3.to_checksum_address(address)

    # Buscar o nonce
    try:
        user = User.objects.get(wallet_address__iexact=address)
        nonce = user.nonce
    except User.DoesNotExist:
        user = None
        nonce = request.session.get(f'web3_nonce_{address}')

    if not nonce:
        return JsonResponse({'error': 'Nonce não encontrado. Solicite um novo.'}, status=400)

    # Verificar a assinatura
    try:
        w3 = Web3()
        message = encode_defunct(text=nonce)
        recovered_address = w3.eth.account.recover_message(message, signature=signature)

        if recovered_address.lower() != address.lower():
            return JsonResponse({'error': 'Assinatura inválida'}, status=401)
    except Exception as e:
        return JsonResponse({'error': f'Erro na verificação: {str(e)}'}, status=400)

    # Login ou registro
    if user:
        # Login
        user.nonce = generate_nonce()  # Renovar nonce
        user.save(update_fields=['nonce'])
        login(request, user)
        return JsonResponse({
            'success': True,
            'message': f'Bem-vindo de volta, {user.username}!',
            'user': {
                'username': user.username,
                'address': user.wallet_address,
            }
        })
    else:
        # Registro automático
        short_addr = f'{address[:6]}...{address[-4:]}'
        username = f'wallet_{address[-8:].lower()}'

        # Garantir username único
        counter = 1
        base_username = username
        while User.objects.filter(username=username).exists():
            username = f'{base_username}_{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            wallet_address=address,
            nonce=generate_nonce(),
        )
        user.set_unusable_password()
        user.save()

        login(request, user)

        # Limpar nonce da sessão
        session_key = f'web3_nonce_{address}'
        if session_key in request.session:
            del request.session[session_key]

        return JsonResponse({
            'success': True,
            'message': f'Conta criada! Endereço: {short_addr}',
            'user': {
                'username': user.username,
                'address': user.wallet_address,
            },
            'new_user': True,
        })


@csrf_exempt
@require_POST
def web3_link(request):
    """Vincula uma wallet MetaMask a uma conta existente."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Faça login primeiro'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    address = data.get('address', '')
    signature = data.get('signature', '')

    if not address or not signature:
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    address = Web3.to_checksum_address(address)

    # Verificar se já está vinculada
    if User.objects.filter(wallet_address__iexact=address).exclude(pk=request.user.pk).exists():
        return JsonResponse({'error': 'Esta wallet já está vinculada a outra conta'}, status=400)

    # Verificar assinatura
    nonce = request.session.get(f'web3_nonce_{address}')
    if not nonce:
        return JsonResponse({'error': 'Nonce expirado'}, status=400)

    try:
        w3 = Web3()
        message = encode_defunct(text=nonce)
        recovered = w3.eth.account.recover_message(message, signature=signature)

        if recovered.lower() != address.lower():
            return JsonResponse({'error': 'Assinatura inválida'}, status=401)
    except Exception:
        return JsonResponse({'error': 'Erro na verificação'}, status=400)

    request.user.wallet_address = address
    request.user.save(update_fields=['wallet_address'])

    return JsonResponse({
        'success': True,
        'message': f'Wallet {address[:6]}...{address[-4:]} vinculada com sucesso!',
    })
