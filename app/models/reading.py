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
    fecha_actualizacion: str = None
    progreso: int = 0

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
            "fecha_actualizacion": self.fecha_actualizacion,
            "estado": self.estado,
            "progreso": self.progreso,
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
            fecha_actualizacion=row.get("fecha_actualizacion"),
            estado=row["estado"],
            progreso=row.get("progreso", 0),
            libro_titulo=row.get("libro_titulo"),
            usuario_nombre=row.get("usuario_nombre"),
            usuario_apellido=row.get("usuario_apellido"),
        )
