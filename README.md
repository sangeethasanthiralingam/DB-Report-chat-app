# DB Report Chat App

A sophisticated Flask-based chat application that allows users to interact with databases using natural language. The app automatically generates SQL queries, executes them, and presents results in various formats including tables, charts, and cards. Built with a modular architecture for maintainability and extensibility.

## 🚀 Features

- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **Multiple Response Formats**: Tables, charts (bar, line, pie, scatter), cards, and text
- **Domain Detection**: Automatically detects business domains (HR, Inventory, Financial, Reporting)
- **Database Diagrams**: Generate relationship and schema diagrams
- **Session Management**: Maintain conversation history and generated images
- **Batch Processing**: Handle multiple questions at once
- **Data Sanitization**: Handle NaT values and complex data types
- **Caching**: Redis-based caching for improved performance
- **Modular Architecture**: Clean separation of concerns with utility modules
- **Type Safety**: Full type annotations and error handling
- **Session Management**: Persistent conversation history and file cleanup
- **Error Recovery**: Automatic retry mechanisms for failed queries

## 📋 Prerequisites

- Python 3.8+
- MySQL/MariaDB database
- Redis server (optional, for caching)
- OpenAI API key

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "DB Report chat app"
   ```

2. **Create and activate virtual environment (recommended)**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=your_database
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # Flask Configuration
   SECRET_KEY=your-secret-key-change-this
   
   # Redis Configuration (optional)
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   
   # Optional: Custom settings
   DEBUG=True
   LOG_LEVEL=INFO
   ```

5. **Configure your database**
   - Ensure your MySQL database is running
   - Update the database connection details in the `.env` file
   - The app will automatically analyze your database schema
   - Create the `static/generated/` directory for image storage:
     ```bash
     mkdir -p static/generated
     ```

## 🏗️ Project Structure

```
DB Report chat app/
├── opendai.py                 # Main Flask application
├── requirements.txt           # Python dependencies
├── business_terms.json        # Business term mappings
├── .env                      # Environment variables
├── .gitignore               # Git ignore rules
├── static/                  # Static files
│   ├── generated/           # Generated images
│   └── styles.css          # CSS styles
├── templates/               # HTML templates
│   └── index.html          # Main chat interface
└── utils/                   # Utility modules
    ├── README.md           # Utils documentation
    ├── chat_processor.py   # Chat processing logic
    ├── data_processor.py   # Data formatting and sanitization
    ├── database_manager.py # Database operations and caching
    ├── domain_analyzer.py  # Domain detection and analysis
    ├── response_formatter.py # Response formatting and visualization
    └── session_manager.py  # Session and conversation management
```

## 🚀 Usage

1. **Start the application**
   ```bash
   python opendai.py
   ```
   The app will start on `http://localhost:5000` with debug mode enabled.

2. **Access the web interface**
   Open your browser and navigate to `http://localhost:5000`

3. **Ask questions in natural language**
   Examples:
   - "Show me all employees"
   - "What products are in stock?"
   - "Generate a pie chart of sales by category"
   - "Create a bar chart of monthly revenue"
   - "Show me the database relationships"
   - "Draw a diagram for the customers table"
   - "What's the total revenue this month?"
   - "List all tables in the database"

4. **Use batch processing**
   Send multiple questions at once using the batch endpoint or web interface.

## 📊 Response Types

The app automatically determines the best response format based on your question:

- **Tables**: Default format for data queries
- **Charts**: Automatically generated for visualization requests
  - Bar charts: "bar chart", "bar diagram"
  - Line charts: "line chart", "line diagram"
  - Pie charts: "pie chart", "pie diagram"
  - Scatter plots: "scatter plot", "scatter chart"
- **Cards**: For metric summaries ("card", "metric")
- **Diagrams**: For database structure requests
- **Text**: For documentation and conversational responses

## 🔧 Configuration

### Business Terms Mapping

The `business_terms.json` file maps business-friendly terms to database table names:

```json
{
  "employees": "staff",
  "products": "items",
  "customers": "clients",
  "sales": "transactions"
}
```

### Domain Detection

The app automatically detects business domains:

- **HR**: employee, hire, attendance, leave, hr, human, resource, staff
- **Inventory**: product, stock, inventory, sales, purchase, customer, item
- **Financial**: account, payment, transaction, financial, money, invoice
- **Reporting**: report, chart, dashboard, analytics, statistics

## 🧪 Testing

Run the test scripts to verify functionality:

