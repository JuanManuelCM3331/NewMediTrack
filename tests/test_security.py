import pytest
from tests.conftest import TestingSessionLocal
from rate_limiter import limiter


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
