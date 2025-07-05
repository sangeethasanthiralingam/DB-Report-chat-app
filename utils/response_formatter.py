#!/usr/bin/env python3
"""
Response Formatter Module
Handles response formatting, visualization generation, and natural language processing
"""

import logging
import time
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask
import matplotlib.pyplot as plt
from openai import OpenAI
from utils.data_processor import get_data_processor
from utils.database_manager import get_database_schema
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize data processor for JSON cleaning
data_processor = get_data_processor()

# Configure OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ResponseFormatter:
    """Handles response formatting and generation"""
    
    def __init__(self):
        self.data_processor = get_data_processor()
    
    def determine_response_type(self, question: str, data_preview: Optional[Dict] = None) -> str:
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
    
    def generate_visualization(self, df: pd.DataFrame, chart_type: str) -> Optional[str]:
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
    
    def generate_nl_from_data(self, question: str, df: pd.DataFrame) -> str:
        """Generate a natural language response from a DataFrame based on the user's question."""
        if df.empty:
            return "I couldn't find any information for your request."
            
        start_time = time.time()
        
        # Prepare the data preview for the prompt - sanitize first
        df_sanitized = self.data_processor.sanitize_dataframe_for_json(df)
        data_preview = df_sanitized.head(10).to_string(index=False)
        
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
            df_sanitized = self.data_processor.sanitize_dataframe_for_json(df)
            return f"I found the following information:\n\n{df_sanitized.to_string(index=False)}"
    
    def format_text_response(self, df: pd.DataFrame, question: str) -> str:
        """Format a textual answer from the DataFrame into natural language using an LLM."""
        if df.empty:
            return "I couldn't find any data matching your query. Please try rephrasing your question."
        
        # Use LLM to generate a natural language response from the data
        return self.generate_nl_from_data(question, df)
    
    def format_card_response(self, df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
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
    
    def format_database_documentation_response(self, df: pd.DataFrame, question: str) -> str:
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
        
        return self.format_text_response(df, question)
    
    def format_table_response(self, df: pd.DataFrame) -> Union[List[Dict[str, Any]], str]:
        """Format DataFrame as table response"""
        if df.empty:
            return "No data found."
        
        # Sanitize DataFrame before JSON conversion to handle NaT values
        try:
            df_sanitized = self.data_processor.sanitize_dataframe_for_json(df)
            return df_sanitized.to_dict(orient='records')
        except Exception as e:
            logging.warning(f"Error converting DataFrame to dict: {e}")
            # Fallback: convert to string representation
            return df.to_string(index=False)
    
    def handle_full_documentation_request(self, database: str) -> str:
        """Handle full documentation generation request"""
        start_time = time.time()
        from utils.database_manager import get_database_schema  # Import here to avoid circular imports
        
        schema_info = get_database_schema(database)
        if not schema_info:
            return "Sorry, I couldn't retrieve the schema."
        
        # Compose a detailed prompt for the LLM
        prompt = f"""
        You are a technical writer. Write a detailed, multi-section documentation (about 2000 words) for the database "{database}".
        Use the following schema information:
        {schema_info}
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
    
    def handle_documentation_query(self, question: str, database: str) -> str:
        """Handle database documentation queries with more natural responses"""
        q_lower = question.lower()
        
        from utils.database_manager import get_database_schema  # Import here to avoid circular imports
        
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

# Global response formatter instance
_response_formatter = None

def get_response_formatter() -> ResponseFormatter:
    """Get the global response formatter instance"""
    global _response_formatter
    if _response_formatter is None:
        _response_formatter = ResponseFormatter()
    return _response_formatter 