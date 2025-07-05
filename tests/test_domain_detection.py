#!/usr/bin/env python3
"""
Test script for domain detection functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.domain_analyzer import get_domain_analyzer

def test_domain_detection():
    """Test the domain detection functionality."""
    print("Testing Domain Detection...")
    
    # Initialize domain analyzer
    analyzer = get_domain_analyzer()
    
    # Test cases for domain detection
    test_cases = [
        # HR domain tests
        ("Show me all employees", "hr"),
        ("List attendance records", "hr"),
        ("What are the leave requests?", "hr"),
        ("Show department information", "hr"),
        
        # Inventory domain tests
        ("Show me all products", "inventory"),
        ("What's the stock level?", "inventory"),
        ("List sales data", "inventory"),
        ("Show product categories", "inventory"),
        
        # Financial domain tests
        ("Show account balances", "financial"),
        ("List all transactions", "financial"),
        ("What are the payments?", "financial"),
        ("Show credit information", "financial"),
        
        # Reporting domain tests
        ("Generate a report", "reporting"),
        ("Show dashboard data", "reporting"),
        ("Create a chart", "reporting"),
        ("Analytics summary", "reporting"),
        
        # General domain tests (core entities)
        ("Show me all customers", "general"),
        ("List all users", "general"),
        ("Show person details", "general"),
        ("What parties are there?", "general"),
        
        # Edge cases
        ("What's the weather like?", "general"),
        ("Hello", "general"),
        ("Show me everything", "general"),
    ]
    
    print("\nTesting domain detection from questions:")
    correct = 0
    total = len(test_cases)
    
    for question, expected_domain in test_cases:
        detected_domain = analyzer.detect_domain_from_question(question)
        status = "[OK]" if detected_domain == expected_domain else "[FAIL]"
        if detected_domain == expected_domain:
            correct += 1
        print(f"{status} '{question}' -> {detected_domain} (expected: {expected_domain})")
    
    print(f"\nDomain detection accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    
    # Test specific problematic case
    print("\nTesting specific case that was failing:")
    question = "Show me all customers"
    detected = analyzer.detect_domain_from_question(question)
    print(f"Question: '{question}'")
    print(f"Detected domain: {detected}")
    print(f"Expected: general")
    print(f"Status: {'[OK] PASS' if detected == 'general' else '[FAIL] FAIL'}")
    
    # Test domain context
    print("\nTesting domain context generation:")
    domains = ['hr', 'inventory', 'financial', 'reporting', 'general']
    for domain in domains:
        context = analyzer.get_domain_prompt_context(domain)
        print(f"[OK] {domain} domain: {context['context'][:50]}...")
    
    print("\n[OK] Domain detection test completed!")

if __name__ == "__main__":
    test_domain_detection() 