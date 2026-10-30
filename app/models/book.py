from dataclasses import dataclass, field

UBICACIONES = ("fisico", "kindle", "web")


@dataclass
class Libro:
    id: int
    usuario_id: int
    titulo: str
    descripcion: str
    categoria_id: int
    categoria_nombre: str = None
    autores: list = field(default_factory=list)
    paginas_totales: int = 0
    paginas_leidas: int = 0
    imagen_portada: str = None
    ubicacion: str = "fisico"
    url_lectura: str = None

    @property
    def porcentaje_lectura(self) -> int:
        if not self.paginas_totales or self.paginas_totales <= 0:
            return 0
        porcentaje = round((self.paginas_leidas / self.paginas_totales) * 100)
        return min(max(porcentaje, 0), 100)

    @property
    def terminado(self) -> bool:
        return bool(self.paginas_totales) and self.paginas_leidas >= self.paginas_totales

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": {
                "id": self.categoria_id,
                "nombre": self.categoria_nombre,
            },
            "autores": self.autores,
            "paginas_totales": self.paginas_totales or 0,
            "paginas_leidas": self.paginas_leidas or 0,
            "porcentaje_lectura": self.porcentaje_lectura,
            "terminado": self.terminado,
            "imagen_portada": self.imagen_portada,
            "ubicacion": self.ubicacion,
            "url_lectura": self.url_lectura,
        }

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            usuario_id=row.get("usuario_id"),
            titulo=row["titulo"],
            descripcion=row.get("descripcion"),
            categoria_id=row.get("categoria_id", 1),
            categoria_nombre=row.get("categoria_nombre"),
            paginas_totales=row.get("paginas_totales", 0) or 0,
            paginas_leidas=row.get("paginas_leidas", 0) or 0,
            imagen_portada=row.get("imagen_portada"),
            ubicacion=row.get("ubicacion") or "fisico",
            url_lectura=row.get("url_lectura"),
        )
