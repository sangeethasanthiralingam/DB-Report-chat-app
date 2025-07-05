#!/usr/bin/env python3
"""
Script to fix Unicode symbols in test files to prevent encoding errors on Windows.
"""

import os
import glob

def fix_unicode_symbols_in_file(filepath):
    """Replace Unicode symbols with ASCII equivalents in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace Unicode symbols with ASCII equivalents
        content = content.replace('✓', '[OK]')
        content = content.replace('✗', '[FAIL]')
        content = content.replace('⚠', '[WARN]')
        content = content.replace('🎉', '[SUCCESS]')
        content = content.replace('❌', '[ERROR]')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed Unicode symbols in {filepath}")
        return True
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Fix Unicode symbols in all test files."""
    print("Fixing Unicode symbols in test files...")
    
    # Find all test files
    test_files = glob.glob("test_*.py")
    
    fixed_count = 0
    for test_file in test_files:
        if fix_unicode_symbols_in_file(test_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} out of {len(test_files)} test files.")
    print("Unicode symbols replaced with ASCII equivalents:")
    print("  ✓ -> [OK]")
    print("  ✗ -> [FAIL]")
    print("  ⚠ -> [WARN]")
    print("  🎉 -> [SUCCESS]")
    print("  ❌ -> [ERROR]")

if __name__ == "__main__":
    main() 