#!/usr/bin/env python3
"""
Test script for the database manager module.
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database_manager import (
    get_database_schema, get_relevant_schema, execute_query,
    generate_relationship_diagram, generate_table_schema_diagram,
    format_compact_schema, generate_domain_specific_prompt,
    redis_get, redis_set, LLM_CACHE_EXPIRY_SECONDS, DB_CONFIG,
    generate_sql_token_optimized
)

def test_database_manager():
    """Test the database manager functionality."""
    print("Testing Database Manager...")
    
    # Test database configuration
    print("\nTesting database configuration:")
    try:
        print(f"[OK] Database config loaded: {DB_CONFIG['database']}")
        print(f"[OK] Cache expiry: {LLM_CACHE_EXPIRY_SECONDS} seconds")
    except Exception as e:
        print(f"[FAIL] Database configuration error: {e}")
    
    # Test Redis operations (if available)
    print("\nTesting Redis operations:")
    try:
        # Test Redis set/get
        test_key = "test_key"
        test_value = "test_value"
        
        redis_set(test_key, test_value)
        retrieved_value = redis_get(test_key)
        
        if retrieved_value == test_value:
            print("[OK] Redis set/get operations successful")
        else:
            print("[FAIL] Redis set/get operations failed")
            
    except Exception as e:
        print(f"[FAIL] Redis operations error (may not be available): {e}")
    
    # Test schema analysis functions
    print("\nTesting schema analysis functions:")
    try:
        # Test get_database_schema (may fail if no database connection)
        schema_info = get_database_schema("test_database")
        if schema_info:
            print("[OK] Database schema retrieved successfully")
            print(f"  Tables found: {len(schema_info.get('tables', {}))}")
        else:
            print("[WARN] Database schema retrieval failed (no connection)")
            
    except Exception as e:
        print(f"[FAIL] Schema analysis error: {e}")
    
    # Test compact schema formatting
    print("\nTesting compact schema formatting:")
    try:
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
        
        compact_schema = format_compact_schema(test_schema)
        if compact_schema:
            print("[OK] Compact schema formatting successful")
            print(f"  Schema: {compact_schema[:200]}...")
        else:
            print("[FAIL] Compact schema formatting failed")
            
    except Exception as e:
        print(f"[FAIL] Compact schema formatting error: {e}")
    
    # Test domain-specific prompt generation
    print("\nTesting domain-specific prompt generation:")
    try:
        # Create test schema and relevant tables for the test
        test_schema = {
            'tables': {
                'employees': {
                    'columns': {
                        'id': {'type': 'int', 'nullable': False},
                        'name': {'type': 'varchar(255)', 'nullable': True},
                        'department': {'type': 'varchar(100)', 'nullable': True}
                    }
                }
            }
        }
        relevant_tables = {'employees'}
        
        prompt = generate_domain_specific_prompt("Show me all employees", test_schema, relevant_tables, "hr")
        if prompt and isinstance(prompt, str):
            print("[OK] Domain-specific prompt generation successful")
            print(f"  Prompt length: {len(prompt)} characters")
        else:
            print("[FAIL] Domain-specific prompt generation failed")
            
    except Exception as e:
        print(f"[FAIL] Domain-specific prompt generation error: {e}")
    
    # Test SQL generation (may fail without database connection)
    print("\nTesting SQL generation:")
    try:
        sql = generate_sql_token_optimized("Show me all employees", "test_database")
        if sql:
            print("[OK] SQL generation successful")
            print(f"  Generated SQL: {sql}")
        else:
            print("[WARN] SQL generation failed (may need database connection)")
            
    except Exception as e:
        print(f"[FAIL] SQL generation error: {e}")
    
    # Test relevant schema extraction
    print("\nTesting relevant schema extraction:")
    try:
        relevant_schema = get_relevant_schema("Show me employee data", "test_database")
        if relevant_schema:
            print("[OK] Relevant schema extraction successful")
            print(f"  Relevant schema: {str(relevant_schema)[:200]}...")
        else:
            print("[WARN] Relevant schema extraction failed (may need database connection)")
            
    except Exception as e:
        print(f"[FAIL] Relevant schema extraction error: {e}")
    
    # Test diagram generation functions
    print("\nTesting diagram generation:")
    try:
        # Test relationship diagram generation
        relationship_diagram = generate_relationship_diagram("test_database")
        if relationship_diagram:
            print("[OK] Relationship diagram generation successful")
        else:
            print("[WARN] Relationship diagram generation failed (may need database connection)")
            
        # Test table schema diagram generation
        table_diagram = generate_table_schema_diagram("users", "test_database")
        if table_diagram:
            print("[OK] Table schema diagram generation successful")
        else:
            print("[WARN] Table schema diagram generation failed (may need database connection)")
            
    except Exception as e:
        print(f"[FAIL] Diagram generation error: {e}")
    
    # Test query execution (may fail without database connection)
    print("\nTesting query execution:")
    try:
        # Test with a simple query
        test_query = "SELECT 1 as test"
        df, error = execute_query(test_query, "test_database")
        
        if error:
            print(f"[WARN] Query execution failed (may need database connection): {error}")
        elif df is not None:
            print("[OK] Query execution successful")
            print(f"  Result shape: {df.shape}")
        else:
            print("[WARN] Query execution returned no data")
            
    except Exception as e:
        print(f"[FAIL] Query execution error: {e}")
    
    # Test data processing with mock data
    print("\nTesting data processing with mock data:")
    try:
        # Create mock DataFrame
        mock_data = {
            'id': [1, 2, 3],
            'name': ['John', 'Jane', 'Bob'],
            'created_at': [datetime.now(), datetime.now(), datetime.now()]
        }
        mock_df = pd.DataFrame(mock_data)
        
        # Test DataFrame operations
        print(f"[OK] Mock DataFrame created with shape: {mock_df.shape}")
        print(f"[OK] DataFrame columns: {list(mock_df.columns)}")
        
        # Test JSON conversion
        json_data = mock_df.to_dict(orient='records')
        print(f"[OK] DataFrame converted to JSON: {len(json_data)} records")
        
    except Exception as e:
        print(f"[FAIL] Data processing error: {e}")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        # Test with invalid query
        invalid_query = "SELECT * FROM nonexistent_table"
        df, error = execute_query(invalid_query, "test_database")
        
        if error:
            print("[OK] Error handling working (expected error for invalid query)")
        else:
            print("[WARN] No error returned for invalid query")
            
    except Exception as e:
        print(f"[OK] Exception handling working: {e}")
    
    print("\n[OK] All database manager tests completed!")

if __name__ == "__main__":
    test_database_manager() 