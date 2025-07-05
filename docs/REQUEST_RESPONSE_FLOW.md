# Request-Response Flow Diagrams - DB Report Chat App

## 🔄 **Complete Request-Response Flow**

### **High-Level Flow Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │───▶│   Flask App     │───▶│    Database     │───▶│   OpenAI API    │
│   (Browser)     │    │  (opendai.py)   │    │    (MySQL)      │    │  (GPT-4o-mini)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │                       │
         │                       ▼                       ▼                       ▼
         │                ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │                │   Response      │    │   Query         │    │   SQL           │
         │                │   Formatter     │    │   Execution     │    │   Generation    │
         │                └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┴───────────────────────┴───────────────────────┘
```

## 📊 **Detailed Request-Response Flow**

### **1. User Input Processing**

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  User types: "Show me all employees"                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (JavaScript)                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Captures user question                               │   │
│  │  • Validates input                                      │   │
│  │  • Sends POST request to /chat                          │   │
│  │                                                         │   │
│  │  POST /chat { "question": "Show me all employees" }     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK ROUTE (/chat)                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Receives JSON payload                                │   │
│  │  • Extracts question                                    │   │
│  │  • Initializes session                                  │   │
│  │                                                         │   │
│  │  question = "Show me all employees"                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **2. Domain Analysis & SQL Generation**

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN ANALYZER                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Analyzes question keywords                           │   │
│  │  • Detects business domain (HR/Inventory/Financial)    │   │
│  │  • Maps business terms to database tables              │   │
│  │                                                         │   │
│  │  Keywords: "employees" → Domain: "hr"                   │   │
│  │  Business Terms: employees → hr_core_employees          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE MANAGER                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Retrieves database schema (cached)                  │   │
│  │  • Identifies relevant tables                          │   │
│  │  • Generates domain-specific prompt                    │   │
│  │                                                         │   │
│  │  Schema: hr_core_employees table                        │   │
│  │  Columns: id, name, department, position               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OPENAI API CALL                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Sends question + schema + domain context             │   │
│  │  • Receives SQL query                                   │   │
│  │  • Handles token optimization                           │   │
│  │                                                         │   │
│  │  Prompt: "You are an expert SQL analyst for HR..."      │   │
│  │  Response: "SELECT * FROM hr_core_employees"            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **3. Query Execution & Data Processing**

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUERY EXECUTION                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Connects to MySQL database                           │   │
│  │  • Executes generated SQL                               │   │
│  │  • Handles errors with retry logic                      │   │
│  │                                                         │   │
│  │  SQL: "SELECT * FROM hr_core_employees"                 │   │
│  │  Result: DataFrame with employee data                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PROCESSOR                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Sanitizes DataFrame                                  │   │
│  │  • Handles NaT/NaN values                               │   │
│  │  • Converts to JSON-safe format                         │   │
│  │                                                         │   │
│  │  Input: DataFrame with NaT values                       │   │
│  │  Output: Clean JSON array                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **4. Response Type Determination & Formatting**

```
┌─────────────────────────────────────────────────────────────────┐
│                RESPONSE TYPE DETECTION                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Analyzes question keywords                           │   │
│  │  • Determines output format:                            │   │
│  │    - table, chart, card, text, diagram                 │   │
│  │                                                         │   │
│  │  Question: "Show me all employees"                      │   │
│  │  Keywords: No chart keywords → Type: "table"            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RESPONSE FORMATTER                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Formats data based on type:                          │   │
│  │    ├─ Table: JSON array of objects                      │   │
│  │    ├─ Chart: Generate matplotlib visualization          │   │
│  │    ├─ Card: Key metrics display                         │   │
│  │    ├─ Text: Natural language response                   │   │
│  │    └─ Diagram: Database schema/relationship             │   │
│  │                                                         │   │
│  │  Type: "table" → Format as JSON array                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **5. Session Management & Response Delivery**

