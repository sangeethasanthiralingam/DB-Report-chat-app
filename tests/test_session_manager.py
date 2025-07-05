#!/usr/bin/env python3
"""
Test script for the session manager module.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.session_manager import get_session_manager

def test_session_manager():
    """Test the session manager functionality."""
    print("Testing Session Manager...")
    
    # Initialize session manager
    manager = get_session_manager()
    print(f"[OK] Session manager initialized")
    
    # Test session initialization
    print("\nTesting session initialization:")
    try:
        # Mock session object
        class MockSession:
            def __init__(self):
                self.data = {}
                self.modified = False
            
            def get(self, key, default=None):
                return self.data.get(key, default)
            
            def __setitem__(self, key, value):
                self.data[key] = value
                self.modified = True
            
            def __getitem__(self, key):
                return self.data[key]
        
        mock_session = MockSession()
        
        # Test session initialization
        manager.init_session()
        print("[OK] Session initialization completed")
        
    except Exception as e:
        print(f"[FAIL] Session initialization error: {e}")
    
    # Test conversation history management
    print("\nTesting conversation history management:")
    try:
        # Test adding to conversation history
        test_question = "Show me all employees"
        test_content = "Here are all employees: [data]"
        test_sql = "SELECT * FROM employees"
        
        manager.add_to_conversation_history(test_question, test_content, test_sql)
        print("[OK] Added to conversation history")
        
        # Test getting conversation history
        history = manager.get_conversation_history()
        if history:
            print("[OK] Retrieved conversation history")
            print(f"  History length: {len(history)}")
        else:
            print("[FAIL] Failed to retrieve conversation history")
        
        # Test clearing conversation history
        manager.clear_conversation_history()
        print("[OK] Cleared conversation history")
        
    except Exception as e:
        print(f"[FAIL] Conversation history management error: {e}")
    
    # Test session info
    print("\nTesting session info:")
    try:
        info = manager.get_session_info()
        if info:
            print("[OK] Retrieved session info")
            print(f"  Session info: {info}")
        else:
            print("[FAIL] Failed to retrieve session info")
    except Exception as e:
        print(f"[FAIL] Session info error: {e}")
    
    # Test file operations (with temporary directory)
    print("\nTesting file operations:")
    try:
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        original_generated_dir = manager.generated_dir
        manager.generated_dir = temp_dir
        
        # Test saving image to file
        test_image_data = "fake_image_data"
        test_filename = manager.save_image_to_file(test_image_data, "test_chart", "test_session")
        
        if test_filename:
            print("[OK] Image saved to file successfully")
            print(f"  Filename: {test_filename}")
            
            # Check if file exists
            file_path = os.path.join(temp_dir, test_filename)
            if os.path.exists(file_path):
                print("[OK] File exists on disk")
            else:
                print("[FAIL] File does not exist on disk")
        else:
            print("[FAIL] Failed to save image to file")
        
        # Test cleanup of old images
        try:
            manager.cleanup_old_images()
            print("[OK] Cleanup of old images completed")
        except Exception as e:
            print(f"[FAIL] Cleanup error: {e}")
        
        # Restore original directory
        manager.generated_dir = original_generated_dir
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        print("[OK] Temporary directory cleaned up")
        
    except Exception as e:
        print(f"[FAIL] File operations error: {e}")
    
    # Test conversation context
    print("\nTesting conversation context:")
    try:
        # Add some test conversation
        manager.add_to_conversation_history("First question", "First answer", "SELECT 1")
        manager.add_to_conversation_history("Second question", "Second answer", "SELECT 2")
        
        context = manager.get_conversation_context()
        if context:
            print("[OK] Retrieved conversation context")
            print(f"  Context length: {len(context)}")
        else:
            print("[FAIL] Failed to retrieve conversation context")
        
        # Clear again for clean state
        manager.clear_conversation_history()
        
    except Exception as e:
        print(f"[FAIL] Conversation context error: {e}")
    
    # Test session ID generation
    print("\nTesting session ID generation:")
    try:
        # Mock session with ID
        mock_session = MockSession()
        mock_session['id'] = 'test_session_123'
        
        # Test session ID handling
        session_id = manager.get_session_id()
        if session_id:
            print("[OK] Session ID generated/retrieved")
            print(f"  Session ID: {session_id}")
        else:
            print("[FAIL] Failed to generate/retrieve session ID")
        
    except Exception as e:
        print(f"[FAIL] Session ID error: {e}")
    
    print("\n[OK] All session manager tests completed!")

if __name__ == "__main__":
    test_session_manager() 