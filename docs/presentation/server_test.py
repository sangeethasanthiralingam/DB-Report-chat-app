#!/usr/bin/env python3
"""
Server Test Script for DB Report Chat App Documentation
Tests file accessibility and path resolution
"""

import requests
import sys
import os
from pathlib import Path

def test_server_paths():
    """Test various server paths to verify they work correctly"""
    
    base_url = "http://localhost:8000"
    
    # Test paths
    test_paths = [
        # Direct markdown files (should work)
        "/docs/ARCHITECTURE.md",
        "/docs/API.md", 
        "/docs/CONFIGURATION.md",
        "/docs/TESTING.md",
        "/docs/DEVELOPER_HINTS.md",
        "/docs/PROMPT_MATRIX.md",
        "/docs/CHART_BEHAVIOR.md",
        "/docs/REQUEST_RESPONSE_FLOW.md",
        "/README.md",
        
        # Presentation files (should work)
        "/docs/presentation/",
        "/docs/presentation/index.html",
        "/docs/presentation/script.js",
        "/docs/presentation/styles.css",
        
        # Relative paths from presentation (should work)
        "/docs/presentation/../ARCHITECTURE.md",
        "/docs/presentation/../API.md",
    ]
    
    print("🧪 Testing Server Paths")
    print("=" * 50)
    
    results = []
    
    for path in test_paths:
        url = f"{base_url}{path}"
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            if response.ok:
                print(f"✅ {path} - {status} OK ({len(response.text)} chars)")
                results.append((path, True, status, len(response.text)))
            else:
                print(f"❌ {path} - {status} {response.reason}")
                results.append((path, False, status, 0))
        except requests.exceptions.RequestException as e:
            print(f"❌ {path} - Error: {e}")
            results.append((path, False, "Error", 0))
    
    print("\n📊 Summary")
    print("=" * 50)
    
    successful = sum(1 for _, success, _, _ in results if success)
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {(successful/total)*100:.1f}%")
    
    if successful < total:
        print("\n❌ Some tests failed. Check server configuration.")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

def test_file_existence():
    """Test if files actually exist on disk"""
    
    print("\n📁 Testing File Existence")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Test files
    test_files = [
        project_root / "docs" / "ARCHITECTURE.md",
        project_root / "docs" / "API.md",
        project_root / "docs" / "CONFIGURATION.md",
        project_root / "docs" / "TESTING.md",
        project_root / "docs" / "DEVELOPER_HINTS.md",
        project_root / "docs" / "PROMPT_MATRIX.md",
        project_root / "docs" / "CHART_BEHAVIOR.md",
        project_root / "docs" / "REQUEST_RESPONSE_FLOW.md",
        project_root / "README.md",
        project_root / "docs" / "presentation" / "index.html",
        project_root / "docs" / "presentation" / "script.js",
        project_root / "docs" / "presentation" / "styles.css",
    ]
    
    all_exist = True
    
    for file_path in test_files:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file_path.name} - {size} bytes")
        else:
            print(f"❌ {file_path.name} - NOT FOUND")
            all_exist = False
    
    return all_exist

def test_server_running():
    """Test if server is running"""
    
    print("\n🚀 Testing Server Status")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not running - Error: {e}")
        print("\n💡 To start the server:")
        print("   python docs/presentation/server.py")
        return False

def main():
    """Main test function"""
    
    print("🔧 DB Report Chat App - Server Test")
    print("=" * 50)
    
    # Test 1: Check if server is running
    if not test_server_running():
        return False
    
    # Test 2: Check if files exist
    if not test_file_existence():
        print("\n❌ Some files are missing. Check your installation.")
        return False
    
    # Test 3: Test server paths
    if not test_server_paths():
        print("\n❌ Server path resolution issues detected.")
        return False
    
    print("\n🎉 All tests passed! Server is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 