```
┌─────────────────────────────────────────────────────────────────┐
│                   SESSION MANAGER                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Stores conversation history                          │   │
│  │  • Manages generated images                             │   │
│  │  • Handles cleanup operations                           │   │
│  │                                                         │   │
│  │  Store: Question + Response + SQL                       │   │
│  │  History: Keep last 10 conversations                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK RESPONSE                               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Formats JSON response                                │   │
│  │  • Includes metadata (SQL, conversation count)         │   │
│  │  • Returns to frontend                                  │   │
│  │                                                         │   │
│  │  Response: {                                            │   │
│  │    "type": "table",                                     │   │
│  │    "content": [...],                                     │   │
│  │    "sql": "SELECT * FROM hr_core_employees",            │   │
│  │    "conversation_count": 1                              │   │
│  │  }                                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND RENDERING                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Receives JSON response                               │   │
│  │  • Renders appropriate component:                       │   │
│  │    ├─ Table: DataTable component                        │   │
│  │    ├─ Chart: Chart.js visualization                     │   │
│  │    ├─ Card: Metric cards                                │   │
│  │    ├─ Text: Formatted text display                      │   │
│  │    └─ Diagram: Image display                            │   │
│  │                                                         │   │
│  │  Type: "table" → Render DataTable                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 **Complete Flow Diagram**

```
┌─────────────────┐
│     USER        │
│   QUESTION      │
│ "Show me all    │
│  employees"     │
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │───▶│     Flask       │───▶│    Domain       │
│   JavaScript    │    │     /chat       │    │   Analyzer      │
│                 │    │                 │    │                 │
│ POST /chat      │    │ Extract         │    │ Detect: "hr"    │
│ {question: ...} │    │ question        │    │ domain          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       ▼
         │                ┌─────────────────┐    ┌─────────────────┐
         │                │   Database      │    │   OpenAI API    │
         │                │   Manager       │───▶│   SQL Gen       │
         │                │                 │    │                 │
         │                │ Get schema      │    │ Generate SQL    │
         │                │ (cached)        │    │ query           │
         │                └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │                ┌─────────────────┐            │
         │                │   Query         │◄───────────┘
         │                │ Execution       │
         │                │                 │
         │                │ Execute SQL     │
         │                │ on MySQL        │
         │                └─────────────────┘
         │                       │
         │                       ▼
         │                ┌─────────────────┐    ┌─────────────────┐
         │                │   Data          │───▶│   Response      │
         │                │   Processor     │    │   Formatter     │
         │                │                 │    │                 │
         │                │ Sanitize        │    │ Format as       │
         │                │ DataFrame       │    │ JSON/Chart      │
         │                └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │                ┌─────────────────┐    ┌─────────────────┐
         │                │   Session       │    │   Chart/Image   │
         │                │   Manager       │    │   Generation    │
         │                │                 │    │                 │
         │                │ Store history   │    │ Generate PNG    │
         │                │ & cleanup       │    │ (if chart)      │
         │                └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │   JSON          │
                           │   Response      │
                           │                 │
                           │ {               │
                           │   "type":       │
                           │   "table",      │
                           │   "content":    │
                           │   [...],        │
                           │   "sql": "..."  │
                           │ }               │
                           └─────────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │   Frontend      │
                           │   Rendering     │
                           │                 │
                           │ Render          │
                           │ DataTable       │
                           │ component       │
                           └─────────────────┘
```

## 📋 **Detailed Component Flow**

### **A. Text/Table Response Flow**

```
User Question: "Show me all employees"
    │
    ▼
┌─────────────────┐
│ Domain Analyzer │───▶ Detects: "hr" domain
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Database Mgr    │───▶ Schema: employees table
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ OpenAI API      │───▶ SQL: "SELECT * FROM employees"
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Query Execution │───▶ DataFrame: employee data
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Data Processor  │───▶ JSON: [{"id": 1, "name": "John"}, ...]
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Response Type   │───▶ "table"
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Session Mgr     │───▶ Store conversation
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ JSON Response   │───▶ {"type": "table", "content": [...], "sql": "..."}
└─────────────────┘
```

### **B. Chart Response Flow**

```
User Question: "Create a bar chart of sales by month"
    │
    ▼
