from django.urls import path
from . import views
from . import web3_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # Web3 / MetaMask
    path('api/web3/nonce/', web3_views.web3_nonce, name='web3_nonce'),
    path('api/web3/verify/', web3_views.web3_verify, name='web3_verify'),
    path('api/web3/link/', web3_views.web3_link, name='web3_link'),
]
