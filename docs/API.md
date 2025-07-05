# API Reference - DB Report Chat App

## 📋 Overview

The DB Report Chat App provides a RESTful API for natural language database queries with support for multiple response formats including tables, charts, cards, and diagrams.

## 🔌 Base URL

```
http://localhost:5000
```

## 🔑 Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## 📊 Response Formats

### Standard Response Structure
```json
{
  "type": "table|chart|card|text|diagram",
  "content": "...",
  "sql": "SELECT ...",
  "conversation_count": 1
}
```

### Response Types

| Type | Description | Content Format |
|------|-------------|----------------|
| `table` | Tabular data | Array of objects |
| `chart` | Chart visualization | Image filename or base64 |
| `card` | Metric cards | Array of card objects |
| `text` | Text response | String |
| `diagram` | Database diagram | Image filename or base64 |

## 🚀 API Endpoints

### 1. **POST /chat**

Main endpoint for processing natural language questions.

#### Request
```json
{
  "question": "Show me all employees"
}
```

#### Response Examples

**Table Response:**
```json
{
  "type": "table",
  "content": [
    {"id": 1, "name": "John Doe", "department": "Engineering"},
    {"id": 2, "name": "Jane Smith", "department": "Marketing"}
  ],
  "sql": "SELECT * FROM employees",
  "conversation_count": 1
}
```

**Chart Response:**
```json
{
  "type": "chart",
  "chart_type": "bar",
  "content": "chart_20250705_143022.png",
  "data_preview": [
    {"department": "Engineering", "count": 15},
    {"department": "Marketing", "count": 8}
  ],
  "sql": "SELECT department, COUNT(*) as count FROM employees GROUP BY department",
  "conversation_count": 1
}
```

**Card Response:**
```json
{
  "type": "card",
  "content": [
    {
      "title": "Total Employees",
      "value": "23",
      "change": null
    },
    {
      "title": "Departments",
      "value": "5",
      "change": null
    }
  ],
  "sql": "SELECT COUNT(*) as total_employees FROM employees",
  "conversation_count": 1
}
```

#### Chart Types Supported

| Chart Type | Keywords | Description |
|------------|----------|-------------|
| `bar` | "bar chart", "bar diagram" | Bar chart for comparisons |
| `line` | "line chart", "line diagram" | Line chart for trends |
| `pie` | "pie chart", "pie diagram" | Pie chart for proportions |
| `scatter` | "scatter plot", "scatter chart" | Scatter plot for relationships |
| `stack` | "stack chart", "stacked chart" | Stacked bar chart |

#### Error Response
```json
{
  "type": "text",
  "content": "There was an error executing the query. The database returned: 'Unknown column'",
  "sql": "SELECT * FROM invalid_table",
  "conversation_count": 1
}
```

### 2. **POST /batch_chat**

Process multiple questions at once for improved efficiency.

#### Request
```json
{
  "questions": [
    "Show me all employees",
    "What products are in stock?",
    "Generate a pie chart of sales by category"
  ]
}
```

#### Response
```json
{
  "responses": [
    {
      "type": "table",
      "content": [...],
      "sql": "SELECT * FROM employees"
    },
    {
      "type": "table", 
      "content": [...],
      "sql": "SELECT * FROM products WHERE stock > 0"
    },
    {
      "type": "chart",
      "chart_type": "pie",
      "content": "chart_20250705_143025.png",
      "sql": "SELECT category, SUM(sales) FROM sales GROUP BY category"
    }
  ]
}
```

### 3. **GET /conversation_history**

Retrieve the current conversation history.

#### Response
```json
{
  "conversation_history": [
    {
      "id": "session_123",
      "question": "Show me all employees",
      "response_obj": {
        "type": "table",
        "content": [...],
        "sql": "SELECT * FROM employees"
      },
      "sql_query": "SELECT * FROM employees",
      "timestamp": "2025-07-05T14:30:22"
    }
  ],
  "current_database": "my_database"
}
```

