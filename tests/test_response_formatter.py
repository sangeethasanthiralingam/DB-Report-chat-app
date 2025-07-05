#!/usr/bin/env python3
"""
Test script for the response formatter module.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.response_formatter import get_response_formatter
from utils.database_manager import format_compact_schema
from utils.data_processor import get_data_processor

def test_response_formatter():
    """Test the response formatter functionality."""
    print("Testing Response Formatter...")
    
    # Initialize response formatter
    formatter = get_response_formatter()
    print(f"[OK] Response formatter initialized")
    
    # Create test data
    test_data = {
        'category': ['Electronics', 'Clothing', 'Books', 'Electronics', 'Clothing'],
        'sales': [1000, 500, 300, 1200, 600],
        'month': ['Jan', 'Jan', 'Jan', 'Feb', 'Feb'],
        'profit': [200, 100, 60, 240, 120]
    }
    df = pd.DataFrame(test_data)
    
    # Test response type determination
    print("\nTesting response type determination:")
    type_tests = [
        (df, "Show me a pie chart", "pie"),
        (df, "Create a bar chart", "bar"),
        (df, "Generate a line chart", "line"),
        (df, "Display a scatter plot", "scatter"),
        (df, "Show me the metrics", "card"),
        (df, "List all data", "table"),
        (df, "What's the weather?", "table")
    ]
    
    for data, question, expected_type in type_tests:
        result = formatter.determine_response_type(question, data.head(2).to_dict())
        status = "[OK]" if result == expected_type else "[FAIL]"
        print(f"{status} '{question}' -> {result} (expected: {expected_type})")
    
    # Test card response formatting
    print("\nTesting card response formatting:")
    try:
        card_response = formatter.format_card_response(df)
        if card_response:
            print("[OK] Card response formatted successfully")
            print(f"  Response: {card_response}")
        else:
            print("[FAIL] Card response formatting failed")
    except Exception as e:
        print(f"[ERROR] Card response formatting error: {e}")
    
    # Test text response formatting
    print("\nTesting text response formatting:")
    try:
        text_response = formatter.format_text_response(df, "Show me sales data")
        if text_response:
            print("[OK] Text response formatted successfully")
            print(f"  Response: {text_response[:100]}...")
        else:
            print("[FAIL] Text response formatting failed")
    except Exception as e:
        print(f"[ERROR] Text response formatting error: {e}")
    
    # Test database documentation response
    print("\nTesting database documentation response:")
    try:
        doc_response = formatter.format_database_documentation_response(df, "Show me all tables")
        if doc_response:
            print("[OK] Documentation response formatted successfully")
            print(f"  Response: {doc_response[:100]}...")
        else:
            print("[FAIL] Documentation response formatting failed")
    except Exception as e:
        print(f"[ERROR] Documentation response formatting error: {e}")
    
    # Test visualization generation (without actual file creation)
    print("\nTesting visualization generation:")
    chart_types = ["bar", "line", "pie", "scatter"]
    
    for chart_type in chart_types:
        try:
            # Create a simple test DataFrame for visualization
            viz_data = {
                'category': ['A', 'B', 'C'],
                'value': [10, 20, 30]
            }
            viz_df = pd.DataFrame(viz_data)
            
            chart = formatter.generate_visualization(viz_df, chart_type)
            if chart:
                print(f"[OK] {chart_type} chart generated successfully")
            else:
                print(f"[FAIL] {chart_type} chart generation failed")
        except Exception as e:
            print(f"[ERROR] {chart_type} chart generation error: {e}")
    
    # Test compact schema formatting
    print("\nTesting compact schema formatting:")
    test_schema = {
        'tables': {
            'users': {
                'columns': {
                    'id': {'type': 'int', 'nullable': False},
                    'name': {'type': 'varchar(255)', 'nullable': True},
                    'email': {'type': 'varchar(255)', 'nullable': True}
                }
            },
            'orders': {
                'columns': {
                    'id': {'type': 'int', 'nullable': False},
                    'user_id': {'type': 'int', 'nullable': False},
                    'total': {'type': 'decimal(10,2)', 'nullable': True}
                }
            }
        }
    }
    
    try:
        compact_schema = format_compact_schema(test_schema)
        if compact_schema:
            print("[OK] Compact schema formatted successfully")
            schema_str = str(compact_schema)
            print(f"  Schema length: {len(schema_str)} characters")
        else:
            print("[FAIL] Compact schema formatting failed")
    except Exception as e:
        print(f"[ERROR] Compact schema formatting error: {e}")
    
    # Test JSON cleaning
    print("\nTesting JSON cleaning:")
    test_object = {
        'string': 'test',
        'number': 123,
        'list': [1, 2, 3],
        'dict': {'key': 'value'},
        'none': None,
        'datetime': datetime.now()
    }
    
    try:
        data_processor = get_data_processor()
        cleaned = data_processor.clean_for_json(test_object)
        if cleaned:
            print("[OK] JSON cleaning successful")
            print(f"  Cleaned object: {cleaned}")
        else:
            print("[FAIL] JSON cleaning failed")
    except Exception as e:
        print(f"[ERROR] JSON cleaning error: {e}")
    
    print("\n[OK] All response formatter tests completed!")

if __name__ == "__main__":
    test_response_formatter() 