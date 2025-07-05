#!/usr/bin/env python3
"""
Test script to verify the new modular structure works correctly
"""

import sys
import os

# Add the project root to Python path so we can import the app module
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        # Test app package imports
        from app import create_app
        print("✓ app package imported successfully")
        
        # Test configuration
        from app.config import Config, DevelopmentConfig, ProductionConfig
        print("✓ Configuration classes imported successfully")
        
        # Test services
        from app.services.session_service import get_session_manager
        from app.services.database_service import get_database_service
        from app.services.chat_service import get_chat_service
        from app.services.response_service import get_response_service
        from app.services.data_service import get_data_service
        print("✓ All services imported successfully")
        
        # Test routes
        from app.routes.main import main_bp
        from app.routes.chat import chat_bp
        from app.routes.session import session_bp
        from app.routes.charts import charts_bp
        print("✓ All route blueprints imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    print("\nTesting app creation...")
    
    try:
        from app import create_app
        
        # Create app with development config
        app = create_app('development')
        print("✓ Flask app created successfully")
        
        # Test that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        expected_blueprints = ['main', 'chat', 'session', 'charts']
        
        for bp_name in expected_blueprints:
            if bp_name in blueprint_names:
                print(f"✓ Blueprint '{bp_name}' registered")
            else:
                print(f"✗ Blueprint '{bp_name}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ App creation error: {e}")
        return False

def test_services():
    """Test that services can be instantiated"""
    print("\nTesting services...")
    
    try:
        # Test session service
        from app.services.session_service import get_session_manager
        session_manager = get_session_manager()
        print("✓ Session service created")
        
        # Test database service
        from app.services.database_service import get_database_service
        db_service = get_database_service()
        print("✓ Database service created")
        
        # Test chat service
        from app.services.chat_service import get_chat_service
        chat_service = get_chat_service()
        print("✓ Chat service created")
        
        # Test response service
        from app.services.response_service import get_response_service
        response_service = get_response_service()
        print("✓ Response service created")
        
        # Test data service
        from app.services.data_service import get_data_service
        data_service = get_data_service()
        print("✓ Data service created")
        
        return True
        
    except Exception as e:
        print(f"✗ Service creation error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing new modular structure...\n")
    
    tests = [
        test_imports,
        test_app_creation,
        test_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The new structure is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 