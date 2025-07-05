from openai import OpenAI
from flask import Flask, request, jsonify, render_template, session, g
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
import pymysql
import pymysql.cursors
from sqlalchemy import create_engine, inspect as sqla_inspect, text
from urllib.parse import quote_plus 
import json
from datetime import datetime
from flask_session import Session
import networkx as nx
import time
import logging
from dotenv import load_dotenv
import redis
import hashlib
import inspect
import re
from collections import defaultdict
from rapidfuzz import fuzz

load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Custom JSON encoder to handle pandas NaT values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if pd.isna(obj):  # Handle NaT and NaN values
            return None
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        return super().default(obj)

# Configure Flask JSON handling - use try/except for compatibility
try:
    # For newer Flask versions
    app.json_provider_class = type('CustomJSONProvider', (app.json_provider_class,), {
        'default': lambda self, obj: CustomJSONEncoder().default(obj)
    })
except:
    # If JSON encoder configuration fails, NaT values will be handled in add_to_conversation_history
    pass

# Configure Flask-Session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MySQL DB config - Single database only
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 3306),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "db") 
}

# Redis connection (add to top-level, after loading .env)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = None
try:
    redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logging.info('Connected to Redis successfully.')
except Exception as e:
    logging.warning(f'Could not connect to Redis: {e}')
    redis_client = None

# Global SQLAlchemy engine with connection pooling
GLOBAL_ENGINE = None
def get_global_engine():
    global GLOBAL_ENGINE
    if GLOBAL_ENGINE is None:
        password = quote_plus(DB_CONFIG['password'])
        GLOBAL_ENGINE = create_engine(
            f"mysql+pymysql://{DB_CONFIG['user']}:{password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
            pool_size=10, max_overflow=20, pool_recycle=1800, pool_pre_ping=True
        )
    return GLOBAL_ENGINE

# Redis cache helpers
def redis_get(key):
    if redis_client:
        try:
            schema_json = redis_client.get(key)
            if inspect.isawaitable(schema_json):
                raise RuntimeError("redis_get returned an awaitable, but this function is not async.")
            if schema_json:
                return schema_json
        except Exception as e:
            logging.warning(f'Redis get error: {e}')
    return None

def redis_set(key, value, ex=None):
    if redis_client:
        try:
            redis_client.set(key, value, ex=ex)
        except Exception as e:
            logging.warning(f'Redis set error: {e}')

# Cache for database schema and metadata
DB_METADATA_CACHE = {}
CACHE_EXPIRY_MINUTES = 60
QUERY_CACHE_EXPIRY_SECONDS = 600  # 10 minutes
LLM_CACHE_EXPIRY_SECONDS = 3600   # 1 hour

# Initialize session for conversation history
def init_session():
    """Initialize session with conversation history"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'generated_images' not in session:
        session['generated_images'] = []
    if 'id' not in session:
        session['id'] = hashlib.md5(f"{datetime.now().isoformat()}{os.getpid()}".encode()).hexdigest()[:8]

def add_to_conversation_history(question, response_obj, sql_query=""):
    """Add a conversation turn to the history"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    # Clean response_obj to handle NaT values
    def clean_for_json(obj):
        if isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(item) for item in obj]
        elif pd.isna(obj):  # Handle NaT and NaN values
            return None
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        else:
            return obj
    
    cleaned_response = clean_for_json(response_obj)
    
    session['conversation_history'].append({
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'response_obj': cleaned_response,
        'sql_query': sql_query,
        'database': DB_CONFIG['database']
    })
    
    # Keep only last 10 conversations to prevent session bloat
    if len(session['conversation_history']) > 10:
        session['conversation_history'] = session['conversation_history'][-10:]
    
    session.modified = True

