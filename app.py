#!/usr/bin/env python3
"""
DB Report Chat Application - Clean Modular Version

This is the main entry point for the Flask application.
The application has been refactored into a modular structure:

- app/__init__.py: Application factory
- app/routes/: Route blueprints
- app/services/: Service layer wrappers
- utils/: Existing utility modules
"""

import logging
from app import create_app
from app.services.session_service import get_session_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        # Create the Flask application
        app = create_app()
        
        # Clean up old images on startup
        session_manager = get_session_manager()
        session_manager.cleanup_old_images()
        
        logger.info("Starting DB Report Chat Application...")
        logger.info("Application initialized successfully")
        
        # Run the application
        app.run(debug=True, port=5000)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == '__main__':
    main() 