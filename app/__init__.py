import os
from flask import Flask
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'

    # Registrar las rutas
    register_routes(app)

    # Registrar otros blueprints si es necesario
    from .views.main import main_bp
    app.register_blueprint(main_bp)

    return app