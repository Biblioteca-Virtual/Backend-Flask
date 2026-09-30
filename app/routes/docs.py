from pathlib import Path

from flask import Blueprint, Response, send_file

docs_bp = Blueprint("docs", __name__)

OPENAPI_FILE = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Biblioteca Virtual API - Swagger UI</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"
    />
    <style>
      body { margin: 0; background: #fafafa; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
    <script>
      window.onload = function () {
        window.ui = SwaggerUIBundle({
          url: "/openapi.yaml",
          dom_id: "#swagger-ui",
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: "BaseLayout",
          persistAuthorization: true,
        });
      };
    </script>
  </body>
</html>
"""


@docs_bp.get("/openapi.yaml")
def openapi_spec():
    return send_file(OPENAPI_FILE, mimetype="application/yaml")


@docs_bp.get("/docs")
def swagger_ui():
    return Response(SWAGGER_UI_HTML, mimetype="text/html")