def save_image_to_file(img_base64, chart_type, session_id=None):
    """Save base64 image to file and return the filename"""
    try:
        # Create generated directory if it doesn't exist
        generated_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')
        os.makedirs(generated_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_suffix = f"_{session_id}" if session_id else ""
        filename = f"{chart_type}_{timestamp}{session_suffix}.png"
        filepath = os.path.join(generated_dir, filename)
        
        # Decode and save image
        img_data = base64.b64decode(img_base64)
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        logging.info(f"Image saved to file: {filepath}")
        return filename
    except Exception as e:
        logging.error(f"Error saving image to file: {e}")
        return None

def delete_session_images():
    """Delete all images associated with the current session"""
    if 'generated_images' not in session:
        return
    
    generated_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')
    if not os.path.exists(generated_dir):
        return
    
    deleted_count = 0
    for filename in session['generated_images']:
        filepath = os.path.join(generated_dir, filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_count += 1
                logging.info(f"Deleted image file: {filepath}")
        except Exception as e:
            logging.error(f"Error deleting image file {filepath}: {e}")
    
    if deleted_count > 0:
        logging.info(f"Deleted {deleted_count} image files for session")
    
    # Clear the list
    session['generated_images'] = []
    session.modified = True

def cleanup_old_images():
    """Clean up old image files that are older than 24 hours"""
    generated_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')
    if not os.path.exists(generated_dir):
        return
    
    current_time = datetime.now()
    deleted_count = 0
    
    try:
        for filename in os.listdir(generated_dir):
            if filename.endswith('.png'):
                filepath = os.path.join(generated_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                # Delete files older than 24 hours
                if (current_time - file_time).total_seconds() > 86400:  # 24 hours
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logging.info(f"Cleaned up old image file: {filepath}")
                    except Exception as e:
                        logging.error(f"Error deleting old image file {filepath}: {e}")
        
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} old image files")
    except Exception as e:
        logging.error(f"Error during image cleanup: {e}")

def get_conversation_context(limit=1, truncate=100):
    if 'conversation_history' not in session or not session['conversation_history']:
        return ""
    recent_conversations = session['conversation_history'][-limit:]
    context = "Recent conversation history:\n"
    for conv in recent_conversations:
        q = conv['question'][:truncate] + ("..." if len(conv['question']) > truncate else "")
        resp = str(conv['response_obj'])[:truncate] + ("..." if len(str(conv['response_obj'])) > truncate else "")
        context += f"User: {q}\nAssistant: {resp}\n---\n"
    return context

def get_optimized_conversation_context(question):
    """Get minimal but relevant conversation context"""
    if 'conversation_history' not in session:
        return ""
    
    history = session['conversation_history']
    if not history:
        return ""
    
    # Only include context if question seems related to previous ones
    question_lower = question.lower()
    context_keywords = ['previous', 'before', 'last', 'earlier', 'that', 'those', 'same']
    
    if not any(keyword in question_lower for keyword in context_keywords):
        return ""
    
    # Include only last 2 conversations and only essential info
    recent = history[-2:]
    context = "Recent context:\n"
    for conv in recent:
        context += f"Q: {conv['question'][:50]}{'...' if len(conv['question']) > 50 else ''}\n"
        # Include only successful query results summary
        if conv.get('sql_query') and not conv['response_obj'].startswith('Error'):
            resp = str(conv['response_obj'])
            resp_preview = resp[:30] + '...' if len(resp) > 30 else resp
            context += f"Found: {resp_preview}\n"
    
    return context

def get_db_connection():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        cursorclass=pymysql.cursors.DictCursor
    )

def get_sqlalchemy_engine(database=None):
    password = quote_plus(DB_CONFIG['password'])
    db_name = database or DB_CONFIG['database']
    return create_engine(
        f"mysql+pymysql://{DB_CONFIG['user']}:{password}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db_name}"
    )

def get_smart_sample_data(table_name, engine, max_rows=2):
    """Get representative sample data with intelligent selection"""
    try:
        # Get total row count
        count_query = f"SELECT COUNT(*) as total FROM `{table_name}`"
        total_rows = pd.read_sql(text(count_query), engine).iloc[0]['total']
        
        if total_rows == 0:
            return []
        
        # For small tables, get all data
        if total_rows <= max_rows:
            query = f"SELECT * FROM `{table_name}`"
        else:
            # Get diverse sample: first row, last row, and middle rows
            query = f"""
            (SELECT * FROM `{table_name}` ORDER BY 1 LIMIT 1)
            UNION ALL
            (SELECT * FROM `{table_name}` ORDER BY 1 DESC LIMIT 1)
            LIMIT {max_rows}
            """
        
        result = pd.read_sql(text(query), engine)
        return result.to_dict('records')
    except:
        return []

def get_database_schema(database=None):
    """Get complete schema with table relationships and sample data, with Redis caching"""
    start_time = time.time()
    cache_key = f"schema_{database or 'default'}"

    schema_json = redis_get(cache_key)
    if schema_json:
        try:
            schema_info = json.loads(schema_json)
            logging.info(f"Schema for '{database}' loaded from Redis in {time.time() - start_time:.4f} seconds.")
            return schema_info
        except Exception as e:
            logging.warning(f"Failed to load schema from Redis: {e}")

    # Fallback to in-memory cache
    if cache_key in DB_METADATA_CACHE:
        cached_data = DB_METADATA_CACHE[cache_key]
        if (datetime.now() - cached_data['timestamp']).total_seconds() < CACHE_EXPIRY_MINUTES * 60:
            logging.info(f"Schema for '{database}' loaded from memory in {time.time() - start_time:.4f} seconds.")
            return cached_data['schema']

    schema_info = {
        "tables": {},
        "relationships": [],
        "timestamp": datetime.now()
    }
    
    try:
        engine = get_global_engine()
        inspector = sqla_inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        
        for table in tables:
            # Get columns
            columns = inspector.get_columns(table)
            column_info = []
            
            for col in columns:
                column_info.append({
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col['nullable'],
                    "primary_key": col.get('primary_key', False)
                })
            
            # Get primary keys
            pks = inspector.get_pk_constraint(table)
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table)
            
            # Get sample data (use smart sampling)
            sample_data = []
            try:
                sample_data = get_smart_sample_data(table, engine, max_rows=2)
            except Exception as e:
                print(f"Error getting sample data for {table}: {e}")
            
            schema_info["tables"][table] = {
                "columns": column_info,
                "primary_key": pks.get('constrained_columns', []),
                "foreign_keys": fks,
                "sample_data": sample_data
            }
            
            # Record relationships
            for fk in fks:
                schema_info["relationships"].append({
                    "source_table": table,
                    "source_column": fk['constrained_columns'][0],
                    "target_table": fk['referred_table'],
                    "target_column": fk['referred_columns'][0]
                })
        
        # Cache in Redis
        try:
            redis_set(cache_key, json.dumps(schema_info, default=str), ex=CACHE_EXPIRY_MINUTES*60)
        except Exception as e:
            logging.warning(f"Failed to set schema in Redis: {e}")
        # Cache in memory
        DB_METADATA_CACHE[cache_key] = {
            "schema": schema_info,
            "timestamp": datetime.now()
        }
        
        logging.info(f"Schema for '{database}' loaded in {time.time() - start_time:.4f} seconds.")
        return schema_info
    
    except Exception as e:
        logging.error(f"Error getting schema: {e}")
        return None

# Load business_terms.json as before
with open(os.path.join(os.path.dirname(__file__), 'business_terms.json'), 'r', encoding='utf-8') as f:
    business_terms = json.load(f)

class SchemaAnalyzer:
    def __init__(self, business_terms):
        self.business_terms = business_terms
        self._build_indexes()
        
    def _build_indexes(self):
        """Build optimized indexes for quick lookup"""
        # Table name to business name mapping
        self.table_map = {k.lower(): v.lower() for k, v in self.business_terms.items()}
        self.reverse_table_map = {v.lower(): k.lower() for k, v in self.business_terms.items()}
        
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
    
    def _classify_domain(self, table_name):
        """Classify table into domain based on naming patterns"""
        table_lower = table_name.lower()
        if table_lower.startswith('hr_') or 'employee' in table_lower:
            return 'hr'
        elif table_lower.startswith('inv_') or any(x in table_lower for x in ['product', 'stock', 'sales', 'purchase']):
            return 'inventory'
        elif table_lower.startswith('core_fin_') or any(x in table_lower for x in ['account', 'transaction', 'payment']):
            return 'financial'
        elif table_lower.startswith('report') or table_lower in ['reports', 'charts', 'dashboards']:
            return 'reporting'
        return 'core'

    def find_relevant_tables(self, question, threshold=75):
        """Find relevant tables using fuzzy matching and domain analysis"""
        question_lower = question.lower()
        matched_tables = set()
        
        # Add this debug line
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
        logging.info(f"[DEBUG] Keyword index: {self.keyword_index}")
        return original_tables

    def get_domain_context(self, domain):
        """Get domain-specific context for SQL generation"""
        contexts = {
            'hr': {
                'description': "HR Management System - Focus on employees, attendance, leaves, and payroll",
                'common_joins': [
                    "employees ↔ persons (employee details)",
                    "employees ↔ departments (organization structure)",
                    "attendance_records ↔ shifts (work schedules)",
                    "leave_requests ↔ leave_types (time off)"
                ],
                'key_metrics': ["headcount", "attendance_rate", "leave_balance"]
            },
            'inventory': {
                'description': "Inventory Management System - Focus on products, stock, sales, and purchases",
                'common_joins': [
                    "products ↔ product_categories (classification)",
                    "sales ↔ sales_items (transaction details)",
                    "stock_transactions ↔ products (inventory movement)"
                ],
                'key_metrics': ["stock_level", "sales_volume", "purchase_orders"]
            },
            'financial': {
                'description': "Financial Management System - Focus on accounts, transactions, and payments",
                'common_joins': [
                    "transactions ↔ accounts (financial activity)",
                    "payments ↔ invoices (settlements)",
                    "transaction_categories ↔ transactions (classification)"
                ],
                'key_metrics': ["account_balance", "transaction_volume", "payment_status"]
            },
            'reporting': {
                'description': "Reporting System - Focus on dashboards, charts, and analytics",
                'common_joins': [
                    "reports ↔ report_types (report classification)",
                    "dashboard_tiles ↔ charts (visualizations)"
                ],
                'key_metrics': ["report_count", "dashboard_usage"]
            }
        }
        return contexts.get(domain, {
            'description': "Core System - General business operations",
            'common_joins': [],
            'key_metrics': []
        })

