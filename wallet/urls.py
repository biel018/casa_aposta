from django.urls import path
from . import views
from . import crypto_views

app_name = 'wallet'

urlpatterns = [
    path('', views.wallet_view, name='wallet'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('history/', views.transaction_history_view, name='history'),
    # Crypto
    path('crypto/', crypto_views.crypto_deposit_view, name='crypto_deposit'),
    path('api/crypto/prices/', crypto_views.crypto_prices_api, name='crypto_prices'),
    path('api/crypto/confirm/', crypto_views.crypto_deposit_confirm, name='crypto_confirm'),
    path('api/crypto/send-tx/', crypto_views.crypto_send_tx, name='crypto_send_tx'),
]
