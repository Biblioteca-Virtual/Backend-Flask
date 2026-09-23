from dataclasses import dataclass


@dataclass
class Resena:
    id: int
    libro_id: int
    usuario_id: int
    calificacion: int
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
            "usuario": (
                f"{self.usuario_nombre} {self.usuario_apellido}".strip()
                if self.usuario_nombre
                else None
            ),
            "calificacion": self.calificacion,
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