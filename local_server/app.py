import os
import sys
from flask import Flask

# Asegurar que la carpeta local_server esté en sys.path para importaciones modulares
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from database import db, init_db_data
from blueprints.dashboard_bp import dashboard_bp
from blueprints.api_bp import api_bp

def create_app():
    """
    Factory para inicialización modular de la aplicación Flask.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Configuración de SQLite local
    db_path = os.path.join(SERVER_DIR, "sifma.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'sifma_secret_key_12345'
    
    # Asegurar directorios estáticos
    upload_dir = os.path.join(SERVER_DIR, "static", "data", "uploads")
    processed_dir = os.path.join(SERVER_DIR, "static", "data", "processed")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Inicializar ORM
    db.init_app(app)
    
    # Registrar Blueprints modulares
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    # Inicializar tablas y datos por defecto
    init_db_data(app)
    
    print("\n==============================================")
    print("Servidor Local SIFMA (Modo Offline / USB activo)")
    print("Dashboard Web en: http://127.0.0.1:5000")
    print("==============================================\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
