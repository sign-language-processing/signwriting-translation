from signwriting_translation.bin import load_sockeye_translator, translate
from signwriting_translation.tokenizer import tokenize_spoken_text

MODEL_ID = "sign/sockeye-text-to-factored-signwriting"


def test_single_translation():
    translator, _ = load_sockeye_translator(MODEL_ID)
    tokenized = tokenize_spoken_text("Hello")
    model_input = f"$en $ase {tokenized}"
    results = translate(translator, [model_input])
    assert len(results) == 1
    assert results[0].startswith("M")
