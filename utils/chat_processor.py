#!/usr/bin/env python3
"""
Chat Processor Module
Handles chat processing logic, response type determination, and workflow orchestration
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatProcessor:
    """Handles chat processing logic and workflow orchestration"""
    
    def __init__(self):
        self.sensitive_keywords = ['password', 'passwd', 'secret', 'credential', 'token']
    
    def check_sensitive_content(self, question: str) -> bool:
        """Check if the question contains sensitive keywords"""
        return any(word in question.lower() for word in self.sensitive_keywords)
    
    def determine_response_type_from_keywords(self, question: str) -> str:
        """Determine response type based on keywords in the question"""
        q_lower = question.lower()
        
        if "pie chart" in q_lower or "pie diagram" in q_lower:
            return "pie"
        elif "bar chart" in q_lower or "bar diagram" in q_lower:
            return "bar"
        elif "line chart" in q_lower or "line diagram" in q_lower:
            return "line"
        elif "scatter plot" in q_lower or "scatter chart" in q_lower or "scatter diagram" in q_lower:
            return "scatter"
        elif "card" in q_lower or "metric" in q_lower:
            return "card"
        else:
            return "table"
    
    def is_documentation_query(self, question: str) -> bool:
        """Check if the question is asking for documentation"""
        q_lower = question.lower()
        doc_keywords = [
            'table', 'column', 'schema', 'structure', 'database', 'list', 
            'describe', 'documentation', 'metadata'
        ]
        return any(word in q_lower for word in doc_keywords)
    
    def is_diagram_request(self, question: str) -> Tuple[bool, str, Optional[str]]:
        """Check if the question is requesting a diagram and return type and table name if applicable"""
        q_lower = question.lower()
        
        # Check for relationship diagram requests
        if 'relationship' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower):
            return True, "relationship", None
        
        # Check for table schema diagram requests
        if 'table' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower or 'schema' in q_lower):
            # Try to extract table name from question
            # This is a simple approach - could be enhanced with NLP
            words = q_lower.split()
            for i, word in enumerate(words):
                if word in ['for', 'of', 'table'] and i + 1 < len(words):
                    potential_table = words[i + 1]
                    if potential_table not in ['diagram', 'draw', 'picture', 'schema', 'show']:
                        return True, "table_schema", potential_table
            return True, "table_schema", None
        
        return False, "", None
    
    def generate_fallback_response(self, question: str, schema_info: Dict[str, Any], database_name: str) -> str:
        """Generate a conversational fallback response when SQL generation fails"""
        start_time = time.time()
        
        schema_overview = ""
        if schema_info:
            schema_overview += f"Database name: {database_name}\n"
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
            return content
        except Exception as e:
            logging.error(f"Error generating fallback LLM response: {e}")
            return "I'm sorry, I couldn't answer your question."
    
    def process_sql_error(self, error_message: str, question: str, database: str, 
                         generate_sql_func, execute_query_func) -> Tuple[Optional[str], Optional[Any], Optional[str]]:
        """Handle SQL errors with retry logic"""
        # MySQL error code 1054 is for "Unknown column"
        if "1054" in error_message or "no such column" in error_message.lower():
            logging.warning(f"SQL query failed with a schema error. Retrying generation. Error: {error_message}")
            sql = generate_sql_func(question, database, error_context=error_message)
            if sql:
                df, err = execute_query_func(sql, database)
                return sql, df, str(err) if err else None
        
        return None, None, error_message
    
    def create_response_payload(self, response_type: str, content: Any, sql: str = "", 
                               chart_type: str = "", data_preview: Optional[List[Dict]] = None,
                               title: str = "") -> Dict[str, Any]:
        """Create a standardized response payload"""
        payload = {
            "type": response_type,
            "content": content,
            "sql": sql,
            "conversation_count": 0  # This will be set by the calling function
        }
        
        if chart_type:
            payload["chart_type"] = chart_type
        if data_preview is not None:
            payload["data_preview"] = data_preview
        if title:
            payload["title"] = title
            
        return payload

def get_chat_processor() -> ChatProcessor:
    """Get a singleton instance of ChatProcessor"""
    if not hasattr(get_chat_processor, '_instance'):
        get_chat_processor._instance = ChatProcessor()
    return get_chat_processor._instance 