analyzer = SchemaAnalyzer(business_terms)
import logging
logging.info(f"[DEBUG] Analyzer initialized with {len(analyzer.business_terms)} business terms")
logging.info(f"[DEBUG] Sample business terms: {list(analyzer.business_terms.items())[:5]}")
logging.info(f"[DEBUG] Does analyzer have 'customers' mapping? {'customers' in [v.lower() for v in analyzer.business_terms.values()]}")

def get_relevant_schema(question, database=None):
    """Get only relevant parts of schema based on question, using business_terms.json for keyword mapping"""
    full_schema = get_database_schema(database)
    if not full_schema:
        return None

    # Use SchemaAnalyzer for better table detection
    relevant_tables = analyzer.find_relevant_tables(question)
    logging.info(f"[DEBUG] Relevant tables for question '{question}': {relevant_tables}")
    if not relevant_tables:
        # Fallback to common tables
        common_tables = ['employees', 'products', 'sales', 'payments', 'users', 'accounts']
        relevant_tables = set(t for t in common_tables if t in full_schema['tables'])
        logging.info(f"[DEBUG] Fallback relevant tables: {relevant_tables}")

    # Build filtered schema
    filtered_schema = {
        'tables': {t: full_schema['tables'][t] for t in relevant_tables if t in full_schema['tables']},
        'relationships': [r for r in full_schema['relationships'] 
                        if r['source_table'] in relevant_tables or r['target_table'] in relevant_tables]
    }

    return filtered_schema

def extract_relevant_tables_columns(question, schema_info):
    """Extract relevant tables and columns from the question using simple keyword matching."""
    q = question.lower()
    relevant_tables = set()
    relevant_columns = defaultdict(set)
    for table, info in schema_info['tables'].items():
        if table.lower() in q:
            relevant_tables.add(table)
        for col in info['columns']:
            if col['name'].lower() in q:
                relevant_tables.add(table)
                relevant_columns[table].add(col['name'])
    # Fallback: if no tables found, return all (to avoid empty prompt)
    if not relevant_tables:
        return set(schema_info['tables'].keys()), defaultdict(set)
    return relevant_tables, relevant_columns

# --- Token-Optimized SQL Generation ---
def generate_sql_token_optimized(question, database=None, error_context=None):
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info:
        return None
    conversation_context = get_conversation_context(limit=1, truncate=100)
    
    # Step 1: Detect domain from the question first
    question_lower = question.lower()
    domain = 'general'  # default
    
    # Simple domain detection based on question keywords
    logging.info(f"[DEBUG] Question lower: '{question_lower}'")
    
    if any(word in question_lower for word in ['employee', 'hire', 'attendance', 'leave', 'hr', 'human']):
        domain = 'hr'
        logging.info(f"[DEBUG] HR domain detected")
    elif any(word in question_lower for word in ['product', 'stock', 'inventory', 'sales', 'purchase', 'customers']):
        domain = 'inventory'
        logging.info(f"[DEBUG] Inventory domain detected")
    elif any(word in question_lower for word in ['account', 'payment', 'transaction', 'financial', 'money']):
        domain = 'financial'
        logging.info(f"[DEBUG] Financial domain detected")
    elif any(word in question_lower for word in ['report', 'chart', 'dashboard']):
        domain = 'reporting'
        logging.info(f"[DEBUG] Reporting domain detected")
    else:
        logging.info(f"[DEBUG] No specific domain detected, using general")
    
    logging.info(f"[DEBUG] Domain detected from question '{question}': {domain}")
    
    # Step 2: Find relevant tables within the detected domain
    relevant_tables = analyzer.find_relevant_tables(question)
    relevant_columns = defaultdict(set)  # We don't need column-level matching for now
    
    logging.info(f"[DEBUG] Relevant tables found: {relevant_tables}")
    
    # Debug: Check if analyzer is working correctly
    logging.info(f"[DEBUG] Analyzer business terms sample: {list(analyzer.business_terms.items())[:3]}")
    logging.info(f"[DEBUG] Analyzer keyword index sample: {dict(list(analyzer.keyword_index.items())[:5])}")
    
    # If no relevant tables found, try to find tables based on the detected domain
    if not relevant_tables and domain != 'general':
        logging.info(f"[DEBUG] No relevant tables found, searching for {domain} domain tables")
        # Get all tables from the schema
        all_tables = list(schema_info['tables'].keys())
        if domain == 'inventory':
            # Look for inventory-related tables
            inventory_tables = [t for t in all_tables if t.startswith('inv_')]
            relevant_tables = set(inventory_tables[:3])  # Take first 3 inventory tables
            logging.info(f"[DEBUG] Found inventory tables: {relevant_tables}")
        elif domain == 'hr':
            # Look for HR-related tables
            hr_tables = [t for t in all_tables if t.startswith('hr_')]
            relevant_tables = set(hr_tables[:3])  # Take first 3 HR tables
            logging.info(f"[DEBUG] Found HR tables: {relevant_tables}")
    
    try:
        domain_prompt = generate_domain_specific_prompt(question, schema_info, relevant_tables, domain)
        if conversation_context:
            domain_prompt += f"\n{conversation_context}\n"
        if error_context:
            domain_prompt += f"\nThe previously generated query failed with the error: \"{error_context}\".\n"
        prompt = domain_prompt
    except Exception as e:
        # Fallback to original prompt if domain-specific fails
        schema_prompt = "Schema (compact format):\n"
        compact_schema = format_compact_schema({
            "tables": {t: schema_info['tables'][t] for t in relevant_tables if t in schema_info['tables']}
            # relationships omitted for token efficiency
        })
        schema_prompt += compact_schema
        context_prompt = f"\n{conversation_context}\n" if conversation_context else ""
        error_feedback_prompt = f"\nThe previously generated query failed with the error: \"{error_context}\".\n" if error_context else ""
        prompt = f"""
        You are an expert SQL analyst.
        {schema_prompt}
        {context_prompt}
        {error_feedback_prompt}
        For the following question: \"{question}\"
        Use only the schema above. Output only the SQL query.
        """
    # --- LLM Result Caching ---
    llm_cache_key = f"llm_sql_{hash(question + json.dumps(list(relevant_tables)))}_{database or 'default'}"
    cached_sql = redis_get(llm_cache_key)
    if cached_sql:
        return cached_sql
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500
        )
        logging.info(f"OpenAI SQL prompt:\n{prompt}")
        if response.usage:
            logging.info(f"OpenAI API usage for SQL generation: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens.")
        sql = (response.choices[0].message.content or "").strip()
        if sql.startswith("```sql"):
            sql = sql[6:-3].strip()
        elif sql.startswith("```"):
            sql = sql[3:-3].strip()
        
        # Validate SQL - check for placeholder values
        if any(placeholder in sql.lower() for placeholder in ['your_table_name', 'your_column_name', 'table_name', 'column_name']):
            logging.error(f"SQL contains placeholder values: {sql}")
            return None
            
        if not sql.startswith("--ERROR"):
            redis_set(llm_cache_key, sql, ex=LLM_CACHE_EXPIRY_SECONDS)
        logging.info(f"Token-optimized SQL generated in {time.time() - start_time:.4f} seconds.")
        if not sql.strip().lower().startswith("select"):
            logging.error(f"Refusing to execute non-SELECT statement: {sql}")
            return None
        return sql if not sql.startswith("--ERROR") else None
    except Exception as e:
        logging.error(f"Error generating SQL (token-optimized): {e}")
        return None

