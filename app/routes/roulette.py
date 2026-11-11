# Ruta de la ruleta de lectura (/api/roulette).
from flask import Blueprint, g, jsonify

from app.security import login_required
from app.services.roulette_service import spin

roulette_bp = Blueprint("roulette", __name__)


# POST /api/roulette/spin: elige al azar un libro sin terminar del usuario
# para leer; si no tiene ninguno responde 409.
@roulette_bp.post("/spin")
@login_required
def roulette_spin():
    return jsonify({"data": spin(g.usuario_id)}), 201
