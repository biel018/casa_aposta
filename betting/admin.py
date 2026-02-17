from django.contrib import admin
from .models import Sport, League, Event, Market, Odd, Bet


class OddInline(admin.TabularInline):
    model = Odd
    extra = 3
    fields = ['name', 'value', 'selection_key', 'is_active']


class MarketInline(admin.TabularInline):
    model = Market
    extra = 1
    show_change_link = True


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ['name', 'sport', 'country', 'is_active']
    list_filter = ['sport', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'league', 'start_time', 'status', 'home_score', 'away_score', 'is_featured']
    list_filter = ['status', 'is_featured', 'league__sport', 'league']
    list_editable = ['status', 'home_score', 'away_score', 'is_featured']
    search_fields = ['home_team', 'away_team']
    inlines = [MarketInline]
    date_hierarchy = 'start_time'

    actions = ['settle_bets_action', 'mark_as_live', 'mark_as_finished']

    def settle_bets_action(self, request, queryset):
        for event in queryset.filter(status='finished'):
            event.settle_bets()
        self.message_user(request, 'Apostas liquidadas com sucesso!')
    settle_bets_action.short_description = 'Liquidar apostas dos eventos selecionados'

    def mark_as_live(self, request, queryset):
        queryset.update(status='live')
    mark_as_live.short_description = 'Marcar como Ao Vivo'

    def mark_as_finished(self, request, queryset):
        queryset.update(status='finished')
    mark_as_finished.short_description = 'Marcar como Encerrado'


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'event__home_team', 'event__away_team']
    inlines = [OddInline]


@admin.register(Odd)
class OddAdmin(admin.ModelAdmin):
    list_display = ['name', 'market', 'value', 'selection_key', 'is_active', 'updated_at']
    list_filter = ['is_active', 'market__event__league__sport']
    list_editable = ['value', 'is_active']
    search_fields = ['name', 'market__event__home_team']


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ['user', 'odd', 'amount', 'odd_value', 'potential_win', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'odd__name']
    readonly_fields = ['created_at', 'settled_at']
    date_hierarchy = 'created_at'

    actions = ['cancel_bets']

    def cancel_bets(self, request, queryset):
        for bet in queryset.filter(status='pending'):
            bet.cancel()
        self.message_user(request, 'Apostas canceladas e reembolsadas.')
    cancel_bets.short_description = 'Cancelar e reembolsar apostas selecionadas'