def determine_response_type(question, data_preview=None):
    """Determine the best way to present the response"""
    start_time = time.time()
    prompt = f"""
    Analyze this user question and determine the best response format:
    
    Question: "{question}"
    
    Available data preview: {str(data_preview)[:500] if data_preview else "Not available"}
    
    Respond with ONLY one of these options:
    - "text" for simple single-value answers or explanations
    - "card" for key metrics display (1-4 important numbers)
    - "table" for tabular data comparisons
    - "bar" for bar charts (comparisons between categories)
    - "line" for line charts (trends over time)
    - "pie" for pie charts (proportion breakdowns)
    - "scatter" for scatter plots (relationships between variables)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        logging.info(f"OpenAI response type prompt:\n{prompt}")
        if response.usage:
            logging.info(f"OpenAI API usage for response type determination: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens.")
        response_type = (response.choices[0].message.content or "").strip().lower()
        logging.info(f"Response type determined as '{response_type}' in {time.time() - start_time:.4f} seconds.")
        return response_type
    except Exception as e:
        logging.error(f"Error determining response type: {e}")
        return "table"  # Default to table

def handle_full_documentation_request(database):
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info:
        return "Sorry, I couldn't retrieve the schema."
    # Compose a detailed prompt for the LLM
    prompt = f"""
    You are a technical writer. Write a detailed, multi-section documentation (about 2000 words) for the database "{database}".
    Use the following schema information:
    {json.dumps(schema_info, indent=2)}
    Structure your answer with sections: Overview, Database Structure, Table Descriptions, Relationships, and any other relevant sections.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048  # or higher, if your model/account allows
        )
        logging.info(f"OpenAI full documentation prompt:\n{prompt}")
        if response.usage:
            logging.info(f"OpenAI API usage for full documentation: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens.")
        content = (response.choices[0].message.content or "").strip()
        logging.info(f"Full documentation generated in {time.time() - start_time:.4f} seconds.")
        return content
    except Exception as e:
        return f"Error generating documentation: {e}"

def get_query_cache_key(sql, database=None):
    return f"queryres_{database or 'default'}_{hash(sql)}"

def execute_query(sql, database=None):
    """Execute SQL and return DataFrame and error, with Redis caching"""
    start_time = time.time()
    cache_key = get_query_cache_key(sql, database)
    # Try Redis cache first
    cached = redis_get(cache_key)
    if inspect.isawaitable(cached):
        raise RuntimeError("redis_get returned an awaitable, but this function is not async.")
    if cached:
        try:
            df = pd.read_json(cached, orient='split')
            logging.info(f"Query result loaded from Redis in {time.time() - start_time:.4f} seconds.")
            return df, None
        except Exception as e:
            logging.warning(f"Failed to load query result from Redis: {e}")
    try:
        engine = get_global_engine()
        df = pd.read_sql(text(sql), engine)
        # Cache result in Redis
        try:
            redis_set(cache_key, df.to_json(orient='split'), ex=QUERY_CACHE_EXPIRY_SECONDS)
        except Exception as e:
            logging.warning(f"Failed to set query result in Redis: {e}")
        logging.info(f"SQL query executed in {time.time() - start_time:.4f} seconds. Result size: {len(df)} rows.")
        return df, None
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return None, e

def generate_visualization(df, chart_type):
    """Generate different types of visualizations"""
    start_time = time.time()
    plt.figure(figsize=(10, 5))
    # Use a valid style, fallback if not available
    try:
        plt.style.use('seaborn-v0_8')
    except Exception:
        plt.style.use('ggplot')
    
    try:
        if chart_type == "bar":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                df.plot(kind='bar', x=x_col, y=y_col, legend=False)
                plt.title(f"{y_col} by {x_col}")
            else:
                df.plot(kind='bar', legend=False)
                plt.title("Data Distribution")
        
        elif chart_type == "line":
            if len(df.columns) >= 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
                df.plot(kind='line', x=x_col, y=y_col, marker='o')
                plt.title(f"{y_col} Trend")
            else:
                df.plot(kind='line', legend=False)
                plt.title("Trend Over Time")
        
        elif chart_type == "pie":
            if len(df.columns) >= 2:
                df.set_index(df.columns[0]).plot(kind='pie', y=df.columns[1], 
                                                autopct='%1.1f%%', legend=False)
                plt.title("Proportion Breakdown")
                plt.ylabel('')
            else:
                df.plot(kind='pie', subplots=True, autopct='%1.1f%%', legend=False)
                plt.title("Distribution")
        
        elif chart_type == "scatter":
            if len(df.columns) >= 3:
                plt.scatter(df.iloc[:, 0], df.iloc[:, 1], c=df.iloc[:, 2], s=100)
                plt.colorbar()
            elif len(df.columns) >= 2:
                plt.scatter(df.iloc[:, 0], df.iloc[:, 1])
            plt.title("Relationship Analysis")
        
        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=120)
        plt.close()
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        logging.info(f"Chart '{chart_type}' generated in {time.time() - start_time:.4f} seconds.")
        return img_base64
    
    except Exception as e:
        logging.error(f"Error generating chart: {e}")
        plt.close()
        return None

