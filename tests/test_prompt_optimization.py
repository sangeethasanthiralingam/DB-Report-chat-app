#!/usr/bin/env python3
"""
Test script to demonstrate prompt optimization results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database_manager import generate_domain_specific_prompt, format_compact_schema

def test_prompt_optimization():
    """Test the optimized prompts vs original"""
    
    # Sample schema
    sample_schema = {
        'tables': {
            'employees': {
                'columns': [
                    {'name': 'id', 'type': 'INT', 'primary_key': True, 'nullable': False},
                    {'name': 'name', 'type': 'VARCHAR(100)', 'primary_key': False, 'nullable': False},
                    {'name': 'email', 'type': 'VARCHAR(255)', 'primary_key': False, 'nullable': True},
                    {'name': 'department_id', 'type': 'INT', 'primary_key': False, 'nullable': True}
                ],
                'foreign_keys': [
                    {'constrained_columns': ['department_id'], 'referred_table': 'departments'}
                ]
            },
            'departments': {
                'columns': [
                    {'name': 'id', 'type': 'INT', 'primary_key': True, 'nullable': False},
                    {'name': 'name', 'type': 'VARCHAR(100)', 'primary_key': False, 'nullable': False},
                    {'name': 'location', 'type': 'VARCHAR(255)', 'primary_key': False, 'nullable': True}
                ],
                'foreign_keys': []
            }
        }
    }
    
    relevant_tables = {'employees', 'departments'}
    question = "Show all employees with their department names"
    
    # Test the optimized prompt
    try:
        optimized_prompt = generate_domain_specific_prompt(question, sample_schema, relevant_tables, 'hr')
        
        print("=== PROMPT OPTIMIZATION RESULTS ===")
        print(f"Question: {question}")
        print()
        print("Optimized Prompt:")
        print("-" * 50)
        print(optimized_prompt)
        print("-" * 50)
        
        # Calculate metrics
        word_count = len(optimized_prompt.split())
        char_count = len(optimized_prompt)
        estimated_tokens = word_count * 1.3
        
        print(f"\nMetrics:")
        print(f"- Words: {word_count}")
        print(f"- Characters: {char_count}")
        print(f"- Estimated tokens: {estimated_tokens:.1f}")
        
        # Compare with original (estimated)
        original_estimated_tokens = 1157  # From your logs
        token_reduction = original_estimated_tokens - estimated_tokens
        reduction_percentage = (token_reduction / original_estimated_tokens) * 100
        
        print(f"\nToken Reduction:")
        print(f"- Original: ~{original_estimated_tokens} tokens")
        print(f"- Optimized: ~{estimated_tokens:.1f} tokens")
        print(f"- Reduction: {token_reduction:.1f} tokens ({reduction_percentage:.1f}%)")
        
        # Speed improvement estimate
        print(f"\nExpected Speed Improvement:")
        print(f"- Original time: ~6.2 seconds")
        print(f"- Expected time: ~{6.2 * (estimated_tokens / original_estimated_tokens):.1f} seconds")
        print(f"- Speed improvement: ~{(1 - estimated_tokens / original_estimated_tokens) * 100:.1f}%")
        
    except Exception as e:
        print(f"Error testing prompt optimization: {e}")

if __name__ == "__main__":
    test_prompt_optimization() 