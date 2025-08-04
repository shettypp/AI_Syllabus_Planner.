from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                instance_relative_config=True,
                static_folder='static', 
                template_folder='templates')

    app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            logging.info("Google Gemini API configured successfully.")
        except Exception as e:
            logging.error(f"Failed to configure Gemini API: {e}")

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    with app.app_context():
        db.create_all()

    return app