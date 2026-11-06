import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, select, text

from crud import create_user
from database import Base, SessionLocal, engine
from models import User
from routers import admin, auth, medications, sessions, treatments

BASE_DIR = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("meditrack")

app = FastAPI(title="MediTrack", version="1.0.0", description="Agenda personal de medicamentos y tratamientos")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class DomainError(Exception):
	def __init__(self, detail: str):
		self.detail = detail


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
	return JSONResponse(status_code=422, content={"success": False, "data": None, "message": exc.detail})


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
	return JSONResponse(status_code=exc.status_code, content={"success": False, "data": None, "message": exc.detail}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
	errors = []
	for error in exc.errors():
		error_copy = dict(error)
		if error_copy.get("ctx"):
			error_copy["ctx"] = {key: str(value) for key, value in error_copy["ctx"].items()}
		errors.append(error_copy)
	return JSONResponse(status_code=422, content={"success": False, "data": None, "message": "Revisa los datos enviados", "errors": errors})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
	logger.exception("Unhandled application error", exc_info=exc)
	return JSONResponse(status_code=500, content={"success": False, "data": None, "message": "Ocurrió un error interno. Intenta de nuevo."})


@app.on_event("startup")
def startup():
	Base.metadata.create_all(bind=engine)
	# Verificación y migración automática de columnas para bases existentes
	try:
		insp = inspect(engine)
		if "doses" in insp.get_table_names():
			cols = [c["name"] for c in insp.get_columns("doses")]
			if "created_at" not in cols:
				with engine.connect() as conn:
					conn.execute(text("ALTER TABLE doses ADD COLUMN created_at DATETIME"))
					conn.commit()
	except Exception as err:
		logger.warning("Error al verificar migración de columnas: %s", err)

	db = SessionLocal()
	try:
		demo_email = os.getenv("DEMO_EMAIL")
		demo_password = os.getenv("DEMO_PASSWORD")
		if demo_email and demo_password and not db.scalar(select(User).where(User.email == demo_email.lower())):
			create_user(db, demo_email, os.getenv("DEMO_NAME", "María MediTrack"), demo_password, "admin")
		elif not demo_email or not demo_password:
			logger.warning("DEMO_EMAIL y DEMO_PASSWORD no están definidas; se omite el usuario demo")
	finally:
		db.close()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
	return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
	return templates.TemplateResponse(request=request, name="dashboard.html", context={})


app.include_router(auth.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(medications.router, prefix="/api")
app.include_router(treatments.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health", tags=["Sistema"])
def health():
	return {"success": True, "data": {"status": "ok"}, "message": "MediTrack activo"}
