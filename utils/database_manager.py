import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict
import pymysql
from pymysql.cursors import DictCursor
import pandas as pd
from sqlalchemy import create_engine, inspect as sqla_inspect, text
from urllib.parse import quote_plus
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import networkx as nx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Load DB config from environment
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "root"),
    "database": os.getenv("DB_NAME", "db")
}

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Redis support (optional, for caching)
try:
    import redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    redis_client = None

# In-memory cache
DB_METADATA_CACHE = {}
CACHE_EXPIRY_MINUTES = 60
QUERY_CACHE_EXPIRY_SECONDS = 600  # 10 minutes
LLM_CACHE_EXPIRY_SECONDS = 3600   # 1 hour

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

def get_db_connection():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        cursorclass=DictCursor
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
        count_query = f"SELECT COUNT(*) as total FROM `{table_name}`"
        total_rows = pd.read_sql(text(count_query), engine).iloc[0]['total']
        if total_rows == 0:
            return []
        if total_rows <= max_rows:
            query = f"SELECT * FROM `{table_name}`"
        else:
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

def redis_get(key):
    if redis_client:
        try:
            schema_json = redis_client.get(key)
            import inspect
            if inspect.isawaitable(schema_json):
                raise RuntimeError("redis_get returned an awaitable, but this function is not async.")
            return schema_json
        except Exception as e:
            pass
    return None

def redis_set(key, value, ex=None):
    if redis_client:
        try:
            redis_client.set(key, value, ex=ex)
        except Exception as e:
            pass

def get_database_schema(database=None):
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
        engine = get_sqlalchemy_engine(database)
        inspector = sqla_inspect(engine)
        tables = inspector.get_table_names()
        for table in tables:
            columns = inspector.get_columns(table)
            column_info = []
            for col in columns:
                column_info.append({
                    "name": col['name'],
                    "type": str(col['type']),
                    "nullable": col['nullable'],
                    "primary_key": col.get('primary_key', False)
                })
            pks = inspector.get_pk_constraint(table)
            fks = inspector.get_foreign_keys(table)
            sample_data = []
            try:
                sample_data = get_smart_sample_data(table, engine, max_rows=2)
            except Exception as e:
                pass
            schema_info["tables"][table] = {
                "columns": column_info,
                "primary_key": pks.get('constrained_columns', []),
                "foreign_keys": fks,
                "sample_data": sample_data
            }
            for fk in fks:
                schema_info["relationships"].append({
                    "source_table": table,
                    "source_column": fk['constrained_columns'][0],
                    "target_table": fk['referred_table'],
                    "target_column": fk['referred_columns'][0]
                })
        try:
            redis_set(cache_key, json.dumps(schema_info, default=str), ex=CACHE_EXPIRY_MINUTES*60)
        except Exception as e:
            pass
        DB_METADATA_CACHE[cache_key] = {
            "schema": schema_info,
            "timestamp": datetime.now()
        }
        logging.info(f"Schema for '{database}' loaded in {time.time() - start_time:.4f} seconds.")
        return schema_info
    except Exception as e:
        logging.error(f"Error getting schema: {e}")
        return None

def get_relevant_schema(question, database=None):
    """Get only relevant parts of schema based on question, using business_terms.json for keyword mapping"""
    from utils.domain_analyzer import get_domain_analyzer
    analyzer = get_domain_analyzer()
    
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

def get_query_cache_key(sql, database=None):
    return f"queryres_{database or 'default'}_{hash(sql)}"

def execute_query(sql, database=None):
    """Execute SQL and return DataFrame and error, with Redis caching"""
    start_time = time.time()
    cache_key = get_query_cache_key(sql, database)
    # Try Redis cache first
    cached = redis_get(cache_key)
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

def generate_domain_specific_prompt(question, schema_info, relevant_tables, domain=None):
    from utils.domain_analyzer import get_domain_analyzer
    domain_analyzer = get_domain_analyzer()
    
    # Use the passed domain parameter, don't detect it again
    if domain is None:
        domain = domain_analyzer.identify_business_domain_from_schema(schema_info)
    
    domain_info = domain_analyzer.get_domain_prompt_context(domain)
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

def generate_sql_token_optimized(question, database=None, error_context=None):
    """Generate SQL using token-optimized approach with domain analysis"""
    from utils.domain_analyzer import get_domain_analyzer
    from utils.session_manager import get_session_manager
    
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info:
        return None
    
    session_manager = get_session_manager()
    conversation_context = session_manager.get_conversation_context(limit=1, truncate=100)
    
    # Step 1: Detect domain from the question using domain analyzer
    domain_analyzer = get_domain_analyzer()
    domain = domain_analyzer.detect_domain_from_question(question)
    logging.info(f"[DEBUG] Domain detected from question '{question}': {domain}")
    
    # Step 2: Find relevant tables within the detected domain
    relevant_tables = domain_analyzer.find_relevant_tables(question)
    relevant_columns = defaultdict(set)  # We don't need column-level matching for now
    
    logging.info(f"[DEBUG] Relevant tables found: {relevant_tables}")
    
    # Debug: Check if analyzer is working correctly
    logging.info(f"[DEBUG] Analyzer business terms sample: {list(domain_analyzer.business_terms.items())[:3]}")
    logging.info(f"[DEBUG] Analyzer keyword index sample: {dict(list(domain_analyzer.keyword_index.items())[:5])}")
    
    # If no relevant tables found, try to find tables based on the detected domain
    if not relevant_tables and domain != 'general':
        logging.info(f"[DEBUG] No relevant tables found, searching for {domain} domain tables")
        # Get all tables from the schema
        all_tables = list(schema_info['tables'].keys())
        relevant_tables = domain_analyzer.get_fallback_tables_for_domain(domain, all_tables)
        logging.info(f"[DEBUG] Found {domain} domain tables: {relevant_tables}")
    
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

# Export constants and functions for use in other modules
__all__ = [
    'get_database_schema', 'get_relevant_schema', 'execute_query',
    'generate_relationship_diagram', 'generate_table_schema_diagram',
    'format_compact_schema', 'generate_domain_specific_prompt',
    'redis_get', 'redis_set', 'LLM_CACHE_EXPIRY_SECONDS', 'DB_CONFIG',
    'generate_sql_token_optimized'
] 