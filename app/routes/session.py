from flask import Blueprint, jsonify
import logging

session_bp = Blueprint('session', __name__)

@session_bp.route('/conversation_history', methods=['GET'])
def get_conversation_history():
    """Get the current conversation history"""
    from app.services.session_service import get_session_manager
    from app.services.database_service import get_database_service
    
    session_manager = get_session_manager()
    database_service = get_database_service()
    
    session_manager.init_session()
    return jsonify({
        "conversation_history": session_manager.get_conversation_history(),
        "current_database": database_service.get_database_name()
    })

@session_bp.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history"""
    from app.services.session_service import get_session_manager
    
    session_manager = get_session_manager()
    session_manager.init_session()
    session_manager.clear_conversation_history()
    return jsonify({"message": "Conversation history cleared"})

@session_bp.route('/cleanup_images', methods=['POST'])
def cleanup_images():
    """Manually trigger cleanup of old images"""
    try:
        from app.services.session_service import get_session_manager
        
        session_manager = get_session_manager()
        session_manager.cleanup_old_images()
        return jsonify({"message": "Image cleanup completed"})
    except Exception as e:
        logging.error(f"Error during image cleanup: {e}")
        return jsonify({"error": str(e)}), 500

@session_bp.route('/session_info', methods=['GET'])
def session_info():
    """Get information about the current session"""
    from app.services.session_service import get_session_manager
    
    session_manager = get_session_manager()
    session_manager.init_session()
    return jsonify(session_manager.get_session_info()) 