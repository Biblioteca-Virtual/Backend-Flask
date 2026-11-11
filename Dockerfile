# Imagen del backend Flask de ÁmbarLy.
# Se construye desde docker-compose.yml (servicio "api"), pero también funciona sola:
#   docker build -t ambarly-api .
FROM python:3.13-slim

# Sin archivos .pyc y con la salida de print/logging al instante en `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias, para que Docker reutilice esta capa si no cambian.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación y la especificación OpenAPI que sirve GET /openapi.yaml.
COPY app/ app/
COPY run.py .
COPY docs/openapi.yaml docs/openapi.yaml

EXPOSE 5000

# Servidor de Flask escuchando en todas las interfaces del contenedor.
CMD ["flask", "--app", "run", "run", "--host=0.0.0.0", "--port=5000"]
