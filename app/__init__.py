"""
Flask app initialization for the Project Tracker.
"""
from flask import Flask
import os
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

def create_app(config_path='config.yaml'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration from YAML
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    # Configure secret key (for session cookies)
    app.secret_key = os.urandom(24)
    
    # Configure app from config.yaml
    app.config['CONFIG'] = config
    
    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    logger.info("Flask app initialized!")
    return app 