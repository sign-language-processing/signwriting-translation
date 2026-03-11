FROM python:3.11-slim

ENV PYTHONUNBUFFERED=True

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD ./pyproject.toml ./pyproject.toml
RUN mkdir -p signwriting_translation && touch README.md
RUN pip install --no-cache-dir ".[server]"

COPY ./signwriting_translation ./signwriting_translation

# Prime the model by starting server, making a request, then stopping
RUN timeout 360 bash -c '\
    PORT=8080 uvicorn signwriting_translation.server:app --host 0.0.0.0 --port 8080 --workers 1 & \
    SERVER_PID=$!; \
    sleep 30; \
    curl --fail --retry 10 --retry-delay 5 --retry-connrefused \
         --location --request POST "http://localhost:8080/" \
         --header "Content-Type: application/json" \
         --data "{\"texts\": [\"hello\"], \"spoken_language\": \"en\", \"signed_language\": \"ase\"}"; \
    CURL_EXIT=$?; \
    kill $SERVER_PID 2>/dev/null || true; \
    wait $SERVER_PID 2>/dev/null || true; \
    exit $CURL_EXIT'

# Enable offline mode for HuggingFace to skip network checks on startup
# This reduces cold start time on slow networks by ~50% (from ~5.8s to ~2.7s)
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

CMD ["sh", "-c", "uvicorn signwriting_translation.server:app --host 0.0.0.0 --port $PORT --workers 1"]
