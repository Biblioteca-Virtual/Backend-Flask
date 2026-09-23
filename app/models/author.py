from dataclasses import asdict, dataclass


@dataclass
class Autor:
    id: int
    nombre: str
    apellido: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            apellido=row["apellido"],
        )