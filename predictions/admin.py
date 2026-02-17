from django.contrib import admin
from .models import (
    Category, PredictionMarket, MarketOutcome,
    Order, Trade, Position, PriceHistory
)


class MarketOutcomeInline(admin.TabularInline):
    model = MarketOutcome
    extra = 2
    fields = ['name', 'slug', 'price', 'is_winner']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']


@admin.register(PredictionMarket)
class PredictionMarketAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'total_volume', 'end_date', 'is_featured']
    list_filter = ['status', 'category', 'is_featured']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [MarketOutcomeInline]
    date_hierarchy = 'end_date'

    actions = ['resolve_yes', 'resolve_no', 'close_market']

    def resolve_yes(self, request, queryset):
        from .engine import MatchingEngine
        for market in queryset:
            yes_outcome = market.outcomes.filter(slug='yes').first()
            if yes_outcome:
                MatchingEngine.resolve_market(market, 'yes')
        self.message_user(request, 'Mercados resolvidos como SIM')
    resolve_yes.short_description = 'Resolver como SIM (Yes)'

    def resolve_no(self, request, queryset):
        from .engine import MatchingEngine
        for market in queryset:
            no_outcome = market.outcomes.filter(slug='no').first()
            if no_outcome:
                MatchingEngine.resolve_market(market, 'no')
        self.message_user(request, 'Mercados resolvidos como NÃO')
    resolve_no.short_description = 'Resolver como NÃO (No)'

    def close_market(self, request, queryset):
        queryset.update(status='closed')
    close_market.short_description = 'Fechar mercados'


@admin.register(MarketOutcome)
class MarketOutcomeAdmin(admin.ModelAdmin):
    list_display = ['name', 'market', 'price', 'price_percent', 'total_shares', 'is_winner']
    list_filter = ['is_winner', 'market__category']
    search_fields = ['name', 'market__title']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'outcome', 'side', 'price', 'quantity', 'filled_quantity', 'status', 'created_at']
    list_filter = ['side', 'status']
    search_fields = ['user__username']
    readonly_fields = ['id', 'created_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['id', 'outcome', 'price', 'quantity', 'created_at']
    readonly_fields = ['id', 'created_at']
    search_fields = ['outcome__name', 'outcome__market__title']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['user', 'outcome', 'shares', 'avg_price', 'current_value', 'unrealized_pnl']
    search_fields = ['user__username', 'outcome__name']
    list_filter = ['outcome__market__category']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['outcome', 'price', 'volume', 'timestamp']
    list_filter = ['outcome__market']
    date_hierarchy = 'timestamp'
