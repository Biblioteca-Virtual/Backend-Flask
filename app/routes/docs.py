from pathlib import Path

from flask import Blueprint, send_file

docs_bp = Blueprint("docs", __name__)

OPENAPI_FILE = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"


@docs_bp.get("/openapi.yaml")
def openapi_spec():
    return send_file(OPENAPI_FILE, mimetype="application/yaml")
