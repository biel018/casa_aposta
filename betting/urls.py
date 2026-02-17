from django.urls import path
from . import views

app_name = 'betting'

urlpatterns = [
    path('', views.events_list, name='events'),
    path('live/', views.live_events, name='live'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/<int:pk>/bet/', views.place_bet, name='place_bet'),
    path('my-bets/', views.my_bets, name='my_bets'),
]
