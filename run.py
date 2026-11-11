# Arranca el servidor de desarrollo de Flask (python run.py).
from app import create_app

# Instancia de la aplicación; también la usa `flask run`.
app = create_app()

# Solo al ejecutar este archivo directamente: modo debug con recarga automática.
if __name__ == '__main__':
    app.run(debug=True)
