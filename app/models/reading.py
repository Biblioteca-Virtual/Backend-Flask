from dataclasses import dataclass


@dataclass
class Prestamo:
    id: int
    usuario_id: int
    libro_id: int
    fecha_prestamo: str
    fecha_devolucion: str
    estado: str
    libro_titulo: str = None
    usuario_nombre: str = None
    usuario_apellido: str = None

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario": (
                f"{self.usuario_nombre} {self.usuario_apellido}".strip()
                if self.usuario_nombre
                else None
            ),
            "libro_id": self.libro_id,
            "libro_titulo": self.libro_titulo,
            "fecha_prestamo": self.fecha_prestamo,
            "fecha_devolucion": self.fecha_devolucion,
            "estado": self.estado,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            usuario_id=row["usuario_id"],
            libro_id=row["libro_id"],
            fecha_prestamo=row["fecha_prestamo"],
            fecha_devolucion=row.get("fecha_devolucion"),
            estado=row["estado"],
            libro_titulo=row.get("libro_titulo"),
            usuario_nombre=row.get("usuario_nombre"),
            usuario_apellido=row.get("usuario_apellido"),
        )