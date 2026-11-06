# MediTrack

Aplicación web desarrollada con FastAPI para registrar medicamentos, crear tratamientos y controlar las dosis del día.

## Requisitos

- Python 3.11 o superior
- Windows PowerShell

## Instalación

Desde la carpeta del proyecto:

```powershell
python -m venv .venv

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No es necesario activar el entorno virtual: los comandos anteriores garantizan que las dependencias se instalen en `.venv`.

Si PowerShell bloquea la activación del entorno virtual, ejecuta PowerShell como usuario y permite scripts locales:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Después vuelve a ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Ejecutar la aplicación

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

También puedes activar el entorno y ejecutar el comando corto:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```

La aplicación estará disponible en:

- Interfaz web: http://127.0.0.1:8000
- Panel principal: http://127.0.0.1:8000/app
- Documentación Swagger: http://127.0.0.1:8000/docs
- Estado del servidor: http://127.0.0.1:8000/health

Para detener el servidor, presiona `Ctrl + C`.

## Usuario demo

El usuario administrador se crea automáticamente al iniciar la aplicación en entorno de desarrollo (`ENVIRONMENT=development`) si todavía no existe.

- Correo: `demo@meditrack.app`
- Contraseña: `MediTrack123!`
- Rol: `admin`

## Funcionalidades

- Inicio de sesión con correo y contraseña.
- Contraseñas almacenadas con hash bcrypt (con validación de límite de 72 bytes).
- Autenticación mediante JWT y Cookies `HttpOnly` seguras.
- Protección contra ataques de fuerza bruta (`slowapi` rate limiting).
- Registro, consulta, actualización y eliminación de medicamentos.
- Creación y administración de tratamientos.
- Configuración de dosis, horarios, duración e indicaciones.
- Agenda diaria de dosis con sincronización automática de stock.
- Opciones para marcar una dosis como tomada o pospuesta (`snooze` de 10 minutos).
- Marcado automático como omitida después de cinco minutos sin decisión.

## Variables de entorno

La aplicación carga las variables desde `.env`. Copia la plantilla y cambia sus valores:

```powershell
Copy-Item .env.example .env
```

Define una `SECRET_KEY` larga y aleatoria (mínimo 32 caracteres en producción). El archivo `.env` está excluido por `.gitignore` y nunca debe subirse al repositorio.

Las rutas principales de la API son:

- `POST /api/sessions`: iniciar sesión y obtener el JWT + Cookie `HttpOnly`.
- `POST /api/sessions/logout`: cerrar sesión.
- `POST /api/users`: registrar un usuario.
- `GET/PUT /api/users/me`: consultar o actualizar el perfil.
- `GET/POST/PUT/DELETE /api/medications`: gestionar medicamentos.
- `GET/POST/PUT/DELETE /api/treatments`: gestionar tratamientos.
- `GET /api/doses/today` y `POST /api/doses/{id}/decision`: agenda diaria y decisiones de dosis.

## Pruebas automatizadas

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Estructura principal

```text
main.py          Configuración, middlewares, ciclo de vida y arranque de FastAPI
core/            Configuración, base de datos, seguridad JWT/bcrypt, excepciones, dependencias y rate limiter
models/          Modelos ORM de SQLAlchemy 2.0 (User, Medication, Treatment, Dose)
schemas/         Validaciones y contratos de datos Pydantic v2
services/        Lógica de negocio desacoplada por dominio
routers/         Endpoints REST modulares (/api/users, /api/sessions, /api/medications, /api/treatments, /api/doses, /api/admin)
alembic/         Migraciones de esquema de base de datos
templates/       Vistas HTML (Jinja2)
static/          Cliente JavaScript y estilos CSS
tests/           Suite de pruebas automatizadas (Pytest)
```