### 4. **POST /clear_conversation**

Clear the current conversation history.

#### Response
```json
{
  "message": "Conversation history cleared"
}
```

### 5. **POST /cleanup_images**

Manually trigger cleanup of old generated images.

#### Response
```json
{
  "message": "Image cleanup completed"
}
```

#### Error Response
```json
{
  "error": "Error message details"
}
```

### 6. **GET /session_info**

Get information about the current session.

#### Response
```json
{
  "session_id": "session_123",
  "conversation_count": 5,
  "generated_images": [
    "chart_20250705_143022.png",
    "diagram_20250705_143025.png"
  ],
  "created_at": "2025-07-05T14:30:22",
  "last_activity": "2025-07-05T14:35:18"
}
```

### 7. **POST /generate_static_chart**

Generate a static chart image from provided data.

#### Request
```json
{
  "chart_type": "bar",
  "data": [
    {"category": "A", "value": 10},
    {"category": "B", "value": 20},
    {"category": "C", "value": 15}
  ]
}
```

#### Response
```json
{
  "success": true,
  "image_data": "iVBORw0KGgoAAAANSUhEUgAA...",
  "chart_type": "bar"
}
```

## 🔍 Query Examples

### Basic Queries
```bash
# Get all employees
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all employees"}'

# Get products in stock
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What products are in stock?"}'
```

### Chart Queries
```bash
# Generate bar chart
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Create a bar chart of sales by month"}'

# Generate pie chart
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me a pie chart of revenue by department"}'

# Generate stack chart
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Sales by date stack chart"}'
```

### Database Structure Queries
```bash
# Get database relationships
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me the database relationships"}'

# Get table schema
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Draw a diagram for the customers table"}'
```

### Batch Queries
```bash
# Process multiple questions
curl -X POST http://localhost:5000/batch_chat \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "Show me all employees",
      "What products are in stock?",
      "Generate a pie chart of sales by category"
    ]
  }'
```

## 🚨 Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 500 | Internal Server Error |

### Error Response Format
```json
{
  "error": "Error description",
  "details": "Additional error information"
}
```

### Common Error Scenarios

1. **Invalid Question**
   ```json
   {
     "error": "Question is required"
   }
   ```

2. **Database Connection Error**
   ```json
   {
     "error": "Database connection failed"
   }
   ```

3. **SQL Generation Error**
   ```json
   {
     "error": "Could not generate SQL for this question"
   }
   ```

4. **Query Execution Error**
   ```json
   {
     "error": "There was an error executing the query. The database returned: 'Unknown column'"
   }
   ```

## 🔧 Rate Limiting

Currently, no rate limiting is implemented. However, it's recommended to:

- Limit requests to reasonable frequency
- Use batch processing for multiple questions
- Implement client-side caching for repeated queries

## 📊 Performance Considerations

### Response Times
- **Simple queries**: 1-3 seconds
- **Chart generation**: 2-5 seconds
- **Batch processing**: 5-15 seconds (depending on number of questions)

### Optimization Tips
1. Use specific questions for better SQL generation
2. Include chart type keywords for visualizations
3. Use batch processing for multiple related questions
4. Leverage conversation history for context

## 🔒 Security Considerations

### Input Validation
- All inputs are validated and sanitized
- SQL injection prevention through parameterized queries
- XSS protection for user inputs

### Content Filtering
- Sensitive content filtering (passwords, credentials)
- Malicious input detection
- Safe error message handling

## 📈 Monitoring

### Request Logging
All API requests are logged with:
- Request timestamp
- Processing time
- Response type
- Error information (if any)

### Performance Metrics
- Request count
- Average response time
- Error rates
- Cache hit rates

---

For more information about the application architecture and configuration, see the [Architecture Guide](./ARCHITECTURE.md) and [Configuration Guide](./CONFIGURATION.md). 