# Configuration Guide - DB Report Chat App

## 📋 Overview

This guide covers all configuration options for the DB Report Chat App, including environment variables, database settings, and application preferences.

## 🔧 Environment Variables

Create a `.env` file in the project root directory with the following variables:

### Required Configuration

#### Database Settings
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
```

#### OpenAI Configuration
```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key
```

#### Flask Configuration
```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-this
```

### Optional Configuration

#### Redis Cache Settings
```env
# Redis Configuration (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password
```

#### Application Settings
```env
# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
FLASK_ENV=development
```

#### Performance Settings
```env
# Performance Configuration
CACHE_ENABLED=True
CACHE_EXPIRY_SECONDS=3600
IMAGE_CLEANUP_HOURS=24
MAX_CONVERSATION_HISTORY=100
```

#### Chart Settings
```env
# Chart Configuration
CHART_DPI=120
CHART_FIGSIZE_WIDTH=10
CHART_FIGSIZE_HEIGHT=5
CHART_STYLE=seaborn-v0_8
```

## 📁 Configuration File Structure

### Example `.env` File
```env
# ========================================
# Database Configuration
# ========================================
DB_HOST=localhost
DB_PORT=3306
DB_USER=db_user
DB_PASSWORD=secure_password_123
DB_NAME=my_database

# ========================================
# OpenAI Configuration
# ========================================
OPENAI_API_KEY=sk-your-openai-api-key-here

# ========================================
# Flask Configuration
# ========================================
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
DEBUG=True

# ========================================
# Redis Cache Configuration (Optional)
# ========================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ========================================
# Application Settings
# ========================================
LOG_LEVEL=INFO
CACHE_ENABLED=True
CACHE_EXPIRY_SECONDS=3600
IMAGE_CLEANUP_HOURS=24
MAX_CONVERSATION_HISTORY=100

# ========================================
# Chart Generation Settings
# ========================================
CHART_DPI=120
CHART_FIGSIZE_WIDTH=10
CHART_FIGSIZE_HEIGHT=5
CHART_STYLE=seaborn-v0_8

# ========================================
# Development Settings
# ========================================
DEV_MODE=False
ENABLE_DEBUG_LOGGING=True
SHOW_SQL_IN_RESPONSE=False
```

## 🔍 Configuration Details

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Database server hostname |
| `DB_PORT` | `3306` | Database server port |
| `DB_USER` | - | Database username |
| `DB_PASSWORD` | - | Database password |
| `DB_NAME` | - | Database name |

**Example:**
```env
DB_HOST=production-db.example.com
DB_PORT=3306
DB_USER=app_user
DB_PASSWORD=secure_password_123
DB_NAME=production_db
```

### OpenAI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Your OpenAI API key |

**Example:**
```env
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

### Flask Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-change-this` | Flask secret key for sessions |
| `FLASK_ENV` | `development` | Flask environment (development/production) |
| `DEBUG` | `True` | Enable debug mode |

**Example:**
```env
SECRET_KEY=your-super-secret-production-key-here
FLASK_ENV=production
DEBUG=False
```

### Redis Cache Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | - | Redis password (if required) |

**Example:**
```env
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis_password_123
```

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `CACHE_ENABLED` | `True` | Enable Redis caching |
| `CACHE_EXPIRY_SECONDS` | `3600` | Cache expiration time in seconds |
| `IMAGE_CLEANUP_HOURS` | `24` | Hours before cleaning up old images |
| `MAX_CONVERSATION_HISTORY` | `100` | Maximum conversation history items |

**Example:**
```env
LOG_LEVEL=DEBUG
CACHE_ENABLED=True
CACHE_EXPIRY_SECONDS=7200
IMAGE_CLEANUP_HOURS=48
MAX_CONVERSATION_HISTORY=200
```

### Chart Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CHART_DPI` | `120` | Chart image DPI (dots per inch) |
| `CHART_FIGSIZE_WIDTH` | `10` | Chart width in inches |
| `CHART_FIGSIZE_HEIGHT` | `5` | Chart height in inches |
| `CHART_STYLE` | `seaborn-v0_8` | Matplotlib style for charts |

**Example:**
```env
CHART_DPI=150
CHART_FIGSIZE_WIDTH=12
CHART_FIGSIZE_HEIGHT=6
CHART_STYLE=ggplot
```

## 🌍 Environment-Specific Configuration

### Development Environment
```env
# Development Settings
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG
CACHE_ENABLED=False
DEV_MODE=True
ENABLE_DEBUG_LOGGING=True
SHOW_SQL_IN_RESPONSE=True
```

