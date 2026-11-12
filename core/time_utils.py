from datetime import date, datetime, timedelta, timezone

from core.config import settings

try:
    import zoneinfo
    APP_TIMEZONE = zoneinfo.ZoneInfo(settings.app_timezone)
except Exception:
    APP_TIMEZONE = timezone(timedelta(hours=settings.timezone_offset_hours))


def get_app_timezone():
    """Retorna la zona horaria oficial de la aplicación (América/Bogotá)."""
    return APP_TIMEZONE


def get_app_now() -> datetime:
    """Retorna la fecha y hora actual consciente de la zona horaria."""
    return datetime.now(APP_TIMEZONE)


def get_app_now_naive() -> datetime:
    """Retorna la fecha y hora actual en hora local de la app como datetime naive para la base de datos."""
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def get_app_today() -> date:
    """Retorna la fecha actual según la zona horaria configurada."""
    return get_app_now().date()


def get_utc_now() -> datetime:
    """Retorna la fecha y hora actual en UTC consciente de zona horaria (para tokens JWT)."""
    return datetime.now(timezone.utc)
