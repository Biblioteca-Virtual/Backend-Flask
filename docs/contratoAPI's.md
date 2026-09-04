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