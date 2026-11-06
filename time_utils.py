import os
from datetime import date, datetime, timedelta, timezone

try:
    import zoneinfo
    APP_TZ_NAME = os.getenv("APP_TIMEZONE", "America/Bogota")
    APP_TIMEZONE = zoneinfo.ZoneInfo(APP_TZ_NAME)
except Exception:
    offset = int(os.getenv("TIMEZONE_OFFSET_HOURS", "-5"))
    APP_TIMEZONE = timezone(timedelta(hours=offset))


def get_app_timezone():
    """Retorna la zona horaria de la aplicación (por defecto América/Bogotá UTC-5)."""
    return APP_TIMEZONE


def get_app_now() -> datetime:
    """Retorna la fecha y hora actual consciente de la zona horaria de la aplicación."""
    return datetime.now(APP_TIMEZONE)


def get_app_now_naive() -> datetime:
    """Retorna la fecha y hora actual en hora local de la app como datetime naive para compatibilidad con la BD."""
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def get_app_today() -> date:
    """Retorna la fecha actual según la zona horaria configurada de la aplicación."""
    return get_app_now().date()


def get_utc_now() -> datetime:
    """Retorna la fecha y hora actual en UTC consciente de zona horaria (para tokens JWT)."""
    return datetime.now(timezone.utc)
