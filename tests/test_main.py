import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-mock"}):
    with patch("google.genai.Client"):
        from main import app

client = TestClient(app)

VALID_RESPONSE = {
    "categoria": "seguro_auto",
    "nivel_riesgo": 3,
    "resumen": "Seguro de auto con cobertura total y deducible bajo.",
    "recomendacion": "Recomendado para conductores frecuentes con vehículo de valor medio-alto.",
    "alertas": [
        "Verificar exclusiones por uso comercial",
        "Revisar proceso de peritaje",
        "Confirmar cobertura en zonas de riesgo"
    ],
    "publico_objetivo": "Conductores adultos con vehículo propio de uso diario"
}

def make_mock(data):
    m = MagicMock()
    m.text = json.dumps(data)
    return m

def test_health_returns_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_analyze_returns_valid_structure():
    with patch("main.client") as mc:
        mc.models.generate_content.return_value = make_mock(VALID_RESPONSE)
        r = client.post("/analyze", json={"texto": "Seguro de auto cobertura total prima $45/mes deducible $200"})
    assert r.status_code == 200
    data = r.json()
    for field in ["categoria", "nivel_riesgo", "resumen", "recomendacion", "alertas", "publico_objetivo"]:
        assert field in data

def test_nivel_riesgo_within_bounds():
    with patch("main.client") as mc:
        mc.models.generate_content.return_value = make_mock(VALID_RESPONSE)
        r = client.post("/analyze", json={"texto": "Seguro de auto cobertura total con deducible de $200"})
    assert 1 <= r.json()["nivel_riesgo"] <= 10

def test_analyze_with_context():
    with patch("main.client") as mc:
        mc.models.generate_content.return_value = make_mock(VALID_RESPONSE)
        r = client.post("/analyze", json={"texto": "Crédito hipotecario a 20 años tasa UF + 3.5%", "contexto": "credito"})
    assert r.status_code == 200

def test_rejects_empty_texto():
    assert client.post("/analyze", json={"texto": ""}).status_code == 422

def test_rejects_missing_body():
    assert client.post("/analyze", json={}).status_code == 422

def test_rejects_texto_too_short():
    assert client.post("/analyze", json={"texto": "corto"}).status_code == 422

def test_alerts_is_a_list():
    with patch("main.client") as mc:
        mc.models.generate_content.return_value = make_mock(VALID_RESPONSE)
        r = client.post("/analyze", json={"texto": "Fondo mutuo renta fija liquidez diaria rentabilidad 4% anual"})
    assert isinstance(r.json()["alertas"], list)

def test_nivel_riesgo_clamped():
    bad = {**VALID_RESPONSE, "nivel_riesgo": 99}
    with patch("main.client") as mc:
        mc.models.generate_content.return_value = make_mock(bad)
        r = client.post("/analyze", json={"texto": "Derivado financiero apalancamiento 10x mercados emergentes"})
    assert r.json()["nivel_riesgo"] <= 10

def test_categories_endpoint():
    r = client.get("/categories")
    assert r.status_code == 200
    assert len(r.json()["categorias"]) > 0

def test_docs_accessible():
    assert client.get("/docs").status_code == 200
