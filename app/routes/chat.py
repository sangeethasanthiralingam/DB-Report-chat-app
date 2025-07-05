from flask import Blueprint, request, jsonify, session
import logging
import pandas as pd

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for processing user questions"""
    try:
        from app.services.session_service import get_session_manager
        from app.services.chat_service import get_chat_service
        from app.services.database_service import get_database_service
        from app.services.response_service import get_response_service
        from app.services.data_service import get_data_service
        
        # Initialize services
        session_manager = get_session_manager()
        chat_service = get_chat_service()
        database_service = get_database_service()
        response_service = get_response_service()
        data_service = get_data_service()
        
        # Initialize session
        session_manager.init_session()
        
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Data privacy: block password/sensitive info requests
        if chat_service.check_sensitive_content(question):
            content = "Sorry, I can't provide sensitive information such as passwords."
            session_manager.add_to_conversation_history(question, content, "")
            return jsonify({
                "type": "text",
                "content": content,
                "sql": "",
                "conversation_count": len(session.get('conversation_history', []))
            })

        q_lower = question.lower()
        logging.info(f"Received question: '{question}' for database '{database_service.get_database_name()}'")
        
        # Handle relationship diagram requests
        if 'relationship' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower):
            return _handle_relationship_diagram(question, session_manager, database_service)
        
        # Handle table schema diagram requests
        if 'table' in q_lower and ('diagram' in q_lower or 'draw' in q_lower or 'picture' in q_lower or 'schema' in q_lower):
            return _handle_table_schema_diagram(question, session_manager, database_service)

        # Generate SQL and execute query
        sql = database_service.generate_sql_token_optimized(question)
        
        if sql:
            return _handle_sql_query(question, sql, session_manager, database_service, response_service, data_service)
        else:
            return _handle_non_sql_query(question, session_manager, database_service, chat_service, response_service)

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        error_msg = f"An error occurred: {str(e)}"
        question_text = locals().get('question', 'N/A')
        try:
            session_manager.add_to_conversation_history(question_text, error_msg, "")
        except:
            pass  # Ignore session errors in exception handler
        return jsonify({
            "type": "text",
            "content": error_msg,
            "sql": "",
            "conversation_count": len(session.get('conversation_history', []))
        }), 500

@chat_bp.route('/batch_chat', methods=['POST'])
def batch_chat():
    """Process multiple questions in batch"""
    try:
        from app.services.session_service import get_session_manager
        from app.services.chat_service import get_chat_service
        from app.services.database_service import get_database_service
        from app.services.response_service import get_response_service
        from app.services.data_service import get_data_service
        
        # Initialize services
        session_manager = get_session_manager()
        chat_service = get_chat_service()
        database_service = get_database_service()
        response_service = get_response_service()
        data_service = get_data_service()
        
        session_manager.init_session()
        data = request.json
        
        if not data or 'questions' not in data or not isinstance(data['questions'], list):
            return jsonify({"error": "Request must include a 'questions' list."}), 400
            
        responses = []
        schema_info = database_service.get_database_schema()
        
        for question in data['questions']:
            q = question.strip()
            if not q:
                responses.append({"type": "text", "content": "Empty question.", "sql": ""})
                continue
                
            # Data privacy check
            if chat_service.check_sensitive_content(q):
                responses.append({"type": "text", "content": "Sorry, I can't provide sensitive information such as passwords.", "sql": ""})
                continue
                
            # Generate SQL and process
            sql = database_service.generate_sql_token_optimized(q)
            if sql:
                df, err = database_service.execute_query(sql)
                if err:
                    responses.append({"type": "text", "content": f"Error: {str(err)}", "sql": sql})
                elif df is not None:
                    response = _process_query_result(q, df, sql, session_manager, response_service, data_service)
                    responses.append(response)
                else:
                    responses.append({"type": "text", "content": "No data found.", "sql": sql})
            else:
                responses.append({"type": "text", "content": "Could not generate SQL for this question.", "sql": ""})
                
        return jsonify({"responses": responses})
        
    except Exception as e:
        logging.error(f"Error in batch_chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

def _handle_relationship_diagram(question, session_manager, database_service):
    """Handle relationship diagram requests"""
    diagram = database_service.generate_relationship_diagram()
    if diagram:
        filename = session_manager.save_image_to_file(diagram, "relationship_diagram", session.get('id'))
        if filename and 'generated_images' in session:
            session['generated_images'].append(filename)
            session.modified = True
        session_manager.add_to_conversation_history(question, {
            "type": "diagram",
            "content": filename,
            "title": f"Database Relationships - {database_service.get_database_name()}",
            "sql": ""
        }, "")
        return jsonify({
            "type": "diagram",
            "content": filename,
            "title": f"Database Relationships - {database_service.get_database_name()}",
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

def _handle_table_schema_diagram(question, session_manager, database_service):
    """Handle table schema diagram requests"""
    schema_info = database_service.get_database_schema()
    if schema_info:
        for table_name in schema_info['tables']:
            if table_name.lower() in question.lower():
                diagram = database_service.generate_table_schema_diagram(table_name)
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
        
        if schema_info['tables']:
            content = "I can generate schema diagrams for specific tables. Please specify which table you'd like to see, for example: 'draw diagram for users table' or 'show schema diagram for orders table'.\n\nAvailable tables:\n" + "\n".join([f"• {table}" for table in schema_info['tables'].keys()])
            session_manager.add_to_conversation_history(question, content, "")
            return jsonify({
                "type": "text",
                "content": content,
                "sql": "",
                "conversation_count": len(session.get('conversation_history', []))
            })
    
    # If no schema info or no tables found
    content = "I couldn't retrieve the database schema to generate a table diagram."
    session_manager.add_to_conversation_history(question, content, "")
    return jsonify({
        "type": "text",
        "content": content,
        "sql": "",
        "conversation_count": len(session.get('conversation_history', []))
    })

def _handle_sql_query(question, sql, session_manager, database_service, response_service, data_service):
    """Handle SQL query execution and response formatting"""
    df, err = database_service.execute_query(sql)
    
    if err:
        error_message = str(err)
        # MySQL error code 1054 is for "Unknown column"
        if "1054" in error_message or "no such column" in error_message.lower():
            logging.warning(f"SQL query failed with a schema error. Retrying generation. Error: {error_message}")
            sql = database_service.generate_sql_token_optimized(question, error_context=error_message)
            if sql:
                df, err = database_service.execute_query(sql)
        
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
        return _process_query_result(question, df, sql, session_manager, response_service, data_service)
    
    # If df is None, return an error response
    error_msg = "No data returned from the query."
    session_manager.add_to_conversation_history(question, error_msg, sql or "")
    return jsonify({
        "type": "text",
        "content": error_msg,
        "sql": sql,
        "conversation_count": len(session.get('conversation_history', []))
    })

def _handle_non_sql_query(question, session_manager, database_service, chat_service, response_service):
    """Handle non-SQL queries (documentation, conversational)"""
    q_lower = question.lower()
    is_doc_keyword = any(word in q_lower for word in [
        'table', 'column', 'schema', 'structure', 'database', 'list', 
        'describe', 'documentation', 'metadata'
    ])
    
    if "detailed documentation" in q_lower or "full documentation" in q_lower:
        content = response_service.handle_full_documentation_request(database_service.get_database_name())
        session_manager.add_to_conversation_history(question, "Generated full documentation.", "")
        return jsonify({
            "type": "text", "content": content, "sql": "",
            "conversation_count": len(session.get('conversation_history', []))
        })

    if is_doc_keyword:
        content = response_service.handle_documentation_query(question, database_service.get_database_name())
        session_manager.add_to_conversation_history(question, content, "")
        return jsonify({
            "type": "text", "content": content, "sql": "",
            "conversation_count": len(session.get('conversation_history', []))
        })

    # Fallback to conversational LLM
    schema_info = database_service.get_database_schema()
    if schema_info:
        content = chat_service.generate_fallback_response(question, schema_info, database_service.get_database_name())
    else:
        content = "I'm sorry, I couldn't retrieve the database schema to help answer your question."
    
    session_manager.add_to_conversation_history(question, content, "")
    
    return jsonify({
        "type": "text",
        "content": content,
        "sql": "",
        "conversation_count": len(session.get('conversation_history', []))
    })

def _process_query_result(question, df, sql, session_manager, response_service, data_service):
    """Process query results and determine response type"""
    q_lower = question.lower()
    
    # Determine response type
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
    
    # Format response based on type
    if response_type == "card":
        content = response_service.format_card_response(df)
        if content:
            session_manager.add_to_conversation_history(question, {
                "type": "card",
                "content": content,
                "sql": sql or ""
            }, sql or "")
            return {
                "type": "card", 
                "content": content, 
                "sql": sql
            }
        else:
            # Fallback to table if card generation fails
            content = data_service.dataframe_to_json_safe(df)
            session_manager.add_to_conversation_history(question, {
                "type": "table",
                "content": content,
                "sql": sql or ""
            }, sql or "")
            return {
                "type": "table",
                "content": content,
                "sql": sql
            }
    
    elif response_type in ("bar", "line", "pie", "scatter"):
        chart = response_service.generate_visualization(df, response_type)
        if chart:
            filename = session_manager.save_image_to_file(chart, response_type, session.get('id'))
            if filename and 'generated_images' in session:
                session['generated_images'].append(filename)
                session.modified = True
            # Sanitize DataFrame for data preview
            data_preview = data_service.dataframe_to_json_safe(df.head(5)) if not df.empty else []
            session_manager.add_to_conversation_history(question, {
                "type": "chart",
                "content": filename,
                "chart_type": response_type,
                "data_preview": data_preview,
                "sql": sql or ""
            }, sql or "")
            return {
                "type": "chart", 
                "chart_type": response_type, 
                "content": filename, 
                "sql": sql,
                "data_preview": data_preview
            }
        else:
            # Fallback to table if chart generation fails
            df_sanitized = data_service.sanitize_dataframe_for_json(df)
            content = df_sanitized.to_dict(orient='records') if not df_sanitized.empty else []
            session_manager.add_to_conversation_history(question, {
                "type": "table",
                "content": content,
                "sql": sql or ""
            }, sql or "")
            return {
                "type": "table",
                "content": content,
                "sql": sql
            }

    # Handle text responses
    is_doc_with_sql = any(word in q_lower for word in ['list']) and \
                            any(word in q_lower for word in ['table', 'column', 'database'])

    if response_type == "text":
        if is_doc_with_sql:
            content = response_service.format_database_documentation_response(df, question)
        else:
            content = response_service.format_text_response(df, question)

        session_manager.add_to_conversation_history(question, {
            "type": "text",
            "content": content,
            "sql": sql or ""
        }, sql or "")
        return {
            "type": "text", 
            "content": content, 
            "sql": sql
        }

    # Default to table for other cases
    try:
        content = data_service.dataframe_to_json_safe(df)
    except Exception as e:
        logging.warning(f"Error converting DataFrame to dict: {e}")
        content = df.to_string(index=False) if not df.empty else ""
    
    session_manager.add_to_conversation_history(question, {
        "type": "table",
        "content": content,
        "sql": sql or ""
    }, sql or "")
    return {
        "type": "table",
        "content": content,
        "sql": sql
    } 