# Ruta que publica la documentación de la API en formato OpenAPI.
from pathlib import Path

from flask import Blueprint, send_file

docs_bp = Blueprint("docs", __name__)

# Ruta al archivo Backend-Flask/docs/openapi.yaml.
OPENAPI_FILE = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"


# GET /openapi.yaml: devuelve la especificación para verla en Swagger u otra herramienta.
@docs_bp.get("/openapi.yaml")
def openapi_spec():
    return send_file(OPENAPI_FILE, mimetype="application/yaml")
