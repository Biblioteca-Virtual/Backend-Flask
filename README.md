<!-- calidad:inicio -->
![Calidad](https://img.shields.io/badge/Calidad-11%2F100-red) ![Cumple](https://img.shields.io/badge/Cumple-10%2F15-yellow) ![Aprobado](https://img.shields.io/badge/Aprobado-NO-red)

**Calidad de servicios (heurístico):** índice **11/100** · cumple **10/15** · aprobado **NO** · capas **3**
`SEC 0 · SQL 1 · DBG 0 · duplicación 17.8% · endpoints 22 · tests 10`
<!-- calidad:fin -->

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
