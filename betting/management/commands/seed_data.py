from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from betting.models import Sport, League, Event, Market, Odd


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de exemplo'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados de exemplo...')

        # Esportes
        futebol, _ = Sport.objects.get_or_create(
            slug='futebol', defaults={'name': 'Futebol', 'icon': 'bi-dribbble', 'order': 1}
        )
        basquete, _ = Sport.objects.get_or_create(
            slug='basquete', defaults={'name': 'Basquete', 'icon': 'bi-basketball', 'order': 2}
        )
        tenis, _ = Sport.objects.get_or_create(
            slug='tenis', defaults={'name': 'Tênis', 'icon': 'bi-circle', 'order': 3}
        )
        mma, _ = Sport.objects.get_or_create(
            slug='mma', defaults={'name': 'MMA/UFC', 'icon': 'bi-person-arms-up', 'order': 4}
        )
        esports, _ = Sport.objects.get_or_create(
            slug='esports', defaults={'name': 'E-Sports', 'icon': 'bi-controller', 'order': 5}
        )

        # Ligas de Futebol
        brasileirao, _ = League.objects.get_or_create(
            slug='brasileirao-a', defaults={'sport': futebol, 'name': 'Brasileirão Série A', 'country': 'Brasil'}
        )
        champions, _ = League.objects.get_or_create(
            slug='champions-league', defaults={'sport': futebol, 'name': 'Champions League', 'country': 'Europa'}
        )
        premier, _ = League.objects.get_or_create(
            slug='premier-league', defaults={'sport': futebol, 'name': 'Premier League', 'country': 'Inglaterra'}
        )
        libertadores, _ = League.objects.get_or_create(
            slug='libertadores', defaults={'sport': futebol, 'name': 'Copa Libertadores', 'country': 'América do Sul'}
        )

        # Ligas de Basquete
        nba, _ = League.objects.get_or_create(
            slug='nba', defaults={'sport': basquete, 'name': 'NBA', 'country': 'EUA'}
        )

        # Ligas de Tênis
        atp, _ = League.objects.get_or_create(
            slug='atp', defaults={'sport': tenis, 'name': 'ATP Tour', 'country': 'Internacional'}
        )

        # UFC
        ufc, _ = League.objects.get_or_create(
            slug='ufc', defaults={'sport': mma, 'name': 'UFC', 'country': 'Internacional'}
        )

        # E-Sports
        lol, _ = League.objects.get_or_create(
            slug='cblol', defaults={'sport': esports, 'name': 'CBLOL', 'country': 'Brasil'}
        )

        now = timezone.now()

        # Eventos de Futebol - Brasileirão
        games = [
            (brasileirao, 'Flamengo', 'Palmeiras', now + timedelta(hours=2), True),
            (brasileirao, 'Corinthians', 'São Paulo', now + timedelta(hours=5), True),
            (brasileirao, 'Grêmio', 'Internacional', now + timedelta(days=1), False),
            (brasileirao, 'Santos', 'Fluminense', now + timedelta(days=1, hours=3), False),
            (brasileirao, 'Atlético-MG', 'Cruzeiro', now + timedelta(days=2), False),
            (brasileirao, 'Botafogo', 'Vasco', now + timedelta(days=2, hours=2), True),
            # Champions League
            (champions, 'Real Madrid', 'Manchester City', now + timedelta(days=3), True),
            (champions, 'Barcelona', 'Bayern München', now + timedelta(days=3, hours=2), True),
            (champions, 'PSG', 'Inter de Milão', now + timedelta(days=4), False),
            # Premier League
            (premier, 'Liverpool', 'Arsenal', now + timedelta(days=1, hours=5), True),
            (premier, 'Chelsea', 'Manchester United', now + timedelta(days=2, hours=4), False),
            # Libertadores
            (libertadores, 'Flamengo', 'River Plate', now + timedelta(days=5), True),
            (libertadores, 'Palmeiras', 'Boca Juniors', now + timedelta(days=5, hours=3), True),
        ]

        for league, home, away, start, featured in games:
            event, created = Event.objects.get_or_create(
                league=league,
                home_team=home,
                away_team=away,
                defaults={
                    'start_time': start,
                    'is_featured': featured,
                }
            )
            if created:
                # Mercado: Resultado Final (1X2)
                market, _ = Market.objects.get_or_create(
                    event=event, slug='resultado-final',
                    defaults={'name': 'Resultado Final'}
                )
                Odd.objects.get_or_create(market=market, selection_key='home', defaults={
                    'name': f'Vitória {home}', 'value': Decimal('1.85')
                })
                Odd.objects.get_or_create(market=market, selection_key='draw', defaults={
                    'name': 'Empate', 'value': Decimal('3.40')
                })
                Odd.objects.get_or_create(market=market, selection_key='away', defaults={
                    'name': f'Vitória {away}', 'value': Decimal('4.20')
                })

                # Mercado: Ambas Marcam
                market2, _ = Market.objects.get_or_create(
                    event=event, slug='ambas-marcam',
                    defaults={'name': 'Ambas Marcam'}
                )
                Odd.objects.get_or_create(market=market2, selection_key='yes', defaults={
                    'name': 'Sim', 'value': Decimal('1.90')
                })
                Odd.objects.get_or_create(market=market2, selection_key='no', defaults={
                    'name': 'Não', 'value': Decimal('1.85')
                })

                # Mercado: Total de Gols
                market3, _ = Market.objects.get_or_create(
                    event=event, slug='total-gols',
                    defaults={'name': 'Total de Gols (2.5)'}
                )
                Odd.objects.get_or_create(market=market3, selection_key='over', defaults={
                    'name': 'Mais de 2.5', 'value': Decimal('2.10')
                })
                Odd.objects.get_or_create(market=market3, selection_key='under', defaults={
                    'name': 'Menos de 2.5', 'value': Decimal('1.70')
                })

        # Eventos de Basquete
        nba_games = [
            ('Lakers', 'Celtics', now + timedelta(hours=8)),
            ('Warriors', 'Nets', now + timedelta(days=1, hours=6)),
        ]
        for home, away, start in nba_games:
            event, created = Event.objects.get_or_create(
                league=nba, home_team=home, away_team=away,
                defaults={'start_time': start, 'is_featured': True}
            )
            if created:
                market, _ = Market.objects.get_or_create(
                    event=event, slug='vencedor', defaults={'name': 'Vencedor'}
                )
                Odd.objects.get_or_create(market=market, selection_key='home', defaults={
                    'name': f'Vitória {home}', 'value': Decimal('1.75')
                })
                Odd.objects.get_or_create(market=market, selection_key='away', defaults={
                    'name': f'Vitória {away}', 'value': Decimal('2.05')
                })

        # Evento UFC
        event, created = Event.objects.get_or_create(
            league=ufc, home_team='Alex Pereira', away_team='Israel Adesanya',
            defaults={'start_time': now + timedelta(days=7), 'is_featured': True}
        )
        if created:
            market, _ = Market.objects.get_or_create(
                event=event, slug='vencedor', defaults={'name': 'Vencedor'}
            )
            Odd.objects.get_or_create(market=market, selection_key='home', defaults={
                'name': 'Alex Pereira', 'value': Decimal('1.65')
            })
            Odd.objects.get_or_create(market=market, selection_key='away', defaults={
                'name': 'Israel Adesanya', 'value': Decimal('2.25')
            })

        self.stdout.write(self.style.SUCCESS('Dados de exemplo criados com sucesso!'))
        self.stdout.write(f'  - {Sport.objects.count()} esportes')
        self.stdout.write(f'  - {League.objects.count()} ligas')
        self.stdout.write(f'  - {Event.objects.count()} eventos')
        self.stdout.write(f'  - {Market.objects.count()} mercados')
        self.stdout.write(f'  - {Odd.objects.count()} odds')
