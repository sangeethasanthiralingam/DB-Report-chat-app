# DB Report Chat App

A sophisticated Flask-based chat application that converts natural language to SQL queries and presents results in multiple formats (tables, charts, cards, diagrams).

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL/MariaDB database
- OpenAI API key

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd "DB Report chat app"
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and OpenAI credentials

# Create image directory
mkdir -p static/generated

# Run the application
python opendai.py
```

Visit `http://localhost:5000` to start chatting!

## 📋 Features

- **Natural Language to SQL**: Ask questions in plain English
- **Multiple Response Formats**: Tables, charts (bar/line/pie/scatter/stack), cards, diagrams
- **Domain Detection**: Automatically detects HR, Inventory, Financial, Reporting domains
- **Database Diagrams**: Generate relationship and schema diagrams
- **Session Management**: Maintain conversation history
- **Batch Processing**: Handle multiple questions at once
- **Error Recovery**: Automatic retry mechanisms for failed queries

## 🎯 Usage Examples

```
"Show me all employees"
"What products are in stock?"
"Generate a pie chart of sales by category"
"Create a bar chart of monthly revenue"
"Show me the database relationships"
"Draw a diagram for the customers table"
"Sales by date stack chart"
```

## 🏗️ Project Structure

```
DB Report chat app/
├── opendai.py                    # Main Flask application
├── requirements.txt              # Python dependencies
├── business_terms.json           # Business term mappings (154 terms)
├── static/                       # Static files & generated images
├── templates/                    # HTML templates
├── utils/                        # Core utility modules
├── tests/                        # Comprehensive test suite
├── tools/                        # Utility scripts
└── docs/                         # Detailed documentation
```

### Key Files Explained

- **`opendai.py`**: Main application (monolithic version)
- **`app.py`**: Modular version (work in progress)
- **`business_terms.json`**: Maps database tables to business terms
- **`utils/`**: Core modules for domain analysis, database management, etc.

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Detailed system architecture
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** - Environment setup
- **[Testing Guide](docs/TESTING.md)** - Running tests and test coverage
- **[Prompt Engineering](docs/PROMPT_MATRIX.md)** - Prompt optimization tracking
- **[Chart Behavior](docs/CHART_BEHAVIOR.md)** - Chart generation details

## 🧪 Testing

```bash
# Run all tests
python tests/run_all_tests.py

# Run specific tests
python tests/test_domain_analyzer.py
python tests/test_database_manager.py
python tests/test_response_formatter.py
```

## 🔧 Configuration

Create a `.env` file with your settings:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Flask
SECRET_KEY=your-secret-key-change-this
```

## 🔌 API Endpoints

- `POST /chat` - Main chat endpoint
- `POST /batch_chat` - Process multiple questions
- `GET /conversation_history` - Get conversation history
- `POST /clear_conversation` - Clear history
- `GET /session_info` - Session information

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify credentials in `.env`
   - Ensure MySQL server is running

2. **OpenAI API Error**
   - Check `OPENAI_API_KEY` in `.env`
   - Verify API quota and billing

3. **Image Generation Issues**
   - Ensure `static/generated/` directory exists
   - Check file permissions

### Debug Tools

```bash
# Check database tables
python tools/check_database_tables.py

# Fix unicode symbols
python tools/fix_unicode_symbols.py

# Run debug tests
python tests/test_debug.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Check the [troubleshooting section](#-troubleshooting)
- Review the [detailed documentation](docs/)
- Create an issue with detailed information

---

**For detailed information, see the [documentation](docs/) directory.** 