# MediTrack

Aplicación web desarrollada con **FastAPI**, **SQLAlchemy 2.0**, **Jinja2** y **Tailwind CSS** para gestionar medicamentos, pautas de tratamiento, agenda diaria de dosis y acompañamiento clínico/familiar de pacientes.

---

## Tabla de contenidos

- [Roles y experiencias de usuario](#roles-y-experiencias-de-usuario)
- [Funcionalidades principales](#funcionalidades-principales)
- [Tecnologías utilizadas](#tecnologías-utilizadas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Variables de entorno](#variables-de-entorno)
- [Instalación y ejecución local](#instalación-y-ejecución-local)
- [Despliegue con Docker](#despliegue-con-docker)
- [Despliegue con Apache y protección .htaccess](#despliegue-con-apache-y-protección-htaccess)
- [Cuentas de demostración (Desarrollo)](#cuentas-de-demostración-desarrollo)
- [Endpoints principales de la API](#endpoints-principales-de-la-api)
- [Pruebas automatizadas](#pruebas-automatizadas)
- [Registro de cambios y licencia](#registro-de-cambios-y-licencia)

---

## Roles y experiencias de usuario

1. **Usuario Estándar (`user`)**:
   - Al iniciar sesión accede siempre al **Selector de Modo** (`/app/selector`) para elegir cómo usar la aplicación:
     - **Adulto Mayor (`/app/asistido`)**: Vista simplificada de alto contraste enfocada en la próxima dosis y botones grandes (*Me la tomé*, *Posponer*, *No tomada*).
     - **Cuidador / Completo (`/app`)**: Panel completo con métricas del día, agenda (`/app/agenda`), medicamentos (`/app/medicamentos`) y tratamientos (`/app/tratamientos`), además de solicitudes de enlace con administradores de pacientes.
2. **Administrador de Pacientes (`patient_admin`)**:
   - Accede directamente a `/app/gestor`, organizado en 4 pestañas:
     - **Principal**: Resumen global, envío de solicitudes de enlace por correo electrónico y estado de la red de cuidado.
     - **Medicamentos**: Catálogo base de medicamentos del gestor para reutilizar en esquemas o asignar a pacientes.
     - **Esquemas de tratamiento**: Creación y administración de plantillas reutilizables (medicamento, stock inicial, dosis, horarios y duración).
     - **Pacientes**: Directorio de pacientes enlazados; al seleccionar un paciente se muestran sus estadísticas/adherencia, track de dosis de hoy, aplicación de esquemas en 1 clic, asignación de medicamentos y menú de tratamientos activos.
3. **Administrador del Sistema (`admin`)**:
   - Acceso al panel completo (`/app`) y a la vista de métricas generales (`/app/resumen`).

---

## Funcionalidades principales

- **Autenticación y sesiones seguras**: Registro e inicio de sesión con contraseñas cifradas con `bcrypt`, tokens JWT firmados (`HS256`) almacenados en cookie `HttpOnly` (`meditrack_token`) y cabecera `Authorization: Bearer`.
- **Protección contra abuso**: Limitación de tasa (`slowapi`) de 5 peticiones/minuto en registro e inicio de sesión y 120 peticiones/minuto por defecto; sanitización contra XSS y cabeceras HTTP de seguridad.
- **Control de dosis y stock**:
  - Ventana estricta de toma: permite registrar decisiones (`taken`, `snoozed`, `missed`) únicamente entre 15 minutos antes y 15 minutos después de la hora programada.
  - Posponer (`snoozed`) reprograma la dosis 10 minutos adelante.
  - Marcado automático como omitida (`missed`) transcurridos 5 minutos desde la ventana límite sin decisión.
  - Descuento automático de existencias en el inventario del medicamento al confirmar la toma.
- **Agenda multi-día**: Consulta tanto las dosis de la jornada actual (`/api/doses/today`) como las próximas tomas futuras (`/api/doses/upcoming`).
- **Gestión remota de pacientes**: Envío y aprobación explícita de enlaces paciente-gestor antes de permitir lectura o registro de medicamentos, tratamientos o aplicación de esquemas.

---

## Tecnologías utilizadas

- **Backend**: Python 3.11+ (probado con Python 3.14), FastAPI `0.140.13`, Uvicorn `0.34.0`, Pydantic `2.13.4`
- **Base de datos y ORM**: SQLAlchemy `2.0.51`, Alembic `1.14+`, SQLite (por defecto, configurable vía `DATABASE_URL`)
- **Seguridad**: `python-jose`, `bcrypt==4.0.1`, `slowapi`
- **Frontend**: Plantillas Jinja2 `3.1.5`, Tailwind CSS (CDN), JavaScript vanilla (`static/app.js`)
- **Pruebas y Contenedores**: Pytest `8.3.4`, `httpx==0.28.1`, Docker & Docker Compose

---

## Estructura del proyecto

```text
NewMediTrack/
├── main.py                  # Punto de entrada FastAPI, ciclo de vida, middlewares y rutas HTML
├── core/                    # Configuración (.env), conexión DB, seguridad JWT/bcrypt, rate limiter y utilidades horarias
├── models/                  # Modelos ORM SQLAlchemy (User, Medication, Treatment, Dose, PatientLink, MedicationSchemaTemplate)
├── schemas/                 # Esquemas y validadores Pydantic v2
├── services/                # Lógica de negocio desacoplada por dominio
├── routers/                 # Routers REST modulares bajo /api/*
├── alembic/                 # Configuración y scripts de migración de base de datos
├── templates/               # Vistas Jinja2 organizadas en layouts/, partials/ y pages/
├── static/                  # Cliente JavaScript (static/app.js) y recursos estáticos
├── tests/                   # Suite de pruebas automatizadas con Pytest
├── Dockerfile               # Imagen Docker de producción (Python 3.14-slim + usuario no root)
├── docker-compose.yml       # Orquestación con volumen persistente para SQLite
├── .dockerignore            # Exclusiones para el contexto de construcción Docker
├── .htaccess                # Reglas de protección de lógica y cabeceras para despliegues Apache
├── requirements.txt         # Dependencias de Python
├── CHANGELOG.md             # Historial de versiones y cambios
└── LICENSE                  # Licencia GNU General Public License v3.0
```

---

## Variables de entorno

Copia `.env.example` a `.env` antes de ejecutar o desplegar:

```powershell
Copy-Item .env.example .env
```

Variables principales configurables en `.env`:

| Variable | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Entorno de ejecución (`development` o `production`) | `development` |
| `SECRET_KEY` | Clave secreta JWT (**en `production` es obligatorio usar >= 32 caracteres aleatorios**) | Valor dev local |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración de la sesión en minutos | `480` |
| `DATABASE_URL` | Cadena de conexión SQLAlchemy | `sqlite:///./meditrack.db` |
| `APP_TIMEZONE` | Zona horaria IANA de la aplicación | `America/Bogota` |
| `TIMEZONE_OFFSET_HOURS` | Desfase horario UTC de respaldo | `-5` |
| `DEMO_*` | Credenciales opcionales sembradas solo cuando `ENVIRONMENT=development` | Ver `.env.example` |

> **Importante para producción**: Cuando `ENVIRONMENT=production`, la aplicación bloquea el arranque si `SECRET_KEY` es insegura o tiene menos de 32 caracteres, desactiva el sembrado de usuarios demo y marca la cookie `meditrack_token` con `Secure=True` (requiere HTTPS).

---

## Instalación y ejecución local

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Rutas principales disponibles tras iniciar:

- **Landing page**: `http://127.0.0.1:8000/`
- **Inicio de sesión**: `http://127.0.0.1:8000/login`
- **Selector de modo (`user`)**: `http://127.0.0.1:8000/app/selector`
- **Panel de Gestor (`patient_admin`)**: `http://127.0.0.1:8000/app/gestor`
- **Documentación OpenAPI / Swagger**: `http://127.0.0.1:8000/docs`
- **Healthcheck**: `http://127.0.0.1:8000/health`

---

## Despliegue con Docker

El repositorio incluye [`Dockerfile`](Dockerfile), [`.dockerignore`](.dockerignore) y [`docker-compose.yml`](docker-compose.yml) listos para levantar el servicio con persistencia de la base de datos SQLite en el volumen `meditrack_data` (`/app/data/meditrack.db`).

### Levantar con Docker Compose

```bash
docker compose up -d --build
```

Ver logs y estado del contenedor:

```bash
docker compose logs -f meditrack
docker compose ps
```

Detener los contenedores (conservando el volumen de base de datos):

```bash
docker compose down
```

### Producción con Docker

Antes de levantar en producción, configura un `.env` seguro (con `ENVIRONMENT=production` y una `SECRET_KEY` aleatoria de al menos 32 caracteres) y sitúalo detrás de un proxy inverso con TLS/HTTPS (Nginx, Traefik, Caddy o Apache):

```env
ENVIRONMENT=production
SECRET_KEY=tu_clave_aleatoria_segura_de_mas_de_32_caracteres
```

---

## Despliegue con Apache y protección `.htaccess`

Si alojas o publicas el proyecto en un servidor con **Apache HTTP Server**, el archivo [`.htaccess`](.htaccess) incluido protege automáticamente la lógica del servidor:

- Deshabilita el listado de directorios (`Options -Indexes -ExecCGI`) y firma del servidor.
- Deniega cualquier descarga HTTP directa de archivos `.py`, `.pyc`, `.db`, `.sqlite`, `.env`, `.log`, `.ini`, `requirements.txt`, `Dockerfile` y documentación.
- Bloquea mediante `mod_rewrite` el acceso HTTP directo a los directorios internos (`core/`, `models/`, `schemas/`, `services/`, `routers/`, `alembic/`, `tests/`, `templates/`, `.venv/`, `.git/`, `data/`).
- Añade cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) y caché para `/static/`.
- Incluye un bloque listo para descomentar en caso de usar Apache como proxy inverso (`mod_proxy` + `mod_proxy_http`) hacia `http://127.0.0.1:8000`.

---

## Cuentas de demostración (Desarrollo)

Cuando `ENVIRONMENT=development`, `init_demo_user()` crea automáticamente usuarios y enlaces de prueba (todos con contraseña `MediTrack123!`) y muestra botones de autorrellenado en `/login`:

| Rol | Correo | Contraseña | Descripción |
| :--- | :--- | :--- | :--- |
| `admin` | `demo@meditrack.app` | `MediTrack123!` | Administradora del sistema |
| `patient_admin` | `gestor@meditrack.app` | `MediTrack123!` | Dra. Laura Ríos (Gestora de pacientes) |
| `user` | `user@meditrack.app` | `MediTrack123!` | Carlos Gómez (Enlazado con la gestora) |
| `user` | `elena@meditrack.app` | `MediTrack123!` | Elena Martínez (Enlazada con la gestora) |
| `user` | `roberto@meditrack.app` | `MediTrack123!` | Roberto Sánchez (Enlazado con la gestora) |
| `user` | `lucia@meditrack.app` | `MediTrack123!` | Lucía Fernández (Solicitud pendiente de aceptar) |
| `user` | `pedro@meditrack.app` | `MediTrack123!` | Pedro Ramírez (Sin enlace previo) |

---

## Endpoints principales de la API

- **Sistema**: `GET /health`
- **Usuarios y Sesiones**:
  - `POST /api/users`, `GET /api/users/me`, `PUT /api/users/me`
  - `POST /api/sessions`, `POST /api/sessions/logout`
- **Medicamentos, Tratamientos y Dosis**:
  - `GET/POST /api/medications`, `GET/PUT/DELETE /api/medications/{id}`
  - `GET/POST /api/treatments`, `GET/PUT/DELETE /api/treatments/{id}`
  - `GET /api/doses/today`, `GET /api/doses/upcoming`, `POST /api/doses/{id}/decision`
- **Enlaces y Administrador de Pacientes**:
  - Paciente: `GET /api/patient-links/my-requests`, `POST /api/patient-links/{id}/decision`, `DELETE /api/patient-links/{id}`
  - Gestor: `GET/POST /api/patient-admin/links`, `GET /api/patient-admin/patients/{id}/overview`
  - Gestor sobre paciente: `POST/DELETE /api/patient-admin/patients/{id}/medications...`, `POST/DELETE /api/patient-admin/patients/{id}/treatments...`
  - Esquemas: `GET/POST /api/patient-admin/schemas`, `DELETE /api/patient-admin/schemas/{id}`, `POST /api/patient-admin/patients/{id}/apply-schema/{schema_id}`
- **Administración**: `GET /api/admin/summary`

---

## Pruebas automatizadas

La suite en `tests/` valida seguridad JWT/bcrypt/XSS, reglas de dosis y stock, selector de experiencia y flujo completo de administrador de pacientes:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

---

## Registro de cambios y licencia

- Consulta el historial de versiones en [`CHANGELOG.md`](CHANGELOG.md).
- Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Consulta el texto completo en [`LICENSE`](LICENSE).
