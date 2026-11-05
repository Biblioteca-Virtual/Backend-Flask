<!-- calidad:inicio -->
![Calidad](https://img.shields.io/badge/Calidad-100%2F100-green) ![Aprobado](https://img.shields.io/badge/Aprobado-NO-red) ![Cumple](https://img.shields.io/badge/Cumple-14%2F15-green) ![Duplicación](https://img.shields.io/badge/Duplicaci%C3%B3n-5.6%25-green) ![SEC](https://img.shields.io/badge/SEC-0-green) ![SQL](https://img.shields.io/badge/SQL-0-green) ![DBG](https://img.shields.io/badge/DBG-0-green) ![Capas](https://img.shields.io/badge/Capas-3-green) ![Tests](https://img.shields.io/badge/Tests-13-green) ![Cob](https://img.shields.io/badge/Cob-67%25-yellow) ![EP](https://img.shields.io/badge/EP-33-green)

**Calidad de servicios (heurístico):** índice **100/100** · cumple **14/15** · aprobado **NO** · capas **3**
Detalle completo en [`docs/EVALUACION.md`](docs/EVALUACION.md).
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

# Migraciones de la base de datos
`database/init.sql` solo se ejecuta la **primera vez** que se crea el volumen
de Docker. Si la base ya existía, los cambios de esquema hay que aplicarlos con
las migraciones de `database/migrations/`, en orden:

```bash
docker exec -i biblioteca_postgres psql -U biblioteca_user -d biblioteca_db < database/migrations/008_catalogo_y_remover_prestamos.sql
docker exec -i biblioteca_postgres psql -U biblioteca_user -d biblioteca_db < database/migrations/009_colecciones.sql
docker exec -i biblioteca_postgres psql -U biblioteca_user -d biblioteca_db < database/migrations/010_bibliotecas_por_usuario.sql
```

Son idempotentes: se pueden volver a ejecutar sin romper nada.

# Ejecutar pruebas
python -m unittest discover -s tests -v

# Documentación OpenAPI
La especificación está en `docs/openapi.yaml` y también disponible en
`http://localhost:5000/openapi.yaml` al ejecutar el servicio.
