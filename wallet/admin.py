from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['balance', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'balance_after', 'status', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['wallet__user__username', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
