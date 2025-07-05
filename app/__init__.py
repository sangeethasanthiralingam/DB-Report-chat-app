from flask import Flask
from flask_session import Session
import logging
import os

def create_app(config_name=None):
    """Application factory pattern for Flask app"""
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format=app.config['LOG_FORMAT']
    )
    
    # Initialize Flask-Session
    Session(app)
    
    # Register blueprints
    from app.routes.chat import chat_bp
    from app.routes.session import session_bp
    from app.routes.charts import charts_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(charts_bp)
    app.register_blueprint(main_bp)
    
    return app 