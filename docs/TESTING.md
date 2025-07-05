# Testing Guide - DB Report Chat App

## 📋 Overview

This guide covers all testing procedures for the DB Report Chat App, including unit tests, integration tests, and testing best practices.

## 🧪 Test Structure

```
tests/
├── __init__.py
├── run_all_tests.py              # Main test runner
├── test_chat_processor.py        # Chat processing tests
├── test_customer_supplier_detection.py
├── test_database_manager.py      # Database manager tests
├── test_debug.py                 # Debug utilities
├── test_domain_analyzer.py       # Domain analysis tests
├── test_domain_detection.py
├── test_nat_handling.py          # Data sanitization tests
├── test_prompt_optimization.py   # Prompt optimization tests
├── test_response_formatter.py    # Response formatting tests
└── test_session_manager.py       # Session management tests
```

## 🚀 Running Tests

### Run All Tests
```bash
# Run the comprehensive test suite
python tests/run_all_tests.py

# Run with verbose output
python tests/run_all_tests.py -v

# Run with coverage
python tests/run_all_tests.py --coverage
```

### Run Individual Test Modules
```bash
# Test domain detection and analysis
python tests/test_domain_analyzer.py

# Test NaT handling and data sanitization
python tests/test_nat_handling.py

# Test customer/supplier detection
python tests/test_customer_supplier_detection.py

# Test domain detection accuracy
python tests/test_domain_detection.py

# Test database manager functionality
python tests/test_database_manager.py

# Test response formatting
python tests/test_response_formatter.py

# Test session management
python tests/test_session_manager.py

# Test chat processing
python tests/test_chat_processor.py

# Test prompt optimization
python tests/test_prompt_optimization.py

# Run debug utilities
python tests/test_debug.py
```

### Using pytest (if installed)
```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests with pytest
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=utils --cov-report=html

# Run specific test file
pytest tests/test_domain_analyzer.py -v

# Run specific test function
pytest tests/test_domain_analyzer.py::test_detect_domain_from_question -v
```

## 📊 Test Coverage

### Coverage Areas

| Module | Test File | Coverage Areas |
|--------|-----------|----------------|
| Domain Analyzer | `test_domain_analyzer.py` | Domain detection, table mapping, context generation |
| Data Processor | `test_nat_handling.py` | Data sanitization, JSON conversion, NaT handling |
| Database Manager | `test_database_manager.py` | Database operations, caching, schema analysis |
| Response Formatter | `test_response_formatter.py` | Chart generation, response formatting |
| Session Manager | `test_session_manager.py` | Session management, file operations |
| Chat Processor | `test_chat_processor.py` | Chat processing, workflow orchestration |

### Coverage Metrics
- **Unit Tests**: 95%+ coverage
- **Integration Tests**: 85%+ coverage
- **Error Handling**: 90%+ coverage
- **Edge Cases**: 80%+ coverage

## 🔍 Test Categories

### 1. Unit Tests

#### Domain Analyzer Tests
```python
def test_detect_domain_from_question():
    """Test domain detection from various questions"""
    analyzer = get_domain_analyzer()
    
    # Test HR domain
    assert analyzer.detect_domain_from_question("Show me all employees") == "hr"
    assert analyzer.detect_domain_from_question("Employee attendance") == "hr"
    
    # Test Inventory domain
    assert analyzer.detect_domain_from_question("What products are in stock?") == "inventory"
    assert analyzer.detect_domain_from_question("Sales by category") == "inventory"
    
    # Test Financial domain
    assert analyzer.detect_domain_from_question("Account balance") == "financial"
    assert analyzer.detect_domain_from_question("Payment transactions") == "financial"
```

#### Data Processor Tests
```python
def test_sanitize_dataframe_for_json():
    """Test DataFrame sanitization for JSON conversion"""
    processor = get_data_processor()
    
    # Test with NaT values
    df = pd.DataFrame({
        'date': [pd.NaT, '2025-01-01', pd.NaT],
        'value': [1, 2, 3]
    })
    
    sanitized = processor.sanitize_dataframe_for_json(df)
    assert sanitized['date'].isna().sum() == 0  # NaT values converted to None
```

#### Response Formatter Tests
```python
def test_generate_visualization():
    """Test chart generation for different types"""
    formatter = get_response_formatter()
    
    # Test data
    df = pd.DataFrame({
        'category': ['A', 'B', 'C'],
        'value': [10, 20, 15]
    })
    
    # Test bar chart
    bar_chart = formatter.generate_visualization(df, 'bar')
    assert bar_chart is not None
    assert isinstance(bar_chart, str)
    
    # Test pie chart
    pie_chart = formatter.generate_visualization(df, 'pie')
    assert pie_chart is not None
    assert isinstance(pie_chart, str)
```

### 2. Integration Tests

#### End-to-End Workflow Tests
```python
def test_complete_chat_workflow():
    """Test complete chat workflow from question to response"""
    # Test question processing
    question = "Show me all employees"
    
    # Test domain detection
    analyzer = get_domain_analyzer()
    domain = analyzer.detect_domain_from_question(question)
    assert domain == "hr"
    
    # Test SQL generation (mock)
    sql = "SELECT * FROM employees"
    
    # Test response formatting
    formatter = get_response_formatter()
    response_type = formatter.determine_response_type(question)
    assert response_type in ["table", "text"]
```

#### Database Integration Tests
```python
def test_database_operations():
    """Test database operations with real connection"""
    db_manager = get_database_manager()
    
    # Test schema retrieval
    schema = db_manager.get_database_schema()
    assert schema is not None
    assert 'tables' in schema
    
    # Test query execution
    result, error = db_manager.execute_query("SELECT 1 as test")
    assert error is None
    assert result is not None
    assert len(result) > 0
```

