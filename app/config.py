"""
Configuration module for the DB Report Chat Application
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    SESSION_TYPE = 'filesystem'
    
    # Application settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    
    # Database configuration (from utils.database_manager)
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'your_database'),
        'charset': 'utf8mb4'
    }
    
    # Redis configuration (if using Redis cache)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    # File paths
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SESSION_FOLDER = 'flask_session'
    GENERATED_IMAGES_FOLDER = 'static/generated'
    
    # Image cleanup settings
    IMAGE_CLEANUP_HOURS = int(os.getenv('IMAGE_CLEANUP_HOURS', 24))
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration"""
        app.config.from_object(cls)
        
        # Ensure directories exist
        os.makedirs(cls.SESSION_FOLDER, exist_ok=True)
        os.makedirs(cls.GENERATED_IMAGES_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Override with production settings
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use test database
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_database',
        'charset': 'utf8mb4'
    }

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 