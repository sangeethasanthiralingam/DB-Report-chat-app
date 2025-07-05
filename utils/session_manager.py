#!/usr/bin/env python3
"""
Session Manager Module
Handles session initialization, conversation history, and image management
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import session
from utils.data_processor import get_data_processor

# Initialize data processor for JSON cleaning
data_processor = get_data_processor()

class SessionManager:
    """Manages session state and conversation history"""
    
    def __init__(self):
        self.generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'generated')
        os.makedirs(self.generated_dir, exist_ok=True)
    
    def init_session(self) -> None:
        """Initialize session with conversation history and other required fields"""
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        if 'generated_images' not in session:
            session['generated_images'] = []
        if 'id' not in session:
            session['id'] = hashlib.md5(f"{datetime.now().isoformat()}{os.getpid()}".encode()).hexdigest()[:8]
    
    def add_to_conversation_history(self, question: str, response_obj: Any, sql_query: str = "") -> None:
        """Add a conversation turn to the history"""
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        # Clean response_obj to handle NaT values using data processor
        cleaned_response = data_processor.clean_for_json(response_obj)
        
        session['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response_obj': cleaned_response,
            'sql_query': sql_query,
            'database': os.getenv('DB_NAME', 'db')
        })
        
        # Keep only last 10 conversations to prevent session bloat
        if len(session['conversation_history']) > 10:
            session['conversation_history'] = session['conversation_history'][-10:]
        
        session.modified = True
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history"""
        return session.get('conversation_history', [])
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history"""
        session['conversation_history'] = []
        session.modified = True
        self.delete_session_images()
    
    def get_conversation_count(self) -> int:
        """Get the number of conversations in history"""
        return len(session.get('conversation_history', []))
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return session.get('id', 'unknown')
    
    def get_generated_images(self) -> List[str]:
        """Get list of generated images for current session"""
        return session.get('generated_images', [])
    
    def save_image_to_file(self, img_base64: str, chart_type: str, session_id: Optional[str] = None) -> Optional[str]:
        """Save base64 image to file and return the filename"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_suffix = f"_{session_id}" if session_id else ""
            filename = f"{chart_type}_{timestamp}{session_suffix}.png"
            filepath = os.path.join(self.generated_dir, filename)
            
            # Decode and save image
            import base64
            img_data = base64.b64decode(img_base64)
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            logging.info(f"Image saved to file: {filepath}")
            return filename
        except Exception as e:
            logging.error(f"Error saving image to file: {e}")
            return None
    
    def add_generated_image(self, filename: str) -> None:
        """Add a generated image filename to session"""
        if 'generated_images' not in session:
            session['generated_images'] = []
        session['generated_images'].append(filename)
        session.modified = True
    
    def delete_session_images(self) -> None:
        """Delete all images associated with the current session"""
        if 'generated_images' not in session:
            return
        
        deleted_count = 0
        for filename in session['generated_images']:
            filepath = os.path.join(self.generated_dir, filename)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted_count += 1
                    logging.info(f"Deleted image file: {filepath}")
            except Exception as e:
                logging.error(f"Error deleting image file {filepath}: {e}")
        
        if deleted_count > 0:
            logging.info(f"Deleted {deleted_count} image files for session")
        
        # Clear the list
        session['generated_images'] = []
        session.modified = True
    
    def cleanup_old_images(self, max_age_hours: int = 24) -> None:
        """Clean up old image files that are older than specified hours"""
        if not os.path.exists(self.generated_dir):
            return
        
        current_time = datetime.now()
        deleted_count = 0
        
        try:
            for filename in os.listdir(self.generated_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(self.generated_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    
                    # Delete files older than specified hours
                    if (current_time - file_time).total_seconds() > max_age_hours * 3600:
                        try:
                            os.remove(filepath)
                            deleted_count += 1
                            logging.info(f"Cleaned up old image file: {filepath}")
                        except Exception as e:
                            logging.error(f"Error deleting old image file {filepath}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned up {deleted_count} old image files")
        except Exception as e:
            logging.error(f"Error during image cleanup: {e}")
    
    def get_conversation_context(self, limit: int = 1, truncate: int = 100) -> str:
        """Get conversation context for LLM prompts"""
        if 'conversation_history' not in session or not session['conversation_history']:
            return ""
        
        recent_conversations = session['conversation_history'][-limit:]
        context = "Recent conversation history:\n"
        for conv in recent_conversations:
            q = conv['question'][:truncate] + ("..." if len(conv['question']) > truncate else "")
            resp = str(conv['response_obj'])[:truncate] + ("..." if len(str(conv['response_obj'])) > truncate else "")
            context += f"User: {q}\nAssistant: {resp}\n---\n"
        return context
    
    def get_optimized_conversation_context(self, question: str) -> str:
        """Get minimal but relevant conversation context"""
        if 'conversation_history' not in session:
            return ""
        
        history = session['conversation_history']
        if not history:
            return ""
        
        # Only include context if question seems related to previous ones
        question_lower = question.lower()
        context_keywords = ['previous', 'before', 'last', 'earlier', 'that', 'those', 'same']
        
        if not any(keyword in question_lower for keyword in context_keywords):
            return ""
        
        # Include only last 2 conversations and only essential info
        recent = history[-2:]
        context = "Recent context:\n"
        for conv in recent:
            context += f"Q: {conv['question'][:50]}{'...' if len(conv['question']) > 50 else ''}\n"
            # Include only successful query results summary
            if conv.get('sql_query') and not conv['response_obj'].startswith('Error'):
                resp = str(conv['response_obj'])
                resp_preview = resp[:30] + '...' if len(resp) > 30 else resp
                context += f"Found: {resp_preview}\n"
        
        return context
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get comprehensive session information"""
        return {
            "session_id": self.get_session_id(),
            "generated_images": self.get_generated_images(),
            "conversation_count": self.get_conversation_count(),
            "current_database": os.getenv('DB_NAME', 'db')
        }

# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager 