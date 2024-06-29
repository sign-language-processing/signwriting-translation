from signwriting_translation.bin import load_sockeye_translator, translate
from signwriting_translation.tokenizer import tokenize_spoken_text

spoken_language = "en"
signed_language = "ase"
texts = [
    "Hello world",
    "World",
    "Hello",
    "How are you?"
    "Hello, how are you?",
    "Hi",
    "goodbye world",
    "My name is Amit.",
    "test",
    "Test",
    "testing",
    "Testing",
    "Washington D.C.",
    "Washington, D.C.",
    "Washington DC",
]
translator, spoken_tokenizer = load_sockeye_translator(
    "/shares/iict-sp2.ebling.cl.uzh/amoryo/checkpoints/signwriting-translation/spoken-to-signed/target-factors-gpt-tuned/model",
    log_timing=True)
tokenized_texts = [tokenize_spoken_text(text) for text in texts]
model_inputs = [f"${spoken_language} ${signed_language} {tokenized_text}" for tokenized_text in tokenized_texts]

for translation in translate(translator, model_inputs, log_timing=True):
    print(translation)
    print("M500x500S38800464x496")
