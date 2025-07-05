#!/usr/bin/env python3
"""
Test script for the chat processor module.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.chat_processor import get_chat_processor

def test_chat_processor():
    """Test the chat processor functionality."""
    print("Testing Chat Processor...")
    
    # Initialize chat processor
    processor = get_chat_processor()
    print(f"[OK] Chat processor initialized")
    
    # Test sensitive content checking
    print("\nTesting sensitive content detection:")
    sensitive_tests = [
        ("Show me all employees", False),
        ("What's the password for admin?", True),
        ("List all products", False),
        ("Give me the secret key", True),
        ("Show customer data", False),
        ("What are the credentials?", True),
        ("Display sales figures", False),
        ("Show me the token", True)
    ]
    
    for question, expected in sensitive_tests:
        result = processor.check_sensitive_content(question)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{question}' -> {result} (expected: {expected})")
    
    # Test response type determination from keywords
    print("\nTesting response type determination:")
    response_tests = [
        ("Show me a pie chart of sales", "pie"),
        ("Create a bar chart of revenue", "bar"),
        ("Generate a line chart of trends", "line"),
        ("Display a scatter plot", "scatter"),
        ("Show me the metrics", "card"),
        ("List all employees", "table"),
        ("What's the weather?", "table")
    ]
    
    for question, expected_type in response_tests:
        result = processor.determine_response_type_from_keywords(question)
        status = "[OK]" if result == expected_type else "[FAIL]"
        print(f"{status} '{question}' -> {result} (expected: {expected_type})")
    
    # Test documentation query detection
    print("\nTesting documentation query detection:")
    doc_tests = [
        ("Show me all tables", True),
        ("List the columns in users", True),
        ("Describe the database schema", True),
        ("What's the structure?", True),
        ("Show me all employees", False),
        ("What products are in stock?", False),
        ("Generate a report", False)
    ]
    
    for question, expected in doc_tests:
        result = processor.is_documentation_query(question)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{question}' -> {result} (expected: {expected})")
    
    # Test diagram request detection
    print("\nTesting diagram request detection:")
    diagram_tests = [
        ("Show me the relationship diagram", (True, "relationship", None)),
        ("Draw a diagram of the database", (True, "relationship", None)),
        ("Show me the table diagram for users", (True, "table_schema", "users")),
        ("Draw the schema for products", (True, "table_schema", "products")),
        ("Show me all employees", (False, "", None)),
        ("What products are in stock?", (False, "", None))
    ]
    
    for question, expected in diagram_tests:
        result = processor.is_diagram_request(question)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"{status} '{question}' -> {result} (expected: {expected})")
    
    # Test response payload creation
    print("\nTesting response payload creation:")
    payload = processor.create_response_payload(
        response_type="chart",
        content="chart.png",
        sql="SELECT * FROM sales",
        chart_type="bar",
        data_preview=[{"month": "Jan", "sales": 1000}],
        title="Sales Chart"
    )
    
    expected_keys = ["type", "content", "sql", "conversation_count", "chart_type", "data_preview", "title"]
    missing_keys = [key for key in expected_keys if key not in payload]
    
    if not missing_keys:
        print("[OK] Response payload created successfully with all expected keys")
        print(f"  Payload: {payload}")
    else:
        print(f"[FAIL] Missing keys in payload: {missing_keys}")
    
    print("\n[OK] All chat processor tests completed!")

if __name__ == "__main__":
    test_chat_processor() 