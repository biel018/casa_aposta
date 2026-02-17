"""API REST para mercados de previsão."""
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from .models import PredictionMarket, MarketOutcome, Order, Trade, Position, PriceHistory
from .engine import MatchingEngine


@require_GET
def api_markets(request):
    """Lista todos os mercados."""
    category = request.GET.get('category', '')
    status = request.GET.get('status', 'open')

    markets = PredictionMarket.objects.prefetch_related('outcomes').all()
    if category:
        markets = markets.filter(category__slug=category)
    if status:
        markets = markets.filter(status=status)

    data = []
    for m in markets:
        outcomes = [{
            'id': o.pk,
            'name': o.name,
            'slug': o.slug,
            'price': str(o.price),
            'price_percent': o.price_percent,
        } for o in m.outcomes.all()]

        data.append({
            'id': m.pk,
            'title': m.title,
            'slug': m.slug,
            'status': m.status,
            'end_date': m.end_date.isoformat(),
            'volume': str(m.total_volume),
            'is_featured': m.is_featured,
            'outcomes': outcomes,
            'image': m.image.url if m.image else None,
        })

    return JsonResponse({'markets': data})


@require_GET
def api_market_detail(request, slug):
    """Detalhes de um mercado com order book."""
    market = PredictionMarket.objects.prefetch_related('outcomes').get(slug=slug)

    outcomes_data = []
    for outcome in market.outcomes.all():
        # Order book
        bids = list(outcome.orders.filter(
            side='buy', status__in=['open', 'partially_filled']
        ).order_by('-price').values('price', 'quantity', 'filled_quantity')[:10])

        asks = list(outcome.orders.filter(
            side='sell', status__in=['open', 'partially_filled']
        ).order_by('price').values('price', 'quantity', 'filled_quantity')[:10])

        # Price history
        history = list(outcome.price_history.order_by('-timestamp').values(
            'price', 'volume', 'timestamp'
        )[:100])

        outcomes_data.append({
            'id': outcome.pk,
            'name': outcome.name,
            'slug': outcome.slug,
            'price': str(outcome.price),
            'price_percent': outcome.price_percent,
            'total_shares': str(outcome.total_shares),
            'order_book': {'bids': bids, 'asks': asks},
            'price_history': history,
        })

    return JsonResponse({
        'market': {
            'id': market.pk,
            'title': market.title,
            'slug': market.slug,
            'description': market.description,
            'rules': market.rules,
            'status': market.status,
            'end_date': market.end_date.isoformat(),
            'volume': str(market.total_volume),
            'outcomes': outcomes_data,
        }
    })


@csrf_exempt
@require_POST
@login_required
def api_place_order(request):
    """API para colocar uma ordem."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    outcome_id = data.get('outcome_id')
    side = data.get('side', 'buy')
    price = data.get('price')
    quantity = data.get('quantity')

    if not all([outcome_id, side, price, quantity]):
        return JsonResponse({'error': 'Dados incompletos'}, status=400)

    try:
        outcome = MarketOutcome.objects.get(pk=outcome_id)
    except MarketOutcome.DoesNotExist:
        return JsonResponse({'error': 'Outcome não encontrado'}, status=404)

    try:
        order = MatchingEngine.place_order(
            user=request.user,
            outcome=outcome,
            side=side,
            price=Decimal(str(price)),
            quantity=Decimal(str(quantity)),
        )
        return JsonResponse({
            'success': True,
            'order': {
                'id': str(order.pk),
                'side': order.side,
                'price': str(order.price),
                'quantity': str(order.quantity),
                'filled': str(order.filled_quantity),
                'status': order.status,
            }
        })
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
@login_required
def api_cancel_order(request, order_id):
    """API para cancelar uma ordem."""
    try:
        order = Order.objects.get(pk=order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Ordem não encontrada'}, status=404)

    try:
        MatchingEngine.cancel_order(order)
        return JsonResponse({'success': True, 'message': 'Ordem cancelada'})
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_GET
@login_required
def api_positions(request):
    """Retorna posições do usuário."""
    positions = Position.objects.filter(
        user=request.user, shares__gt=0
    ).select_related('outcome__market')

    data = [{
        'market': p.outcome.market.title,
        'outcome': p.outcome.name,
        'shares': str(p.shares),
        'avg_price': str(p.avg_price),
        'current_price': str(p.outcome.price),
        'current_value': str(p.current_value),
        'pnl': str(p.unrealized_pnl),
        'pnl_percent': str(p.pnl_percent),
    } for p in positions]

    return JsonResponse({'positions': data})


@require_GET
def api_price_history(request, outcome_id):
    """Histórico de preço para gráficos."""
    history = PriceHistory.objects.filter(
        outcome_id=outcome_id
    ).order_by('timestamp').values('price', 'volume', 'timestamp')

    return JsonResponse({
        'history': list(history)
    })
