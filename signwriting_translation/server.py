import os
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from signwriting_translation.bin import (
    load_sockeye_translator,
    tokenize_signwriting,
    translate,
    translate_to_text,
)
from signwriting_translation.tokenizer import tokenize_spoken_text

TEXT_TO_SW_MODEL = "sign/sockeye-text-to-factored-signwriting"
SW_TO_TEXT_MODEL = "sign/sockeye-signwriting-to-text"

text_to_sw_translator, _ = load_sockeye_translator(TEXT_TO_SW_MODEL, log_timing=True)
sw_to_text_translator, _ = load_sockeye_translator(SW_TO_TEXT_MODEL, log_timing=True)

app = FastAPI(title="Signwriting Translation API")


class TranslationRequest(BaseModel):
    texts: list[str]
    spoken_language: str
    signed_language: str


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "service": "signwriting-translation",
    }


@app.post("/")
def spoken_text_to_signwriting(request: TranslationRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="Missing `texts`")

    tokenized_texts = [
        f"${request.spoken_language} ${request.signed_language} {tokenize_spoken_text(text)}"
        for text in request.texts
    ]

    output_texts = translate(text_to_sw_translator, tokenized_texts, log_timing=True)

    return {"input": request.texts, "output": output_texts}


@app.post("/signwriting-to-text")
def signwriting_to_spoken_text(request: TranslationRequest):
    if not request.texts:
        raise HTTPException(status_code=400, detail="Missing `texts`")

    tokenized_texts = [
        f"${request.spoken_language} ${request.signed_language} {tokenize_signwriting(text)}"
        for text in request.texts
    ]

    output_texts = translate_to_text(sw_to_text_translator, tokenized_texts, log_timing=True)

    return {"input": request.texts, "output": output_texts}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), reload=True)
