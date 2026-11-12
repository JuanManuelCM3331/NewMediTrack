# Changelog

Todos los cambios notables de **MediTrack** se documentan en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y sigue versionado semántico.

## [1.0.0] - 2026-11-11

### Agregado
- **Rol Administrador de Pacientes (`patient_admin`)**:
  - Vista dedicada (`/app/gestor`) organizada en 4 pestañas: **Principal**, **Medicamentos**, **Esquemas de tratamiento** y **Pacientes**.
  - Sistema de solicitudes de enlace (`PatientLink`) entre administradores de pacientes y usuarios (`pending`, `accepted`, `rejected`), con aceptación/rechazo y desvinculación desde el panel del paciente (`/app` y `/app/asistido`).
  - Catálogo de medicamentos base del gestor para reutilizar en plantillas de esquemas o asignar directamente a pacientes enlazados.
  - Esquemas de tratamiento preconfigurados (`MedicationSchemaTemplate`) con aplicación en un clic desde la ficha del paciente seleccionado (`POST /api/patient-admin/patients/{patient_id}/apply-schema/{schema_id}`).
  - Menú de tratamientos activos y estadísticas/seguimiento (`stats` y `track` en tiempo real) por paciente enlazado en `GET /api/patient-admin/patients/{patient_id}/overview`.
  - Datos de demostración ampliados en desarrollo (`gestor@meditrack.app` y múltiples pacientes enlazados, pendientes y libres) con autorrelleno rápido en `/login`.
- **Selector de experiencia para usuarios estándar (`/app/selector`)**:
  - Redirección automática al iniciar sesión como usuario (`role == "user"`) hacia la pantalla de selección entre **Adulto Mayor** (`/app/asistido`) y **Cuidador** (`/app`), con tarjetas seleccionables de cuerpo completo e iconos centrales de rol.
- **Empaquetado, licencia y seguridad de despliegue**:
  - Licencia **GNU General Public License v3.0** (`LICENSE`).
  - Dockerización completa mediante `Dockerfile`, `.dockerignore` y `docker-compose.yml` con volumen persistente SQLite en `/app/data/meditrack.db`.
  - Archivo `.htaccess` para proteger código fuente Python, variables `.env`, bases de datos `.db`, carpetas internas y configurar cabeceras HTTP de seguridad en servidores Apache.
  - Documentación completa en `README.md` y registro histórico en `CHANGELOG.md`.

### Cambiado
- Mejoras responsivas en las cabeceras, selector de esquemas y tarjetas del panel de Administrador de Pacientes (`/app/gestor`) para evitar colisiones o desbordamientos en distintos tamaños de pantalla.

## [0.3.0] - 2026-11-06

### Agregado
- **Modo Asistido (`/app/asistido`)**: Interfaz de alto contraste y tipografía ampliada centrada en la próxima dosis y sus acciones directas.
- **Agenda multi-día (`GET /api/doses/upcoming`)**: Visualización de las próximas dosis programadas para hoy y días posteriores.
- **Rediseño visual y modularización**: Plantillas Jinja2 organizadas en `templates/layouts/`, `templates/partials/` y `templates/pages/`, estilos Tailwind CSS, vista de detalles de dosis y edición de medicamentos.
- **Cuentas de prueba iniciales**: Usuario administrador (`demo@meditrack.app`) y usuario paciente estándar (`user@meditrack.app`) inicializados automáticamente en `ENVIRONMENT=development`.

### Cambiado
- Validación estricta de ventana horaria en la toma de decisiones sobre dosis (±15 minutos respecto a `scheduled_at`).

## [0.2.0] - 2026-11-06

### Agregado
- **Autenticación segura**: Migración de JWT a cookies `HttpOnly` (`meditrack_token`) además de soporte Bearer para API, y hashes con `bcrypt` (validación de límite de 72 bytes).
- **Rate limiting**: Integración de `slowapi` (límite general de 120 req/min y 5 req/min en registro/inicio de sesión).
- **Seguridad HTTP y XSS**: Middleware de cabeceras de seguridad (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`), sanitización en esquemas Pydantic v2 y escape seguro en cliente JS.
- **Arquitectura modular**: Reorganización explícita por capas de responsabilidad (`core/`, `models/`, `schemas/`, `services/`, `routers/`).

### Corregido
- Sincronización de existencias de medicamentos al tomar dosis, reprogramación al posponer (`snooze` de 10 minutos), omisión automática (`missed`) tras 5 minutos y soporte explícito de zona horaria (`APP_TIMEZONE` / `TIMEZONE_OFFSET_HOURS`).

## [0.1.0] - 2026-09-14

### Agregado
- Versión inicial del proyecto MediTrack con FastAPI, SQLAlchemy, modelos base (`User`, `Medication`, `Treatment`, `Dose`), migraciones con Alembic y endpoints iniciales de gestión de medicamentos y tratamientos.
