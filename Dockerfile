FROM python:3.15.2-slim-trixie@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928

ENV PYTHONUNBUFFERED=True

RUN apt-get update && apt-get upgrade -y && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.lock /opt/requirements.lock

ADD ./pyproject.toml ./pyproject.toml
RUN mkdir -p signwriting_translation && touch README.md
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /opt/requirements.lock && pip install --no-deps ".[server]" --extra-index-url https://download.pytorch.org/whl/cpu

COPY ./signwriting_translation ./signwriting_translation

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

# Enable offline mode for HuggingFace to skip network checks on startup
# This reduces cold start time on slow networks by ~50% (from ~5.8s to ~2.7s)
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

RUN useradd --create-home --uid 1000 app && chmod -R a+rX /root/.cache && mv /root/.cache/huggingface /opt/hf-cache
ENV HF_HOME=/opt/hf-cache PORT=8080
RUN rm -rf /usr/local/lib/python*/ensurepip /usr/local/lib/python*/site-packages/pip /usr/local/lib/python*/site-packages/pip-*.dist-info /opt/venv/lib/python*/site-packages/pip /opt/venv/lib/python*/site-packages/pip-*.dist-info

USER app

CMD ["sh", "-c", "exec uvicorn signwriting_translation.server:app --host 0.0.0.0 --port $PORT --workers 1"]
