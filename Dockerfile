FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD ./pyproject.toml ./pyproject.toml
RUN mkdir -p signwriting_translation && touch README.md
RUN pip install --no-cache-dir ".[server]"

COPY ./signwriting_translation ./signwriting_translation

CMD exec uvicorn signwriting_translation.server:app --host 0.0.0.0 --port $PORT --workers 1
