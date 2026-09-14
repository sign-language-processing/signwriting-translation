from fastapi.testclient import TestClient

from signwriting_translation.server import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "signwriting-translation"
    assert "timestamp" in body
    assert "version" in body
    assert body["version"].startswith("sw-text-")
    assert ":text-sw-" in body["version"]


def test_translate():
    response = client.post("/", json={
        "texts": ["hello"],
        "spoken_language": "en",
        "signed_language": "ase",
    })
    assert response.status_code == 200
    assert len(response.headers["X-Model-Tag"]) == 32
    body = response.json()
    assert body["input"] == ["hello"]
    assert len(body["output"]) == 1
    assert body["output"][0].startswith("M")


def test_translate_signwriting_to_text():
    response = client.post("/signwriting-to-text", json={
        "texts": ["M528x518S15a28472x487S1f010490x502"],
        "spoken_language": "en",
        "signed_language": "ase",
    })
    assert response.status_code == 200
    assert len(response.headers["X-Model-Tag"]) == 32
    body = response.json()
    assert len(body["output"]) == 1
    assert isinstance(body["output"][0], str)
    assert body["output"][0]


def test_translate_empty_texts():
    response = client.post("/", json={
        "texts": [],
        "spoken_language": "en",
        "signed_language": "ase",
    })
    assert response.status_code == 400


def test_translate_missing_field():
    response = client.post("/", json={
        "texts": ["hello"],
    })
    assert response.status_code == 422
