from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import Sport, League, Event, Market, Odd, Bet


# --- Serializers ---

class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'slug', 'icon']


class OddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Odd
        fields = ['id', 'name', 'value', 'selection_key', 'is_active']


class MarketSerializer(serializers.ModelSerializer):
    odds = OddSerializer(many=True, read_only=True)

    class Meta:
        model = Market
        fields = ['id', 'name', 'slug', 'odds', 'is_active']


class EventSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source='league.sport.name', read_only=True)
    league_name = serializers.CharField(source='league.name', read_only=True)
    markets = MarketSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'home_team', 'away_team', 'start_time', 'status',
            'home_score', 'away_score', 'is_featured', 'sport_name',
            'league_name', 'markets',
        ]


class BetSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    selection = serializers.CharField(source='odd.name', read_only=True)

    class Meta:
        model = Bet
        fields = [
            'id', 'amount', 'odd_value', 'potential_win', 'status',
            'created_at', 'settled_at', 'event_name', 'selection',
        ]

    def get_event_name(self, obj):
        return str(obj.odd.market.event)


# --- ViewSets ---

class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Event.objects.select_related('league', 'league__sport').prefetch_related('markets__odds')
        sport = self.request.query_params.get('sport')
        status_param = self.request.query_params.get('status')
        if sport:
            qs = qs.filter(league__sport__slug=sport)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=False, methods=['get'])
    def live(self, request):
        events = self.get_queryset().filter(status='live')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)


class BetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bet.objects.filter(user=self.request.user).select_related('odd__market__event')


# --- Router & URLs ---

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'bets', BetViewSet, basename='bet')

urlpatterns = [
    path('', include(router.urls)),
]
