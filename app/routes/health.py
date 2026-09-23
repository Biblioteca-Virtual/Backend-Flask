from flask import Blueprint, jsonify

from app.db import fetch_one

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    database = "ok"
    try:
        fetch_one("SELECT 1")
    except Exception:
        database = "indisponible"
    return jsonify({"status": "ok", "database": database}), 200