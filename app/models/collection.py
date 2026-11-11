# Modelo de una colección: un grupo de libros que arma el usuario.
from dataclasses import dataclass, field


# Colección con su nombre, la cantidad de libros y, en el detalle, la lista de libros.
# - to_dict(): arma el JSON que devuelve la API.
# - from_row(): crea la colección a partir de una fila; los libros se cargan aparte.
@dataclass
class Coleccion:
    id: int
    usuario_id: int
    nombre: str
    fecha_creacion: str
    cantidad_libros: int = 0
    libros: list = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "nombre": self.nombre,
            "fecha_creacion": self.fecha_creacion,
            "cantidad_libros": self.cantidad_libros,
            "libros": self.libros,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            usuario_id=row["usuario_id"],
            nombre=row["nombre"],
            fecha_creacion=row["fecha_creacion"],
            cantidad_libros=row.get("cantidad_libros", 0) or 0,
        )
