import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app(config_name='default'):
    """Create and configure Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Enable CORS
    CORS(app)
    
    # Load configuration
    if config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    else:
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['UNPROCESSED_FOLDER'], exist_ok=True)
    except OSError:
        pass
        
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.controllers.receipt_controller import receipt_bp
    app.register_blueprint(receipt_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for the API"""
        return {'status': 'healthy'}, 200
        
    return app