"""Seed data para mercados de previsão estilo Polymarket."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from predictions.models import Category, PredictionMarket, MarketOutcome, PriceHistory


class Command(BaseCommand):
    help = 'Cria dados iniciais de mercados de previsão'

    def handle(self, *args, **options):
        self.stdout.write('Criando categorias...')

        categories_data = [
            {'name': 'Política', 'slug': 'politica', 'icon': 'bi-bank', 'color': 'primary', 'order': 1},
            {'name': 'Crypto', 'slug': 'crypto', 'icon': 'bi-currency-bitcoin', 'color': 'warning', 'order': 2},
            {'name': 'Esportes', 'slug': 'esportes', 'icon': 'bi-trophy', 'color': 'success', 'order': 3},
            {'name': 'Economia', 'slug': 'economia', 'icon': 'bi-graph-up-arrow', 'color': 'info', 'order': 4},
            {'name': 'Tecnologia', 'slug': 'tecnologia', 'icon': 'bi-cpu', 'color': 'danger', 'order': 5},
            {'name': 'Cultura Pop', 'slug': 'cultura-pop', 'icon': 'bi-stars', 'color': 'secondary', 'order': 6},
        ]

        cats = {}
        for cd in categories_data:
            cat, _ = Category.objects.get_or_create(slug=cd['slug'], defaults=cd)
            cats[cd['slug']] = cat
            self.stdout.write(f'  ✓ {cat.name}')

        self.stdout.write('\nCriando mercados...')

        markets_data = [
            # Política
            {
                'category': cats['politica'],
                'title': 'Lula será reeleito em 2026?',
                'slug': 'lula-reeleito-2026',
                'description': 'Este mercado será resolvido como SIM se Luiz Inácio Lula da Silva for reeleito presidente do Brasil nas eleições de 2026.',
                'rules': 'Resolução baseada no resultado oficial do TSE.',
                'end_date': timezone.now() + timedelta(days=365),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.3200')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.6800')},
                ],
            },
            {
                'category': cats['politica'],
                'title': 'Trump vence eleição 2028?',
                'slug': 'trump-2028',
                'description': 'Trump será eleito na eleição presidencial dos EUA em 2028? (Nota: constitucionalmente inelegível, mas mercado especulativo).',
                'rules': 'Resolução baseada no resultado oficial da eleição.',
                'end_date': timezone.now() + timedelta(days=1200),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.0500')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.9500')},
                ],
            },
            {
                'category': cats['politica'],
                'title': 'Reforma tributária será implementada até 2026?',
                'slug': 'reforma-tributaria-2026',
                'description': 'A reforma tributária aprovada pelo Congresso será efetivamente implementada até dezembro de 2026?',
                'rules': 'Resolução baseada na publicação oficial de medidas regulatórias completas.',
                'end_date': timezone.now() + timedelta(days=400),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.5500')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.4500')},
                ],
            },
            # Crypto
            {
                'category': cats['crypto'],
                'title': 'Bitcoin acima de $150K até fim de 2025?',
                'slug': 'btc-150k-2025',
                'description': 'O preço do Bitcoin (BTC/USD) atingirá ou ultrapassará $150,000 antes de 31 de dezembro de 2025?',
                'rules': 'Resolução baseada no preço do BTC/USD no CoinGecko.',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.4200')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.5800')},
                ],
            },
            {
                'category': cats['crypto'],
                'title': 'Ethereum ultrapassa $10K até 2025?',
                'slug': 'eth-10k-2025',
                'description': 'O preço do Ethereum (ETH/USD) atingirá $10,000 antes do fim de 2025?',
                'rules': 'Resolução baseada no preço do ETH/USD no CoinGecko.',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.1800')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.8200')},
                ],
            },
            {
                'category': cats['crypto'],
                'title': 'Solana (SOL) acima de $500 até 2026?',
                'slug': 'sol-500-2026',
                'description': 'O preço da Solana (SOL/USD) atingirá $500 antes de 2026?',
                'rules': 'Resolução baseada no preço do SOL/USD no CoinGecko.',
                'end_date': timezone.now() + timedelta(days=365),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.2500')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.7500')},
                ],
            },
            # Esportes
            {
                'category': cats['esportes'],
                'title': 'Brasil ganha a Copa do Mundo 2026?',
                'slug': 'brasil-copa-2026',
                'description': 'A seleção brasileira vencerá a Copa do Mundo da FIFA 2026 nos EUA, Canadá e México?',
                'rules': 'Resolução baseada no resultado final da FIFA.',
                'end_date': timezone.now() + timedelta(days=365),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.1500')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.8500')},
                ],
            },
            {
                'category': cats['esportes'],
                'title': 'Flamengo campeão da Libertadores 2025?',
                'slug': 'flamengo-libertadores-2025',
                'description': 'O Flamengo vencerá a Copa Libertadores 2025?',
                'rules': 'Resolução baseada no resultado da final da CONMEBOL Libertadores.',
                'end_date': timezone.now() + timedelta(days=150),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.2000')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.8000')},
                ],
            },
            # Economia
            {
                'category': cats['economia'],
                'title': 'Selic abaixo de 10% até fim de 2025?',
                'slug': 'selic-10-2025',
                'description': 'A taxa Selic (taxa básica de juros do Brasil) ficará abaixo de 10% a.a. até 31/12/2025?',
                'rules': 'Resolução baseada na decisão do COPOM/Banco Central.',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.1200')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.8800')},
                ],
            },
            {
                'category': cats['economia'],
                'title': 'Dólar abaixo de R$5,00 até 2025?',
                'slug': 'dolar-5-2025',
                'description': 'O dólar americano ficará abaixo de R$5,00 até o final de 2025?',
                'rules': 'Resolução baseada na cotação oficial do Banco Central (PTAX).',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.0800')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.9200')},
                ],
            },
            # Tecnologia
            {
                'category': cats['tecnologia'],
                'title': 'Apple lança óculos AR consumer até 2026?',
                'slug': 'apple-ar-glasses-2026',
                'description': 'A Apple lançará óculos de realidade aumentada para consumidores (não Vision Pro) até fim de 2026?',
                'rules': 'Resolução baseada em anúncio oficial da Apple.',
                'end_date': timezone.now() + timedelta(days=500),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.3000')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.7000')},
                ],
            },
            {
                'category': cats['tecnologia'],
                'title': 'AGI será alcançada até 2027?',
                'slug': 'agi-2027',
                'description': 'Uma inteligência artificial geral (AGI) será reconhecida por pelo menos 3 das 5 maiores big techs até 2027?',
                'rules': 'Resolução baseada em declarações oficiais de Google, Microsoft, OpenAI, Meta ou Apple.',
                'end_date': timezone.now() + timedelta(days=700),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.2200')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.7800')},
                ],
            },
            # Cultura Pop
            {
                'category': cats['cultura-pop'],
                'title': 'GTA 6 lança até fim de 2025?',
                'slug': 'gta6-2025',
                'description': 'O jogo Grand Theft Auto VI será lançado oficialmente até 31 de dezembro de 2025?',
                'rules': 'Resolução baseada na data de lançamento oficial pela Rockstar Games.',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': True,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.7500')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.2500')},
                ],
            },
            {
                'category': cats['cultura-pop'],
                'title': 'Novo álbum de Kendrick Lamar até 2025?',
                'slug': 'kendrick-album-2025',
                'description': 'Kendrick Lamar lançará um novo álbum de estúdio até o fim de 2025?',
                'rules': 'Resolução baseada no lançamento oficial em plataformas de streaming.',
                'end_date': timezone.now() + timedelta(days=180),
                'is_featured': False,
                'outcomes': [
                    {'name': 'Sim', 'slug': 'yes', 'price': Decimal('0.6000')},
                    {'name': 'Não', 'slug': 'no', 'price': Decimal('0.4000')},
                ],
            },
        ]

        for md in markets_data:
            outcomes_data = md.pop('outcomes')
            market, created = PredictionMarket.objects.get_or_create(
                slug=md['slug'], defaults=md
            )
            if created:
                for od in outcomes_data:
                    outcome = MarketOutcome.objects.create(market=market, **od)
                    # Criar histórico de preço inicial
                    PriceHistory.objects.create(
                        outcome=outcome, price=od['price'], volume=Decimal('0')
                    )
                self.stdout.write(f'  ✓ {market.title}')
            else:
                self.stdout.write(f'  - {market.title} (já existe)')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Seed completo! {PredictionMarket.objects.count()} mercados, '
            f'{MarketOutcome.objects.count()} outcomes, '
            f'{Category.objects.count()} categorias.'
        ))
