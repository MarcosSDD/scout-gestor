# SCOUTS-GESTOR

Sistema de gestión para grupos scouts de Chile. Es un monorepo con Django/DRF en `backend/` y React/Vite en `frontend/`.

## Estructura

```text
backend/    # Django, API, migraciones, media y colección Postman
frontend/   # React, Vite y pruebas de interfaz
docs/       # Alcance y planes de implementación
```

La configuración compartida (`docker-compose.yml`, `.env.example` y archivos de herramientas) permanece en la raíz.

## Desarrollo con Docker (recomendado)

Requiere Docker Compose. Crea el entorno local y levanta PostgreSQL, Django y Vite con recarga en caliente:

```bash
cp .env.example .env
docker compose up --build
```

Servicios disponibles:

- Frontend: <http://localhost:5173>
- Backend/admin: <http://localhost:8007/admin/>
- API health: <http://localhost:8007/api/v1/health/>
- PostgreSQL: `localhost:5432`

El frontend usa el proxy de Vite: el navegador solicita `/api` y `/media` al origen `5173`, y Vite los reenvía al servicio `backend`. No requiere CORS para este flujo.

El backend ejecuta `migrate` y `seed_catalogos` antes de iniciar. Los datos PostgreSQL y los archivos subidos persisten en los volúmenes `postgres_data` y `media_data`.

Comandos útiles:

```bash
docker compose exec backend python manage.py test
docker compose exec backend python manage.py makemigrations --check
docker compose exec backend python manage.py createsuperuser
docker compose exec frontend npm run test:run
docker compose down
```

No uses `docker compose down -v` salvo que quieras eliminar explícitamente las bases y archivos locales persistidos.

> El Compose incluido es solo para desarrollo local. No usar Vite, `runserver`, credenciales de ejemplo ni PostgreSQL publicado para producción.

## Desarrollo sin Docker

### Backend

Requiere Python 3.13+. Django no carga `.env` automáticamente:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
set -a && source .env && set +a
python backend/manage.py migrate
python backend/manage.py seed_catalogos
python backend/manage.py runserver 8007
```

Si `POSTGRES_DB` no está definido, Django usa `backend/db.sqlite3`.

### Frontend

Requiere Node `24.16.0`:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

Fuera de Docker, el proxy apunta a `http://localhost:8007`. Dentro de Compose apunta automáticamente a `http://backend:8007`.

## Grupo demo local y RBAC

Solo para SQLite local con `DJANGO_DEBUG=true`:

```bash
unset POSTGRES_DB
export DJANGO_DEBUG=true
python backend/manage.py migrate
python backend/manage.py seed_grupo_demo
```

Para reconstruir los datos demo identificados:

```bash
python backend/manage.py seed_grupo_demo --reset --no-input
```

No se permite ejecutar este comando con PostgreSQL ni con `DEBUG=false`.

## Validación

```bash
python backend/manage.py check
python backend/manage.py test
python backend/manage.py test api.tests
python backend/manage.py makemigrations --check
npm --prefix frontend run test:run
npm --prefix frontend run build
npm --prefix frontend run lint
```

## Seguridad y API

- API base: `/api/v1/`; usa JWT exclusivamente.
- La autorización crítica y el RBAC se aplican en Django/DRF; el frontend solo refleja permisos para UX.
- Las respuestas exitosas usan `{success, message, data, meta?}`; los errores usan `{success: false, error: {code, message, details}}`.
- Los archivos privados se descargan por endpoints DRF autorizados; no se publica `MEDIA_ROOT` genéricamente.
- Nunca subir `.env` ni reutilizar valores de desarrollo en entornos compartidos.

## Documentación

- `docs/project-spec.md`
- `docs/implementation-plan-backend-api-spec.md`
- `docs/frontend-implementation-plan-spec.md`
- `docs/frontend-ui-responsive-context-spec.md`
- `docs/post-entrega-10-implementation-plan-spec.md`
