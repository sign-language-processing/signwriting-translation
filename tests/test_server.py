from fastapi.testclient import TestClient

from signwriting_translation.server import app

client = TestClient(app)

TURNSTILE_HEADERS = {"cf-turnstile-response": "test-token"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "signwriting-translation"
    assert "timestamp" in body


def test_translate():
    response = client.post("/", json={
        "texts": ["hello"],
        "spoken_language": "en",
        "signed_language": "ase",
    }, headers=TURNSTILE_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["input"] == ["hello"]
    assert len(body["output"]) == 1
    assert body["output"][0].startswith("M")


def test_translate_empty_texts():
    response = client.post("/", json={
        "texts": [],
        "spoken_language": "en",
        "signed_language": "ase",
    }, headers=TURNSTILE_HEADERS)
    assert response.status_code == 400


def test_translate_missing_field():
    response = client.post("/", json={
        "texts": ["hello"],
    }, headers=TURNSTILE_HEADERS)
    assert response.status_code == 422
