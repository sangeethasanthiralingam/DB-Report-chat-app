import openai
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
from sqlalchemy import create_engine, inspect, text
from urllib.parse import quote_plus 
import json
from datetime import datetime
from flask_session import Session
import networkx as nx
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Configure Flask-Session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# MySQL DB config
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root@1234",
    "database": "job_portal"  # Default database, can be changed
}

# Cache for database schema and metadata
DB_METADATA_CACHE = {}
CACHE_EXPIRY_MINUTES = 60

# Initialize session for conversation history
def init_session():
    """Initialize session with conversation history"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'current_database' not in session:
        session['current_database'] = DB_CONFIG['database']

def add_to_conversation_history(question, response, sql_query=""):
    """Add a conversation turn to the history"""
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    session['conversation_history'].append({
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'response': response,
        'sql_query': sql_query,
        'database': session.get('current_database', DB_CONFIG['database'])
    })
    
    # Keep only last 10 conversations to prevent session bloat
    if len(session['conversation_history']) > 10:
        session['conversation_history'] = session['conversation_history'][-10:]
    
    session.modified = True

def get_conversation_context():
    """Get recent conversation context for LLM"""
    if 'conversation_history' not in session or not session['conversation_history']:
        return ""
    
    # Get last 3 conversations for context
    recent_conversations = session['conversation_history'][-3:]
    context = "Recent conversation history:\n"
    
    for conv in recent_conversations:
        context += f"User: {conv['question']}\n"
        if conv['response']:
            # Truncate long responses
            response_preview = str(conv['response'])[:200] + "..." if len(str(conv['response'])) > 200 else str(conv['response'])
            context += f"Assistant: {response_preview}\n"
        context += "---\n"
    
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

def get_database_schema(database=None):
    """Get complete schema with table relationships and sample data"""
    start_time = time.time()
    cache_key = f"schema_{database or 'default'}"
    
    # Check cache
    if cache_key in DB_METADATA_CACHE:
        cached_data = DB_METADATA_CACHE[cache_key]
        if (datetime.now() - cached_data['timestamp']).total_seconds() < CACHE_EXPIRY_MINUTES * 60:
            logging.info(f"Schema for '{database}' loaded in {time.time() - start_time:.4f} seconds.")
            return cached_data['schema']
    
    schema_info = {
        "tables": {},
        "relationships": [],
        "timestamp": datetime.now()
    }
    
    try:
        engine = get_sqlalchemy_engine(database)
        inspector = inspect(engine)
        
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
            
            # Get sample data (first 3 rows)
            sample_data = []
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM `{table}` LIMIT 3"))
                    sample_data = [dict(row._mapping) for row in result]  # Updated for SQLAlchemy 2.0 compatibility
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
        
        # Cache the schema
        DB_METADATA_CACHE[cache_key] = {
            "schema": schema_info,
            "timestamp": datetime.now()
        }
        
        logging.info(f"Schema for '{database}' loaded in {time.time() - start_time:.4f} seconds.")
        return schema_info
    
    except Exception as e:
        logging.error(f"Error getting schema: {e}")
        return None

def generate_sql(question, database=None, error_context=None):
    """Generate SQL query using enhanced prompt with schema understanding and conversation context"""
    start_time = time.time()
    schema_info = get_database_schema(database)
    if not schema_info:
        return None
    
    # Get conversation context
    conversation_context = get_conversation_context()
    
    # Format schema information for the prompt
    schema_prompt = "Database Schema:\n"
    for table_name, table_info in schema_info['tables'].items():
        schema_prompt += f"\nTable: {table_name}\n"
        schema_prompt += "Columns:\n"
        for col in table_info['columns']:
            schema_prompt += f"- {col['name']} ({col['type']})"
            if col['primary_key']:
                schema_prompt += " [PRIMARY KEY]"
            schema_prompt += "\n"
        
        if table_info['primary_key']:
            schema_prompt += f"Primary Key: {', '.join(table_info['primary_key'])}\n"
        
        if table_info['foreign_keys']:
            schema_prompt += "Foreign Keys:\n"
            for fk in table_info['foreign_keys']:
                schema_prompt += f"- {fk['constrained_columns'][0]} → {fk['referred_table']}.{fk['referred_columns'][0]}\n"
        
        if table_info['sample_data']:
            schema_prompt += "Sample Data:\n"
            for row in table_info['sample_data'][:2]:  # Show first 2 rows
                schema_prompt += str(row) + "\n"
    
    # Add relationships
    if schema_info['relationships']:
        schema_prompt += "\nTable Relationships:\n"
        for rel in schema_info['relationships']:
            schema_prompt += f"{rel['source_table']}.{rel['source_column']} → {rel['target_table']}.{rel['target_column']}\n"
    
    # Build the enhanced prompt with conversation context
    context_prompt = ""
    if conversation_context:
        context_prompt = f"""
        {conversation_context}
        
        Consider the conversation history above when generating the SQL query.
        If the user is referring to previous results or asking follow-up questions,
        make sure to maintain consistency with the previous queries.
        """
    
    error_feedback_prompt = ""
    if error_context:
        error_feedback_prompt = f"""
        The previously generated query failed with the error: "{error_context}".
        This indicates that there is likely an issue with table or column names in the query.
        Please review the database schema and sample data provided above very carefully.
        You MUST ONLY use the tables and columns listed in the schema.
        Pay close attention to the sample data as it shows real examples of column names and content.
        Correct the query based on this feedback.
        """

    prompt = f"""
    You are an expert SQL analyst with deep knowledge of this database schema:
    {schema_prompt}
    
    {context_prompt}

    {error_feedback_prompt}
    
    For the following question: "{question}"
    
    Generate the most appropriate SQL query following these rules:
    1. Use only the tables and columns that exist in the schema
    2. Prefer JOINs over subqueries when possible
    3. Include all necessary WHERE clauses to answer the question
    4. For aggregate questions, include appropriate GROUP BY
    5. For time series data, use appropriate date functions
    6. If this is a follow-up question, consider the context from previous queries
    7. Return ONLY the SQL query, no explanations or markdown
    
    If the question cannot be answered with the available schema, return: 
    --ERROR: Question cannot be answered with available data
    
    SQL Query:
    """
    
    try:
        # Use the current OpenAI API format
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Updated to a valid model name
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500
        )
        sql = response['choices'][0]['message']['content'].strip() # type: ignore
        
        # Clean up the SQL
        if sql.startswith("```sql"):
            sql = sql[6:-3].strip()
        elif sql.startswith("```"):
            sql = sql[3:-3].strip()
        
        logging.info(f"SQL generated in {time.time() - start_time:.4f} seconds.")
        return sql if not sql.startswith("--ERROR") else None
    except Exception as e:
        logging.error(f"Error generating SQL: {e}")
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
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10
        )
        response_type = response['choices'][0]['message']['content'].strip().lower() # type: ignore
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
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048  # or higher, if your model/account allows
        )
        content = response['choices'][0]['message']['content'].strip() # type: ignore
        logging.info(f"Full documentation generated in {time.time() - start_time:.4f} seconds.")
        return content
    except Exception as e:
        return f"Error generating documentation: {e}"

def execute_query(sql, database=None):
    """Execute SQL and return DataFrame and error"""
    start_time = time.time()
    try:
        engine = get_sqlalchemy_engine(database)
        df = pd.read_sql(text(sql), engine)  # Wrap SQL with text() for SQLAlchemy 2.0
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
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250
        )
        content = response['choices'][0]['message']['content'].strip() # type: ignore
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

@app.route('/databases', methods=['GET'])
def list_databases():
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result if row[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
            return jsonify({"databases": databases})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_database', methods=['POST'])
def set_database():
    data = request.json
    if not data or 'database' not in data:
        return jsonify({"error": "Database name required"}), 400
    
    session['current_database'] = data['database']
    DB_CONFIG['database'] = data['database']
    # Clear schema cache for the new database
    cache_key = f"schema_{data['database']}"
    if cache_key in DB_METADATA_CACHE:
        del DB_METADATA_CACHE[cache_key]
    
    return jsonify({"message": f"Database changed to {data['database']}"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Initialize session
        init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        question = data.get('question', '').strip()
        database = data.get('database', session.get('current_database', DB_CONFIG['database']))

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

        # Update session database if provided
        if database != session.get('current_database'):
            session['current_database'] = database
            DB_CONFIG['database'] = database

        q_lower = question.lower()
        logging.info(f"Received question: '{question}' for database '{database}'")
        
        # Handle relationship diagram requests
        if 'relationship' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower):
            diagram = generate_relationship_diagram(database)
            if diagram:
                add_to_conversation_history(question, "Generated database relationship diagram", "")
                return jsonify({
                    "type": "diagram",
                    "content": diagram,
                    "title": f"Database Relationships - {database}",
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
            schema_info = get_database_schema(database)
            if schema_info:
                for table_name in schema_info['tables']:
                    if table_name.lower() in q_lower:
                        diagram = generate_table_schema_diagram(table_name, database)
                        if diagram:
                            add_to_conversation_history(question, f"Generated schema diagram for {table_name}", "")
                            return jsonify({
                                "type": "diagram",
                                "content": diagram,
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

        # Step 1: Generate SQL
        sql = generate_sql(question, database)

        if sql:
            # Step 2: Execute query and handle errors with a retry
            df, err = execute_query(sql, database)

            if err:
                error_message = str(err)
                # MySQL error code 1054 is for "Unknown column"
                if "1054" in error_message or "no such column" in error_message.lower():
                    logging.warning(f"SQL query failed with a schema error. Retrying generation. Error: {error_message}")
                    sql = generate_sql(question, database, error_context=error_message)
                    if sql:
                        df, err = execute_query(sql, database)
            
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
                # Step 3: Determine response type
                if "pie chart" in q_lower: response_type = "pie"
                elif "bar chart" in q_lower: response_type = "bar"
                elif "line chart" in q_lower: response_type = "line"
                else: response_type = determine_response_type(question, df.head(2).to_dict())
                
                # Step 4: Format response
                if response_type == "card":
                    content = format_card_response(df)
                    if content:
                        add_to_conversation_history(question, f"Key metrics: {[card['title'] for card in content]}", sql or "")
                        return jsonify({
                            "type": "card", "content": content, "sql": sql,
                            "conversation_count": len(session.get('conversation_history', []))
                        })
                
                elif response_type in ("bar", "line", "pie", "scatter"):
                    chart = generate_visualization(df, response_type)
                    if chart:
                        add_to_conversation_history(question, f"Generated {response_type} chart", sql or "")
                        return jsonify({
                            "type": "chart", "chart_type": response_type, "content": chart, "sql": sql,
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

                    add_to_conversation_history(question, content, sql or "")
                    return jsonify({
                        "type": "text", "content": content, "sql": sql,
                        "conversation_count": len(session.get('conversation_history', []))
                    })

                # Default to table for other cases
                add_to_conversation_history(question, "Query results in table format", sql or "")
                return jsonify({
                    "type": "table",
                    "content": df.to_dict(orient='records'),
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
                content = handle_full_documentation_request(database)
                add_to_conversation_history(question, "Generated full documentation.", "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            if is_doc_keyword:
                content = handle_documentation_query(question, database)
                add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            # Fallback to conversational LLM
            start_time = time.time()
            schema_info = get_database_schema(database)
            conversation_context = get_conversation_context()
            
            schema_overview = ""
            if schema_info:
                schema_overview += f"Database name: {database}\n"
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
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=150
                )
                content = response['choices'][0]['message']['content'].strip() # type: ignore
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
        "current_database": session.get('current_database', DB_CONFIG['database'])
    })

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history"""
    init_session()
    session['conversation_history'] = []
    session.modified = True
    return jsonify({"message": "Conversation history cleared"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)