┌─────────────────┐
│ Domain Analyzer │───▶ Detects: "inventory" domain
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Database Mgr    │───▶ Schema: sales table
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ OpenAI API      │───▶ SQL: "SELECT month, SUM(sales) FROM sales GROUP BY month"
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Query Execution │───▶ DataFrame: monthly sales data
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Response Type   │───▶ "bar" (detected from "bar chart")
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Response Fmt    │───▶ Generate matplotlib chart
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Image Save      │───▶ Save as PNG file
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Session Mgr     │───▶ Store image filename
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ JSON Response   │───▶ {"type": "chart", "chart_type": "bar", "content": "filename.png"}
└─────────────────┘
```

### **C. Error Handling Flow**

```
SQL Error: "Unknown column 'invalid_column'"
    │
    ▼
┌─────────────────┐
│ Error Detection │───▶ MySQL Error 1054
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Retry Logic     │───▶ Regenerate SQL with error context
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ OpenAI API      │───▶ "Error: Unknown column. Please use valid columns: ..."
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Query Execution │───▶ New SQL attempt
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Success/Failure │───▶ Continue or return error message
└─────────────────┘
```

## 🔧 **Technical Implementation Details**

### **Key Functions in Flow**

| **Component** | **Function** | **Purpose** | **Input** | **Output** |
|---------------|--------------|-------------|-----------|------------|
| `opendai.py` | `chat()` | Main request handler | JSON payload | JSON response |
| `domain_analyzer.py` | `detect_domain_from_question()` | Domain detection | Question string | Domain type |
| `database_manager.py` | `generate_sql_token_optimized()` | SQL generation | Question + schema | SQL query |
| `database_manager.py` | `execute_query()` | Query execution | SQL string | DataFrame |
| `data_processor.py` | `dataframe_to_json_safe()` | Data sanitization | DataFrame | JSON array |
| `response_formatter.py` | `generate_visualization()` | Chart generation | DataFrame + type | Base64 image |
| `session_manager.py` | `add_to_conversation_history()` | Session storage | Q&A + SQL | Stored in session |

### **Data Transformation Flow**

```
Raw Question → Domain Context → SQL Query → DataFrame → 
Sanitized Data → Response Format → JSON Response → Frontend Display
```

### **Performance Optimizations**

- **Redis Caching**: Schema and query results
- **Connection Pooling**: Database connections
- **Token Optimization**: LLM API calls
- **Image Cleanup**: Automatic file management
- **Session Management**: Conversation history limits

## 📊 **Response Time Analysis**

| **Step** | **Typical Time** | **Optimization** | **Component** |
|----------|------------------|------------------|---------------|
| Domain Analysis | 1-5ms | Cached business terms | Domain Analyzer |
| Schema Retrieval | 10-50ms | Redis caching | Database Manager |
| SQL Generation | 500-2000ms | OpenAI API call | OpenAI API |
| Query Execution | 10-500ms | Connection pooling | Database Manager |
| Data Processing | 1-10ms | Optimized sanitization | Data Processor |
| Response Formatting | 10-100ms | Efficient rendering | Response Formatter |
| **Total** | **532-2665ms** | **~1-3 seconds** | **Complete Flow** |

## 🎯 **Flow Summary**

The request-response flow in your DB Report Chat App follows a **well-structured, modular architecture** with:

1. **Clear separation of concerns** across utility modules
2. **Efficient data flow** from user input to response
3. **Robust error handling** with retry mechanisms
4. **Performance optimizations** through caching and pooling
5. **Flexible response formatting** for multiple output types

This architecture ensures **scalability, maintainability, and reliability** while providing a smooth user experience. 

User Question → Frontend → Flask → Domain Analysis → SQL Generation → 
Query Execution → Data Processing → Response Formatting → Session Storage → 
JSON Response → Frontend Rendering 