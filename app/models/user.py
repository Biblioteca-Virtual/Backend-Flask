# Modelo de un usuario registrado.
from dataclasses import asdict, dataclass


# Usuario con sus datos personales y el hash de su contraseña.
# - to_dict(): arma el JSON para la API sin incluir nunca la contraseña.
# - from_row(): crea el usuario a partir de una fila de la base de datos.
# email_verificado vale True por defecto para los usuarios creados antes de la verificación.
@dataclass
class Usuario:
    id: int
    nombre: str
    apellido: str
    email: str
    password: str
    fecha_registro: str
    email_verificado: bool = True

    def to_dict(self):
        data = asdict(self)
        # el hash de la contraseña no sale nunca de la API
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
            email_verificado=row.get("email_verificado", True),
        )
