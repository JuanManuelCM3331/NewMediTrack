import pytest
from pydantic import ValidationError
from tests.conftest import TestingSessionLocal
from core.config import Settings
from core.rate_limiter import limiter
from core.security import hash_password
from models import User


def test_stored_xss_sanitization_in_medication_and_user(client):
    """5.1: Verifica que el backend sanitice etiquetas HTML/JavaScript al guardar medicamentos y usuarios."""
    reg_res = client.post(
        "/api/users",
        json={
            "email": "hacker@test.com",
            "full_name": "<script>alert('xss')</script>Juan",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    user_data = reg_res.json()["data"]["user"]
    assert "<script>" not in user_data["full_name"]
    assert "&lt;script&gt;" in user_data["full_name"]

    token = reg_res.json()["data"]["access_token"]

    med_res = client.post(
        "/api/medications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "<img src=x onerror=alert(document.cookie)>Aspirina",
            "presentation": "Tableta",
            "stock": 10,
            "notes": "<svg/onload=alert(1)>",
        },
    )
    assert med_res.status_code == 201
    med_data = med_res.json()["data"]
    assert "<img" not in med_data["name"]
    assert "&lt;img" in med_data["name"]
    assert "<svg" not in med_data["notes"]
    assert "&lt;svg" in med_data["notes"]


def test_httponly_cookie_authentication_flow(client):
    """5.2: Verifica que el login y registro establezcan la cookie HttpOnly y que endpoints protegidos la reconozcan."""
    # 1. Registrar usuario
    reg_res = client.post(
        "/api/users",
        json={
            "email": "cookieuser@test.com",
            "full_name": "Cookie User",
            "password": "CookiePass123!",
        },
    )
    assert reg_res.status_code == 201
    assert "meditrack_token" in reg_res.cookies
    assert reg_res.cookies["meditrack_token"] is not None

    # 2. Iniciar sesión y validar cookie HttpOnly
    login_res = client.post(
        "/api/sessions",
        json={
            "email": "cookieuser@test.com",
            "password": "CookiePass123!",
        },
    )
    assert login_res.status_code == 200
    assert "meditrack_token" in login_res.cookies

    # 3. Acceder a endpoint protegido /api/users/me SIN cabecera Authorization (usando la cookie)
    me_res = client.get("/api/users/me")
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "cookieuser@test.com"

    # 4. Logout debe eliminar la cookie
    logout_res = client.post("/api/sessions/logout")
    assert logout_res.status_code == 200

    # 5. Sin la cookie, debe responder 401 Unauthorized
    client.cookies.clear()
    unauth_res = client.get("/api/users/me")
    assert unauth_res.status_code == 401


def test_bcrypt_72_bytes_limit_enforced(client):
    """5.5: Verifica que contraseñas mayores a 72 bytes sean rechazadas con 422 en login y registro."""
    long_password = "A" * 73
    res_reg = client.post(
        "/api/users",
        json={
            "email": "overflow@test.com",
            "full_name": "Overflow User",
            "password": long_password,
        },
    )
    assert res_reg.status_code == 422

    res_login = client.post(
        "/api/sessions",
        json={
            "email": "overflow@test.com",
            "password": long_password,
        },
    )
    assert res_login.status_code == 422


def test_rate_limiting_on_login(client):
    """5.3: Verifica que el rate limiter de slowapi bloquee ataques de fuerza bruta con código 429."""
    limiter.enabled = True
    limiter.reset()

    for _ in range(5):
        client.post(
            "/api/sessions",
            json={"email": "wrong@test.com", "password": "WrongPassword123!"},
        )

    blocked_res = client.post(
        "/api/sessions",
        json={"email": "wrong@test.com", "password": "WrongPassword123!"},
    )
    assert blocked_res.status_code == 429
    assert "Demasiadas solicitudes" in blocked_res.json()["message"]

    limiter.reset()
    limiter.enabled = False


def test_inactive_user_cannot_login(client):
    """Verifica que una cuenta desactivada (is_active=False) no pueda iniciar sesión."""
    db = TestingSessionLocal()
    inactive_user = User(
        email="inactive@test.com",
        full_name="Usuario Inactivo",
        password_hash=hash_password("ValidPass123!"),
        role="user",
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()
    db.close()

    res = client.post(
        "/api/sessions",
        json={"email": "inactive@test.com", "password": "ValidPass123!"},
    )
    assert res.status_code == 401
    assert "meditrack_token" not in res.cookies


def test_no_double_html_escaping_on_repeated_updates(client):
    """Verifica que actualizar un nombre con caracteres especiales no duplique entidades HTML (&amp;amp;)."""
    reg_res = client.post(
        "/api/users",
        json={
            "email": "special@test.com",
            "full_name": "María & José",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["data"]["access_token"]
    saved_name = reg_res.json()["data"]["user"]["full_name"]
    assert saved_name == "María &amp; José"

    # Enviar el valor ya escapado en una actualización no debe producir &amp;amp;
    upd_res = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": saved_name},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["full_name"] == "María &amp; José"


def test_security_headers_and_production_secret_validation(client):
    """Verifica las cabeceras HTTP de seguridad y el bloqueo de SECRET_KEY débil en producción."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    with pytest.raises(ValidationError):
        Settings(environment="production", secret_key="meditrack-local-7f4b9d2c8a1e6f3b5d7c9a2e4f6b8d1c")
