import os
import sys
import importlib
import traceback
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()
sess = Session()
mail = Mail()

sys.modules.setdefault('backend', sys.modules.get(__name__))
sys.modules.setdefault('__init__', sys.modules.get(__name__))


def _load_routes_module():
    pkg_module_name = "backend.routes"
    try:
        return importlib.import_module(pkg_module_name)
    except Exception:
        try:
            routes_path = os.path.join(os.path.dirname(__file__), "routes.py")
            if not os.path.exists(routes_path):
                raise FileNotFoundError(f"routes.py not found at {routes_path}")
            spec = importlib.util.spec_from_file_location(pkg_module_name, routes_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[pkg_module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            traceback.print_exc()
            raise


def create_app():
    app = Flask(__name__)

    # --- Config ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///parking.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me')
    app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE', 'filesystem')
    app.config['SESSION_PERMANENT'] = False

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True if os.environ.get('MAIL_USE_TLS', '1') in ('1', 'true', 'True') else False
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'] or 'no-reply@example.com')
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        app.logger.warning("MAIL_USERNAME or MAIL_PASSWORD not set — disabling outbound email (MAIL_SUPPRESS_SEND=True).")
        app.config['MAIL_SUPPRESS_SEND'] = True

    
    db.init_app(app)
    migrate.init_app(app, db)
    sess.init_app(app)
    mail.init_app(app)

    CORS(app,
         supports_credentials=True,
         origins=["http://localhost:5173"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

  
    routes_mod = _load_routes_module()
    if not hasattr(routes_mod, "api"):
        raise RuntimeError("routes module does not expose `api` blueprint")
    app.register_blueprint(routes_mod.api)

    with app.app_context():
        try:
            models_mod = importlib.import_module("backend.models")
        except Exception:
            models_mod = importlib.import_module("models")
        User = getattr(models_mod, "User")

      
        db.create_all()

        
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(users);"))
            columns = [row[1] for row in result]
            if 'preferred_reminder_hour' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN preferred_reminder_hour INTEGER DEFAULT 18;"))
                conn.commit()

       
        if not User.query.filter_by(role='admin').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                preferred_reminder_hour=18
            )
            db.session.add(admin)
            db.session.commit()

    return app