from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('', views.market_list, name='market_list'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('market/<slug:slug>/', views.market_detail, name='market_detail'),
    path('market/<slug:slug>/order/', views.place_order, name='place_order'),
    path('order/<uuid:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
]
