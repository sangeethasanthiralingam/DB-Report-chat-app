#!/usr/bin/env python3
"""
Comprehensive test runner for all utility modules.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test(test_file):
    """Run a single test file and return the result."""
    print(f"\n{'='*60}")
    print(f"Running {test_file}...")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print("✓ Test completed successfully")
            print(f"Duration: {duration:.2f} seconds")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True, duration
        else:
            print("✗ Test failed")
            print(f"Duration: {duration:.2f} seconds")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            if result.stderr:
                print("Error:")
                print(result.stderr)
            return False, duration
            
    except subprocess.TimeoutExpired:
        print("✗ Test timed out after 60 seconds")
        return False, 60.0
    except Exception as e:
        print(f"✗ Test execution error: {e}")
        return False, 0.0

def main():
    """Run all tests and provide a summary."""
    print("🧪 DB Report Chat App - Comprehensive Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    
    # Define all test files
    test_files = [
        "test_domain_analyzer.py",
        "test_nat_handling.py", 
        "test_domain_detection.py",
        "test_customer_supplier_detection.py",
        "test_chat_processor.py",
        "test_response_formatter.py",
        "test_session_manager.py",
        "test_database_manager.py"
    ]
    
    # Track results
    results = []
    total_passed = 0
    total_failed = 0
    total_duration = 0.0
    
    # Run each test
    for test_file in test_files:
        if os.path.exists(test_file):
            passed, duration = run_test(test_file)
            results.append({
                'file': test_file,
                'passed': passed,
                'duration': duration
            })
            
            if passed:
                total_passed += 1
            else:
                total_failed += 1
            
            total_duration += duration
        else:
            print(f"\n⚠ Test file {test_file} not found")
            results.append({
                'file': test_file,
                'passed': False,
                'duration': 0.0,
                'error': 'File not found'
            })
            total_failed += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {len(test_files)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success rate: {(total_passed/len(test_files)*100):.1f}%")
    print(f"Total duration: {total_duration:.2f} seconds")
    print(f"Average duration: {(total_duration/len(test_files)):.2f} seconds")
    
    print(f"\n{'='*60}")
    print("📋 DETAILED RESULTS")
    print(f"{'='*60}")
    
    for result in results:
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        duration = f"{result['duration']:.2f}s"
        error = result.get('error', '')
        
        print(f"{status} | {result['file']:<30} | {duration:>8} | {error}")
    
    print(f"\n{'='*60}")
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("Your DB Report Chat App is working correctly.")
    else:
        print(f"❌ {total_failed} TEST(S) FAILED")
        print("Please review the failed tests and fix any issues.")
    print(f"{'='*60}")
    
    # Return appropriate exit code
    return 0 if total_failed == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 