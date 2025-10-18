from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config
import os

# Initialize extensions
db = SQLAlchemy()


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__, static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

