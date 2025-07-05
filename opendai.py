from flask import Flask, request, jsonify, render_template, session, g, Response
import pandas as pd
import json
import os
from flask_session import Session
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates', static_folder='static')

# Custom JSON encoder to handle pandas NaT values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if pd.isna(obj):  # Handle NaT and NaN values
            return None
        elif hasattr(obj, 'isoformat'):  # Handle datetime objects
            return obj.isoformat()
        return super().default(obj)

# Configure Flask JSON handling
try:
    app.json_provider_class = type('CustomJSONProvider', (app.json_provider_class,), {
        'default': lambda self, obj: CustomJSONEncoder().default(obj)
    })
except:
    pass

# Configure Flask-Session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Import utility modules
from utils.domain_analyzer import get_domain_analyzer
from utils.data_processor import get_data_processor
from utils.session_manager import get_session_manager
from utils.response_formatter import get_response_formatter
from utils.database_manager import (
    get_database_schema, get_relevant_schema, execute_query, 
    generate_relationship_diagram, generate_table_schema_diagram,
    format_compact_schema, generate_domain_specific_prompt,
    redis_get, redis_set, LLM_CACHE_EXPIRY_SECONDS, DB_CONFIG,
    generate_sql_token_optimized
)
from utils.chat_processor import get_chat_processor

