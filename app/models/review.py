# Modelo de una reseña: la calificación y el comentario de un usuario sobre un libro.
from dataclasses import dataclass

from app.models.common import format_user_name


# Reseña con el título del libro y el nombre del autor de la reseña (vienen de un JOIN).
# La calificación admite medias estrellas (por ejemplo, 3.5).
# - to_dict(): arma el JSON que devuelve la API.
# - from_row(): crea la reseña a partir de una fila de la base de datos.
@dataclass
class Resena:
    id: int
    libro_id: int
    usuario_id: int
    calificacion: float
    comentario: str
    fecha_creacion: str
    libro_titulo: str = None
    usuario_nombre: str = None
    usuario_apellido: str = None

    def to_dict(self):
        return {
            "id": self.id,
            "libro_id": self.libro_id,
            "libro_titulo": self.libro_titulo,
            "usuario_id": self.usuario_id,
            "usuario": format_user_name(self.usuario_nombre, self.usuario_apellido),
            # La columna es NUMERIC: psycopg2 da un Decimal, que en JSON sería texto.
            "calificacion": float(self.calificacion),
            "comentario": self.comentario,
            "fecha_creacion": self.fecha_creacion,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            libro_id=row["libro_id"],
            usuario_id=row["usuario_id"],
            calificacion=row["calificacion"],
            comentario=row.get("comentario"),
            fecha_creacion=row["fecha_creacion"],
            libro_titulo=row.get("libro_titulo"),
            usuario_nombre=row.get("usuario_nombre"),
            usuario_apellido=row.get("usuario_apellido"),
        )
