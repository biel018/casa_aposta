from django.urls import path
from . import api_views

urlpatterns = [
    path('predictions/', api_views.api_markets, name='api_markets'),
    path('predictions/<slug:slug>/', api_views.api_market_detail, name='api_market_detail'),
    path('predictions/order/place/', api_views.api_place_order, name='api_place_order'),
    path('predictions/order/<uuid:order_id>/cancel/', api_views.api_cancel_order, name='api_cancel_order'),
    path('predictions/positions/', api_views.api_positions, name='api_positions'),
    path('predictions/price-history/<int:outcome_id>/', api_views.api_price_history, name='api_price_history'),
]
