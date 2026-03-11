import os
from datetime import datetime, timezone
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from signwriting_translation.bin import load_sockeye_translator, translate
from signwriting_translation.tokenizer import tokenize_spoken_text

MODEL_ID = "sign/sockeye-text-to-factored-signwriting"

translator, _ = load_sockeye_translator(MODEL_ID, log_timing=True)

app = FastAPI(title="Signwriting Translation API")


class TranslationRequest(BaseModel):  # pylint: disable=too-few-public-methods
    texts: List[str]
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

    output_texts = translate(translator, tokenized_texts, log_timing=True)

    return {"input": request.texts, "output": output_texts}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), reload=True)
