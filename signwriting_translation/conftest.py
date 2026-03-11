import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock heavy dependencies before importing server.py
# This avoids needing sockeye/torch/tiktoken in the test environment
sys.modules["signwriting.tokenizer"] = MagicMock()
sys.modules["sockeye"] = MagicMock()
sys.modules["sockeye.inference"] = MagicMock()
sys.modules["sockeye.translate"] = MagicMock()
sys.modules["tiktoken"] = MagicMock()
sys.modules["huggingface_hub"] = MagicMock()

with patch("signwriting_translation.bin.load_sockeye_translator", return_value=(MagicMock(), None)):
    from signwriting_translation.server import app  # pylint: disable=wrong-import-position


@pytest.fixture()
def client():
    return TestClient(app)
