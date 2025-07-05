import json
import os
import re
import logging
from collections import defaultdict
from rapidfuzz import fuzz
from typing import Dict, Set, List, Optional, Any


class DomainAnalyzer:
    """Analyzes and classifies database domains based on schema and business terms."""
    
    def __init__(self, business_terms_path: Optional[str] = None):
        """Initialize the domain analyzer with business terms."""
        self.business_terms = self._load_business_terms(business_terms_path)
        self._build_indexes()
        
    def _load_business_terms(self, business_terms_path: Optional[str] = None) -> Dict[str, str]:
        """Load business terms from JSON file."""
        if business_terms_path is None:
            business_terms_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'business_terms.json')
        
        try:
            with open(business_terms_path, 'r', encoding='utf-8') as f:
                business_terms = json.load(f)
            logging.info(f"Loaded {len(business_terms)} business terms from {business_terms_path}")
            return business_terms
        except Exception as e:
            logging.warning(f"Could not load business terms from {business_terms_path}: {e}")
            return {}
    
    def _build_indexes(self):
        """Build optimized indexes for quick lookup."""
        # Table name to business name mapping
        self.table_map = {k.lower(): v.lower() for k, v in self.business_terms.items()}
        self.reverse_table_map = {v.lower(): k.lower() for k, v in self.business_terms.items()}
        
        # Special handling for core_parties which can represent both customers and suppliers
        self.reverse_table_map['suppliers'] = 'core_parties'
        self.reverse_table_map['supplier'] = 'core_parties'
        
        # Domain classification
        self.domain_tables = defaultdict(set)
        for table in self.business_terms.keys():
            domain = self._classify_domain(table)
            self.domain_tables[domain].add(table.lower())
        
        # Build keyword index
        self.keyword_index = defaultdict(set)
        for table, business_name in self.business_terms.items():
            # Add table name parts
            for part in re.split(r'[_\s]', table.lower()):
                if part and len(part) > 2:  # Ignore very short parts
                    self.keyword_index[part].add(table.lower())
            
            # Add business name parts
            for part in re.split(r'[_\s]', business_name.lower()):
                if part and len(part) > 2:
                    self.keyword_index[part].add(table.lower())
            
            # Add full names
            self.keyword_index[table.lower()].add(table.lower())
            self.keyword_index[business_name.lower()].add(table.lower())
            
            # Add singular/plural forms for key business terms
            for word in [business_name.lower()]:
                if word.endswith('s'):
                    self.keyword_index[word[:-1]].add(table.lower())
                else:
                    self.keyword_index[word + 's'].add(table.lower())
        
        # Special handling for suppliers
        self.keyword_index['suppliers'].add('core_parties')
        self.keyword_index['supplier'].add('core_parties')
    
    def _classify_domain(self, table_name: str) -> str:
        """Classify table into domain based on naming patterns."""
        table_lower = table_name.lower()
        
        # HR domain patterns
        if (table_lower.startswith('hr_') or 
            any(x in table_lower for x in ['employee', 'attendance', 'leave', 'payroll', 'shift'])):
            return 'hr'
        
        # Inventory domain patterns
        elif (table_lower.startswith('inv_') or 
              any(x in table_lower for x in ['product', 'stock', 'sales', 'purchase', 'inventory', 'item'])):
            return 'inventory'
        
        # Financial domain patterns
        elif (table_lower.startswith('core_fin_') or 
              any(x in table_lower for x in ['account', 'transaction', 'payment', 'invoice', 'bank'])):
            return 'financial'
        
        # Reporting domain patterns
        elif (table_lower.startswith('report') or 
              table_lower in ['reports', 'charts', 'dashboards', 'analytics']):
            return 'reporting'
        
        # Core domain (default)
        return 'core'
    
    def detect_domain_from_question(self, question: str) -> str:
        """Detect domain from user question using keyword analysis."""
        question_lower = question.lower()
        
        # HR domain keywords - more specific to HR operations
        hr_keywords = ['employee', 'hire', 'attendance', 'leave', 'hr', 'human', 'resource', 
                      'staff', 'personnel', 'workforce', 'payroll', 'shift', 'schedule', 'department']
        if any(word in question_lower for word in hr_keywords):
            return 'hr'
        
        # Inventory domain keywords - more specific to inventory operations
        inventory_keywords = ['product', 'stock', 'inventory', 'sales', 'purchase', 'item', 
                            'goods', 'merchandise', 'supply', 'order', 'category', 'brand']
        if any(word in question_lower for word in inventory_keywords):
            return 'inventory'
        
        # Financial domain keywords - more specific to financial operations
        financial_keywords = ['account', 'payment', 'transaction', 'financial', 'money', 
                            'invoice', 'bank', 'balance', 'revenue', 'expense', 'budget', 'credit']
        if any(word in question_lower for word in financial_keywords):
            return 'financial'
        
        # Reporting domain keywords
        reporting_keywords = ['report', 'chart', 'dashboard', 'analytics', 'statistics', 
                            'summary', 'overview', 'trend', 'graph']
        if any(word in question_lower for word in reporting_keywords):
            return 'reporting'
        
        # Core entity keywords - these should be treated as general, not specific domains
        # But customers and suppliers are also part of inventory management
        core_entity_keywords = ['user', 'person', 'party', 'entity']
        if any(word in question_lower for word in core_entity_keywords):
            return 'general'
        
        # Customer and supplier keywords - these can be both general and inventory-related
        # Check for inventory context first
        inventory_context_keywords = ['product', 'stock', 'inventory', 'sales', 'purchase', 'order', 'supply']
        if any(word in question_lower for word in ['customer', 'supplier']):
            # If there's inventory context, treat as inventory domain
            if any(word in question_lower for word in inventory_context_keywords):
                return 'inventory'
            # Otherwise treat as general
            return 'general'
        
        return 'general'
    
    def identify_business_domain_from_schema(self, schema_info: Dict[str, Any]) -> str:
        """Identify business domain from schema information using table analysis."""
        if not schema_info or 'tables' not in schema_info:
            return 'general'
        
        tables = set(schema_info['tables'].keys())
        
        # HR domain tables
        hr_tables = ['employees', 'attendance_records', 'leave_requests', 'shifts', 'payroll']
        if any(t.startswith('hr_') or t in hr_tables for t in tables):
            return 'hr'
        
        # Inventory domain tables
        inventory_tables = ['products', 'sales', 'stock_levels', 'purchases', 'inventory', 'customers', 'suppliers']
        if any(t.startswith('inv_') or t in inventory_tables for t in tables):
            return 'inventory'
        
        # Financial domain tables
        financial_tables = ['accounts', 'transactions', 'payments', 'invoices', 'bank_accounts']
        if any(t.startswith('core_fin_') or t in financial_tables for t in tables):
            return 'financial'
        
        return 'general'
    
    def find_relevant_tables(self, question: str, threshold: int = 75) -> Set[str]:
        """Find relevant tables using fuzzy matching and domain analysis."""
        question_lower = question.lower()
        matched_tables = set()
        
        logging.info(f"[DEBUG] Question words: {re.findall(r'\w{3,}', question_lower)}")
        logging.info(f"[DEBUG] Available keywords: {list(self.keyword_index.keys())}")
        
        # 1. Exact matches in business terms
        for term, tables in self.keyword_index.items():
            if term in question_lower:
                matched_tables.update(tables)
        
        # 2. Fuzzy matching for partial matches
        words = re.findall(r'\w{3,}', question_lower)  # Get words with 3+ chars
        for word in words:
            for term in self.keyword_index.keys():
                if fuzz.ratio(word, term) >= threshold:
                    matched_tables.update(self.keyword_index[term])
        
        # 3. Domain analysis to expand results
        domains_in_question = set()
        for domain in self.domain_tables:
            domain_words = domain.split('_')
            if any(dw in question_lower for dw in domain_words):
                domains_in_question.add(domain)
        
        for domain in domains_in_question:
            matched_tables.update(self.domain_tables[domain])
        
        # Convert back to original table names
        original_tables = set()
        for table in matched_tables:
            if table in self.reverse_table_map:
                original_tables.add(self.reverse_table_map[table])
            else:
                # Handle case where we matched a business name directly
                original_tables.add(table)
        
        logging.info(f"[DEBUG] Matched tables for question '{question}': {matched_tables}")
        return original_tables
    
    def get_domain_context(self, domain: str) -> Dict[str, Any]:
        """Get domain-specific context for SQL generation."""
        contexts = {
            'hr': {
                'description': "HR Management System - Focus on employees, attendance, leaves, and payroll",
                'common_joins': [
                    "employees ↔ persons (employee details)",
                    "employees ↔ departments (organization structure)",
                    "attendance_records ↔ shifts (work schedules)",
                    "leave_requests ↔ leave_types (time off)"
                ],
                'key_metrics': ["headcount", "attendance_rate", "leave_balance"],
                'common_patterns': [
                    "For attendance queries, join employees with attendance_records",
                    "For leave queries, use leave_requests and leave_types",
                    "Employee data is in employees table, personal info in persons"
                ]
            },
            'inventory': {
                'description': "Inventory Management System - Focus on products, stock, sales, purchases, customers, and suppliers",
                'common_joins': [
                    "products ↔ product_categories (classification)",
                    "sales ↔ sales_items (transaction details)",
                    "stock_transactions ↔ products (inventory movement)",
                    "customers ↔ sales (customer transactions)",
                    "suppliers ↔ purchases (supplier transactions)"
                ],
                'key_metrics': ["stock_level", "sales_volume", "purchase_orders", "customer_count", "supplier_count"],
                'common_patterns': [
                    "For stock queries, use product_stock_levels",
                    "For sales analysis, join sales with sales_items",
                    "Product info is in products table with categories and brands",
                    "Customer data is in customers table",
                    "Supplier data is in suppliers table"
                ]
            },
            'financial': {
                'description': "Financial Management System - Focus on accounts, transactions, and payments",
                'common_joins': [
                    "transactions ↔ accounts (financial activity)",
                    "payments ↔ invoices (settlements)",
                    "transaction_categories ↔ transactions (classification)"
                ],
                'key_metrics': ["account_balance", "transaction_volume", "payment_status"],
                'common_patterns': [
                    "For payment queries, use payments and transactions tables",
                    "Account balances are in accounts table",
                    "Transaction categories help classify financial data"
                ]
            },
            'reporting': {
                'description': "Reporting System - Focus on dashboards, charts, and analytics",
                'common_joins': [
                    "reports ↔ report_types (report classification)",
                    "dashboard_tiles ↔ charts (visualizations)"
                ],
                'key_metrics': ["report_count", "dashboard_usage"],
                'common_patterns': [
                    "For report queries, use reports and report_types",
                    "For dashboard data, join dashboard_tiles with charts"
                ]
            }
        }
        
        contexts['general'] = {
            'description': "Core System - General business operations with core entities",
            'common_joins': [
                "core_parties ↔ core_persons (customer details)",
                "core_parties ↔ core_users (created/updated by)",
                "core_users ↔ core_persons (user details)"
            ],
            'key_metrics': ["customer_count", "user_count", "party_count"],
            'common_patterns': [
                "For customer queries, use core_parties table with type='CUSTOMER'",
                "For user queries, use core_users table",
                "For person queries, use core_persons table",
                "Core entities are linked through foreign key relationships"
            ]
        }
        
        return contexts.get(domain, {
            'description': "Core System - General business operations",
            'common_joins': [],
            'key_metrics': [],
            'common_patterns': []
        })
    
    def get_domain_prompt_context(self, domain: str) -> Dict[str, str]:
        """Get domain-specific prompt context for SQL generation."""
        domain_contexts = {
            'hr': {
                'context': "This is an HR management system. Focus on employee, attendance, leave, and payroll data.",
                'common_patterns': [
                    "For attendance queries, join employees with attendance_records",
                    "For leave queries, use leave_requests and leave_types",
                    "Employee data is in employees table, personal info in persons"
                ]
            },
            'inventory': {
                'context': "This is an inventory management system. Focus on products, sales, purchases, and stock.",
                'common_patterns': [
                    "For stock queries, use product_stock_levels",
                    "For sales analysis, join sales with sales_items",
                    "Product info is in products table with categories and brands"
                ]
            },
            'financial': {
                'context': "This is a financial management system. Focus on accounts, transactions, and payments.",
                'common_patterns': [
                    "For payment queries, use payments and transactions tables",
                    "Account balances are in accounts table",
                    "Transaction categories help classify financial data"
                ]
            },
            'reporting': {
                'context': "This is a reporting system. Focus on dashboards, charts, and analytics.",
                'common_patterns': [
                    "For report queries, use reports and report_types",
                    "For dashboard data, join dashboard_tiles with charts"
                ]
            },
            'general': {
                'context': "This is a general business system with core entities like customers, users, and parties.",
                'common_patterns': [
                    "For customer queries, use core_parties table with type='CUSTOMER'",
                    "For user queries, use core_users table",
                    "For person queries, use core_persons table",
                    "Core entities are linked through foreign key relationships"
                ]
            }
        }
        
        return domain_contexts.get(domain, {
            'context': "This is a general business system.",
            'common_patterns': []
        })
    
    def get_fallback_tables_for_domain(self, domain: str, all_tables: List[str]) -> Set[str]:
        """Get fallback tables for a specific domain when no relevant tables are found."""
        if domain == 'inventory':
            inventory_tables = [t for t in all_tables if t.startswith('inv_')]
            return set(inventory_tables[:3])  # Take first 3 inventory tables
        elif domain == 'hr':
            hr_tables = [t for t in all_tables if t.startswith('hr_')]
            return set(hr_tables[:3])  # Take first 3 HR tables
        elif domain == 'financial':
            financial_tables = [t for t in all_tables if t.startswith('core_fin_')]
            return set(financial_tables[:3])  # Take first 3 financial tables
        else:
            # General fallback
            common_tables = ['employees', 'products', 'sales', 'payments', 'users', 'accounts']
            return set(t for t in common_tables if t in all_tables)


# Global instance for easy access
_domain_analyzer = None

def get_domain_analyzer(business_terms_path: Optional[str] = None) -> DomainAnalyzer:
    """Get or create the global domain analyzer instance."""
    global _domain_analyzer
    if _domain_analyzer is None:
        _domain_analyzer = DomainAnalyzer(business_terms_path)
    return _domain_analyzer 