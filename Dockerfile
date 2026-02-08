# syntax=docker/dockerfile:1

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for torch/cv (sentence-transformers pulls torch)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Aplica patch do chromadb para Python 3.10+/pydantic v2
RUN python scripts/patch_chromadb.py

EXPOSE 3000

# Le .env se montado; HOST/PORT podem ser sobrescritos no compose
CMD ["python", "-m", "src.server"]
