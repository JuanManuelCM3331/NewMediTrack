from html.parser import HTMLParser

from core.security import hash_password
from models import User
from tests.conftest import TestingSessionLocal


class SelectorCardParser(HTMLParser):
    """Extrae los botones de selección de modo y valida que la tarjeta completa sea un botón."""

    def __init__(self):
        super().__init__()
        self.cards: list[dict] = []
        self._current_card: dict | None = None
        self._depth = 0
        self.has_article_cards = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attr_map = dict(attrs)
        if tag == "article":
            self.has_article_cards = True

        if tag == "button" and "data-select-mode" in attr_map:
            self._current_card = {
                "mode": attr_map["data-select-mode"],
                "classes": attr_map.get("class", ""),
                "inner_classes": [],
                "nested_buttons": 0,
                "large_svg_icons": 0,
            }
            self._depth = 1
            return

        if self._current_card is not None:
            self._depth += 1
            if tag == "button":
                self._current_card["nested_buttons"] += 1
            if tag == "svg" and "h-20" in attr_map.get("class", "").split():
                self._current_card["large_svg_icons"] += 1
            if "class" in attr_map and attr_map["class"]:
                self._current_card["inner_classes"].append(attr_map["class"])

    def handle_endtag(self, tag: str):
        if self._current_card is not None:
            self._depth -= 1
            if self._depth == 0:
                self.cards.append(self._current_card)
                self._current_card = None


def test_selector_cards_are_full_buttons_with_primary_color_and_white_text(client):
    """Verifica que las tarjetas del selector sean botones completos con color del botón y texto blanco."""
    res = client.get("/app/selector")
    assert res.status_code == 200

    parser = SelectorCardParser()
    parser.feed(res.text)

    assert parser.has_article_cards is False
    assert [card["mode"] for card in parser.cards] == ["asistido", "cuidador"]

    asistido_card, cuidador_card = parser.cards

    # Ninguna tarjeta debe contener botones anidados
    assert asistido_card["nested_buttons"] == 0
    assert cuidador_card["nested_buttons"] == 0

    # Color primordial del botón y letras blancas en la tarjeta completa
    assert "bg-brand" in asistido_card["classes"].split()
    assert "text-white" in asistido_card["classes"].split()
    assert "cursor-pointer" in asistido_card["classes"].split()

    assert "bg-[#28637c]" in cuidador_card["classes"].split()
    assert "text-white" in cuidador_card["classes"].split()
    assert "cursor-pointer" in cuidador_card["classes"].split()

    # No deben quedar clases de texto oscuro dentro de las tarjetas y cada una tiene su ícono central grande
    dark_text_classes = {"text-ink", "text-muted", "text-brand", "text-brand-dark", "text-[#2f5d75]"}
    for card in parser.cards:
        all_inner = " ".join(card["inner_classes"]).split()
        assert dark_text_classes.isdisjoint(all_inner)
        assert "justify-center" in all_inner
        assert card["large_svg_icons"] == 1


def test_auth_responses_include_role_for_post_login_selector_routing(client):
    """Verifica que registro y login devuelvan el rol para dirigir a usuarios no admin al selector."""
    reg_res = client.post(
        "/api/users",
        json={
            "email": "paciente@test.com",
            "full_name": "Paciente Prueba",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["data"]["user"]["role"] == "user"

    login_user_res = client.post(
        "/api/sessions",
        json={"email": "paciente@test.com", "password": "Password123!"},
    )
    assert login_user_res.status_code == 200
    assert login_user_res.json()["data"]["user"]["role"] == "user"

    db = TestingSessionLocal()
    admin = User(
        email="admin@test.com",
        full_name="Admin Prueba",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    login_admin_res = client.post(
        "/api/sessions",
        json={"email": "admin@test.com", "password": "AdminPass123!"},
    )
    assert login_admin_res.status_code == 200
    assert login_admin_res.json()["data"]["user"]["role"] == "admin"
