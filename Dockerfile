FROM python:3.15.2-slim-trixie AS builder

ENV PYTHONUNBUFFERED=True HF_HOME=/opt/hf-cache PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get upgrade -y && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD ./pyproject.toml ./pyproject.toml
RUN mkdir -p signwriting_translation && touch README.md
RUN python -m venv --without-pip /opt/venv
RUN /usr/local/bin/python -m pip --python /opt/venv/bin/python install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
RUN /usr/local/bin/python -m pip --python /opt/venv/bin/python install --no-cache-dir --upgrade --upgrade-strategy eager ".[server]" --extra-index-url https://download.pytorch.org/whl/cpu

COPY ./signwriting_translation ./signwriting_translation

ENV TIKTOKEN_CACHE_DIR=/opt/tiktoken-cache

# Prime the model by starting server, making a request, then stopping
RUN timeout 360 bash -c '\
    PORT=8080 uvicorn signwriting_translation.server:app --host 0.0.0.0 --port 8080 --workers 1 & \
    SERVER_PID=$!; \
    sleep 30; \
    curl --fail --retry 10 --retry-delay 5 --retry-connrefused \
         --location --request POST "http://localhost:8080/" \
         --header "Content-Type: application/json" \
         --data "{\"texts\": [\"hello\"], \"spoken_language\": \"en\", \"signed_language\": \"ase\"}" && \
    curl --fail --location --request POST "http://localhost:8080/signwriting-to-text" \
         --header "Content-Type: application/json" \
         --data "{\"texts\": [\"M528x518S15a28472x487S1f010490x502\"], \"spoken_language\": \"en\", \"signed_language\": \"ase\"}"; \
    CURL_EXIT=$?; \
    kill $SERVER_PID 2>/dev/null || true; \
    wait $SERVER_PID 2>/dev/null || true; \
    exit $CURL_EXIT'

FROM python:3.15.2-slim-trixie AS runtime

# The builder supplies the venv; the base interpreter's installer is unnecessary.
RUN apt-get update && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* /usr/local/lib/python3.15/ensurepip /usr/local/lib/python3.15/site-packages /usr/local/bin/pip* \
    && useradd --create-home --uid 1000 app

ENV PYTHONUNBUFFERED=True PATH="/opt/venv/bin:$PATH" PORT=8080 \
    HF_HOME=/opt/hf-cache TIKTOKEN_CACHE_DIR=/opt/tiktoken-cache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/hf-cache /opt/hf-cache
COPY --from=builder /opt/tiktoken-cache /opt/tiktoken-cache
COPY ./signwriting_translation ./signwriting_translation

USER app

CMD ["sh", "-c", "exec uvicorn signwriting_translation.server:app --host 0.0.0.0 --port $PORT --workers 1"]
