import sys
from unittest.mock import MagicMock, patch

import pytest

mock_translator = MagicMock()


@pytest.fixture(autouse=True)
def _mock_deps():
    with patch.dict(sys.modules, {
        "signwriting_translation.bin": MagicMock(
            load_sockeye_translator=MagicMock(return_value=(mock_translator, None)),
            translate=MagicMock(return_value=["M500x500S14c20489x524"]),
        ),
        "signwriting_translation.tokenizer": MagicMock(
            tokenize_spoken_text=MagicMock(side_effect=lambda t: t),
        ),
        "signwriting.tokenizer": MagicMock(),
        "sockeye": MagicMock(),
        "sockeye.inference": MagicMock(),
        "tiktoken": MagicMock(),
    }):
        # Remove cached server module so it re-imports with mocks
        sys.modules.pop("signwriting_translation.server", None)
        yield


@pytest.fixture()
def client(_mock_deps):
    from signwriting_translation.server import app
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "signwriting-translation"
    assert "timestamp" in body


def test_translate(client):
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
