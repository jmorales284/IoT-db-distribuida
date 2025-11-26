# Dockerfile
FROM python:3.11-slim

# Evitar buffering y problemas con logs en contenedor
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /app

# Instalar dependencias del sistema si hace falta (por ahora solo ca-certificates y curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Puerto interno que usa la app
ENV PORT=8080

# Comando de arranque (Cloud Run espera que escuche en $PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
