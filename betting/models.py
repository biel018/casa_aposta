from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Sport(models.Model):
    """Modalidade esportiva."""
    name = models.CharField('Nome', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    icon = models.CharField('Ícone', max_length=50, default='bi-trophy', help_text='Classe do Bootstrap Icons')
    is_active = models.BooleanField('Ativo', default=True)
    order = models.IntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Esporte'
        verbose_name_plural = 'Esportes'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class League(models.Model):
    """Liga/Campeonato."""
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='leagues', verbose_name='Esporte')
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    country = models.CharField('País', max_length=100, blank=True)
    logo = models.ImageField('Logo', upload_to='leagues/', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Liga'
        verbose_name_plural = 'Ligas'
        ordering = ['sport', 'name']

    def __str__(self):
        return f'{self.name} ({self.sport.name})'


class Event(models.Model):
    """Evento esportivo (partida/jogo)."""
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('live', 'Ao Vivo'),
        ('finished', 'Encerrado'),
        ('cancelled', 'Cancelado'),
        ('postponed', 'Adiado'),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='events', verbose_name='Liga')
    home_team = models.CharField('Time da Casa', max_length=200)
    away_team = models.CharField('Time Visitante', max_length=200)
    home_logo = models.ImageField('Logo Casa', upload_to='teams/', blank=True, null=True)
    away_logo = models.ImageField('Logo Visitante', upload_to='teams/', blank=True, null=True)
    start_time = models.DateTimeField('Início')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    home_score = models.IntegerField('Placar Casa', default=0)
    away_score = models.IntegerField('Placar Visitante', default=0)
    is_featured = models.BooleanField('Destaque', default=False)
    result = models.CharField('Resultado', max_length=20, blank=True,
                              help_text='home, away ou draw')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['start_time']

    def __str__(self):
        return f'{self.home_team} vs {self.away_team}'

    @property
    def is_live(self):
        return self.status == 'live'

    @property
    def is_open_for_betting(self):
        return self.status in ['scheduled', 'live'] and self.start_time > timezone.now()

    @property
    def sport(self):
        return self.league.sport

    def settle_bets(self):
        """Liquida todas as apostas deste evento após o resultado."""
        if not self.result or self.status != 'finished':
            return

        for market in self.markets.all():
            for odd in market.odds.all():
                if odd.is_winner(self.result):
                    # Pagar apostas ganhadoras
                    for bet in odd.bets.filter(status='pending'):
                        bet.win()
                else:
                    # Marcar apostas perdedoras
                    for bet in odd.bets.filter(status='pending'):
                        bet.lose()


class Market(models.Model):
    """Mercado de apostas (ex: Resultado Final, Ambas Marcam, etc)."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='markets', verbose_name='Evento')
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug')
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Mercado'
        verbose_name_plural = 'Mercados'
        unique_together = ['event', 'slug']

    def __str__(self):
        return f'{self.name} - {self.event}'


class Odd(models.Model):
    """Odd (cotação) para uma seleção dentro de um mercado."""
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='odds', verbose_name='Mercado')
    name = models.CharField('Seleção', max_length=200, help_text='Ex: Vitória Casa, Empate, Vitória Visitante')
    value = models.DecimalField('Odd', max_digits=8, decimal_places=2)
    selection_key = models.CharField('Chave', max_length=50,
                                     help_text='home, draw, away, over, under, yes, no')
    is_active = models.BooleanField('Ativo', default=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Odd'
        verbose_name_plural = 'Odds'
        ordering = ['market', 'name']

    def __str__(self):
        return f'{self.name} @ {self.value}'

    def is_winner(self, result):
        """Verifica se esta odd é vencedora baseado no resultado."""
        return self.selection_key == result


class Bet(models.Model):
    """Aposta de um usuário."""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('won', 'Ganha'),
        ('lost', 'Perdida'),
        ('cancelled', 'Cancelada'),
        ('cashout', 'Cash Out'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bets',
        verbose_name='Usuário'
    )
    odd = models.ForeignKey(Odd, on_delete=models.CASCADE, related_name='bets', verbose_name='Odd')
    amount = models.DecimalField('Valor Apostado', max_digits=12, decimal_places=2)
    odd_value = models.DecimalField('Odd no Momento', max_digits=8, decimal_places=2)
    potential_win = models.DecimalField('Ganho Potencial', max_digits=12, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Data da Aposta', auto_now_add=True)
    settled_at = models.DateTimeField('Liquidada em', null=True, blank=True)

    class Meta:
        verbose_name = 'Aposta'
        verbose_name_plural = 'Apostas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.odd} - R$ {self.amount}'

    def save(self, *args, **kwargs):
        if not self.odd_value:
            self.odd_value = self.odd.value
        if not self.potential_win:
            self.potential_win = self.amount * self.odd_value
        super().save(*args, **kwargs)

    def win(self):
        """Marca aposta como ganha e credita o valor."""
        from wallet.models import Wallet
        self.status = 'won'
        self.settled_at = timezone.now()
        self.save()

        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.bet_credit(
            self.potential_win,
            f'Ganho: {self.odd.market.event} - {self.odd.name}'
        )

    def lose(self):
        """Marca aposta como perdida."""
        self.status = 'lost'
        self.settled_at = timezone.now()
        self.save()

    def cancel(self):
        """Cancela a aposta e reembolsa."""
        from wallet.models import Wallet
        self.status = 'cancelled'
        self.settled_at = timezone.now()
        self.save()

        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.deposit(self.amount, f'Reembolso: {self.odd.market.event}')