def generate_nl_from_data(question, df):
    """Generate a natural language response from a DataFrame based on the user's question."""
    if df.empty:
        return "I couldn't find any information for your request."
        
    start_time = time.time()
    
    # Prepare the data preview for the prompt
    data_preview = df.head(10).to_string(index=False)
    
    prompt = f"""
    You are an AI assistant designed to communicate data insights in a human-friendly way.
    A user asked the following question: "{question}"
    
    The following data was retrieved from the database to answer the question:
    --- DATA ---
    {data_preview}
    --- END DATA ---
    
    Based on this data, please provide a clear and conversational answer to the user's question.
    Your response should be in a paragraph format.
    
    Follow these rules STRICTLY:
    1.  **Do not** mention table names, column names, or any other database-specific terms.
    2.  Summarize the key information from the data.
    3.  If there are multiple results, describe them naturally. For example, instead of a list, you can say "There are several items..."
    4.  If the data contains a single number or result, state it clearly.
    5.  Keep the tone helpful and easy to understand for a non-technical person.
    6.  If the data seems empty or doesn't answer the question, say that you couldn't find the specific information.
    
    Your Answer:
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250
        )
        logging.info(f"OpenAI NL generation prompt:\n{prompt}")
        if response.usage:
            logging.info(f"OpenAI API usage for NL generation: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens.")
        content = (response.choices[0].message.content or "").strip()
        logging.info(f"Natural language response generated in {time.time() - start_time:.4f} seconds.")
        return content
    except Exception as e:
        logging.error(f"Error generating natural language response: {e}")
        # Fallback to a simple table string if NL generation fails
        return f"I found the following information:\n\n{df.to_string(index=False)}"

def format_text_response(df, question):
    """Format a textual answer from the DataFrame into natural language using an LLM."""
    if df.empty:
        return "I couldn't find any data matching your query. Please try rephrasing your question."
    
    # Use LLM to generate a natural language response from the data
    return generate_nl_from_data(question, df)

def format_card_response(df):
    """Format key metrics in card style"""
    if df.empty:
        return None
    
    # For single metric
    if df.shape[0] == 1 and df.shape[1] == 1:
        return [{
            "title": "Result",
            "value": str(df.iloc[0,0]),
            "change": None
        }]
    
    # For multiple metrics
    cards = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            cards.append({
                "title": col,
                "value": f"{df[col].sum():,.2f}",
                "change": None
            })
        else:
            cards.append({
                "title": col,
                "value": str(df[col].iloc[0]),
                "change": None
            })
    
    return cards[:4]  # Return max 4 cards

def format_database_documentation_response(df, question):
    """Format database documentation responses in a more user-friendly way"""
    if df.empty:
        return "I couldn't find any database documentation matching your query. Could you please be more specific about what you're looking for?"
    
    # Check if this is a table listing query
    if 'table' in question.lower() and df.shape[0] > 1:
        table_names = df.iloc[:, 0].tolist() if len(df.columns) > 0 else []
        if table_names:
            return f"I found **{len(table_names)}** tables in the database:\n\n" + "\n".join([f"• {table}" for table in table_names])
    
    # Check if this is a column listing query
    if 'column' in question.lower() and df.shape[0] > 1:
        column_info = []
        for _, row in df.iterrows():
            col_name = row.iloc[0] if len(row) > 0 else "Unknown"
            col_type = row.iloc[1] if len(row) > 1 else ""
            column_info.append(f"• **{col_name}** ({col_type})" if col_type else f"• **{col_name}**")
        return "Here are the columns:\n\n" + "\n".join(column_info)
    
    # For general documentation queries
    if df.shape[0] == 1 and df.shape[1] == 1:
        return f"**{df.iloc[0,0]}**"
    
    # For multiple results, format as a nice list
    if df.shape[0] > 1:
        result_lines = []
        for _, row in df.iterrows():
            if len(row) == 1:
                result_lines.append(f"• {row.iloc[0]}")
            else:
                result_lines.append(f"• **{row.iloc[0]}**: {row.iloc[1]}")
        return "Here's what I found:\n\n" + "\n".join(result_lines)
    
    return format_text_response(df, question)

def handle_documentation_query(question, database):
    """Handle database documentation queries with more natural responses"""
    q_lower = question.lower()
    
    # Get database schema
    schema_info = get_database_schema(database)
    if not schema_info:
        return "I'm sorry, I couldn't retrieve the database schema. Please check your database connection."
    
    # Handle different types of documentation queries
    if 'table' in q_lower and ('list' in q_lower or 'show' in q_lower or 'what' in q_lower):
        tables = list(schema_info['tables'].keys())
        if tables:
            return f"I found {len(tables)} tables in the {database} database:\n\n" + "\n".join([f"• {table}" for table in tables])
        else:
            return f"The {database} database doesn't have any tables."
    
    elif 'column' in q_lower and ('list' in q_lower or 'show' in q_lower):
        # Try to identify which table they're asking about
        for table_name in schema_info['tables']:
            if table_name.lower() in q_lower:
                columns = schema_info['tables'][table_name]['columns']
                column_list = []
                for col in columns:
                    col_type = col['type']
                    pk_marker = " (Primary Key)" if col['primary_key'] else ""
                    column_list.append(f"• {col['name']} ({col_type}){pk_marker}")
                
                return f"The {table_name} table has {len(columns)} columns:\n\n" + "\n".join(column_list)
        
        # If no specific table mentioned, show all tables with column counts
        table_summary = []
        for table_name, table_info in schema_info['tables'].items():
            col_count = len(table_info['columns'])
            table_summary.append(f"• {table_name}: {col_count} columns")
        
        return f"Here are all tables in the {database} database with their column counts:\n\n" + "\n".join(table_summary)
    
    elif 'schema' in q_lower or 'structure' in q_lower:
        tables = list(schema_info['tables'].keys())
        if tables:
            summary = f"The {database} database contains {len(tables)} tables:\n\n"
            for table_name, table_info in schema_info['tables'].items():
                col_count = len(table_info['columns'])
                fk_count = len(table_info['foreign_keys'])
                summary += f"• {table_name}: {col_count} columns, {fk_count} foreign keys\n"
            return summary
        else:
            return f"The {database} database is empty (no tables found)."
    
    elif 'describe' in q_lower or 'what is' in q_lower:
        # Try to identify a specific table
        for table_name in schema_info['tables']:
            if table_name.lower() in q_lower:
                table_info = schema_info['tables'][table_name]
                columns = table_info['columns']
                
                description = f"The {table_name} table contains {len(columns)} columns:\n\n"
                
                for col in columns:
                    col_desc = f"• {col['name']} ({col['type']})"
                    if col['primary_key']:
                        col_desc += " - Primary Key"
                    if not col['nullable']:
                        col_desc += " - Not Null"
                    description += col_desc + "\n"
                
                # Add foreign key information
                if table_info['foreign_keys']:
                    description += "\nForeign Key Relationships:\n"
                    for fk in table_info['foreign_keys']:
                        description += f"• {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}\n"
                
                return description
        
        # If no specific table mentioned, give database overview
        tables = list(schema_info['tables'].keys())
        if tables:
            return f"The {database} database contains {len(tables)} tables: {', '.join(tables)}. You can ask me about specific tables or columns for more details."
        else:
            return f"The {database} database is empty."
    
    # Default response for documentation queries
    return f"I can help you explore the {database} database. You can ask me to:\n\n• List all tables\n• Show columns for a specific table\n• Describe the database structure\n• Get information about specific tables or columns"

def generate_relationship_diagram(database=None):
    """Generate a visual diagram of database table relationships"""
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info or not schema_info['relationships']:
        return None
    
    try:
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes (tables)
        for table_name in schema_info['tables']:
            G.add_node(table_name)
        
        # Add edges (relationships)
        for rel in schema_info['relationships']:
            G.add_edge(
                rel['source_table'], 
                rel['target_table'], 
                label=f"{rel['source_column']} → {rel['target_column']}"
            )
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        plt.clf()
        
        # Use a layout that works well for hierarchical structures
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, 
                              node_color='lightblue', 
                              node_size=3000, 
                              alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, 
                              edge_color='gray', 
                              arrows=True, 
                              arrowsize=20, 
                              arrowstyle='->',
                              connectionstyle='arc3,rad=0.1')
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, 
                               font_size=10, 
                               font_weight='bold')
        
        # Add edge labels
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, 
                                    edge_labels=edge_labels, 
                                    font_size=8)
        
        plt.title(f"Database Relationships - {database or 'Default Database'}", 
                 fontsize=14, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        # Save to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        logging.info(f"Relationship diagram generated in {time.time() - start_time:.4f} seconds.")
        return img_base64
        
    except Exception as e:
        logging.error(f"Error generating relationship diagram: {e}")
        plt.close()
        return None

def generate_table_schema_diagram(table_name, database=None):
    """Generate a visual diagram of a specific table's schema"""
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info or table_name not in schema_info['tables']:
        return None
    
    try:
        table_info = schema_info['tables'][table_name]
        columns = table_info['columns']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('off')
        
        # Table title
        ax.text(0.5, 0.95, f"Table: {table_name}", 
                ha='center', va='top', fontsize=16, fontweight='bold',
                transform=ax.transAxes)
        
        # Create table data
        table_data = []
        headers = ['Column', 'Type', 'Constraints']
        
        for col in columns:
            constraints = []
            if col['primary_key']:
                constraints.append('PK')
            if not col['nullable']:
                constraints.append('NOT NULL')
            
            table_data.append([
                col['name'],
                col['type'],
                ', '.join(constraints) if constraints else '-'
            ])
        
        # Create table
        table = ax.table(cellText=table_data,
                        colLabels=headers,
                        cellLoc='left',
                        loc='center')
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Color header
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#3b82f6')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Color primary key rows
        for i, col in enumerate(columns):
            if col['primary_key']:
                for j in range(len(headers)):
                    table[(i+1, j)].set_facecolor('#fef3c7')
        
        # Add foreign key information if any
        if table_info['foreign_keys']:
            fk_text = "Foreign Keys:\n"
            for fk in table_info['foreign_keys']:
                fk_text += f"• {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}\n"
            
            ax.text(0.05, 0.02, fk_text, 
                   transform=ax.transAxes, fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
        
        plt.tight_layout()
        
        # Save to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        logging.info(f"Table schema diagram for '{table_name}' generated in {time.time() - start_time:.4f} seconds.")
        return img_base64
        
    except Exception as e:
        logging.error(f"Error generating table schema diagram: {e}")
        plt.close()
        return None

def format_compact_schema(schema_info):
    """Format schema in compact, token-efficient way"""
    compact = []
    
    for table_name, table_info in schema_info['tables'].items():
        # Compact column representation
        cols = []
        for col in table_info['columns']:
            col_str = f"{col['name']}({col['type'][:10]})"  # Truncate type
            if col['primary_key']:
                col_str += "*PK"
            if not col['nullable']:
                col_str += "!NULL"
            cols.append(col_str)
        
        # Add foreign keys inline
        fks = []
        for fk in table_info['foreign_keys']:
            fks.append(f"{fk['constrained_columns'][0]}→{fk['referred_table']}")
        
        table_compact = f"{table_name}[{','.join(cols)}]"
        if fks:
            table_compact += f"FK:{','.join(fks)}"
        
        compact.append(table_compact)
    
    return "\n".join(compact)

def identify_business_domain(schema_info):
    """Identify business domain from schema_info (simple heuristic)"""
    # Heuristic: look for key tables
    tables = set(schema_info.get('tables', {}).keys())
    if any(t.startswith('hr_') or t in ['employees', 'attendance_records', 'leave_requests'] for t in tables):
        return 'hr'
    if any(t.startswith('inv_') or t in ['products', 'sales', 'stock_levels'] for t in tables):
        return 'inventory'
    if any(t.startswith('core_fin_') or t in ['accounts', 'transactions', 'payments'] for t in tables):
        return 'financial'
    return 'general'

def generate_domain_specific_prompt(question, schema_info, relevant_tables, domain=None):
    # Use the passed domain parameter, don't detect it again
    if domain is None:
        domain = identify_business_domain(schema_info)
    domain_prompts = {
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
        }
    }
    domain_info = domain_prompts.get(domain, {})
    base_prompt = f"""
    You are an expert SQL analyst for a {domain} system.
    {domain_info.get('context', '')}
    
    IMPORTANT: Use ONLY the actual table names and column names from the schema below. Do NOT use placeholder names like 'your_table_name' or 'table_name'.
    
    Schema (compact format):
    {format_compact_schema({
        "tables": {t: schema_info['tables'][t] for t in relevant_tables if t in schema_info['tables']}
        # relationships omitted for token efficiency
    })}
    
    Common patterns for this domain:
    {chr(10).join(domain_info.get('common_patterns', []))}
    
    Question: \"{question}\"
    
    Use only the schema above. Output only the SQL query with actual table and column names.
    """
    return base_prompt

