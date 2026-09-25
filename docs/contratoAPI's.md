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
| `POST` | `/roulette/spin` | ✅ | Seleccionar y registrar lectura |

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

## Ruleta de lectura

La ruleta selecciona de forma aleatoria un libro con al menos una copia libre.
El usuario se obtiene del token: cada giro registra una lectura activa con
progreso `0` y no acepta un `usuario_id` desde el cliente.

La disponibilidad se calcula comparando la cantidad total de cada libro con sus
lecturas activas. Si un libro se agota después de ser seleccionado, la API
reintenta con otro candidato. Si no quedan libros disponibles, responde `409`.

### Girar la ruleta

```http
POST /api/roulette/spin
Authorization: Bearer <token>
```

La respuesta exitosa es `201` con la lectura creada:

```json
{
  "data": {
    "id": 10,
    "usuario_id": 42,
    "libro_id": 3,
    "estado": "activo",
    "progreso": 0
  }
}
```

## Gestión de reseñas

Las reseñas pertenecen a un usuario y a un libro. Todos los endpoints requieren
autenticación. La API toma el usuario del token y no acepta un `usuario_id` del
cliente para crear, modificar o eliminar una reseña.

Un usuario puede registrar como máximo una reseña por libro. Las consultas son
públicas para los usuarios autenticados; la modificación y eliminación solo
pueden realizarse sobre reseñas propias.

### Crear una reseña

```http
POST /api/reviews
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "libro_id": 1,
  "calificacion": 5,
  "comentario": "Excelente lectura"
}
```

`libro_id` y `calificacion` son obligatorios. La calificación debe ser un entero
entre 1 y 5. El comentario es opcional y puede ser texto o `null`.

### Consultar reseñas

```http
GET /api/reviews
GET /api/reviews/{id}
Authorization: Bearer <token>
```

La colección devuelve las reseñas ordenadas por identificador y la consulta
individual devuelve una reseña con el título del libro y el nombre del usuario
que la escribió.

### Modificar una reseña

```http
PUT /api/reviews/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "calificacion": 4,
  "comentario": "Actualización de mi reseña"
}
```

Se debe enviar `calificacion`, `comentario` o ambos. Los campos omitidos conservan
su valor. Una reseña perteneciente a otro usuario responde `404`.

### Eliminar una reseña

```http
DELETE /api/reviews/{id}
Authorization: Bearer <token>
```

Solo el propietario puede eliminar la reseña. La respuesta exitosa es `200` con
`{"message": "Reseña eliminada"}`.
