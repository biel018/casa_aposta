from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modelo de usuário customizado com campos adicionais."""
    cpf = models.CharField('CPF', max_length=14, unique=True, blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    date_of_birth = models.DateField('Data de Nascimento', null=True, blank=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField('Verificado', default=False)
    # Web3 / MetaMask
    wallet_address = models.CharField('Endereço Wallet', max_length=42, unique=True, blank=True, null=True,
                                      help_text='Endereço Ethereum (MetaMask)')
    nonce = models.CharField('Nonce', max_length=100, blank=True, default='',
                             help_text='Nonce para autenticação Web3')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    @property
    def balance(self):
        """Retorna o saldo atual da carteira do usuário."""
        from wallet.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=self)
        return wallet.balance
