# Debe coincidir con requires-python (>=3.12) y .python-version
FROM python:3.12-slim

# Versión fija de uv para builds reproducibles
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

# Tesseract y sus modelos de idioma (inglés viene incluido con tesseract-ocr)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ruta del binario de Tesseract dentro de la imagen (sobrescribe la de Windows del .env)
ENV URL_TESSERACT=/usr/bin/tesseract \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Instalar solo dependencias (capa cacheable mientras no cambie el lock)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copiar el código (el proyecto vive en la raíz, no en app/)
COPY pyproject.toml uv.lock README.md main.py ./
COPY config ./config
COPY llm ./llm
COPY models ./models
COPY routes ./routes

# 3. Instalar el proyecto
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Carpeta para archivos subidos
RUN mkdir -p /app/files

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
