"""Reconoce cuándo dos títulos escritos distinto son el mismo libro.

Cada usuario carga sus libros a mano, así que el mismo libro llega como
"Harry Potter y la cámara de los secretos", "harry potter y la camara de los
secretos" o con algún error de tipeo. Para compartir reseñas entre ellos se
comparan los títulos normalizados y se aceptan pequeñas diferencias.
"""

import re
import unicodedata
from difflib import SequenceMatcher

# Parecido mínimo (0 a 1) para considerar que dos títulos son el mismo libro.
# 0.85 acepta una o dos letras distintas en un título mediano, pero separa
# libros de una misma saga como "Harry Potter y la piedra filosofal" y
# "Harry Potter y la cámara de los secretos".
SIMILARITY_THRESHOLD = 0.85

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title):
    """Minúsculas, sin tildes ni signos y con un solo espacio entre palabras."""
    decomposed = unicodedata.normalize("NFKD", title or "")
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _NON_ALNUM.sub(" ", without_accents.lower()).strip()


def same_book(title_a, title_b):
    a, b = normalize_title(title_a), normalize_title(title_b)
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= SIMILARITY_THRESHOLD
