from django.db import models
from django.conf import settings
from decimal import Decimal


class Wallet(models.Model):
    """Carteira digital do usuário."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='Usuário'
    )
    balance = models.DecimalField('Saldo', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Carteira'
        verbose_name_plural = 'Carteiras'

    def __str__(self):
        return f'Carteira de {self.user.username} - R$ {self.balance}'

    def deposit(self, amount, description=''):
        """Realiza um depósito na carteira."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('O valor do depósito deve ser positivo.')
        self.balance += amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            type=Transaction.DEPOSIT,
            amount=amount,
            balance_after=self.balance,
            description=description or 'Depósito'
        )

    def withdraw(self, amount, description=''):
        """Realiza um saque da carteira."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('O valor do saque deve ser positivo.')
        if amount > self.balance:
            raise ValueError('Saldo insuficiente.')
        self.balance -= amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            type=Transaction.WITHDRAWAL,
            amount=amount,
            balance_after=self.balance,
            description=description or 'Saque'
        )

    def bet_debit(self, amount, description=''):
        """Débito para aposta."""
        amount = Decimal(str(amount))
        if amount > self.balance:
            raise ValueError('Saldo insuficiente para esta aposta.')
        self.balance -= amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            type=Transaction.BET,
            amount=amount,
            balance_after=self.balance,
            description=description or 'Aposta realizada'
        )

    def bet_credit(self, amount, description=''):
        """Crédito de ganho de aposta."""
        amount = Decimal(str(amount))
        self.balance += amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            type=Transaction.WIN,
            amount=amount,
            balance_after=self.balance,
            description=description or 'Ganho de aposta'
        )


class Transaction(models.Model):
    """Registro de transação financeira."""
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    BET = 'bet'
    WIN = 'win'
    REFUND = 'refund'

    TYPE_CHOICES = [
        (DEPOSIT, 'Depósito'),
        (WITHDRAWAL, 'Saque'),
        (BET, 'Aposta'),
        (WIN, 'Ganho'),
        (REFUND, 'Reembolso'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelado'),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Carteira'
    )
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    balance_after = models.DecimalField('Saldo Após', max_digits=12, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='completed')
    description = models.CharField('Descrição', max_length=255, blank=True)
    created_at = models.DateTimeField('Data', auto_now_add=True)

    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_type_display()} - R$ {self.amount} ({self.wallet.user.username})'

    @property
    def is_credit(self):
        return self.type in [self.DEPOSIT, self.WIN, self.REFUND]


class CryptoDeposit(models.Model):
    """Registro de depósito em criptomoeda."""
    CRYPTO_CHOICES = [
        ('ETH', 'Ethereum (ETH)'),
        ('USDT', 'Tether (USDT)'),
        ('USDC', 'USD Coin (USDC)'),
        ('BTC', 'Bitcoin (BTC)'),
        ('MATIC', 'Polygon (MATIC)'),
    ]
    NETWORK_CHOICES = [
        ('ethereum', 'Ethereum Mainnet'),
        ('polygon', 'Polygon'),
        ('bsc', 'BNB Smart Chain'),
        ('arbitrum', 'Arbitrum'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirming', 'Confirmando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE,
        related_name='crypto_deposits', verbose_name='Carteira'
    )
    crypto = models.CharField('Criptomoeda', max_length=10, choices=CRYPTO_CHOICES)
    network = models.CharField('Rede', max_length=20, choices=NETWORK_CHOICES, default='ethereum')
    amount_crypto = models.DecimalField('Valor Crypto', max_digits=18, decimal_places=8)
    amount_usd = models.DecimalField('Valor USD', max_digits=12, decimal_places=2)
    tx_hash = models.CharField('TX Hash', max_length=66, unique=True)
    from_address = models.CharField('Endereço Origem', max_length=42)
    to_address = models.CharField('Endereço Destino', max_length=42)
    confirmations = models.IntegerField('Confirmações', default=0)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    confirmed_at = models.DateTimeField('Confirmado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Depósito Crypto'
        verbose_name_plural = 'Depósitos Crypto'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.amount_crypto} {self.crypto} - {self.wallet.user.username}'