# Initialize utility modules
domain_analyzer = get_domain_analyzer()
data_processor = get_data_processor()
session_manager = get_session_manager()
response_formatter = get_response_formatter()
chat_processor = get_chat_processor()

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
    session_manager.init_session()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat() -> tuple[Response, int] | Response:
    try:
        session_manager.init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Data privacy: block password/sensitive info requests
        if chat_processor.check_sensitive_content(question):
            content = "Sorry, I can't provide sensitive information such as passwords."
            session_manager.add_to_conversation_history(question, content, "")
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
                filename = session_manager.save_image_to_file(diagram, "relationship_diagram", session.get('id'))
                if filename and 'generated_images' in session:
                    session['generated_images'].append(filename)
                    session.modified = True
                session_manager.add_to_conversation_history(question, {
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
                session_manager.add_to_conversation_history(question, content, "")
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
                            filename = session_manager.save_image_to_file(diagram, f"schema_diagram_{table_name}", session.get('id'))
                            if filename and 'generated_images' in session:
                                session['generated_images'].append(filename)
                                session.modified = True
                            session_manager.add_to_conversation_history(question, {
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
                session_manager.add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text",
                    "content": content,
                    "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

        # Generate SQL (token-optimized)
        sql = generate_sql_token_optimized(question, DB_CONFIG['database'])

        if sql:
            # Execute query and handle errors with a retry
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
                session_manager.add_to_conversation_history(question, error_msg, sql or "")
                return jsonify({
                    "type": "text",
                    "content": error_msg,
                    "sql": sql,
                    "conversation_count": len(session.get('conversation_history', []))
                })

            if df is not None:
                # Determine response type
                if "pie chart" in q_lower or "pie diagram" in q_lower:
                    response_type = "pie"
                elif "stack chart" in q_lower or "stacked chart" in q_lower or "stacked bar" in q_lower:
                    response_type = "stack"
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
                
                # Format response
                if response_type == "card":
                    content = response_formatter.format_card_response(df)
                    if content:
                        session_manager.add_to_conversation_history(question, {
                            "type": "card",
                            "content": content,
                            "sql": sql or ""
                        }, sql or "")
                        return jsonify({
                            "type": "card", "content": content, "sql": sql,
                            "conversation_count": len(session.get('conversation_history', []))
                        })
                    else:
                        # Fallback to table if card generation fails
                        content = data_processor.dataframe_to_json_safe(df)
                        session_manager.add_to_conversation_history(question, {
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
                
                elif response_type in ("bar", "line", "pie", "scatter", "stack"):
                    chart = response_formatter.generate_visualization(df, response_type)
                    if chart:
                        filename = session_manager.save_image_to_file(chart, response_type, session.get('id'))
                        if filename and 'generated_images' in session:
                            session['generated_images'].append(filename)
                            session.modified = True
                        # Sanitize DataFrame for data preview
                        data_preview = data_processor.dataframe_to_json_safe(df.head(5)) if not df.empty else []
                        session_manager.add_to_conversation_history(question, {
                            "type": "chart",
                            "content": filename,
                            "chart_type": response_type,
                            "data_preview": data_preview,
                            "sql": sql or ""
                        }, sql or "")
                        return jsonify({
                            "type": "chart", "chart_type": response_type, "content": filename, "sql": sql,
                            "data_preview": data_preview,
                            "conversation_count": len(session.get('conversation_history', []))
                        })
                    else:
                        # Fallback to table if chart generation fails
                        df_sanitized = data_processor.sanitize_dataframe_for_json(df)
                        content = df_sanitized.to_dict(orient='records') if not df_sanitized.empty else []
                        session_manager.add_to_conversation_history(question, {
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

                # Fallback for failed charts or text/table responses
                is_doc_with_sql = any(word in q_lower for word in ['list']) and \
                                        any(word in q_lower for word in ['table', 'column', 'database'])

                if response_type == "text":
                    if is_doc_with_sql:
                        content = response_formatter.format_database_documentation_response(df, question)
                    else:
                        content = response_formatter.format_text_response(df, question)

                    session_manager.add_to_conversation_history(question, {
                        "type": "text",
                        "content": content,
                        "sql": sql or ""
                    }, sql or "")
                    return jsonify({
                        "type": "text", "content": content, "sql": sql,
                        "conversation_count": len(session.get('conversation_history', []))
                    })

                # Default to table for other cases
                try:
                    content = data_processor.dataframe_to_json_safe(df)
                except Exception as e:
                    logging.warning(f"Error converting DataFrame to dict: {e}")
                    content = df.to_string(index=False) if not df.empty else ""
                
                session_manager.add_to_conversation_history(question, {
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

        # Handle non-SQL queries (documentation, conversational)
        else:
            is_doc_keyword = any(word in q_lower for word in [
                'table', 'column', 'schema', 'structure', 'database', 'list', 
                'describe', 'documentation', 'metadata'
            ])
            
            if "detailed documentation" in q_lower or "full documentation" in q_lower:
                content = response_formatter.handle_full_documentation_request(DB_CONFIG['database'])
                session_manager.add_to_conversation_history(question, "Generated full documentation.", "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            if is_doc_keyword:
                content = response_formatter.handle_documentation_query(question, DB_CONFIG['database'])
                session_manager.add_to_conversation_history(question, content, "")
                return jsonify({
                    "type": "text", "content": content, "sql": "",
                    "conversation_count": len(session.get('conversation_history', []))
                })

            # Fallback to conversational LLM
            schema_info = get_database_schema(DB_CONFIG['database'])
            if schema_info:
                content = chat_processor.generate_fallback_response(question, schema_info, DB_CONFIG['database'])
            else:
                content = "I'm sorry, I couldn't retrieve the database schema to help answer your question."
            
            session_manager.add_to_conversation_history(question, content, "")
            
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
        session_manager.add_to_conversation_history(question_text, error_msg, "")
        return jsonify({
            "type": "text",
            "content": error_msg,
            "sql": "",
            "conversation_count": len(session.get('conversation_history', []))
        }), 500
    
    # Fallback return to satisfy type checker (should never be reached)
    return jsonify({
        "type": "text",
        "content": "An unexpected error occurred",
        "sql": "",
        "conversation_count": len(session.get('conversation_history', []))
    }), 500

@app.route('/conversation_history', methods=['GET'])
def get_conversation_history():
    """Get the current conversation history"""
    session_manager.init_session()
    return jsonify({
        "conversation_history": session_manager.get_conversation_history(),
        "current_database": DB_CONFIG['database']
    })

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history"""
    session_manager.init_session()
    session_manager.clear_conversation_history()
    return jsonify({"message": "Conversation history cleared"})

@app.route('/cleanup_images', methods=['POST'])
def cleanup_images():
    """Manually trigger cleanup of old images"""
    try:
        session_manager.cleanup_old_images()
        return jsonify({"message": "Image cleanup completed"})
    except Exception as e:
        logging.error(f"Error during image cleanup: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/session_info', methods=['GET'])
def session_info():
    """Get information about the current session"""
    session_manager.init_session()
    return jsonify(session_manager.get_session_info())

@app.route('/generate_static_chart', methods=['POST'])
def generate_static_chart():
    """Generate a static chart image from data"""
    try:
        session_manager.init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        chart_type = data.get('chart_type', 'bar')
        chart_data = data.get('data', [])
        
        if not chart_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Convert data to DataFrame
        df = pd.DataFrame(chart_data)
        
        # Generate the chart using the response formatter
        chart_image = response_formatter.generate_visualization(df, chart_type)
        
        if chart_image:
            return jsonify({
                "success": True,
                "image_data": chart_image,
                "chart_type": chart_type
            })
        else:
            return jsonify({"error": "Failed to generate chart"}), 500
            
    except Exception as e:
        logging.error(f"Error generating static chart: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/batch_chat', methods=['POST'])
def batch_chat():
    try:
        session_manager.init_session()
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
            if chat_processor.check_sensitive_content(q):
                responses.append({"type": "text", "content": "Sorry, I can't provide sensitive information such as passwords.", "sql": ""})
                continue
            # Token-optimized SQL generation
            sql = generate_sql_token_optimized(q, DB_CONFIG['database'])
            if sql:
                df, err = execute_query(sql, DB_CONFIG['database'])
                if err:
                    responses.append({"type": "text", "content": f"Error: {str(err)}", "sql": sql})
                elif df is not None:
                    response_type = response_formatter.determine_response_type(q, df.head(2).to_dict())
                    if response_type == "card":
                        content = response_formatter.format_card_response(df)
                        responses.append({"type": "card", "content": content, "sql": sql})
                    elif response_type in ("bar", "line", "pie", "scatter", "stack"):
                        chart = response_formatter.generate_visualization(df, response_type)
                        filename = None
                        if chart:
                            filename = session_manager.save_image_to_file(chart, response_type, session.get('id'))
                            if filename and 'generated_images' in session:
                                session['generated_images'].append(filename)
                                session.modified = True
                        # Sanitize DataFrame for data preview
                        data_preview = data_processor.dataframe_to_json_safe(df.head(5)) if not df.empty else []
                        responses.append({"type": "chart", "chart_type": response_type, "content": filename or "", "sql": sql, "data_preview": data_preview})
                    elif response_type == "text":
                        content = response_formatter.format_text_response(df, q)
                        responses.append({"type": "text", "content": content, "sql": sql})
                    else:
                        # Sanitize DataFrame for table response
                        content = data_processor.dataframe_to_json_safe(df)
                        responses.append({"type": "table", "content": content, "sql": sql})
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
    session_manager.cleanup_old_images()
    app.run(debug=True, port=5000)