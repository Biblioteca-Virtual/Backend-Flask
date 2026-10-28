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
    paginas_totales: int = 0
    paginas_leidas: int = 0
    imagen_portada: str = None

    @property
    def porcentaje_lectura(self) -> int:
        if not self.paginas_totales or self.paginas_totales <= 0:
            return 0
        porcentaje = round((self.paginas_leidas / self.paginas_totales) * 100)
        return min(max(porcentaje, 0), 100)

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
            "paginas_totales": self.paginas_totales or 0,
            "paginas_leidas": self.paginas_leidas or 0,
            "porcentaje_lectura": self.porcentaje_lectura,
            "imagen_portada": self.imagen_portada,
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
            cantidad=row.get("cantidad", 1),
            categoria_id=row.get("categoria_id", 1),
            categoria_nombre=row.get("categoria_nombre"),
            paginas_totales=row.get("paginas_totales", 0) or 0,
            paginas_leidas=row.get("paginas_leidas", 0) or 0,
            imagen_portada=row.get("imagen_portada"),
        )
