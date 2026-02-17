from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


class Category(models.Model):
    """Categoria de mercados de previsão."""
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Ícone', max_length=50, default='bi-graph-up')
    color = models.CharField('Cor', max_length=20, default='primary')
    order = models.IntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class PredictionMarket(models.Model):
    """Mercado de previsão estilo Polymarket."""
    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('closed', 'Fechado'),
        ('resolved', 'Resolvido'),
        ('cancelled', 'Cancelado'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='markets', verbose_name='Categoria'
    )
    title = models.CharField('Título', max_length=300)
    slug = models.SlugField('Slug', unique=True, max_length=300)
    description = models.TextField('Descrição', blank=True)
    rules = models.TextField('Regras de Resolução', blank=True,
                             help_text='Como este mercado será resolvido')
    image = models.ImageField('Imagem', upload_to='predictions/', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    end_date = models.DateTimeField('Data de Encerramento')
    resolution_date = models.DateTimeField('Data de Resolução', null=True, blank=True)
    resolution_source = models.CharField('Fonte de Resolução', max_length=500, blank=True)
    is_featured = models.BooleanField('Destaque', default=False)
    total_volume = models.DecimalField('Volume Total', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_liquidity = models.DecimalField('Liquidez', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_markets',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Mercado de Previsão'
        verbose_name_plural = 'Mercados de Previsão'
        ordering = ['-is_featured', '-total_volume']

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.status == 'open' and self.end_date > timezone.now()

    @property
    def time_left(self):
        if self.end_date > timezone.now():
            return self.end_date - timezone.now()
        return None


class MarketOutcome(models.Model):
    """Opções de resultado de um mercado (ex: Sim/Não, ou múltiplas opções)."""
    market = models.ForeignKey(
        PredictionMarket, on_delete=models.CASCADE,
        related_name='outcomes', verbose_name='Mercado'
    )
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug')
    # Preço = probabilidade implícita (0.01 a 0.99)
    price = models.DecimalField(
        'Preço', max_digits=5, decimal_places=4,
        default=Decimal('0.5000'),
        help_text='Preço atual (0.01 a 0.99) = probabilidade implícita'
    )
    total_shares = models.DecimalField(
        'Total de Shares', max_digits=15, decimal_places=2,
        default=Decimal('0.00')
    )
    is_winner = models.BooleanField('Vencedor', default=False, null=True, blank=True)

    class Meta:
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'
        unique_together = ['market', 'slug']

    def __str__(self):
        return f'{self.name} ({self.price_percent}%)'

    @property
    def price_percent(self):
        return int(self.price * 100)

    def update_price_from_orders(self):
        """Recalcula o preço baseado no order book."""
        buy_orders = self.orders.filter(side='buy', status='open').order_by('-price')
        sell_orders = self.orders.filter(side='sell', status='open').order_by('price')

        if buy_orders.exists() and sell_orders.exists():
            best_bid = buy_orders.first().price
            best_ask = sell_orders.first().price
            self.price = (best_bid + best_ask) / 2
        elif buy_orders.exists():
            self.price = buy_orders.first().price
        elif sell_orders.exists():
            self.price = sell_orders.first().price

        self.save(update_fields=['price'])


class Order(models.Model):
    """Ordem de compra/venda no order book."""
    SIDE_CHOICES = [
        ('buy', 'Compra'),
        ('sell', 'Venda'),
    ]
    STATUS_CHOICES = [
        ('open', 'Aberta'),
        ('filled', 'Executada'),
        ('partially_filled', 'Parcialmente Executada'),
        ('cancelled', 'Cancelada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='prediction_orders', verbose_name='Usuário'
    )
    outcome = models.ForeignKey(
        MarketOutcome, on_delete=models.CASCADE,
        related_name='orders', verbose_name='Resultado'
    )
    side = models.CharField('Lado', max_length=10, choices=SIDE_CHOICES)
    price = models.DecimalField(
        'Preço', max_digits=5, decimal_places=4,
        help_text='Preço por share (0.01 a 0.99)'
    )
    quantity = models.DecimalField('Quantidade', max_digits=15, decimal_places=2)
    filled_quantity = models.DecimalField(
        'Quantidade Executada', max_digits=15, decimal_places=2,
        default=Decimal('0.00')
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Ordem'
        verbose_name_plural = 'Ordens'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_side_display()} {self.quantity} @ {self.price} - {self.outcome.name}'

    @property
    def remaining_quantity(self):
        return self.quantity - self.filled_quantity

    @property
    def total_cost(self):
        return self.quantity * self.price


class Trade(models.Model):
    """Trade executado (match entre ordens)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buy_order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='buy_trades', verbose_name='Ordem de Compra'
    )
    sell_order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='sell_trades', verbose_name='Ordem de Venda'
    )
    outcome = models.ForeignKey(
        MarketOutcome, on_delete=models.CASCADE,
        related_name='trades', verbose_name='Resultado'
    )
    price = models.DecimalField('Preço', max_digits=5, decimal_places=4)
    quantity = models.DecimalField('Quantidade', max_digits=15, decimal_places=2)
    created_at = models.DateTimeField('Executado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        ordering = ['-created_at']

    def __str__(self):
        return f'Trade {self.quantity} @ {self.price} - {self.outcome.name}'


class Position(models.Model):
    """Posição do usuário em um outcome (shares que possui)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='positions', verbose_name='Usuário'
    )
    outcome = models.ForeignKey(
        MarketOutcome, on_delete=models.CASCADE,
        related_name='positions', verbose_name='Resultado'
    )
    shares = models.DecimalField('Shares', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    avg_price = models.DecimalField(
        'Preço Médio', max_digits=5, decimal_places=4,
        default=Decimal('0.0000')
    )
    total_invested = models.DecimalField(
        'Total Investido', max_digits=15, decimal_places=2,
        default=Decimal('0.00')
    )
    realized_pnl = models.DecimalField(
        'P&L Realizado', max_digits=15, decimal_places=2,
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Posição'
        verbose_name_plural = 'Posições'
        unique_together = ['user', 'outcome']

    def __str__(self):
        return f'{self.user.username}: {self.shares} shares de {self.outcome.name}'

    @property
    def current_value(self):
        return self.shares * self.outcome.price

    @property
    def unrealized_pnl(self):
        return self.current_value - self.total_invested

    @property
    def pnl_percent(self):
        if self.total_invested > 0:
            return ((self.current_value - self.total_invested) / self.total_invested) * 100
        return Decimal('0')


class PriceHistory(models.Model):
    """Histórico de preço de uma outcome para gráficos."""
    outcome = models.ForeignKey(
        MarketOutcome, on_delete=models.CASCADE,
        related_name='price_history', verbose_name='Resultado'
    )
    price = models.DecimalField('Preço', max_digits=5, decimal_places=4)
    volume = models.DecimalField('Volume', max_digits=15, decimal_places=2, default=Decimal('0.00'))
    timestamp = models.DateTimeField('Timestamp', auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Histórico de Preços'
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.outcome.name}: {self.price} @ {self.timestamp}'
