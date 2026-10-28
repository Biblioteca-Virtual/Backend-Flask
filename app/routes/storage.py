import os
import uuid
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app.errors.exceptions import ValidationError
from app.security import login_required

storage_bp = Blueprint("storage", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_covers_dir() -> str:
    base_dir = current_app.config.get("STORAGE_DIR")
    if not base_dir:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "storage")
        )
    covers_dir = os.path.join(base_dir, "covers")
    os.makedirs(covers_dir, exist_ok=True)
    return covers_dir


@storage_bp.post("/upload")
@login_required
def upload_file():
    if "file" not in request.files:
        raise ValidationError(["No se envió ningún archivo con el campo 'file'"])

    file = request.files["file"]
    if not file or not file.filename:
        raise ValidationError(["El archivo está vacío o no tiene nombre"])

    if not _allowed_file(file.filename):
        raise ValidationError([
            f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        ])

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "png"
    unique_name = f"{uuid.uuid4().hex}.{extension}"

    covers_dir = _get_covers_dir()
    destination = os.path.join(covers_dir, unique_name)
    file.save(destination)

    relative_url = f"/api/storage/covers/{unique_name}"
    return jsonify({"data": {"url": relative_url, "filename": unique_name}}), 201


@storage_bp.get("/covers/<path:filename>")
def serve_cover(filename):
    covers_dir = _get_covers_dir()
    return send_from_directory(covers_dir, filename)
