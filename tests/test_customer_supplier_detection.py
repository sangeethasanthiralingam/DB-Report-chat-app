#!/usr/bin/env python3
"""
Test script to verify customer and supplier domain detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.domain_analyzer import get_domain_analyzer

def test_customer_supplier_detection():
    """Test domain detection for customer and supplier related questions"""
    
    analyzer = get_domain_analyzer()
    
    # Test cases
    test_cases = [
        # Customer questions - should be inventory domain when there's inventory context
        ("Show me all customers", "general"),  # No inventory context
        ("List customers who bought products", "inventory"),  # Has inventory context
        ("Customers with recent sales", "inventory"),  # Has inventory context
        ("Customer information", "general"),  # No inventory context
        ("Customers in our inventory system", "inventory"),  # Explicit inventory context
        
        # Supplier questions - should be inventory domain when there's inventory context
        ("Show me all suppliers", "general"),  # No inventory context
        ("Suppliers who provided products", "inventory"),  # Has inventory context
        ("Suppliers with recent purchases", "inventory"),  # Has inventory context
        ("Supplier information", "general"),  # No inventory context
        ("Suppliers in our inventory system", "inventory"),  # Explicit inventory context
        
        # Mixed questions
        ("Customers and suppliers", "general"),  # No inventory context
        ("Customers and suppliers for our products", "inventory"),  # Has inventory context
        ("Customer and supplier orders", "inventory"),  # Has inventory context
        
        # Other entity questions - should remain general
        ("Show me all users", "general"),
        ("List all persons", "general"),
        ("Party information", "general"),
    ]
    
    print("Testing customer and supplier domain detection:")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for question, expected_domain in test_cases:
        detected_domain = analyzer.detect_domain_from_question(question)
        status = "[OK] PASS" if detected_domain == expected_domain else "[FAIL] FAIL"
        
        print(f"{status} | Expected: {expected_domain:10} | Got: {detected_domain:10} | Question: {question}")
        
        if detected_domain == expected_domain:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("[SUCCESS] All tests passed! Customer and supplier detection is working correctly.")
    else:
        print("[ERROR] Some tests failed. Please review the domain detection logic.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_customer_supplier_detection()
    sys.exit(0 if success else 1) 