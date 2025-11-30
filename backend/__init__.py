
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
import os


db = SQLAlchemy()
migrate = Migrate()
sess = Session()
mail = Mail()
def create_app():
    app = Flask(__name__)

    # Basic configuration (override with environment variables in production)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///parking.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me')

    # Celery config defaults (optional)
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Session configuration (filesystem for dev; use redis in production)
    app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE', 'filesystem')
    app.config['SESSION_PERMANENT'] = False
    sess.init_app(app)

     # --- Flask-Mail Config ---
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')
    mail.init_app(app)


    # Initialize DB and migrations
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS - allow local frontend during development with credentials
    CORS(app,
         supports_credentials=True,
         origins=["http://localhost:5173"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

    # Register blueprints after extensions are initialized
    from routes import api
    app.register_blueprint(api)

    # use app context for DB operations (create tables / seed admin)
    with app.app_context():
        from models import User
        db.create_all()
        # Create initial admin if not present
        if not User.query.filter_by(role='admin').first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
            )
            db.session.add(admin)
            db.session.commit()

    return app