```bash
# Test domain detection and analysis
python test_domain_analyzer.py

# Test NaT handling and data sanitization
python test_nat_handling.py

# Test customer/supplier detection
python test_customer_supplier_detection.py

# Test domain detection accuracy
python test_domain_detection.py

# Run all tests (if you have pytest installed)
pytest test_*.py -v
```

### Test Coverage
- Domain detection accuracy
- Data sanitization and NaT handling
- SQL generation and execution
- Response formatting
- Session management
- Error handling and recovery

## 🔌 API Endpoints

### POST `/chat`
Main chat endpoint for single questions.

**Request:**
```json
{
  "question": "Show me all employees"
}
```

**Response:**
```json
{
  "type": "table",
  "content": [...],
  "sql": "SELECT * FROM employees",
  "conversation_count": 1
}
```

### POST `/batch_chat`
Process multiple questions at once.

**Request:**
```json
{
  "questions": [
    "Show me all employees",
    "What products are in stock?",
    "Generate a pie chart of sales by category"
  ]
}
```

### GET `/conversation_history`
Get the current conversation history.

### POST `/clear_conversation`
Clear the conversation history.

### GET `/session_info`
Get information about the current session.

## 🏛️ Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Modules

1. **`chat_processor.py`**: Handles chat processing logic, response type determination, and workflow orchestration
2. **`data_processor.py`**: Manages data formatting, sanitization, and processing
3. **`database_manager.py`**: Handles all database operations, schema analysis, and caching
4. **`domain_analyzer.py`**: Detects business domains and provides context-aware analysis
5. **`response_formatter.py`**: Formats responses and generates visualizations
6. **`session_manager.py`**: Manages sessions, conversation history, and file operations

### Key Features

- **Singleton Pattern**: Each utility module uses singleton instances for efficiency
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Caching**: Redis-based caching for database schemas and LLM responses
- **Type Safety**: Full type annotations for better code quality
- **Modularity**: Clean separation of concerns for maintainability
- **Token Optimization**: Efficient SQL generation with context-aware prompts
- **Data Sanitization**: Robust handling of NaT values and complex data types
- **Session Persistence**: Maintains conversation context across requests

### Data Flow

```
User Question → Domain Detection → SQL Generation → Query Execution → 
Response Formatting → Visualization (if needed) → Session Storage → Response
```

## 🔒 Security

- Environment variables for sensitive configuration
- Input validation and sanitization
- SQL injection prevention through parameterized queries
- Session management with secure file storage
- Sensitive content filtering (passwords, credentials)
- Automatic cleanup of old session files and images
- Rate limiting and error handling
- Secure JSON encoding with custom handlers

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify database credentials in `.env`
   - Ensure MySQL server is running
   - Check network connectivity

2. **OpenAI API Error**
   - Verify `OPENAI_API_KEY` in `.env`
   - Check API quota and billing
   - Ensure internet connectivity

3. **Redis Connection Error**
   - Redis is optional; the app will work without it
   - Verify Redis server is running if using caching
   - Check Redis configuration in `.env`

4. **Image Generation Issues**
   - Ensure `static/generated/` directory exists and is writable
   - Check matplotlib backend configuration
   - Verify sufficient disk space

### Logs

The application logs important events. Check the console output for:
- Request processing times
- SQL generation attempts
- Error messages
- Cache hits/misses
- Domain detection results
- Session management events

### Performance Monitoring

- Request timing is automatically logged
- Cache performance metrics
- Database query execution times
- Image generation statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Test with the provided test scripts
4. Create an issue with detailed information

## 🔄 Updates & Maintenance

The application automatically:
- Cleans up old generated images on startup
- Refreshes database schema cache
- Maintains conversation history
- Handles session timeouts
- Logs performance metrics
- Manages Redis cache expiration

### Manual Maintenance

```bash
# Clean up old session files
curl -X POST http://localhost:5000/cleanup_images

# Clear conversation history
curl -X POST http://localhost:5000/clear_conversation

# Check session info
curl http://localhost:5000/session_info
```

---

## 📈 Performance Tips

- Use Redis caching for better performance
- Keep database connections optimized
- Monitor generated image storage
- Regular cleanup of old session files
- Use batch processing for multiple queries

## 🎯 Best Practices

- Use specific questions for better SQL generation
- Include chart type keywords for visualizations
- Leverage domain-specific terminology
- Use batch processing for multiple related questions
- Monitor logs for performance insights

---

**Note**: This application is designed for development and testing environments. For production use, ensure proper security measures, error handling, and monitoring are in place. 