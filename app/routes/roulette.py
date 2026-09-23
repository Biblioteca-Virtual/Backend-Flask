from flask import Blueprint, jsonify

from app.security import login_required
from app.services.roulette_service import spin

roulette_bp = Blueprint("roulette", __name__)


@roulette_bp.post("/spin")
@login_required
def roulette_spin():
    return jsonify({"data": spin()}), 200