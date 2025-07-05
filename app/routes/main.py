from flask import Blueprint, render_template, g, request
import time
import logging

main_bp = Blueprint('main', __name__)

@main_bp.before_request
def before_request():
    """Log request timing"""
    g.start_time = time.time()

@main_bp.after_request
def after_request(response):
    """Log request completion time"""
    if 'start_time' in g:
        elapsed_time = time.time() - g.start_time
        logging.info(f"Request to {request.path} completed in {elapsed_time:.4f} seconds.")
    return response

@main_bp.route('/')
def home():
    """Main home page"""
    from app.services.session_service import get_session_manager
    session_manager = get_session_manager()
    session_manager.init_session()
    return render_template('index.html') 