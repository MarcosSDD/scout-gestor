# SCOUTS-GESTOR Backend

![Coverage Status](https://img.shields.io/badge/Coverage%20Status-Not%20Configured-lightgrey)


Backend en Django para la gestion de grupos scouts en Chile. Este repositorio contiene el modelado y configuracion de admin y base API (`/api/v1/`) para seguir avanzando por etapas co el gentil auspisio  de cualquier colaborador que se pueda integrar.

## Environment

- Python 3.13+
- Django 5.2+
- Base de datos:
  - SQLite por defecto (si `POSTGRES_DB` no existe)
  - PostgreSQL cuando se configuran variables `POSTGRES_*`

## Bibliotecas principales

- `django`
- `psycopg[binary]`
- `djangorestframework`
- `django-oauth-toolkit`
- `djangorestframework-simplejwt`

## Configurar `.env`

1. Copia el ejemplo:

```bash
cp .env.example .env
```

2. Completa al menos `DJANGO_SECRET_KEY`.

3. Carga variables antes de ejecutar comandos (Django no carga `.env` automaticamente):

```bash
set -a
source .env
set +a
```

Variables disponibles en `.env.example`:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

## Como correr el proyecto

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

set -a && source .env && set +a

python manage.py migrate
python manage.py seed_catalogos
python manage.py runserver
```

Rutas utiles:

- Admin: `http://127.0.0.1:8000/admin/`
- API health: `http://127.0.0.1:8000/api/v1/health/`

## Como correr los tests

Suite completa:

```bash
python manage.py test
```

Tests focalizados:

```bash
python manage.py test api.tests
python manage.py test organizacion.tests
python manage.py test unidades.tests.AdultoUnidadRolTests
```

## Lint / formato

Actualmente el repositorio no tiene configuracion de lint/formatter (no hay `ruff`, `flake8`, `black` ni `pre-commit` definidos). Por Ahora se utiliza black n local

## Cobertura

El proyecto aun no tiene pipeline de cobertura configurado (por eso el badge esta en `Not Configured`).