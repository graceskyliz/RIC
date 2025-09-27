import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv  # <--- agregar esta importación

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables desde .env antes de leer os.environ
load_dotenv()  # <--- agregar esta línea

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database with error handling
database_url = os.environ.get("DATABASE_URL")
if database_url:
    logger.info(f"Using PostgreSQL database: {database_url[:50]}...")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "max_overflow": 0,
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "ric_app"
        }
    }
else:
    logger.warning("No DATABASE_URL found, falling back to SQLite")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ric.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

# Configure upload settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialize extensions
db.init_app(app)

# Ensure upload directory exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    logger.info(f"Upload directory created: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    logger.error(f"Failed to create upload directory: {str(e)}")

# Add health check function
@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    status = {
        'status': 'healthy',
        'database': 'connected' if db_initialized else 'disconnected',
        'upload_dir': os.path.exists(app.config['UPLOAD_FOLDER'])
    }
    return status, 200 if 'db_initialized' in globals() and db_initialized else 503

def initialize_database():
    """Initialize database with proper error handling"""
    try:
        with app.app_context():
            # Test database connection
            with db.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.info("Database connection successful")
            
            # Import models and routes
            import models  # noqa: F401
            import routes  # noqa: F401
            
            # Create all database tables
            db.create_all()
            logger.info("Database tables created successfully")
            return True
            
    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        logger.error("Application will continue with limited functionality")
        return False
    except Exception as e:
        logger.error(f"Unexpected database error: {str(e)}")
        return False

# Initialize database
db_initialized = initialize_database()

# Import routes even if database fails (for health checks, etc.)
if not db_initialized:
    try:
        import routes  # noqa: F401
        logger.info("Routes imported despite database connection failure")
    except Exception as e:
        logger.error(f"Failed to import routes: {str(e)}")