### Production Environment
```env
# Production Settings
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO
CACHE_ENABLED=True
DEV_MODE=False
ENABLE_DEBUG_LOGGING=False
SHOW_SQL_IN_RESPONSE=False
```

### Testing Environment
```env
# Testing Settings
FLASK_ENV=testing
DEBUG=True
LOG_LEVEL=DEBUG
CACHE_ENABLED=False
DEV_MODE=True
ENABLE_DEBUG_LOGGING=True
SHOW_SQL_IN_RESPONSE=True
```

## 🔒 Security Configuration

### Production Security Checklist

1. **Change Default Secret Key**
   ```env
   SECRET_KEY=your-super-secure-production-secret-key
   ```

2. **Disable Debug Mode**
   ```env
   DEBUG=False
   FLASK_ENV=production
   ```

3. **Use Strong Database Passwords**
   ```env
   DB_PASSWORD=your-very-secure-database-password
   ```

4. **Configure Redis Security**
   ```env
   REDIS_PASSWORD=your-secure-redis-password
   ```

5. **Disable Development Features**
   ```env
   DEV_MODE=False
   ENABLE_DEBUG_LOGGING=False
   SHOW_SQL_IN_RESPONSE=False
   ```

## 📊 Performance Configuration

### High-Performance Settings
```env
# Performance Optimization
CACHE_ENABLED=True
CACHE_EXPIRY_SECONDS=7200
MAX_CONVERSATION_HISTORY=50
CHART_DPI=100
CHART_FIGSIZE_WIDTH=8
CHART_FIGSIZE_HEIGHT=4
```

### Memory-Optimized Settings
```env
# Memory Optimization
CACHE_ENABLED=False
MAX_CONVERSATION_HISTORY=25
IMAGE_CLEANUP_HOURS=12
CHART_DPI=80
```

## 🔧 Configuration Validation

### Required Variables Check
The application validates required configuration variables on startup:

```python
# Required variables
REQUIRED_VARS = [
    'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
    'OPENAI_API_KEY', 'SECRET_KEY'
]
```

### Configuration Validation Script
```bash
# Validate configuration
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'OPENAI_API_KEY', 'SECRET_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f'Missing required variables: {missing_vars}')
    exit(1)
else:
    print('Configuration validation passed!')
"
```

## 🚀 Configuration Examples

### Local Development
```env
# Local Development
DB_HOST=localhost
DB_PORT=3306
DB_USER=dev_user
DB_PASSWORD=dev_password
DB_NAME=dev_database
OPENAI_API_KEY=sk-your-dev-api-key
SECRET_KEY=dev-secret-key
DEBUG=True
LOG_LEVEL=DEBUG
CACHE_ENABLED=False
```

### Docker Development
```env
# Docker Development
DB_HOST=db
DB_PORT=3306
DB_USER=docker_user
DB_PASSWORD=docker_password
DB_NAME=docker_database
OPENAI_API_KEY=sk-your-docker-api-key
SECRET_KEY=docker-secret-key
REDIS_HOST=redis
REDIS_PORT=6379
DEBUG=True
```

### Production Deployment
```env
# Production
DB_HOST=production-db.example.com
DB_PORT=3306
DB_USER=prod_user
DB_PASSWORD=very-secure-password
DB_NAME=production_database
OPENAI_API_KEY=sk-your-production-api-key
SECRET_KEY=very-secure-production-secret-key
REDIS_HOST=production-redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=secure-redis-password
DEBUG=False
LOG_LEVEL=INFO
CACHE_ENABLED=True
```

## 🔍 Troubleshooting Configuration

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check database connectivity
   mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD -e "USE $DB_NAME; SHOW TABLES;"
   ```

2. **Redis Connection Error**
   ```bash
   # Check Redis connectivity
   redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
   ```

3. **OpenAI API Error**
   ```bash
   # Test OpenAI API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

4. **Configuration Loading Error**
   ```bash
   # Check environment variables
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DB_HOST:', os.getenv('DB_HOST'))"
   ```

### Configuration Debug Mode
```env
# Enable configuration debugging
DEBUG=True
LOG_LEVEL=DEBUG
ENABLE_DEBUG_LOGGING=True
```

## 📚 Additional Resources

- [Environment Variables Best Practices](https://12factor.net/config)
- [Flask Configuration Documentation](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [Redis Configuration Guide](https://redis.io/topics/config)

---

For more information about the application architecture and API usage, see the [Architecture Guide](ARCHITECTURE.md) and [API Reference](API.md). 