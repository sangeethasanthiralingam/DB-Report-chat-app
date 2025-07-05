# Architecture Guide - DB Report Chat App

## 🏗️ System Architecture

The DB Report Chat App follows a modular architecture with clear separation of concerns, designed for maintainability, scalability, and extensibility.

## 📊 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   Database      │
│   (HTML/JS)     │◄──►│   (opendai.py)  │◄──►│   (MySQL)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4o-mini) │
                       └─────────────────┘
```

## 🔧 Core Modules

### 1. **Main Application (`opendai.py`)**
- **Purpose**: Flask application entry point and route definitions
- **Responsibilities**: 
  - HTTP request handling
  - Route management
  - Response formatting
  - Error handling
- **Key Features**:
  - Session management
  - Image generation
  - Batch processing
  - API endpoints

### 2. **Domain Analyzer (`utils/domain_analyzer.py`)**
- **Purpose**: Business domain detection and analysis
- **Responsibilities**:
  - Detect business domains (HR, Inventory, Financial, Reporting)
  - Map business terms to database tables
  - Provide domain-specific context
  - Generate domain-aware SQL prompts
- **Key Features**:
  - 154 business term mappings
  - Fuzzy matching for table names
  - Domain-specific SQL patterns
  - Context generation for LLM prompts

### 3. **Database Manager (`utils/database_manager.py`)**
- **Purpose**: Database operations and schema management
- **Responsibilities**:
  - Database connection management
  - SQL query execution
  - Schema analysis and caching
  - Relationship diagram generation
- **Key Features**:
  - Redis-based caching
  - Schema analysis
  - Query optimization
  - Error recovery mechanisms

### 4. **Response Formatter (`utils/response_formatter.py`)**
- **Purpose**: Response formatting and visualization
- **Responsibilities**:
  - Chart generation (bar, line, pie, scatter, stack)
  - Response type determination
  - Data formatting and sanitization
  - Natural language response generation
- **Key Features**:
  - Multiple chart types
  - Interactive and static charts
  - Data sanitization for JSON
  - LLM-powered response formatting

### 5. **Data Processor (`utils/data_processor.py`)**
- **Purpose**: Data formatting and sanitization
- **Responsibilities**:
  - DataFrame sanitization
  - JSON conversion
  - NaT value handling
  - Data type conversion
- **Key Features**:
  - Safe JSON serialization
  - DateTime handling
  - Data validation
  - Error recovery

### 6. **Session Manager (`utils/session_manager.py`)**
- **Purpose**: Session and conversation management
- **Responsibilities**:
  - Conversation history management
  - Image file management
  - Session persistence
  - Cleanup operations
- **Key Features**:
  - Persistent conversation history
  - Image file storage
  - Automatic cleanup
  - Session isolation

### 7. **Chat Processor (`utils/chat_processor.py`)**
- **Purpose**: Chat processing and workflow orchestration
- **Responsibilities**:
  - Question processing
  - Response type determination
  - Sensitive content filtering
  - Workflow coordination
- **Key Features**:
  - Content filtering
  - Response type detection
  - Workflow management
  - Error handling

## 🔄 Data Flow

### 1. **Question Processing Flow**
```
User Question → Domain Detection → SQL Generation → Query Execution → 
Response Formatting → Visualization → Session Storage → Response
```

### 2. **SQL Generation Flow**
```
Question → Domain Analysis → Schema Retrieval → Prompt Generation → 
OpenAI API → SQL Query → Validation → Execution
```

### 3. **Response Formatting Flow**
```
Query Results → Data Sanitization → Response Type Detection → 
Formatting → Visualization (if needed) → Session Storage → Response
```

## 🏛️ Design Patterns

### 1. **Singleton Pattern**
- All utility modules use singleton instances
- Ensures single instance per application
- Improves performance and memory usage

### 2. **Factory Pattern**
- Application factory for Flask app creation
- Service factory for utility module instantiation
- Configuration factory for environment-based settings

### 3. **Strategy Pattern**
- Multiple response formatting strategies
- Different chart generation strategies
- Configurable domain detection strategies

### 4. **Observer Pattern**
- Session management with automatic cleanup
- Cache invalidation on schema changes
- Event-driven image cleanup

## 🔧 Configuration Management

### Environment-Based Configuration
```python
# Development
DEBUG=True
LOG_LEVEL=DEBUG
CACHE_ENABLED=False

