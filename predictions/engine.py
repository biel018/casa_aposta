"""
Motor de matching de ordens para o prediction market.
Implementa um order book com matching price-time priority.
"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Order, Trade, Position, MarketOutcome, PriceHistory
from wallet.models import Wallet


class MatchingEngine:
    """
    Motor de matching para mercados de previsão.
    - Compra (buy): comprar shares de um outcome a um preço (0.01 - 0.99)
    - Venda (sell): vender shares que você possui
    - Preço = probabilidade implícita. Se Yes = $0.65, o mercado acha 65% provável.
    - Share paga $1.00 se correto no final, $0.00 se errado.
    """

    @staticmethod
    @transaction.atomic
    def place_order(user, outcome, side, price, quantity):
        """
        Coloca uma ordem no order book e tenta fazer matching.

        Args:
            user: Usuário que está colocando a ordem
            outcome: MarketOutcome onde a ordem será colocada
            side: 'buy' ou 'sell'
            price: Preço por share (0.01 a 0.99)
            quantity: Quantidade de shares

        Returns:
            Order: A ordem criada

        Raises:
            ValueError: Se os parâmetros forem inválidos
        """
        price = Decimal(str(price))
        quantity = Decimal(str(quantity))

        # Validações
        if not outcome.market.is_open:
            raise ValueError('Este mercado não está aberto para trading.')

        if price < Decimal('0.01') or price > Decimal('0.99'):
            raise ValueError('O preço deve estar entre $0.01 e $0.99.')

        if quantity < Decimal('1'):
            raise ValueError('A quantidade mínima é 1 share.')

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if side == 'buy':
            # Custo = preço × quantidade
            cost = price * quantity
            if wallet.balance < cost:
                raise ValueError(f'Saldo insuficiente. Necessário: R$ {cost:.2f}')
            # Reservar o valor
            wallet.bet_debit(cost, f'Ordem de compra: {outcome.market.title} - {outcome.name}')

        elif side == 'sell':
            # Verificar se possui shares suficientes
            position, _ = Position.objects.get_or_create(
                user=user, outcome=outcome
            )
            if position.shares < quantity:
                raise ValueError(f'Shares insuficientes. Você possui: {position.shares}')
        else:
            raise ValueError('Side deve ser "buy" ou "sell".')

        # Criar a ordem
        order = Order.objects.create(
            user=user,
            outcome=outcome,
            side=side,
            price=price,
            quantity=quantity,
        )

        # Tentar fazer matching
        MatchingEngine._match_order(order)

        return order

    @staticmethod
    @transaction.atomic
    def _match_order(order):
        """Tenta fazer match da ordem com ordens opostas."""
        if order.side == 'buy':
            # Buscar ordens de venda com preço <= preço de compra
            opposite_orders = Order.objects.filter(
                outcome=order.outcome,
                side='sell',
                status__in=['open', 'partially_filled'],
                price__lte=order.price,
            ).exclude(user=order.user).order_by('price', 'created_at')
        else:
            # Buscar ordens de compra com preço >= preço de venda
            opposite_orders = Order.objects.filter(
                outcome=order.outcome,
                side='buy',
                status__in=['open', 'partially_filled'],
                price__gte=order.price,
            ).exclude(user=order.user).order_by('-price', 'created_at')

        for opposite in opposite_orders:
            if order.remaining_quantity <= 0:
                break

            # Quantidade do trade
            trade_qty = min(order.remaining_quantity, opposite.remaining_quantity)
            # Preço do trade (preço da ordem mais antiga - price-time priority)
            trade_price = opposite.price

            # Criar trade
            if order.side == 'buy':
                trade = Trade.objects.create(
                    buy_order=order,
                    sell_order=opposite,
                    outcome=order.outcome,
                    price=trade_price,
                    quantity=trade_qty,
                )
            else:
                trade = Trade.objects.create(
                    buy_order=opposite,
                    sell_order=order,
                    outcome=order.outcome,
                    price=trade_price,
                    quantity=trade_qty,
                )

            # Atualizar quantidades preenchidas
            order.filled_quantity += trade_qty
            opposite.filled_quantity += trade_qty

            # Atualizar status
            if order.filled_quantity >= order.quantity:
                order.status = 'filled'
            else:
                order.status = 'partially_filled'

            if opposite.filled_quantity >= opposite.quantity:
                opposite.status = 'filled'
            else:
                opposite.status = 'partially_filled'

            order.save()
            opposite.save()

            # Transferir shares e dinheiro
            MatchingEngine._settle_trade(trade)

        # Se a ordem de compra não foi totalmente preenchida,
        # devolver o excedente reservado
        if order.side == 'buy' and order.status != 'filled':
            remaining_cost = order.remaining_quantity * order.price
            if order.status == 'partially_filled':
                # Devolver diferença de preço se executou a um preço menor
                pass  # Já reservamos o total, o que sobrar fica na ordem

        # Atualizar preço do outcome
        order.outcome.update_price_from_orders()

        # Registrar preço no histórico
        PriceHistory.objects.create(
            outcome=order.outcome,
            price=order.outcome.price,
            volume=order.filled_quantity * order.price if order.filled_quantity > 0 else Decimal('0'),
        )

        # Atualizar volume do mercado
        if order.filled_quantity > 0:
            market = order.outcome.market
            market.total_volume += order.filled_quantity * order.price
            market.save(update_fields=['total_volume'])

    @staticmethod
    @transaction.atomic
    def _settle_trade(trade):
        """Liquida um trade: transfere shares e dinheiro."""
        buyer = trade.buy_order.user
        seller = trade.sell_order.user
        trade_value = trade.price * trade.quantity

        # Buyer recebe shares
        buyer_pos, _ = Position.objects.get_or_create(
            user=buyer, outcome=trade.outcome
        )
        old_total = buyer_pos.shares * buyer_pos.avg_price
        buyer_pos.shares += trade.quantity
        buyer_pos.total_invested += trade_value
        if buyer_pos.shares > 0:
            buyer_pos.avg_price = buyer_pos.total_invested / buyer_pos.shares
        buyer_pos.save()

        # Seller perde shares e recebe dinheiro
        seller_pos, _ = Position.objects.get_or_create(
            user=seller, outcome=trade.outcome
        )
        seller_pos.shares -= trade.quantity
        # Calcular P&L realizado
        sell_revenue = trade_value
        cost_basis = trade.quantity * seller_pos.avg_price
        seller_pos.realized_pnl += sell_revenue - cost_basis
        seller_pos.total_invested -= cost_basis
        if seller_pos.total_invested < 0:
            seller_pos.total_invested = Decimal('0')
        seller_pos.save()

        # Creditar seller
        seller_wallet, _ = Wallet.objects.get_or_create(user=seller)
        seller_wallet.bet_credit(
            trade_value,
            f'Venda: {trade.outcome.market.title} - {trade.outcome.name}'
        )

    @staticmethod
    @transaction.atomic
    def cancel_order(order):
        """Cancela uma ordem aberta e devolve o dinheiro reservado."""
        if order.status not in ['open', 'partially_filled']:
            raise ValueError('Esta ordem não pode ser cancelada.')

        remaining = order.remaining_quantity

        if order.side == 'buy':
            # Devolver valor reservado
            refund = remaining * order.price
            wallet, _ = Wallet.objects.get_or_create(user=order.user)
            wallet.deposit(refund, f'Cancelamento ordem: {order.outcome.market.title}')

        order.status = 'cancelled'
        order.save()
        return order

    @staticmethod
    @transaction.atomic
    def resolve_market(market, winning_outcome_slug):
        """
        Resolve um mercado: paga $1.00 por share do outcome vencedor,
        $0.00 para os demais.
        """
        if market.status == 'resolved':
            raise ValueError('Este mercado já foi resolvido.')

        market.status = 'resolved'
        market.resolution_date = timezone.now()
        market.save()

        # Marcar vencedor
        for outcome in market.outcomes.all():
            if outcome.slug == winning_outcome_slug:
                outcome.is_winner = True
                outcome.price = Decimal('1.0000')
            else:
                outcome.is_winner = False
                outcome.price = Decimal('0.0000')
            outcome.save()

        # Cancelar ordens abertas
        open_orders = Order.objects.filter(
            outcome__market=market,
            status__in=['open', 'partially_filled']
        )
        for order in open_orders:
            MatchingEngine.cancel_order(order)

        # Pagar holders do outcome vencedor
        winning_outcome = market.outcomes.get(slug=winning_outcome_slug)
        positions = Position.objects.filter(
            outcome=winning_outcome,
            shares__gt=0
        )

        for position in positions:
            payout = position.shares * Decimal('1.00')  # $1 por share
            wallet, _ = Wallet.objects.get_or_create(user=position.user)
            wallet.bet_credit(
                payout,
                f'Resolução: {market.title} - {winning_outcome.name} ✓'
            )
            position.realized_pnl += payout - position.total_invested
            position.save()

    @staticmethod
    def get_order_book(outcome):
        """Retorna o order book formatado para um outcome."""
        buy_orders = (
            Order.objects.filter(
                outcome=outcome,
                side='buy',
                status__in=['open', 'partially_filled'],
            )
            .values('price')
            .annotate(
                total_qty=models.Sum('quantity') - models.Sum('filled_quantity')
            )
            .order_by('-price')[:10]
        )

        sell_orders = (
            Order.objects.filter(
                outcome=outcome,
                side='sell',
                status__in=['open', 'partially_filled'],
            )
            .values('price')
            .annotate(
                total_qty=models.Sum('quantity') - models.Sum('filled_quantity')
            )
            .order_by('price')[:10]
        )

        return {
            'bids': list(buy_orders),
            'asks': list(sell_orders),
        }
