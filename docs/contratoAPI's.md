| Método | Endpoint | Auth | Función |
|---|---|---:|---|
| `GET` | `/health` | ❌ | Estado del servidor |
| `POST` | `/auth/register` | ❌ | Registrar usuario |
| `POST` | `/auth/login` | ❌ | Iniciar sesión |
| `GET` | `/books` | ✅ | Listar libros |
| `GET` | `/books/{id}` | ✅ | Obtener libro |
| `POST` | `/books` | ✅ | Crear libro |
| `PUT` | `/books/{id}` | ✅ | Editar libro |
| `DELETE` | `/books/{id}` | ✅ | Eliminar libro |
| `GET` | `/readings` | ✅ | Listar lecturas |
| `GET` | `/readings/{id}` | ✅ | Obtener lectura |
| `POST` | `/readings` | ✅ | Comenzar lectura |
| `PUT` | `/readings/{id}` | ✅ | Actualizar lectura |
| `DELETE` | `/readings/{id}` | ✅ | Eliminar lectura |
| `GET` | `/reviews` | ✅ | Listar reseñas |
| `GET` | `/reviews/{id}` | ✅ | Obtener reseña |
| `POST` | `/reviews` | ✅ | Crear reseña |
| `PUT` | `/reviews/{id}` | ✅ | Editar reseña |
| `DELETE` | `/reviews/{id}` | ✅ | Eliminar reseña |
| `POST` | `/roulette/spin` | ✅ | Seleccionar lectura |

## Gestión de lecturas

Los endpoints de lecturas pertenecen al usuario autenticado. Por eso, el cliente
no debe enviar `usuario_id`: la API lo obtiene del token y evita que un usuario
consulte o modifique la lectura de otra persona.

El recurso conserva los estados del préstamo y de la disponibilidad de las
copias:

- `activo`: lectura/préstamo abierto.
- `devuelto`: lectura/préstamo cerrado; se conserva la fecha de devolución.

`progreso` es un porcentaje entero entre 0 y 100. Es independiente del estado:
actualizar el progreso a 100 no devuelve automáticamente el libro. Para cerrar
la lectura se debe enviar `estado: "devuelto"`; al reactivarla se comprueba que
haya una copia disponible.

`GET /api/readings` admite los filtros opcionales `estado` y `libro_id`.

### Crear una lectura

```http
POST /api/readings
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "libro_id": 1,
  "progreso": 0
}
```

`libro_id` es obligatorio y `progreso` es opcional (0 por defecto). La creación
registra un préstamo activo y no necesita que el cliente indique el usuario.

### Actualizar una lectura

```http
PUT /api/readings/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "progreso": 60
}
```

Se puede enviar `progreso`, `estado` o ambos. La API conserva los campos no
enviados, valida el rango del progreso y actualiza `fecha_actualizacion`. Al
cambiar de `devuelto` a `activo` se verifica la disponibilidad de copias dentro
de una transacción.

### Migración de bases existentes

Las instalaciones nuevas usan `database/init.sql`. Para una base PostgreSQL que
ya tenga el volumen inicial, aplicar `database/migrations/007_gestion_lecturas.sql`
con `psql` antes de iniciar la API.