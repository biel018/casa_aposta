# Casa de Apostas 🎲

Sistema completo de casa de apostas esportivas desenvolvido com Django.

## Funcionalidades

- **Cadastro/Login de Usuários** - Registro, autenticação e perfil
- **Carteira Digital** - Depósito e saque com histórico de transações
- **Apostas Esportivas** - Aposte em eventos com odds dinâmicas
- **Painel Administrativo** - Gerencie eventos, odds, usuários e pagamentos
- **Odds em Tempo Real** - Atualização dinâmica de odds via WebSocket
- **Histórico de Apostas** - Acompanhe todas as suas apostas

## Tecnologias

- Python 3.12+
- Django 5.1
- Django REST Framework
- Django Channels (WebSocket para odds em tempo real)
- SQLite (desenvolvimento) / PostgreSQL (produção)
- Bootstrap 5 (frontend)

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Criar superusuário (admin)
python manage.py createsuperuser

# Popular banco com dados de exemplo
python manage.py seed_data

# Rodar servidor
python manage.py runserver
```

## Acesso

- **Site**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **API**: http://localhost:8000/api/

## Estrutura

```
├── config/          # Configurações do Django
├── accounts/        # App de usuários e autenticação
├── wallet/          # App de carteira (depósito/saque)
├── betting/         # App de apostas e eventos
├── templates/       # Templates globais
└── static/          # Arquivos estáticos (CSS, JS)
```
