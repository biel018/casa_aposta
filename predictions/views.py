from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from decimal import Decimal
import json
from .models import (
    Category, PredictionMarket, MarketOutcome,
    Order, Trade, Position, PriceHistory
)
from .engine import MatchingEngine
from wallet.models import Wallet


def market_list(request):
    """Lista de mercados de previsão estilo Polymarket."""
    categories = Category.objects.all()
    category_slug = request.GET.get('cat', '')
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'open')

    markets = PredictionMarket.objects.prefetch_related('outcomes').all()

    if category_slug:
        markets = markets.filter(category__slug=category_slug)
    if search:
        markets = markets.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    if status_filter:
        markets = markets.filter(status=status_filter)

    featured = markets.filter(is_featured=True)[:6]

    return render(request, 'predictions/market_list.html', {
        'markets': markets,
        'featured': featured,
        'categories': categories,
        'current_category': category_slug,
        'search': search,
        'current_status': status_filter,
    })


def market_detail(request, slug):
    """Página do mercado com order book e trading."""
    market = get_object_or_404(
        PredictionMarket.objects.prefetch_related('outcomes__orders', 'outcomes__price_history'),
        slug=slug
    )

    # Order book para cada outcome
    order_books = {}
    order_books_json = {}
    for outcome in market.outcomes.all():
        buy_orders = outcome.orders.filter(
            side='buy', status__in=['open', 'partially_filled']
        ).order_by('-price')[:10]
        sell_orders = outcome.orders.filter(
            side='sell', status__in=['open', 'partially_filled']
        ).order_by('price')[:10]
        order_books[outcome.slug] = {
            'bids': buy_orders,
            'asks': sell_orders,
        }
        order_books_json[outcome.slug] = {
            'bids': [{'price': float(o.price), 'qty': float(o.remaining_quantity)} for o in buy_orders],
            'asks': [{'price': float(o.price), 'qty': float(o.remaining_quantity)} for o in sell_orders],
        }

    # Trades recentes
    recent_trades = Trade.objects.filter(
        outcome__market=market
    ).select_related('outcome').order_by('-created_at')[:20]

    # Posição do usuário
    user_positions = {}
    user_orders = []
    if request.user.is_authenticated:
        for outcome in market.outcomes.all():
            pos = Position.objects.filter(
                user=request.user, outcome=outcome
            ).first()
            if pos and pos.shares > 0:
                user_positions[outcome.slug] = pos

        user_orders = Order.objects.filter(
            user=request.user,
            outcome__market=market,
            status__in=['open', 'partially_filled'],
        ).select_related('outcome')

    # Histórico de preço para gráfico
    price_data = {}
    for outcome in market.outcomes.all():
        history = outcome.price_history.order_by('timestamp').values_list(
            'timestamp', 'price'
        )
        price_data[outcome.slug] = [
            {'t': h[0].isoformat(), 'p': float(h[1])} for h in history
        ]

    return render(request, 'predictions/market_detail.html', {
        'market': market,
        'order_books': order_books,
        'order_books_json': json.dumps(order_books_json),
        'recent_trades': recent_trades,
        'user_positions': user_positions,
        'user_orders': user_orders,
        'price_data': price_data,
    })


@login_required
def place_order(request, slug):
    """Coloca uma ordem de compra/venda."""
    if request.method != 'POST':
        return redirect('predictions:market_detail', slug=slug)

    market = get_object_or_404(PredictionMarket, slug=slug)
    outcome_id = request.POST.get('outcome_id')
    side = request.POST.get('side', 'buy')
    price = request.POST.get('price', '0.50')
    quantity = request.POST.get('quantity', '0')

    outcome = get_object_or_404(MarketOutcome, pk=outcome_id, market=market)

    try:
        order = MatchingEngine.place_order(
            user=request.user,
            outcome=outcome,
            side=side,
            price=Decimal(price),
            quantity=Decimal(quantity),
        )
        if order.status == 'filled':
            messages.success(request, f'Ordem executada! {quantity} shares de "{outcome.name}" @ ${price}')
        elif order.status == 'partially_filled':
            messages.info(request, f'Ordem parcialmente executada ({order.filled_quantity}/{quantity} shares)')
        else:
            messages.info(request, f'Ordem aberta: {side.upper()} {quantity} shares @ ${price}')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('predictions:market_detail', slug=slug)


@login_required
def cancel_order_view(request, order_id):
    """Cancela uma ordem aberta."""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    slug = order.outcome.market.slug

    try:
        MatchingEngine.cancel_order(order)
        messages.success(request, 'Ordem cancelada.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('predictions:market_detail', slug=slug)


@login_required
def portfolio_view(request):
    """Portfólio do usuário com todas as posições."""
    positions = Position.objects.filter(
        user=request.user, shares__gt=0
    ).select_related('outcome__market', 'outcome__market__category')

    open_orders = Order.objects.filter(
        user=request.user,
        status__in=['open', 'partially_filled'],
    ).select_related('outcome__market')

    # Trades do usuário
    trades = Trade.objects.filter(
        Q(buy_order__user=request.user) | Q(sell_order__user=request.user)
    ).select_related('outcome__market').order_by('-created_at')[:50]

    # Calcular totais
    total_invested = positions.aggregate(s=Sum('total_invested'))['s'] or Decimal('0')
    total_value = sum(p.current_value for p in positions)
    total_pnl = total_value - total_invested

    return render(request, 'predictions/portfolio.html', {
        'positions': positions,
        'open_orders': open_orders,
        'trades': trades,
        'total_invested': total_invested,
        'total_value': total_value,
        'total_pnl': total_pnl,
    })
