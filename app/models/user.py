from dataclasses import asdict, dataclass


@dataclass
class Usuario:
    id: int
    nombre: str
    apellido: str
    email: str
    password: str
    fecha_registro: str

    def to_dict(self):
        data = asdict(self)
        data.pop("password")
        return data

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            apellido=row["apellido"],
            email=row["email"],
            password=row["password"],
            fecha_registro=row["fecha_registro"],
        )