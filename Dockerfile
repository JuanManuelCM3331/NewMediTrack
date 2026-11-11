FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Bogota \
    DATABASE_URL=sqlite:////app/data/meditrack.db

WORKDIR /app

# Instalar dependencias del sistema mínimas y zona horaria
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python primero para aprovechar caché de capas
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear usuario sin privilegios y directorio persistente para SQLite
RUN useradd --create-home --shell /bin/bash meditrack \
    && mkdir -p /app/data \
    && chown -R meditrack:meditrack /app

USER meditrack

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
