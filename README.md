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
- `django-cors-headers`
- `gunicorn` (imagen de producción)
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

- `DJANGO_SECRET_KEY`, obligatorio cuando `DJANGO_DEBUG=false`; usar un valor aleatorio provisto por el gestor de secretos de la plataforma.
- `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`. Producción requiere `false` y hosts explícitos, sin comodines.
- `DJANGO_CORS_ALLOWED_ORIGINS` y `DJANGO_CSRF_TRUSTED_ORIGINS`, listas CSV de orígenes completos y explícitos; déjalas vacías cuando frontend y API comparten origen.
- `DJANGO_SECURE_PROXY_SSL_HEADER=true` únicamente si un proxy confiable sobrescribe `X-Forwarded-Proto`.
- `DJANGO_SECURE_HSTS_SECONDS`, 31536000 por defecto en producción. `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` es `false` por defecto y solo debe activarse tras verificar todos los subdominios.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.

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

### Grupo demo local y RBAC

Solo para SQLite local con `DJANGO_DEBUG=true`, se puede crear una muestra completa para probar la UI y los alcances RBAC:

```bash
unset POSTGRES_DB
export DJANGO_DEBUG=true
python manage.py migrate
python manage.py seed_catalogos
python manage.py seed_grupo_demo
```

El comando también ejecuta `seed_catalogos`, es idempotente y crea `Grupo Scout Demo`, seis ramas/unidades/subgrupos, **tres beneficiarios y tres apoderados por unidad** (18 de cada uno), responsables y certificados PDF privados de prueba. El acceso JWT es por correo electrónico; todas estas cuentas usan la contraseña **`ScoutDemo!2026`**:

- `demo_staff@demo.scout.local`
- `20000201@demo.scout.local` (Responsable de Grupo)
- `20000202@demo.scout.local` a `20000207@demo.scout.local` (Responsables de Unidad)
- `20000101@demo.scout.local` (Apoderado; los demás apoderados demo no tienen usuario)
- `demo_sin_persona@demo.scout.local` (sirve para comprobar ausencia de alcance RBAC)

Para reconstruir exclusivamente los datos identificados del demo (incluidos sus certificados privados), usa la confirmación no interactiva explícita:

```bash
python manage.py seed_grupo_demo --reset --no-input
```

**No ejecutar este comando con PostgreSQL ni con `DEBUG=false`**: se rechaza deliberadamente para impedir que credenciales conocidas y datos de muestra lleguen a entornos compartidos o productivos.

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

## Despliegue backend

La imagen por defecto ejecuta Gunicorn como usuario sin privilegios; no contiene secretos porque `.env` está excluido del contexto de build. `docker-compose.yml` es **solo desarrollo**: publica PostgreSQL, usa credenciales conocidas y eleva `web` a root para que los bind mounts locales sigan funcionando. No debe utilizarse en producción.

Antes de desplegar, inyecta las variables desde el gestor de secretos de la plataforma y ejecuta:

```bash
export DJANGO_DEBUG=false
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
export DJANGO_ALLOWED_HOSTS=api.example.cl
# Solo si hay un origen de frontend distinto:
export DJANGO_CORS_ALLOWED_ORIGINS=https://app.example.cl
export DJANGO_CSRF_TRUSTED_ORIGINS=https://app.example.cl
./scripts/check_deploy.sh
```

El proceso debe quedar detrás de TLS. Si termina TLS un proxy, confirmar que la aplicación solo es alcanzable desde ese proxy y recién entonces activar `DJANGO_SECURE_PROXY_SSL_HEADER=true`; de lo contrario puede confiarse un header de cliente. Servir estáticos y media privada mediante la infraestructura de despliegue: Django no publica `MEDIA_ROOT` en producción. No publicar PostgreSQL al host; mantenerlo en red privada y usar un secreto de base de datos diferente al de desarrollo.

La API usa JWT (access de 30 minutos, refresh de 1 día, rotación y blacklist). OAuth2 se retiró de DRF y de dependencias porque no existen rutas OAuth2 montadas. Se limitan login, refresh y escrituras que aceptan archivos; no registrar cuerpos de petición ni encabezados `Authorization`/tokens.

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

- Login usa `POST /api/v1/auth/token/` con `email` y `password`. Para una cuenta vinculada a Persona, el correo de Persona es el identificador de acceso.
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
- Autenticación DRF: JWT exclusivamente; el admin Django conserva su propia sesión fuera de DRF. OAuth2 no está instalado ni tiene rutas.
- Permiso DRF global: `IsAuthenticated`; endpoints publicos deben declarar `AllowAny`.
- Respuestas exitosas usan `{success, message, data, meta?}` desde `api/v1/responses.py`.
- Errores usan `{success: false, error: {code, message, details}}` desde `api/v1/exceptions.py`.
- `POST/PATCH /api/v1/personas/` acepta JSON o `multipart/form-data` para `foto`.
- `GET /api/v1/grupos/{id}/estructura/` devuelve ramas, unidades, subgrupos, miembros y alertas etarias RN-05.
- `GET /api/v1/dashboard/grupo/{id}/` devuelve KPIs y alertas de cumpleanos proximos.
