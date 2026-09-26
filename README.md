# Backend-Flask
Hacer las mismas Issues  para este backend que para el otro
# Crear el entorno virtual
python -m venv .venv

# Activarlo
.venv\Scripts\activate

# Ejecutar el servicio
python run.py

# Ejecutar BD
docker compose up

# Ejecutar pruebas
python -m unittest discover -s tests -v

# Documentación OpenAPI
La especificación está en `docs/openapi.yaml` y también disponible en
`http://localhost:5000/openapi.yaml` al ejecutar el servicio.
