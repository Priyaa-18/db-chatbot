"""
Configuration management for the enterprise database chatbot.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.models import DatabaseType, LLMProvider


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # LLM Configuration
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    llm_model: str = "claude-sonnet-4-20250514"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # Database Configuration
    default_database_type: DatabaseType = DatabaseType.SNOWFLAKE
    
    # Snowflake
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None
    snowflake_database: Optional[str] = None
    snowflake_schema: Optional[str] = None
    snowflake_warehouse: Optional[str] = None
    snowflake_role: Optional[str] = None
    
    # Databricks
    databricks_server_hostname: Optional[str] = None
    databricks_http_path: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_catalog: Optional[str] = None
    databricks_schema: Optional[str] = None
    
    # PostgreSQL
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_database: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    
    # MySQL
    mysql_host: Optional[str] = None
    mysql_port: int = 3306
    mysql_database: Optional[str] = None
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    
    # Application Settings
    max_query_rows: int = 10000
    query_timeout_seconds: int = 300
    schema_cache_ttl_seconds: int = 3600
    log_level: str = "INFO"
    
    # Security Settings
    allow_destructive_queries: bool = False  # DROP, DELETE, TRUNCATE
    enable_audit_logging: bool = True
    max_retries: int = 3
    
    # Visualization Settings
    default_chart_type: str = "bar"
    max_chart_points: int = 1000
    
    def get_database_config(self, db_type: DatabaseType) -> dict:
        """Get configuration for specific database type."""
        if db_type == DatabaseType.SNOWFLAKE:
            return {
                "account": self.snowflake_account,
                "user": self.snowflake_user,
                "password": self.snowflake_password,
                "database": self.snowflake_database,
                "schema": self.snowflake_schema,
                "warehouse": self.snowflake_warehouse,
                "role": self.snowflake_role,
            }
        elif db_type == DatabaseType.DATABRICKS:
            return {
                "server_hostname": self.databricks_server_hostname,
                "http_path": self.databricks_http_path,
                "token": self.databricks_token,
                "catalog": self.databricks_catalog,
                "schema": self.databricks_schema,
            }
        elif db_type == DatabaseType.POSTGRESQL:
            return {
                "host": self.postgres_host,
                "port": self.postgres_port,
                "database": self.postgres_database,
                "user": self.postgres_user,
                "password": self.postgres_password,
            }
        elif db_type == DatabaseType.MYSQL:
            return {
                "host": self.mysql_host,
                "port": self.mysql_port,
                "database": self.mysql_database,
                "user": self.mysql_user,
                "password": self.mysql_password,
            }
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def validate_config(self, db_type: DatabaseType) -> bool:
        """Validate that required config is present for database type."""
        config = self.get_database_config(db_type)
        
        if db_type == DatabaseType.SNOWFLAKE:
            required = ["account", "user", "password", "database"]
        elif db_type == DatabaseType.DATABRICKS:
            required = ["server_hostname", "http_path", "token"]
        elif db_type == DatabaseType.POSTGRESQL:
            required = ["host", "database", "user", "password"]
        elif db_type == DatabaseType.MYSQL:
            required = ["host", "database", "user", "password"]
        else:
            return False
        
        return all(config.get(key) for key in required)
