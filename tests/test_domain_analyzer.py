#!/usr/bin/env python3
"""
Test script for the domain analyzer module.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.domain_analyzer import get_domain_analyzer

def test_domain_analyzer():
    """Test the domain analyzer functionality."""
    print("Testing Domain Analyzer...")
    
    # Initialize domain analyzer
    analyzer = get_domain_analyzer()
    print(f"[OK] Domain analyzer initialized with {len(analyzer.business_terms)} business terms")
    
    # Test domain detection from questions
    test_questions = [
        ("Show me all employees", "hr"),
        ("What products are in stock?", "inventory"),
        ("List all financial transactions", "financial"),
        ("Generate a sales report", "reporting"),
        ("What's the weather like?", "general")
    ]
    
    print("\nTesting domain detection from questions:")
    for question, expected_domain in test_questions:
        detected_domain = analyzer.detect_domain_from_question(question)
        status = "[OK]" if detected_domain == expected_domain else "[FAIL]"
        print(f"{status} '{question}' -> {detected_domain} (expected: {expected_domain})")
    
    # Test table finding
    print("\nTesting table finding:")
    test_questions_for_tables = [
        "Show me employee data",
        "List all products",
        "What are the sales figures?",
        "Show financial transactions"
    ]
    
    for question in test_questions_for_tables:
        tables = analyzer.find_relevant_tables(question)
        print(f"[OK] '{question}' -> Found tables: {tables}")
    
    # Test domain context
    print("\nTesting domain context:")
    domains = ['hr', 'inventory', 'financial', 'reporting', 'general']
    for domain in domains:
        context = analyzer.get_domain_context(domain)
        print(f"[OK] {domain} domain: {context['description'][:50]}...")
    
    print("\n[OK] All tests completed!")

if __name__ == "__main__":
    test_domain_analyzer() 