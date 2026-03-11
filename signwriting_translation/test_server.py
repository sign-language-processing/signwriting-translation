from unittest.mock import patch


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "signwriting-translation"
    assert "timestamp" in body


def test_translate(client):
    with patch("signwriting_translation.server.translate", return_value=["M500x500S14c20489x524"]):
        response = client.post("/", json={
            "texts": ["hello"],
            "spoken_language": "en",
            "signed_language": "ase",
        })
    assert response.status_code == 200
    body = response.json()
    assert body["input"] == ["hello"]
    assert body["output"] == ["M500x500S14c20489x524"]


def test_translate_empty_texts(client):
    response = client.post("/", json={
        "texts": [],
        "spoken_language": "en",
        "signed_language": "ase",
    })
    assert response.status_code == 400


def test_translate_missing_field(client):
    response = client.post("/", json={
        "texts": ["hello"],
    })
    assert response.status_code == 422
