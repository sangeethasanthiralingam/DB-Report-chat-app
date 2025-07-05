# Utils Directory

This directory contains utility modules for the DB Report Chat App.

## Domain Analyzer (`domain_analyzer.py`)

The Domain Analyzer is a comprehensive module that handles domain detection and analysis for database queries. It helps identify the business domain of user questions and provides relevant context for SQL generation.

## Data Processor (`data_processor.py`)

The Data Processor is a comprehensive module that handles data formatting, sanitization, and processing for the application. It ensures that DataFrames can be safely converted to JSON and provides various formatting utilities.

### Features

- **Domain Detection**: Automatically detects business domains (HR, Inventory, Financial, Reporting) from user questions
- **Table Mapping**: Maps business terms to database table names using fuzzy matching
- **Schema Analysis**: Analyzes database schemas to identify domain-specific patterns
- **Context Generation**: Provides domain-specific context and common patterns for SQL generation

### Usage

```python
from utils.domain_analyzer import get_domain_analyzer

# Get the domain analyzer instance
analyzer = get_domain_analyzer()

# Detect domain from a question
domain = analyzer.detect_domain_from_question("Show me all employees")
# Returns: 'hr'

# Find relevant tables for a question
tables = analyzer.find_relevant_tables("What products are in stock?")
# Returns: Set of relevant table names

# Get domain-specific context
context = analyzer.get_domain_context('hr')
# Returns: Dictionary with description, common joins, key metrics, etc.
```

### Supported Domains

1. **HR (Human Resources)**
   - Keywords: employee, hire, attendance, leave, hr, human, resource, staff, personnel, workforce, payroll, shift, schedule
   - Tables: employees, attendance_records, leave_requests, shifts, payroll

2. **Inventory**
   - Keywords: product, stock, inventory, sales, purchase, customer, item, goods, merchandise, supply, order
   - Tables: products, sales, stock_levels, purchases, inventory

3. **Financial**
   - Keywords: account, payment, transaction, financial, money, invoice, bank, balance, revenue, expense, budget
   - Tables: accounts, transactions, payments, invoices, bank_accounts

4. **Reporting**
   - Keywords: report, chart, dashboard, analytics, statistics, summary, overview, trend, graph
   - Tables: reports, charts, dashboards

5. **General**
   - Default domain for questions that don't match specific business domains

### Configuration

The domain analyzer uses the `business_terms.json` file to map technical table names to business-friendly terms. This file should be located in the project root directory.

### Integration

The domain analyzer is automatically integrated into the main application (`opendai.py`) and is used for:

- Domain detection in SQL generation
- Table relevance scoring
- Domain-specific prompt generation
- Fallback table selection

### Testing

Run the test script to verify the domain analyzer functionality:

```bash
python test_domain_analyzer.py
```

This will test domain detection, table finding, and context generation for various types of questions.

## Data Processor (`data_processor.py`)

The Data Processor is a comprehensive module that handles data formatting, sanitization, and processing for the application. It ensures that DataFrames can be safely converted to JSON and provides various formatting utilities.

### Features

- **Data Sanitization**: Safely converts DataFrames to JSON by handling NaT values, datetime objects, and other problematic data types
- **Response Formatting**: Provides utilities for formatting different types of responses (cards, tables, text)
- **Schema Formatting**: Formats database schemas in compact, token-efficient ways
- **Documentation Formatting**: Formats database documentation responses in user-friendly ways
- **JSON Cleaning**: Recursively cleans objects for JSON serialization

### Usage

```python
from utils.data_processor import get_data_processor

# Get the data processor instance
processor = get_data_processor()

# Sanitize a DataFrame for JSON conversion
df_sanitized = processor.sanitize_dataframe_for_json(df)

# Format a card response
cards = processor.format_card_response(df)

# Format database documentation
doc_response = processor.format_database_documentation_response(df, question)

# Clean an object for JSON
cleaned_obj = processor.clean_for_json(response_object)
```

### Key Methods

1. **`sanitize_dataframe_for_json(df)`**: Converts NaT values to None and formats datetime objects
2. **`format_card_response(df)`**: Creates card-style metrics from DataFrame data
3. **`format_database_documentation_response(df, question)`**: Formats documentation queries
4. **`format_compact_schema(schema_info)`**: Creates compact schema representations
5. **`clean_for_json(obj)`**: Recursively cleans objects for JSON serialization

### Integration

The data processor is automatically integrated into the main application (`opendai.py`) and is used for:

- DataFrame sanitization before JSON conversion
- Response formatting for different output types
- Schema formatting for SQL generation prompts
- Conversation history cleaning

### Testing

Run the test script to verify the data processor functionality:

```bash
python test_nat_handling.py
```

This will test NaT handling, DataFrame sanitization, and JSON conversion for various data types. 