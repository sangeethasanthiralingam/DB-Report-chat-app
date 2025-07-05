#!/usr/bin/env python3
"""
Test script for NaT handling in the application.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_nat_handling():
    """Test the NaT handling functionality."""
    print("Testing NaT Handling...")
    
    # Import the data processor
    from utils.data_processor import get_data_processor
    
    # Create a test DataFrame with NaT values
    test_data = {
        'id': [1, 2, 3, 4],
        'name': ['John', 'Jane', 'Bob', 'Alice'],
        'created_at': [
            datetime(2023, 1, 1, 10, 0, 0),
            pd.NaT,  # This should cause issues
            datetime(2023, 1, 3, 14, 30, 0),
            None
        ],
        'updated_at': [
            datetime(2023, 1, 1, 10, 0, 0),
            datetime(2023, 1, 2, 11, 0, 0),
            pd.NaT,  # Another NaT value
            datetime(2023, 1, 4, 16, 0, 0)
        ],
        'score': [85.5, np.nan, 92.0, 78.5]
    }
    
    df = pd.DataFrame(test_data)
    print("Original DataFrame:")
    print(df)
    print(f"DataFrame dtypes: {df.dtypes}")
    print()
    
    # Test the sanitization function
    try:
        data_processor = get_data_processor()
        df_sanitized = data_processor.sanitize_dataframe_for_json(df)
        print("Sanitized DataFrame:")
        print(df_sanitized)
        print(f"Sanitized DataFrame dtypes: {df_sanitized.dtypes}")
        print()
        
        # Test JSON conversion
        json_data = df_sanitized.to_dict(orient='records')
        print("JSON conversion successful!")
        print("First record:", json_data[0])
        print()
        
        # Test that NaT values are properly handled
        for i, record in enumerate(json_data):
            print(f"Record {i+1}:")
            for key, value in record.items():
                print(f"  {key}: {value} (type: {type(value)})")
            print()
        
        print("[OK] NaT handling test passed!")
        
    except Exception as e:
        print(f"[FAIL] NaT handling test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nat_handling() 