# Production
DEBUG=False
LOG_LEVEL=INFO
CACHE_ENABLED=True
```

### Configuration Sources
1. **Environment Variables**: Primary configuration source
2. **Default Values**: Fallback for missing settings
3. **Validation**: Runtime configuration validation

## 🗄️ Data Storage

### 1. **Database (MySQL/MariaDB)**
- **Purpose**: Primary data storage
- **Features**: 
  - ACID compliance
  - Complex queries
  - Relationship support
  - Performance optimization

### 2. **Redis Cache (Optional)**
- **Purpose**: Performance optimization
- **Features**:
  - Schema caching
  - Query result caching
  - Session data caching
  - Automatic expiration

### 3. **File System**
- **Purpose**: Generated images and session data
- **Features**:
  - Chart image storage
  - Session file storage
  - Automatic cleanup
  - Backup support

## 🔒 Security Architecture

### 1. **Input Validation**
- SQL injection prevention
- XSS protection
- Input sanitization
- Content filtering

### 2. **Authentication & Authorization**
- Session management
- Access control
- Rate limiting
- Secure file handling

### 3. **Data Protection**
- Environment variable configuration
- Secure JSON encoding
- Error message sanitization
- Logging security

## 📈 Performance Optimization

### 1. **Caching Strategy**
- **Schema Caching**: Redis-based schema storage
- **Query Caching**: Frequently used query results
- **Response Caching**: Formatted response caching
- **Image Caching**: Generated chart images

### 2. **Database Optimization**
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Indexed queries
- **Batch Processing**: Multiple query execution
- **Error Recovery**: Automatic retry mechanisms

### 3. **Response Optimization**
- **Token Optimization**: Reduced prompt tokens
- **Image Compression**: Optimized chart images
- **Lazy Loading**: On-demand resource loading
- **Parallel Processing**: Concurrent operations

## 🧪 Testing Architecture

### 1. **Unit Testing**
- Individual module testing
- Mock service testing
- Error condition testing
- Performance testing

### 2. **Integration Testing**
- End-to-end workflow testing
- API endpoint testing
- Database integration testing
- External service testing

### 3. **Test Coverage**
- Code coverage metrics
- Functional coverage
- Error path coverage
- Performance testing

## 🔄 Deployment Architecture

### 1. **Development Environment**
- Local Flask development server
- Debug mode enabled
- Detailed logging
- Hot reloading

### 2. **Production Environment**
- WSGI server (Gunicorn/uWSGI)
- Reverse proxy (Nginx)
- Process management
- Monitoring and logging

### 3. **Containerization**
- Docker support
- Environment isolation
- Scalable deployment
- Easy configuration

## 🚀 Scalability Considerations

### 1. **Horizontal Scaling**
- Stateless application design
- Load balancer support
- Session externalization
- Database connection pooling

### 2. **Vertical Scaling**
- Resource optimization
- Memory management
- CPU utilization
- I/O optimization

### 3. **Performance Monitoring**
- Request timing
- Resource usage
- Error rates
- Cache hit rates

## 🔮 Future Architecture Enhancements

### 1. **Microservices Architecture**
- Service decomposition
- API gateway
- Service discovery
- Distributed tracing

### 2. **Event-Driven Architecture**
- Message queues
- Event sourcing
- CQRS pattern
- Event streaming

### 3. **Cloud-Native Architecture**
- Container orchestration
- Auto-scaling
- Service mesh
- Cloud-native monitoring

---

This architecture provides a solid foundation for the current application while maintaining flexibility for future enhancements and scalability requirements. 

## 📁 **Modular Structure Overview:**

```
app/
├── __init__.py          # Application factory
├── config.py            # Configuration management
├── routes/
│   ├── chat.py          # Chat endpoints
│   ├── session.py       # Session management
│   ├── charts.py        # Chart generation
│   └── main.py          # Main routes
└── services/
    ├── chat_service.py
    ├── data_service.py
    ├── database_service.py
    ├── response_service.py
    └── session_service.py
``` 