def generate_sql(question, schema, database, error_context=None):
    """Placeholder for SQL generation logic. Returns None."""
    # TODO: Integrate with your LLM or SQL generation logic
    return None

def generate_conservative_sql(question, database):
    """Placeholder for conservative SQL generation. Returns None."""
    # TODO: Implement a conservative SQL generation strategy
    return None

def execute_query_with_recovery(question, database=None, max_retries=3):
    """Execute query with intelligent error recovery"""
    last_error = None
    for attempt in range(max_retries):
        if attempt == 0:
            # First attempt: use filtered schema
            schema = get_relevant_schema(question, database)
            # TODO: Replace with your actual SQL generation function
            sql = generate_sql(question, schema, database)
        elif attempt == 1:
            # Second attempt: use full schema with error context
            schema = get_database_schema(database)
            sql = generate_sql(question, schema, database, error_context=last_error)
        else:
            # Final attempt: use conservative approach
            # TODO: Replace with your actual conservative SQL generation function
            sql = generate_conservative_sql(question, database)
        
        if not sql:
            continue
        
        df, error = execute_query(sql, database)
        
        if df is not None:
            return df, sql, None
        
        last_error = str(error)
        
        # Specific error handling
        if "1054" in last_error or "no such column" in last_error.lower():
            # Schema mismatch - will retry with different schema
            continue
        elif "syntax error" in last_error.lower():
            # Syntax error - try conservative approach
            continue
        else:
            # Other errors - return immediately
            return None, sql, error
    
    return None, sql, last_error

