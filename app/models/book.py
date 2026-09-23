from dataclasses import dataclass, field


@dataclass
class Libro:
    id: int
    titulo: str
    isbn: str
    descripcion: str
    anio_publicacion: int
    cantidad: int
    categoria_id: int
    categoria_nombre: str = None
    autores: list = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "isbn": self.isbn,
            "descripcion": self.descripcion,
            "anio_publicacion": self.anio_publicacion,
            "cantidad": self.cantidad,
            "categoria": {
                "id": self.categoria_id,
                "nombre": self.categoria_nombre,
            },
            "autores": self.autores,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            titulo=row["titulo"],
            isbn=row.get("isbn"),
            descripcion=row.get("descripcion"),
            anio_publicacion=row.get("anio_publicacion"),
            cantidad=row["cantidad"],
            categoria_id=row["categoria_id"],
            categoria_nombre=row.get("categoria_nombre"),
        )