import os
from datetime import datetime, timezone

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from signwriting_translation.bin import load_sockeye_translator, translate
from signwriting_translation.tokenizer import tokenize_spoken_text

MODEL_ID = "sign/sockeye-text-to-factored-signwriting"

translator, _ = load_sockeye_translator(MODEL_ID, log_timing=True)

TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY")

app = FastAPI(title="Signwriting Translation API")


@app.middleware("http")
async def turnstile_verification(request: Request, call_next):
    if request.url.path == "/health" or not TURNSTILE_SECRET_KEY:
        return await call_next(request)

    token = request.headers.get("cf-turnstile-response")
    if not token:
        return JSONResponse(status_code=403, content={"error": "Missing Turnstile token"})

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET_KEY, "response": token},
        )

    if not response.json().get("success"):
        return JSONResponse(status_code=403, content={"error": "Invalid Turnstile token"})

    return await call_next(request)


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

    output_texts = translate(translator, tokenized_texts, log_timing=True)

    return {"input": request.texts, "output": output_texts}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), reload=True)
