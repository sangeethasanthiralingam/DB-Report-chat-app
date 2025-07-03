# Database Analytics Chat App

## Overview
This is a Flask-based web application that allows users to interact with a database using natural language. The app leverages OpenAI's GPT models to translate user questions into SQL, execute them, and present results as text, tables, charts, or diagrams. It also provides database documentation and schema exploration features.

---

## Features
- **Natural Language to SQL**: Ask questions about your data in plain English.
- **Automatic Visualization**: Get results as tables, cards, or charts (bar, line, pie, scatter) based on the data and question.
- **Database Documentation**: Ask for schema, table, or column info in natural language.
- **Relationship & Table Diagrams**: Visualize table relationships and individual table schemas.
- **Session-based Conversation History**: Keeps track of your recent questions and answers.
- **Caching**: Uses Redis for fast schema and query result caching.

---

## Architecture & Main Flows

### 1. User Interaction (Frontend)
- User enters a question in the chat UI (`templates/index.html`).
- The frontend sends the question to the `/chat` endpoint via AJAX.
- The UI displays responses as text, cards, tables, charts, or diagrams based on the backend's reply.

### 2. Backend API Endpoints (`opendai.py`)
- `/` : Home page (renders chat UI)
- `/chat` : Main endpoint for chat Q&A (POST)
- `/conversation_history` : Get current session's conversation history (GET)
- `/clear_conversation` : Clear the conversation history (POST)
- `/batch_chat` : Submit multiple questions at once (POST)

### 3. Main Backend Logic (`/chat` endpoint)
1. **Session Initialization**: Ensures a session and conversation history exist.
2. **Sensitive Data Check**: Blocks questions about passwords, tokens, etc.
3. **Diagram Requests**: Handles requests for relationship or table diagrams.
4. **SQL Generation**: Uses OpenAI to generate SQL for the user's question, with schema context.
5. **Query Execution**: Runs the SQL against the MySQL database using SQLAlchemy and Pandas.
6. **Response Type Determination**: Uses OpenAI to decide if the answer should be text, table, card, or chart. If the user asks for a paragraph/explanation, it forces a text response.
7. **Formatting**: Formats the result as text (using LLM), table, card, or chart. Generates and saves chart/diagram images if needed.
8. **Conversation History**: Stores each Q&A turn in the session.
9. **Returns**: Sends a JSON response with the answer type, content, and optional SQL/query info.

### 4. Visualization & Documentation
- **Charts**: Generated with Matplotlib, saved as images, and served from `/static/generated/`.
- **Diagrams**: Uses NetworkX and Matplotlib for ER diagrams and table schemas.
- **Documentation**: Uses LLM to generate human-friendly explanations of schema, tables, and columns.

---

## Setup & Installation

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables** (see `.env.example`):
   - `OPENAI_API_KEY` (required)
   - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (MySQL)
   - `REDIS_URL` (optional, for caching)
   - `SECRET_KEY` (Flask session)
4. **Run the app**
   ```bash
   python opendai.py
   ```
5. **Access the app**
   - Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## File Structure
- `opendai.py` : Main Flask app, API endpoints, OpenAI and DB logic
- `templates/index.html` : Chat UI (Bootstrap, JS)
- `static/` : CSS and generated images
- `business_terms.json` : (Optional) Maps business terms to table names
- `requirements.txt` : Python dependencies

---

## Key Functions & Flow

### SQL Generation & Execution
- `generate_sql_token_optimized(question, database)`: Uses OpenAI to generate SQL from a question.
- `execute_query(sql, database)`: Runs SQL and returns a Pandas DataFrame.
- `determine_response_type(question, data_preview)`: Uses OpenAI to decide if the answer should be text, table, card, or chart.
- `format_text_response(df, question)`: Uses LLM to turn data into a paragraph answer.
- `generate_visualization(df, chart_type)`: Creates and saves chart images.

### Schema & Documentation
- `get_database_schema(database)`: Loads schema, columns, relationships, and sample data (with Redis caching).
- `handle_documentation_query(question, database)`: Answers schema/table/column questions in natural language.
- `generate_relationship_diagram(database)`: Creates an ER diagram of the database.
- `generate_table_schema_diagram(table_name, database)`: Creates a diagram for a single table.

### Caching
- Uses Redis for schema and query result caching.
- Session-based conversation history (Flask-Session).

---

## Customization & Extending
- Add more keywords to force text/paragraph answers in the `/chat` endpoint.
- Extend `business_terms.json` to improve business term mapping.
- Add more chart types or custom visualizations as needed.

---

## Troubleshooting
- **OpenAI errors**: Check your API key and usage limits.
- **Database errors**: Ensure DB credentials and schema are correct.
- **Redis not available**: The app will still work, but without caching.

---

## License
MIT 