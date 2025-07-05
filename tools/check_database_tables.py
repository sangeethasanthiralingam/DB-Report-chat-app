#!/usr/bin/env python3
"""
Script to check what tables exist in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database_manager import get_database_schema, DB_CONFIG

def check_database_tables():
    """Check what tables exist in the database"""
    
    print("=== Database Table Check ===")
    print(f"Database: {DB_CONFIG['database']}")
    print()
    
    try:
        schema_info = get_database_schema(DB_CONFIG['database'])
        
        if not schema_info or 'tables' not in schema_info:
            print("❌ Could not retrieve database schema")
            return
        
        tables = list(schema_info['tables'].keys())
        print(f"✅ Found {len(tables)} tables in database:")
        print()
        
        # Group tables by domain
        hr_tables = [t for t in tables if t.startswith('hr_') or any(x in t.lower() for x in ['employee', 'attendance', 'leave', 'payroll'])]
        inventory_tables = [t for t in tables if t.startswith('inv_') or any(x in t.lower() for x in ['product', 'stock', 'sales', 'purchase', 'inventory', 'item'])]
        financial_tables = [t for t in tables if t.startswith('core_fin_') or any(x in t.lower() for x in ['account', 'transaction', 'payment', 'invoice', 'bank'])]
        core_tables = [t for t in tables if t.startswith('core_') and not t.startswith('core_fin_')]
        other_tables = [t for t in tables if t not in hr_tables + inventory_tables + financial_tables + core_tables]
        
        if hr_tables:
            print("🏢 HR Tables:")
            for table in sorted(hr_tables):
                print(f"  • {table}")
            print()
        
        if inventory_tables:
            print("📦 Inventory Tables:")
            for table in sorted(inventory_tables):
                print(f"  • {table}")
            print()
        
        if financial_tables:
            print("💰 Financial Tables:")
            for table in sorted(financial_tables):
                print(f"  • {table}")
            print()
        
        if core_tables:
            print("🔧 Core Tables:")
            for table in sorted(core_tables):
                print(f"  • {table}")
            print()
        
        if other_tables:
            print("📋 Other Tables:")
            for table in sorted(other_tables):
                print(f"  • {table}")
            print()
        
        # Check for specific problematic tables
        problematic_tables = ['suppliers', 'customers', 'employees', 'products']
        print("🔍 Checking for specific tables:")
        for table in problematic_tables:
            if table in tables:
                print(f"  ✅ {table} - EXISTS")
            else:
                print(f"  ❌ {table} - NOT FOUND")
        
        print()
        print("📊 Summary:")
        print(f"  Total tables: {len(tables)}")
        print(f"  HR tables: {len(hr_tables)}")
        print(f"  Inventory tables: {len(inventory_tables)}")
        print(f"  Financial tables: {len(financial_tables)}")
        print(f"  Core tables: {len(core_tables)}")
        print(f"  Other tables: {len(other_tables)}")
        
    except Exception as e:
        print(f"❌ Error checking database tables: {e}")

if __name__ == "__main__":
    check_database_tables() 