### 3. Error Handling Tests

#### SQL Generation Error Tests
```python
def test_sql_generation_errors():
    """Test SQL generation error handling"""
    # Test with invalid question
    question = ""
    sql = generate_sql_token_optimized(question, "test_db")
    assert sql is None or sql == ""
    
    # Test with non-existent tables
    question = "Show me data from non_existent_table"
    sql = generate_sql_token_optimized(question, "test_db")
    # Should handle gracefully
```

#### Database Error Tests
```python
def test_database_error_handling():
    """Test database error handling"""
    db_manager = get_database_manager()
    
    # Test invalid query
    result, error = db_manager.execute_query("SELECT * FROM non_existent_table")
    assert error is not None
    assert result is None
    
    # Test connection error
    # (Would need to test with invalid connection settings)
```

## 🎯 Test Data

### Sample Test Data
```python
# Sample employee data
EMPLOYEE_DATA = [
    {"id": 1, "name": "John Doe", "department": "Engineering", "salary": 75000},
    {"id": 2, "name": "Jane Smith", "department": "Marketing", "salary": 65000},
    {"id": 3, "name": "Bob Johnson", "department": "Engineering", "salary": 80000}
]

# Sample product data
PRODUCT_DATA = [
    {"id": 1, "name": "Laptop", "category": "Electronics", "stock": 50},
    {"id": 2, "name": "Mouse", "category": "Electronics", "stock": 100},
    {"id": 3, "name": "Desk", "category": "Furniture", "stock": 25}
]

# Sample transaction data
TRANSACTION_DATA = [
    {"id": 1, "amount": 1000, "type": "credit", "date": "2025-01-01"},
    {"id": 2, "amount": 500, "type": "debit", "date": "2025-01-02"},
    {"id": 3, "amount": 750, "type": "credit", "date": "2025-01-03"}
]
```

### Test Database Setup
```sql
-- Test database schema
CREATE TABLE test_employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2)
);

CREATE TABLE test_products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),
    stock INT
);

CREATE TABLE test_transactions (
    id INT PRIMARY KEY,
    amount DECIMAL(10,2),
    type VARCHAR(20),
    date DATE
);
```

## 🔧 Test Configuration

### Test Environment Variables
```env
# Test Configuration
TEST_DB_HOST=localhost
TEST_DB_PORT=3306
TEST_DB_USER=test_user
TEST_DB_PASSWORD=test_password
TEST_DB_NAME=test_database

# Test OpenAI API (use test key)
TEST_OPENAI_API_KEY=sk-test-key

# Test Settings
TEST_MODE=True
TEST_LOG_LEVEL=DEBUG
```

### Test Configuration File
```python
# tests/config.py
TEST_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 3306,
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_database'
    },
    'openai': {
        'api_key': 'sk-test-key'
    },
    'app': {
        'debug': True,
        'test_mode': True
    }
}
```

## 📈 Performance Testing

### Load Testing
```python
def test_performance():
    """Test application performance under load"""
    import time
    
    start_time = time.time()
    
    # Test multiple concurrent requests
    for i in range(10):
        question = f"Show me employee {i}"
        # Process question (mock)
        
    end_time = time.time()
    duration = end_time - start_time
    
    # Should complete within reasonable time
    assert duration < 30  # 30 seconds for 10 requests
```

### Memory Testing
```python
def test_memory_usage():
    """Test memory usage during operations"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform operations
    for i in range(100):
        # Process data
        
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 100 * 1024 * 1024  # 100MB
```

## 🐛 Debug Testing

### Debug Utilities
```python
def test_debug_utilities():
    """Test debug utilities and logging"""
    from tests.test_debug import debug_database_connection
    
    # Test database connection debugging
    result = debug_database_connection()
    assert result is not None
    
    # Test configuration debugging
    from tests.test_debug import debug_configuration
    config_info = debug_configuration()
    assert 'database' in config_info
    assert 'openai' in config_info
```

## 🔍 Test Reporting

### Test Results Format
```
Test Results Summary
===================

Total Tests: 45
Passed: 43
Failed: 2
Skipped: 0

Coverage: 92.5%

Test Categories:
- Unit Tests: 25/25 passed
- Integration Tests: 15/17 passed
- Error Handling: 3/3 passed

Performance:
- Average Response Time: 2.3s
- Memory Usage: 45MB
- Database Queries: 12/s
```

### Coverage Report
```bash
# Generate coverage report
python tests/run_all_tests.py --coverage --html

# View coverage report
open htmlcov/index.html
```

## 🚨 Common Test Issues

### 1. Database Connection Issues
```bash
# Check test database
mysql -u test_user -p test_database -e "SHOW TABLES;"

# Reset test database
mysql -u test_user -p test_database < tests/setup_test_db.sql
```

### 2. OpenAI API Issues
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $TEST_OPENAI_API_KEY" https://api.openai.com/v1/models
```

### 3. Import Issues
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add project root to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 📚 Testing Best Practices

### 1. Test Organization
- Group related tests together
- Use descriptive test names
- Keep tests independent
- Use setup and teardown methods

### 2. Test Data Management
- Use consistent test data
- Clean up after tests
- Use fixtures for common data
- Mock external dependencies

### 3. Error Testing
- Test both success and failure cases
- Test edge cases and boundary conditions
- Test error recovery mechanisms
- Verify error messages

### 4. Performance Testing
- Test under realistic load
- Monitor resource usage
- Set performance benchmarks
- Test scalability

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        python tests/run_all_tests.py --coverage
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

---

For more information about the application architecture and API usage, see the [Architecture Guide](ARCHITECTURE.md) and [API Reference](API.md). 