def validate_and_sanitize_results(df, question):
    """Validate and sanitize query results"""
    if df is None or df.empty:
        return df, "No results found"
    
    # Check for reasonable result size
    if len(df) > 10000:
        return df.head(1000), f"Results truncated to 1000 rows (original: {len(df)})"
    
    # Sanitize sensitive data
    sensitive_columns = ['password', 'secret', 'token', 'key']
    for col in df.columns:
        if any(sens in col.lower() for sens in sensitive_columns):
            df[col] = '[REDACTED]'
    
    # Handle data types for JSON serialization
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            # Handle NaT values in datetime columns
            df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None)
        elif df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    
    return df, "Success"

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    if 'start_time' in g:
        elapsed_time = time.time() - g.start_time
        logging.info(f"Request to {request.path} completed in {elapsed_time:.4f} seconds.")
    return response

@app.route('/')
def home():
    init_session()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Initialize session
        init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Data privacy: block password/sensitive info requests
        sensitive_keywords = ['password', 'passwd', 'secret', 'credential', 'token']
        if any(word in question.lower() for word in sensitive_keywords):
            content = "Sorry, I can't provide sensitive information such as passwords."
            add_to_conversation_history(question, content, "")
            return jsonify({
                "type": "text",
                "content": content,
                "sql": "",
                "conversation_count": len(session.get('conversation_history', []))
            })

        q_lower = question.lower()
        logging.info(f"Received question: '{question}' for database '{DB_CONFIG['database']}'")
        
        # Handle relationship diagram requests
        if 'relationship' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower):
            diagram = generate_relationship_diagram(DB_CONFIG['database'])
            if diagram:
                filename = save_image_to_file(diagram, "relationship_diagram", session.get('id'))
                if filename and 'generated_images' in session:
                    session['generated_images'].append(filename)
                    session.modified = True
                add_to_conversation_history(question, {
                    "type": "diagram",
                    "content": filename,
                    "title": f"Database Relationships - {DB_CONFIG['database']}",
                    "sql": ""
                }, "")
                return jsonify({
                    "type": "diagram",
                    "content": filename,
                    "title": f"Database Relationships - {DB_CONFIG['database']}",
                    "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })
            else:
                content = "I couldn't generate a relationship diagram. This might be because there are no foreign key relationships in the database, or the database schema couldn't be retrieved."
                add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text",
                    "content": content,
                    "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })
        
        # Handle table schema diagram requests
        if 'table' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower or 'schema' in q_lower):
            schema_info = get_database_schema(DB_CONFIG['database'])
            if schema_info:
                for table_name in schema_info['tables']:
                    if table_name.lower() in q_lower:
                        diagram = generate_table_schema_diagram(table_name, DB_CONFIG['database'])
                        if diagram:
                            filename = save_image_to_file(diagram, f"schema_diagram_{table_name}", session.get('id'))
                            if filename and 'generated_images' in session:
                                session['generated_images'].append(filename)
                                session.modified = True
                            add_to_conversation_history(question, {
                                "type": "diagram",
                                "content": filename,
                                "title": f"Table Schema - {table_name}",
                                "sql": ""
                            }, "")
                            return jsonify({
                                "type": "diagram",
                                "content": filename,
                                "title": f"Table Schema - {table_name}",
                                "sql": "",
                                "conversation_count": len(session.get('conversation_history', []))
                            })
            
            if schema_info and schema_info['tables']:
                content = "I can generate schema diagrams for specific tables. Please specify which table you'd like to see, for example: 'draw diagram for users table' or 'show schema diagram for orders table'.\n\nAvailable tables:\n" + "\n".join([f"• {table}" for table in schema_info['tables'].keys()])
                add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text",
                    "content": content,
                    "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

        # Step 1: Generate SQL (token-optimized)
        sql = generate_sql_token_optimized(question, DB_CONFIG['database'])

        if sql:
            # Step 2: Execute query and handle errors with a retry
            df, err = execute_query(sql, DB_CONFIG['database'])

            if err:
                error_message = str(err)
                # MySQL error code 1054 is for "Unknown column"
                if "1054" in error_message or "no such column" in error_message.lower():
                    logging.warning(f"SQL query failed with a schema error. Retrying generation. Error: {error_message}")
                    sql = generate_sql_token_optimized(question, DB_CONFIG['database'], error_context=error_message)
                    if sql:
                        df, err = execute_query(sql, DB_CONFIG['database'])
            
            # If there's still an error after the potential retry, show it
            if err:
                error_msg = f"There was an error executing the query. The database returned: '{str(err)}'"
                add_to_conversation_history(question, error_msg, sql or "")
                return jsonify({
                    "type": "text",
                    "content": error_msg,
                    "sql": sql,
                    "conversation_count": len(session.get('conversation_history', []))
                })

            if df is not None:
                # This block runs if the query was successful (either first try or retry)
                # Step 3: Determine response type (without AI)
                if "pie chart" in q_lower or "pie diagram" in q_lower:
                    response_type = "pie"
                elif "bar chart" in q_lower or "bar diagram" in q_lower:
                    response_type = "bar"
                elif "line chart" in q_lower or "line diagram" in q_lower:
                    response_type = "line"
                elif "scatter plot" in q_lower or "scatter chart" in q_lower or "scatter diagram" in q_lower:
                    response_type = "scatter"
                elif "card" in q_lower or "metric" in q_lower:
                    response_type = "card"
                else:
                    response_type = "table"
                
                # Step 4: Format response
                if response_type == "card":
                    content = format_card_response(df)
                    if content:
                        add_to_conversation_history(question, {
                            "type": "card",
                            "content": content,
                            "sql": sql or ""
                        }, sql or "")
                        return jsonify({
                            "type": "card", "content": content, "sql": sql,
                            "conversation_count": len(session.get('conversation_history', []))
                        })
                
                elif response_type in ("bar", "line", "pie", "scatter"):
                    chart = generate_visualization(df, response_type)
                    if chart:
                        filename = save_image_to_file(chart, response_type, session.get('id'))
                        if filename and 'generated_images' in session:
                            session['generated_images'].append(filename)
                            session.modified = True
                        add_to_conversation_history(question, {
                            "type": "chart",
                            "content": filename,
                            "chart_type": response_type,
                            "data_preview": df.head(5).to_dict(orient='records'),
                            "sql": sql or ""
                        }, sql or "")
                        return jsonify({
                            "type": "chart", "chart_type": response_type, "content": filename, "sql": sql,
                            "data_preview": df.head(5).to_dict(orient='records'),
                            "conversation_count": len(session.get('conversation_history', []))
                        })

                # Fallback for failed charts or text/table responses
                is_doc_with_sql = any(word in q_lower for word in ['list']) and \
                                        any(word in q_lower for word in ['table', 'column', 'database'])

                if response_type == "text":
                    if is_doc_with_sql:
                        content = format_database_documentation_response(df, question)
                    else:
                        content = format_text_response(df, question)

                    add_to_conversation_history(question, {
                        "type": "text",
                        "content": content,
                        "sql": sql or ""
                    }, sql or "")
                    return jsonify({
                        "type": "text", "content": content, "sql": sql,
                        "conversation_count": len(session.get('conversation_history', []))
                    })

                # Default to table for other cases
                # Handle datetime serialization issues
                try:
                    content = df.to_dict(orient='records')
                except Exception as e:
                    logging.warning(f"Error converting DataFrame to dict: {e}")
                    # Fallback: convert to string representation
                    content = df.to_string(index=False)
                
                add_to_conversation_history(question, {
                    "type": "table",
                    "content": content,
                    "sql": sql or ""
                }, sql or "")
                return jsonify({
                    "type": "table",
                    "content": content,
                    "sql": sql,
                    "conversation_count": len(session.get('conversation_history', []))
                })

        # Step 5: Handle non-SQL queries (documentation, conversational)
        else:
            is_doc_keyword = any(word in q_lower for word in [
                'table', 'column', 'schema', 'structure', 'database', 'list', 
                'describe', 'documentation', 'metadata'
            ])
            
            if "detailed documentation" in q_lower or "full documentation" in q_lower:
                content = handle_full_documentation_request(DB_CONFIG['database'])
                add_to_conversation_history(question, "Generated full documentation.", "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            if is_doc_keyword:
                content = handle_documentation_query(question, DB_CONFIG['database'])
                add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            # Fallback to conversational LLM
            start_time = time.time()
            schema_info = get_database_schema(DB_CONFIG['database'])
            conversation_context = get_conversation_context()
            
            schema_overview = ""
            if schema_info:
                schema_overview += f"Database name: {DB_CONFIG['database']}\n"
                schema_overview += "Tables:\n"
                for t in schema_info['tables']:
                    schema_overview += f"- {t}\n"
            
            prompt = f"""
            You are a helpful and intelligent assistant for a database chat application. Your goal is to help non-technical users get information from a database without them needing to know anything about its structure.

            The user asked the following question: "{question}"

            An attempt to automatically generate a database query for this question failed, likely because the question was too general or ambiguous.

            Your task is to respond to the user conversationally.
            Follow these rules STRICTLY:
            1.  **DO NOT** use the words "table," "column," "query," or any other technical database terms.
            2.  Politely inform the user that their request is a bit too general and that you need more specific information to help.
            3.  Suggest some possible areas of interest in a user-friendly way. Use the provided database overview to understand the business concepts available.
            4.  Keep your response concise and friendly.

            Here is a high-level overview of the available data:
            {schema_overview}
            
            If the question is a greeting, respond politely.
            If the question is about the database, answer using the context above.
            If the question refers to previous conversation, acknowledge the context.
            If the question cannot be answered, politely say so.
            Respond concisely and conversationally.
            """
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=150
                )
                logging.info(f"OpenAI fallback prompt:\n{prompt}")
                if response.usage:
                    logging.info(f"OpenAI API usage for fallback response: {response.usage.prompt_tokens} prompt tokens, {response.usage.completion_tokens} completion tokens.")
                content = (response.choices[0].message.content or "").strip()
                logging.info(f"Fallback LLM response generated in {time.time() - start_time:.4f} seconds.")
            except Exception as e:
                logging.error(f"Error generating fallback LLM response: {e}")
                content = "I'm sorry, I couldn't answer your question."
            
            add_to_conversation_history(question, content, "")
            
            return jsonify({
                "type": "text",
                "content": content,
                "sql": "",
                "conversation_count": len(session.get('conversation_history', []))
            })

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        error_msg = f"An error occurred: {str(e)}"
        question_text = locals().get('question', 'N/A')
        add_to_conversation_history(question_text, error_msg, "")
        return jsonify({
            "type": "text",
            "content": error_msg,
            "sql": "",
            "conversation_count": len(session.get('conversation_history', []))
        }), 500

@app.route('/conversation_history', methods=['GET'])
def get_conversation_history():
    """Get the current conversation history"""
    init_session()
    return jsonify({
        "conversation_history": session.get('conversation_history', []),
        "current_database": DB_CONFIG['database']
    })

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history"""
    init_session()
    session['conversation_history'] = []
    session.modified = True
    delete_session_images()
    return jsonify({"message": "Conversation history cleared"})

@app.route('/cleanup_images', methods=['POST'])
def cleanup_images():
    """Manually trigger cleanup of old images"""
    try:
        cleanup_old_images()
        return jsonify({"message": "Image cleanup completed"})
    except Exception as e:
        logging.error(f"Error during manual image cleanup: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/session_info', methods=['GET'])
def session_info():
    """Get information about the current session"""
    init_session()
    return jsonify({
        "session_id": session.get('id'),
        "generated_images": session.get('generated_images', []),
        "conversation_count": len(session.get('conversation_history', [])),
        "current_database": DB_CONFIG['database']
    })

@app.route('/batch_chat', methods=['POST'])
def batch_chat():
    try:
        init_session()
        data = request.json
        if not data or 'questions' not in data or not isinstance(data['questions'], list):
            return jsonify({"error": "Request must include a 'questions' list."}), 400
        responses = []
        schema_info = get_database_schema(DB_CONFIG['database'])
        for question in data['questions']:
            q = question.strip()
            if not q:
                responses.append({"type": "text", "content": "Empty question.", "sql": ""})
                continue
            # Data privacy check
            sensitive_keywords = ['password', 'passwd', 'secret', 'credential', 'token']
            if any(word in q.lower() for word in sensitive_keywords):
                responses.append({"type": "text", "content": "Sorry, I can't provide sensitive information such as passwords.", "sql": ""})
                continue
            # Token-optimized SQL generation
            sql = generate_sql_token_optimized(q, DB_CONFIG['database'])
            if sql:
                df, err = execute_query(sql, DB_CONFIG['database'])
                if err:
                    responses.append({"type": "text", "content": f"Error: {str(err)}", "sql": sql})
                elif df is not None:
                    response_type = determine_response_type(q, df.head(2).to_dict())
                    if response_type == "card":
                        content = format_card_response(df)
                        responses.append({"type": "card", "content": content, "sql": sql})
                    elif response_type in ("bar", "line", "pie", "scatter"):
                        chart = generate_visualization(df, response_type)
                        if chart:
                            filename = save_image_to_file(chart, response_type, session.get('id'))
                            if filename and 'generated_images' in session:
                                session['generated_images'].append(filename)
                                session.modified = True
                        responses.append({"type": "chart", "chart_type": response_type, "content": filename, "sql": sql, "data_preview": df.head(5).to_dict(orient='records')})
                    elif response_type == "text":
                        content = format_text_response(df, q)
                        responses.append({"type": "text", "content": content, "sql": sql})
                    else:
                        responses.append({"type": "table", "content": df.to_dict(orient='records'), "sql": sql})
                else:
                    responses.append({"type": "text", "content": "No data found.", "sql": sql})
            else:
                responses.append({"type": "text", "content": "Could not generate SQL for this question.", "sql": ""})
        return jsonify({"responses": responses})
    except Exception as e:
        logging.error(f"Error in batch_chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Clean up old images on startup
    cleanup_old_images()
    app.run(debug=True, port=5000)