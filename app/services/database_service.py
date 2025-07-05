from utils.database_manager import (
    get_database_schema, get_relevant_schema, execute_query, 
    generate_relationship_diagram, generate_table_schema_diagram,
    format_compact_schema, generate_domain_specific_prompt,
    redis_get, redis_set, LLM_CACHE_EXPIRY_SECONDS, DB_CONFIG,
    generate_sql_token_optimized
)

class DatabaseService:
    """Service wrapper for database operations"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_database_name(self):
        """Get the current database name"""
        return self.db_config['database']
    
    def get_database_schema(self, database=None):
        """Get database schema"""
        if database is None:
            database = self.db_config['database']
        return get_database_schema(database)
    
    def get_relevant_schema(self, question, database=None):
        """Get relevant schema for a question"""
        if database is None:
            database = self.db_config['database']
        return get_relevant_schema(question, database)
    
    def execute_query(self, sql, database=None):
        """Execute a SQL query"""
        if database is None:
            database = self.db_config['database']
        return execute_query(sql, database)
    
    def generate_relationship_diagram(self, database=None):
        """Generate relationship diagram"""
        if database is None:
            database = self.db_config['database']
        return generate_relationship_diagram(database)
    
    def generate_table_schema_diagram(self, table_name, database=None):
        """Generate table schema diagram"""
        if database is None:
            database = self.db_config['database']
        return generate_table_schema_diagram(table_name, database)
    
    def format_compact_schema(self, schema_info):
        """Format schema information"""
        return format_compact_schema(schema_info)
    
    def generate_domain_specific_prompt(self, question, database=None):
        """Generate domain-specific prompt"""
        if database is None:
            database = self.db_config['database']
        return generate_domain_specific_prompt(question, database,relevant_tables = None)
    
    def generate_sql_token_optimized(self, question, database=None, error_context=None):
        """Generate SQL with token optimization"""
        if database is None:
            database = self.db_config['database']
        return generate_sql_token_optimized(question, database, error_context)
    
    def redis_get(self, key):
        """Get value from Redis cache"""
        return redis_get(key)
    
    def redis_set(self, key, value, expiry=None):
        """Set value in Redis cache"""
        if expiry is None:
            expiry = LLM_CACHE_EXPIRY_SECONDS
        return redis_set(key, value, expiry)

_database_service_instance = None

def get_database_service():
    """Get the database service instance (singleton pattern)"""
    global _database_service_instance
    if _database_service_instance is None:
        _database_service_instance = DatabaseService()
    return _database_service_instance 