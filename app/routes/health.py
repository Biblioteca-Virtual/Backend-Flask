# Ruta de estado del servicio (/health), útil para comprobar que el backend responde.
from flask import Blueprint, jsonify

from app.db import fetch_one

health_bp = Blueprint("health", __name__)


# GET /health: responde siempre 200 e indica si la base de datos contesta ("ok")
# o no ("indisponible").
@health_bp.get("/health")
def health():
    database = "ok"
    try:
        fetch_one("SELECT 1")
    except Exception:
        database = "indisponible"
    return jsonify({"status": "ok", "database": database}), 200