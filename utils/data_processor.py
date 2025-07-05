import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json


class DataProcessor:
    """Handles data formatting, sanitization, and processing for the application."""
    
    def __init__(self):
        """Initialize the data processor."""
        pass
    
    def sanitize_dataframe_for_json(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize DataFrame to ensure it can be safely converted to JSON."""
        if df is None or df.empty:
            return df
        
        # Create a copy to avoid modifying the original
        df_sanitized = df.copy()
        
        # Handle datetime columns and NaT values
        for col in df_sanitized.columns:
            if df_sanitized[col].dtype == 'datetime64[ns]':
                # Convert NaT values to None and format datetime objects
                df_sanitized[col] = df_sanitized[col].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else None
                )
            elif df_sanitized[col].dtype == 'object':
                # Handle object columns that might contain NaT or other problematic values
                df_sanitized[col] = df_sanitized[col].apply(
                    lambda x: str(x) if pd.notna(x) else None
                )
            elif pd.api.types.is_numeric_dtype(df_sanitized[col]):
                # Handle numeric columns with NaN values
                df_sanitized[col] = df_sanitized[col].apply(
                    lambda x: float(x) if pd.notna(x) else None
                )
        
        return df_sanitized
    
    def validate_and_sanitize_results(self, df: pd.DataFrame, question: str) -> Tuple[pd.DataFrame, str]:
        """Validate and sanitize query results."""
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
    
    def format_compact_schema(self, schema_info: Dict[str, Any]) -> str:
        """Format schema in compact, token-efficient way."""
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
    
    def format_card_response(self, df: pd.DataFrame) -> Optional[List[Dict[str, Any]]]:
        """Format key metrics in card style."""
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
        """Format database documentation responses in a more user-friendly way."""
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
    
    def format_text_response(self, df: pd.DataFrame, question: str) -> str:
        """Format a textual answer from the DataFrame into natural language using an LLM."""
        if df.empty:
            return "I couldn't find any data matching your query. Please try rephrasing your question."
        
        # Use LLM to generate a natural language response from the data
        return self.generate_nl_from_data(question, df)
    
    def generate_nl_from_data(self, question: str, df: pd.DataFrame) -> str:
        """Generate a natural language response from a DataFrame based on the user's question."""
        if df.empty:
            return "I couldn't find any information for your request."
        
        # Prepare the data preview for the prompt - sanitize first
        df_sanitized = self.sanitize_dataframe_for_json(df)
        data_preview = df_sanitized.head(10).to_string(index=False)
        
        # For now, return a simple formatted response
        # In the future, this could be enhanced with LLM integration
        if df.shape[0] == 1:
            if df.shape[1] == 1:
                return f"I found: {df.iloc[0,0]}"
            else:
                return f"I found {df.shape[1]} pieces of information: " + ", ".join([f"{col}: {df.iloc[0, i]}" for i, col in enumerate(df.columns)])
        else:
            return f"I found {df.shape[0]} records with {df.shape[1]} columns each."
    
    def clean_for_json(self, obj: Any) -> Any:
        """Clean response object to handle NaT values for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self.clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_for_json(item) for item in obj]
        elif pd.isna(obj):  # Handle NaT and NaN values
            return None
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        else:
            return obj
    
    def extract_relevant_tables_columns(self, question: str, schema_info: Dict[str, Any]) -> Tuple[set, Dict[str, set]]:
        """Extract relevant tables and columns from the question using simple keyword matching."""
        from collections import defaultdict
        
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


# Global instance for easy access
_data_processor = None

def get_data_processor() -> DataProcessor:
    """Get or create the global data processor instance."""
    global _data_processor
    if _data_processor is None:
        _data_processor = DataProcessor()
    return _data_processor 