import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from crud import create_user
from database import Base, SessionLocal, engine
from models import User
from routers import auth, medications, treatments

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


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
	return JSONResponse(status_code=422, content={"success": False, "data": None, "message": "Revisa los datos enviados", "errors": exc.errors()})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
	logger.exception("Unhandled application error", exc_info=exc)
	return JSONResponse(status_code=500, content={"success": False, "data": None, "message": "Ocurrió un error interno. Intenta de nuevo."})


@app.on_event("startup")
def startup():
	Base.metadata.create_all(bind=engine)
	db = SessionLocal()
	try:
		if not db.scalar(select(User).where(User.email == os.getenv("DEMO_EMAIL", "demo@meditrack.app"))):
			create_user(db, os.getenv("DEMO_EMAIL", "demo@meditrack.app"), "María MediTrack", os.getenv("DEMO_PASSWORD", "MediTrack123!"), "admin")
	finally:
		db.close()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
	return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
	return templates.TemplateResponse(request=request, name="dashboard.html", context={})


app.include_router(auth.router, prefix="/api")
app.include_router(medications.router, prefix="/api")
app.include_router(treatments.router, prefix="/api")


@app.get("/health", tags=["Sistema"])
def health():
	return {"success": True, "data": {"status": "ok"}, "message": "MediTrack activo"}
