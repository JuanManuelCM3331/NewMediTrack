# MediTrack

Aplicación web desarrollada con FastAPI para registrar medicamentos, crear tratamientos y controlar las dosis del día.

## Requisitos

- Python 3.11 o superior
- Windows PowerShell

## Instalación

Desde la carpeta del proyecto:

```powershell
cd "C:\Users\JuanMa3331\Downloads\Dso\NewMediTrack"

python -m venv .venv

\.\.venv\Scripts\python.exe -m pip install --upgrade pip
\.\.venv\Scripts\python.exe -m pip install -r requirements.txt
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
\.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

También puedes activar el entorno y ejecutar el comando corto:

```powershell
\.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --port 8000
```

La aplicación estará disponible en:

- Interfaz web: http://127.0.0.1:8000
- Panel principal: http://127.0.0.1:8000/app
- Documentación Swagger: http://127.0.0.1:8000/docs
- Estado del servidor: http://127.0.0.1:8000/health

Para detener el servidor, presiona `Ctrl + C`.

## Usuario demo

El usuario administrador se crea automáticamente al iniciar la aplicación si todavía no existe.

- Correo: `demo@meditrack.app`
- Contraseña: `MediTrack123!`
- Rol: `admin`

## Funcionalidades

- Inicio de sesión con correo y contraseña.
- Contraseñas almacenadas con hash bcrypt.
- Registro, consulta, actualización y eliminación de medicamentos.
- Creación y administración de tratamientos.
- Configuración de dosis, horarios, duración e indicaciones.
- Agenda diaria de dosis.
- Opciones para marcar una dosis como tomada o pospuesta.
- Marcado automático como omitida después de cinco minutos sin decisión.
- Autenticación JWT con expiración.

## Variables de entorno opcionales

Puedes configurar estos valores antes de iniciar la aplicación:

```powershell
$env:SECRET_KEY="cambia-esta-clave-en-produccion"
$env:ACCESS_TOKEN_EXPIRE_MINUTES="480"
$env:DATABASE_URL="sqlite:///./meditrack.db"
$env:DEMO_EMAIL="demo@meditrack.app"
$env:DEMO_PASSWORD="MediTrack123!"
```

En producción se recomienda cambiar `SECRET_KEY`, `DEMO_EMAIL` y `DEMO_PASSWORD`.

## Estructura principal

```text
main.py          Configuración y arranque de FastAPI
database.py      Conexión SQLAlchemy y get_db()
models/          Modelos de base de datos
schemas/         Validaciones Pydantic
routers/         Endpoints REST
crud.py          Lógica CRUD y contraseñas
dependencies.py  JWT, usuario actual y roles
templates/       Interfaz HTML
static/          JavaScript y estilos
```
# NewMediTrack
