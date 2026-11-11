from core.time_utils import get_app_today


def _register_and_get_token(client, email: str, full_name: str, role: str = "user"):
    res = client.post(
        "/api/users",
        json={
            "email": email,
            "full_name": full_name,
            "password": "Password123!",
            "role": role,
        },
    )
    assert res.status_code == 201
    data = res.json()["data"]
    return data["user"], data["access_token"]


def test_login_page_contains_patient_admin_demo_autofill_and_gestor_view(client):
    """Verifica el botón de autorrelleno del administrador de pacientes en /login y la vista /app/gestor."""
    login_res = client.get("/login")
    assert login_res.status_code == 200
    assert "gestor@meditrack.app" in login_res.text
    assert "Administrador de pacientes" in login_res.text

    gestor_res = client.get("/app/gestor")
    assert gestor_res.status_code == 200
    assert "Enviar solicitud de enlace" in gestor_res.text
    assert 'data-gestor-tab="main"' in gestor_res.text
    assert 'data-gestor-tab="medicamentos"' in gestor_res.text
    assert 'data-gestor-tab="esquemas"' in gestor_res.text
    assert 'data-gestor-tab="pacientes"' in gestor_res.text
    assert "Mis esquemas de tratamiento" in gestor_res.text
    assert "Estadísticas y Track en tiempo real" in gestor_res.text
    assert "elena@meditrack.app" in login_res.text
    assert "roberto@meditrack.app" in login_res.text
    assert "lucia@meditrack.app" in login_res.text


def test_patient_admin_linking_and_schema_application_flow(client):
    """Verifica el flujo completo: solicitud de enlace, bloqueo previo, aceptación, registro directo y esquemas."""
    manager, manager_token = _register_and_get_token(
        client, "laura.gestor@test.com", "Dra. Laura Gestora", role="patient_admin"
    )
    patient1, patient1_token = _register_and_get_token(
        client, "carlos.paciente@test.com", "Carlos Paciente", role="user"
    )
    patient2, patient2_token = _register_and_get_token(
        client, "elena.paciente@test.com", "Elena Paciente", role="user"
    )

    assert manager["role"] == "patient_admin"
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    patient1_headers = {"Authorization": f"Bearer {patient1_token}"}
    patient2_headers = {"Authorization": f"Bearer {patient2_token}"}

    # 1. El administrador de pacientes envía solicitudes de enlace a varios usuarios
    link1_res = client.post(
        "/api/patient-admin/links",
        headers=manager_headers,
        json={"patient_email": "carlos.paciente@test.com"},
    )
    assert link1_res.status_code == 201
    link1_data = link1_res.json()["data"]
    assert link1_data["status"] == "pending"
    assert link1_data["patient_id"] == patient1["id"]

    link2_res = client.post(
        "/api/patient-admin/links",
        headers=manager_headers,
        json={"patient_email": "elena.paciente@test.com"},
    )
    assert link2_res.status_code == 201
    link2_data = link2_res.json()["data"]
    assert link2_data["status"] == "pending"

    # 2. Antes de aceptar la solicitud, no puede ver ni registrar medicamentos al paciente (403)
    blocked_med = client.post(
        f"/api/patient-admin/patients/{patient1['id']}/medications",
        headers=manager_headers,
        json={"name": "Losartán", "presentation": "Tableta", "stock": 30},
    )
    assert blocked_med.status_code == 403

    # 3. Los pacientes consultan sus solicitudes y las aceptan
    req_list = client.get("/api/patient-links/my-requests", headers=patient1_headers)
    assert req_list.status_code == 200
    assert len(req_list.json()["data"]) == 1

    accept1 = client.post(
        f"/api/patient-links/{link1_data['id']}/decision?decision=accept",
        headers=patient1_headers,
    )
    assert accept1.status_code == 200
    assert accept1.json()["data"]["status"] == "accepted"

    accept2 = client.post(
        f"/api/patient-links/{link2_data['id']}/decision?decision=accept",
        headers=patient2_headers,
    )
    assert accept2.status_code == 200
    assert accept2.json()["data"]["status"] == "accepted"

    # 4. Una vez aceptado el enlace, el administrador de pacientes registra medicamento y dosis manuales
    med_res = client.post(
        f"/api/patient-admin/patients/{patient1['id']}/medications",
        headers=manager_headers,
        json={
            "name": "Atorvastatina",
            "presentation": "Tabletas 20 mg",
            "stock": 28,
            "notes": "Control de colesterol",
        },
    )
    assert med_res.status_code == 201
    created_med_id = med_res.json()["data"]["id"]

    treat_res = client.post(
        f"/api/patient-admin/patients/{patient1['id']}/treatments",
        headers=manager_headers,
        json={
            "medication_id": created_med_id,
            "dosage": "1 tableta",
            "schedule_times": ["21:00"],
            "start_date": get_app_today().isoformat(),
            "duration_days": 28,
            "instructions": "Tomar antes de dormir",
        },
    )
    assert treat_res.status_code == 201
    assert treat_res.json()["data"]["medication_name"] == "Atorvastatina"

    # 5. El administrador de pacientes configura un esquema rápido y lo aplica a ambos pacientes enlazados
    schema_res = client.post(
        "/api/patient-admin/schemas",
        headers=manager_headers,
        json={
            "title": "Esquema Hipertensión Dual",
            "medication_name": "Enalapril",
            "presentation": "Tabletas 10 mg",
            "default_stock": 60,
            "dosage": "1 tableta",
            "schedule_times": ["08:00", "20:00"],
            "duration_days": 30,
            "instructions": "Tomar cada 12 horas con agua",
            "notes": "Esquema base antihipertensivo",
        },
    )
    assert schema_res.status_code == 201
    schema_id = schema_res.json()["data"]["id"]

    apply1 = client.post(
        f"/api/patient-admin/patients/{patient1['id']}/apply-schema/{schema_id}",
        headers=manager_headers,
    )
    assert apply1.status_code == 201
    apply1_data = apply1.json()["data"]
    assert apply1_data["medication"]["name"] == "Enalapril"
    assert apply1_data["treatment"]["schedule_times"] == ["08:00", "20:00"]
    assert len(apply1_data["today_doses"]) == 3  # 1 de Atorvastatina + 2 de Enalapril

    apply2 = client.post(
        f"/api/patient-admin/patients/{patient2['id']}/apply-schema/{schema_id}",
        headers=manager_headers,
    )
    assert apply2.status_code == 201
    assert len(apply2.json()["data"]["today_doses"]) == 2

    # 6. El paciente 1 ve sus medicamentos y dosis registradas por el administrador de pacientes
    p1_meds = client.get("/api/medications", headers=patient1_headers)
    assert p1_meds.status_code == 200
    assert {m["name"] for m in p1_meds.json()["data"]} == {"Atorvastatina", "Enalapril"}

    p1_doses = client.get("/api/doses/today", headers=patient1_headers)
    assert p1_doses.status_code == 200
    assert len(p1_doses.json()["data"]) == 3

    # 7. El administrador consulta el resumen del paciente con sus tratamientos y estadísticas/track
    overview_res = client.get(
        f"/api/patient-admin/patients/{patient1['id']}/overview",
        headers=manager_headers,
    )
    assert overview_res.status_code == 200
    ov = overview_res.json()["data"]
    assert ov["stats"]["medications_count"] == 2
    assert ov["stats"]["active_treatments_count"] == 2
    assert ov["stats"]["today_total"] == 3
