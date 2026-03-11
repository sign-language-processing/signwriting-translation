import sys
from unittest.mock import MagicMock

# Mock heavy dependencies before any test imports server.py
# This avoids needing sockeye/torch/tiktoken in the test environment
sys.modules["signwriting.tokenizer"] = MagicMock()
sys.modules["sockeye"] = MagicMock()
sys.modules["sockeye.inference"] = MagicMock()
sys.modules["sockeye.translate"] = MagicMock()
sys.modules["tiktoken"] = MagicMock()
sys.modules["huggingface_hub"] = MagicMock()

from unittest.mock import patch

with patch("signwriting_translation.bin.load_sockeye_translator", return_value=(MagicMock(), None)):
    from signwriting_translation.server import app

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    return TestClient(app)
