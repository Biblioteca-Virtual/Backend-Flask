# Rutas de archivos (/api/storage): subida de portadas y descarga de las imágenes.
import os
import uuid
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from app.errors.exceptions import ValidationError
from app.security import login_required

# Blueprint que agrupa estas rutas; create_app() lo registra con el prefijo /api/storage.
storage_bp = Blueprint("storage", __name__)

# Extensiones de imagen que se aceptan como portada.
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}


# Verdadero si el nombre tiene una extensión permitida (sin importar mayúsculas).
def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Carpeta donde se guardan las portadas: <STORAGE_DIR>/covers. Si no hay STORAGE_DIR
# configurado usa Backend-Flask/storage. Crea la carpeta si todavía no existe.
def _get_covers_dir() -> str:
    base_dir = current_app.config.get("STORAGE_DIR")
    if not base_dir:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "storage")
        )
    covers_dir = os.path.join(base_dir, "covers")
    os.makedirs(covers_dir, exist_ok=True)
    return covers_dir


# Comprueba que el pedido traiga un archivo en el campo 'file', con nombre y con una
# extensión permitida. Si algo falla responde 400; si no, devuelve el archivo.
def _validated_upload():
    if "file" not in request.files:
        raise ValidationError(["No se envió ningún archivo con el campo 'file'"])

    file = request.files["file"]
    if not file or not file.filename:
        raise ValidationError(["El archivo está vacío o no tiene nombre"])

    if not _allowed_file(file.filename):
        raise ValidationError([
            f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        ])
    return file


# Genera un nombre aleatorio (uuid) con la extensión original, para que dos archivos
# con el mismo nombre no se pisen y el nombre no traiga rutas peligrosas.
def _unique_name(filename: str) -> str:
    safe_name = secure_filename(filename)
    extension = safe_name.rsplit(".", 1)[1].lower() if "." in safe_name else "png"
    return f"{uuid.uuid4().hex}.{extension}"


# POST /api/storage/upload: guarda la portada y devuelve la URL para mostrarla.
@storage_bp.post("/upload")
@login_required
def upload_file():
    file = _validated_upload()
    unique_name = _unique_name(file.filename)
    file.save(os.path.join(_get_covers_dir(), unique_name))

    relative_url = f"/api/storage/covers/{unique_name}"
    return jsonify({"data": {"url": relative_url, "filename": unique_name}}), 201


# GET /api/storage/covers/<archivo>: sirve la imagen. Es pública para que funcione
# en <img src>. send_from_directory impide salir de la carpeta de portadas.
@storage_bp.get("/covers/<path:filename>")
def serve_cover(filename):
    covers_dir = _get_covers_dir()
    return send_from_directory(covers_dir, filename)
