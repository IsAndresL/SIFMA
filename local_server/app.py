import os
import sys
from flask import Flask

# Asegurar sys.path para importaciones modulares
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from core.dependencies import ensure_dependencies
ensure_dependencies()

from core.config import config
from core.logger import logger
from infrastructure.database import db, init_db_data
from presentation.web import dashboard_bp
from presentation.api import api_bp

def create_app():
    """
    Fábrica de inicialización de la aplicación Flask (Application Factory Pattern).
    Configura extensiones, directorios seguros y blueprints de presentación.
    """
    app = Flask(
        __name__, 
        static_folder=config.STATIC_DIR, 
        template_folder=os.path.join(SERVER_DIR, "templates")
    )
    
    # Configuración desde AppConfig
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = config.SECRET_KEY
    
    # Asegurar directorios de almacenamiento
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(config.PROCESSED_DIR, exist_ok=True)
    os.makedirs(config.TELEMETRY_DIR, exist_ok=True)
    
    # Inicializar ORM
    db.init_app(app)
    
    with app.app_context():
        from sqlalchemy import event
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    
    # Registrar Blueprints de presentación (Web y APIs REST)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    
    # Ruta directa para el favicon del navegador
    from flask import send_from_directory
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.static_folder, 'img'),
            'sifma_sin_texto.svg',
            mimetype='image/svg+xml'
        )
    
    return app

app = create_app()

if __name__ == '__main__':
    # Inicializar tablas y datos por defecto
    init_db_data(app)

    logger.info("==============================================")
    logger.info("Servidor Local SIFMA - Arquitectura Refactorizada")
    logger.info("Dashboard Web en: http://127.0.0.1:5000")
    logger.info("==============================================")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
