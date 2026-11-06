from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.database import SessionLocal, init_db
from core.exceptions import DomainError
from core.rate_limiter import limiter
from routers import (
    admin_router,
    auth_router,
    dose_router,
    medication_router,
    session_router,
    treatment_router,
)
from schemas.common_schema import ApiResponse
from services.user_service import create_user, get_user_by_email

BASE_DIR = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meditrack")


def init_demo_user():
    """Siembra el usuario demo solo en entornos de desarrollo."""
    if not settings.is_development:
        logger.info("Entorno no es desarrollo: se omite la creación del usuario demo por seguridad")
        return

    if not settings.demo_email or not settings.demo_password:
        logger.warning("DEMO_EMAIL y DEMO_PASSWORD no están definidas; se omite el usuario demo")
        return

    db = SessionLocal()
    try:
        exists = get_user_by_email(db, settings.demo_email)
        if not exists:
            create_user(
                db,
                email=settings.demo_email,
                full_name=settings.demo_name,
                password=settings.demo_password,
                role="admin",
            )
            logger.info("Usuario demo inicializado correctamente: %s", settings.demo_email)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestor de ciclo de vida moderno de FastAPI (reemplaza eventos startup/shutdown deprecados)."""
    logger.info("Iniciando %s versión %s...", settings.app_name, settings.app_version)
    init_db()
    init_demo_user()
    yield
    logger.info("Deteniendo %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)

# Integración del limitador de tasa
app.state.limiter = limiter

# Archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inyecta cabeceras de seguridad HTTP estándar en todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ============================================================================
# Manejadores de Excepciones Estandarizados
# ============================================================================

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=getattr(exc, "status_code", 422),
        content={"success": False, "data": None, "message": exc.detail},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "data": None, "message": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        error_copy = dict(error)
        if error_copy.get("ctx"):
            error_copy["ctx"] = {key: str(value) for key, value in error_copy["ctx"].items()}
        errors.append(error_copy)
    return JSONResponse(
        status_code=422,
        content={"success": False, "data": None, "message": "Revisa los datos enviados", "errors": errors},
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"success": False, "data": None, "message": "Demasiadas solicitudes. Por favor, intenta de nuevo más tarde."},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "message": "Ocurrió un error interno. Intenta de nuevo."},
    )


# ============================================================================
# Vistas HTML Frontend
# ============================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/landing.html", context={})


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/login.html",
        context={"show_demo_hint": settings.is_development},
    )


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def panel_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/panel.html", context={})


@app.get("/app/agenda", response_class=HTMLResponse, include_in_schema=False)
async def agenda_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/agenda.html", context={})


@app.get("/app/medicamentos", response_class=HTMLResponse, include_in_schema=False)
async def medications_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/medicamentos.html", context={})


@app.get("/app/tratamientos", response_class=HTMLResponse, include_in_schema=False)
async def treatments_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/tratamientos.html", context={})


@app.get("/app/resumen", response_class=HTMLResponse, include_in_schema=False)
async def summary_page(request: Request):
    return templates.TemplateResponse(request=request, name="pages/resumen.html", context={})


# ============================================================================
# Registro Modular de Routers de API
# ============================================================================

app.include_router(auth_router.router, prefix="/api")
app.include_router(session_router.router, prefix="/api")
app.include_router(medication_router.router, prefix="/api")
app.include_router(treatment_router.router, prefix="/api")
app.include_router(dose_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")


@app.get("/health", response_model=ApiResponse[dict], tags=["Sistema"])
def health():
    return ApiResponse(
        success=True,
        data={"status": "ok", "environment": settings.environment, "version": settings.app_version},
        message="MediTrack activo",
    )
