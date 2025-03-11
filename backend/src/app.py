from flask import Flask, jsonify
from flask_cors import CORS
import logging
from backend.src import models
from backend.src import routes
from backend.src import tasks
from backend.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(routes.api_bp)
    
    # Initialize database on startup
    with app.app_context():
        logger.info("Initializing database...")
        models.init_db()
        logger.info("Database initialized")
        
        # Initialize scheduler only once
        if not hasattr(app, 'scheduler'):
            logger.info("Starting scheduler...")
            app.scheduler = tasks.start_scheduler()
            logger.info("Scheduler started")
        
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'name': 'PredictPool API',
            'version': '0.1.0',
            'status': 'running'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    try:
        # Run the app
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            use_reloader=False  # Disable reloader to prevent duplicate scheduler initialization
        )
    except KeyboardInterrupt:
        logger.info("Application stopped")
