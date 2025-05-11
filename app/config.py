import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration"""
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'uploads')
    PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
    UNPROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'unprocessed')
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # OCR configuration
    OCR_ENGINE = os.environ.get('OCR_ENGINE', 'tesseract')  # 'tesseract' or 'google_vision'
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(BASE_DIR), 'instance', 'receipts.db')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'tests', 'uploads')
    PROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'processed')
    UNPROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, 'unprocessed')


class ProductionConfig(Config):
    """Production configuration"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(BASE_DIR), 'instance', 'receipts.db')
    
    # Production specific settings
    DEBUG = False
    TESTING = False