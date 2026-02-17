from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Sport, League, Event, Market, Odd, Bet
from .forms import PlaceBetForm
from wallet.models import Wallet


def events_list(request):
    """Lista de todos os eventos disponíveis."""
    sports = Sport.objects.filter(is_active=True)
    sport_slug = request.GET.get('sport', '')
    search = request.GET.get('q', '')

    events = Event.objects.filter(
        status__in=['scheduled', 'live'],
        start_time__gte=timezone.now() - timezone.timedelta(hours=3),
    ).select_related('league', 'league__sport').prefetch_related('markets__odds')

    if sport_slug:
        events = events.filter(league__sport__slug=sport_slug)

    if search:
        events = events.filter(
            Q(home_team__icontains=search) | Q(away_team__icontains=search) |
            Q(league__name__icontains=search)
        )

    featured = events.filter(is_featured=True)[:5]

    return render(request, 'betting/events.html', {
        'events': events,
        'featured': featured,
        'sports': sports,
        'current_sport': sport_slug,
        'search': search,
    })


def event_detail(request, pk):
    """Detalhes de um evento com todos os mercados e odds."""
    event = get_object_or_404(
        Event.objects.select_related('league', 'league__sport').prefetch_related('markets__odds'),
        pk=pk
    )
    return render(request, 'betting/event_detail.html', {
        'event': event,
        'form': PlaceBetForm(),
    })


@login_required
def place_bet(request, pk):
    """Realiza uma aposta."""
    event = get_object_or_404(Event, pk=pk)

    if request.method != 'POST':
        return redirect('betting:event_detail', pk=pk)

    form = PlaceBetForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Dados inválidos. Tente novamente.')
        return redirect('betting:event_detail', pk=pk)

    odd = get_object_or_404(Odd, pk=form.cleaned_data['odd_id'], is_active=True)
    amount = form.cleaned_data['amount']

    # Verificar se o evento está aberto
    if event.status not in ['scheduled', 'live']:
        messages.error(request, 'Este evento não está mais disponível para apostas.')
        return redirect('betting:event_detail', pk=pk)

    # Debitar da carteira
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    try:
        wallet.bet_debit(amount, f'Aposta: {event} - {odd.name}')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('betting:event_detail', pk=pk)

    # Criar a aposta
    bet = Bet.objects.create(
        user=request.user,
        odd=odd,
        amount=amount,
        odd_value=odd.value,
        potential_win=amount * odd.value,
    )

    messages.success(
        request,
        f'Aposta realizada! R$ {amount:.2f} em "{odd.name}" @ {odd.value}. '
        f'Ganho potencial: R$ {bet.potential_win:.2f}'
    )
    return redirect('betting:my_bets')


@login_required
def my_bets(request):
    """Lista de apostas do usuário."""
    status_filter = request.GET.get('status', '')
    bets = Bet.objects.filter(user=request.user).select_related(
        'odd__market__event', 'odd__market__event__league'
    )

    if status_filter:
        bets = bets.filter(status=status_filter)

    # Estatísticas
    total_bets = Bet.objects.filter(user=request.user).count()
    won_bets = Bet.objects.filter(user=request.user, status='won').count()
    pending_bets = Bet.objects.filter(user=request.user, status='pending').count()

    return render(request, 'betting/my_bets.html', {
        'bets': bets,
        'current_status': status_filter,
        'total_bets': total_bets,
        'won_bets': won_bets,
        'pending_bets': pending_bets,
    })


def live_events(request):
    """Eventos ao vivo."""
    events = Event.objects.filter(status='live').select_related(
        'league', 'league__sport'
    ).prefetch_related('markets__odds')

    return render(request, 'betting/live.html', {'events': events})
