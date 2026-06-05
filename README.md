# SCOUTS-GESTOR

Sistema de gestion para grupos scouts de Chile. El repositorio contiene backend Django/DRF y frontend React/Vite.

## Estado actual

- Backend Django 5.2 + DRF implementado hasta Stage 7: auth JWT, catalogos, grupos, personas, unidades, dashboard y RBAC simple.
- Frontend React 19 + Vite implementado hasta Entrega 3: health, login, sesion, `/me`, logout, restauracion con refresh y `AppShell` autenticado.
- `formacion` tiene modelos/migraciones, pero `/api/v1/formacion/` aun no expone endpoints funcionales.
- Documentos de alcance: `project-spec.md`, `implementation-plan-backend-api-spec.md`, `frontend-implementation-plan-spec.md`, `frontend-ui-responsive-context-spec.md`.

## Requisitos

- Python 3.13+
- Node 24.16.0 para frontend
- Docker Compose opcional para backend + PostgreSQL

Backend:

- `django`
- `djangorestframework`
- `django-oauth-toolkit`
- `djangorestframework-simplejwt`
- `psycopg[binary]`
- `Pillow`

Frontend:

- React 19
- Vite 8
- TypeScript 6
- React Router 7
- Axios
- TanStack Query
- React Toastify
- Vitest + jsdom

## Configurar `.env`

```bash
cp .env.example .env
```

Completa al menos `DJANGO_SECRET_KEY`. Django no carga `.env` automaticamente; antes de comandos backend usa:

```bash
set -a && source .env && set +a
```

Variables principales:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

Si `POSTGRES_DB` no existe, Django usa SQLite local (`db.sqlite3`). Si existe, usa PostgreSQL.

## Levantar backend local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
set -a && source .env && set +a
python manage.py migrate
python manage.py seed_catalogos
python manage.py runserver 8007
```

Rutas utiles:

- Admin: `http://127.0.0.1:8007/admin/`
- API health: `http://127.0.0.1:8007/api/v1/health/`
- API root: `http://127.0.0.1:8007/api/v1/`

## Levantar backend con Docker

```bash
docker compose up --build
```

El servicio `web` ejecuta `migrate` + `seed_catalogos` antes de iniciar Django en `0.0.0.0:8007`.

Puertos segun `docker-compose.yml`:

- Django: `8007:8007`
- PostgreSQL: `5432:5432`

Comandos utiles:

```bash
docker compose run --rm web python manage.py test
docker compose run --rm web python manage.py createsuperuser
docker compose down -v
```

## Levantar frontend local

Usa Node `24.16.0` (`.node-version`, `frontend/.node-version`, `frontend/package.json`). `jsdom@29` puede fallar con Node 22 antiguo (`ERR_REQUIRE_ESM`).

```bash
cd frontend
npm install
npm run dev
```

El frontend levanta en Vite (`localhost:5173` por defecto). `frontend/vite.config.ts` proxya:

- `/api` -> `http://localhost:8007`
- `/media` -> `http://localhost:8007`

Para desarrollo fullstack, levanta primero backend en `8007` y luego `npm run dev` desde `frontend/`.

## Autenticacion frontend

- Login usa `POST /api/v1/auth/token/` con `username` y `password`.
- `access` se mantiene en memoria.
- `refresh` se guarda temporalmente en `sessionStorage`.
- Al recargar, `AuthProvider` llama `/auth/token/refresh/`, reemplaza el refresh rotado y luego carga usuario desde `GET /auth/me/`.
- Logout llama `/auth/logout/` con el refresh vigente cuando existe y siempre limpia estado local.
- La ruta autenticada actual es `/app`; `/sesion-iniciada` redirige a `/app`.

## Layout frontend

- `frontend/src/app-shell/`: header, sidebar, main content, right panel, mobile search y footer mobile.
- `frontend/public/images/`: imagenes publicas usadas por Vite (`scout.png`, `login-bg.jpg`).
- `sitio/` es referencia visual. No importar su jQuery, Bootstrap JS, Owl Carousel ni `sitio/css/style.css` completo en Vite; replicar patrones con React/CSS propio.

## Tests y validacion

Backend:

```bash
python manage.py test
python manage.py test api.tests
python manage.py makemigrations --check
```

Frontend desde `frontend/`:

```bash
npm run test:run
npm run build
npm run lint
```

No hay CI ni pre-commit configurados. Backend no tiene lint/formatter de repo; frontend usa ESLint via `npm run lint`.

## Convenciones API importantes

- API base: `/api/v1/`.
- OAuth2 esta configurado como clase de auth, pero no hay rutas `/o/` montadas.
- Permiso DRF global: `IsAuthenticated`; endpoints publicos deben declarar `AllowAny`.
- Respuestas exitosas usan `{success, message, data, meta?}` desde `api/v1/responses.py`.
- Errores usan `{success: false, error: {code, message, details}}` desde `api/v1/exceptions.py`.
- `POST/PATCH /api/v1/personas/` acepta JSON o `multipart/form-data` para `foto`.
- `GET /api/v1/grupos/{id}/estructura/` devuelve ramas, unidades, subgrupos, miembros y alertas etarias RN-05.
- `GET /api/v1/dashboard/grupo/{id}/` devuelve KPIs y alertas de cumpleanos proximos.
