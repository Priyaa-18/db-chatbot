"""
Snowflake database connector implementation.
"""
from typing import Dict, Any
from src.database.base import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SnowflakeConnector(DatabaseConnector):
    """Snowflake database connector."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account = config.get("account")
        self.user = config.get("user")
        self.password = config.get("password")
        self.database = config.get("database")
        self.schema = config.get("schema")
        self.warehouse = config.get("warehouse")
        self.role = config.get("role")
        
        # Validate required fields
        if not all([self.account, self.user, self.password, self.database]):
            raise ValueError("Missing required Snowflake configuration")
    
    def get_connection_string(self) -> str:
        """Get Snowflake connection string."""
        # URL encode special characters in password
        from urllib.parse import quote_plus
        password_encoded = quote_plus(self.password)
        
        # Build connection string
        conn_str = f"snowflake://{self.user}:{password_encoded}@{self.account}"
        
        # Add database and schema
        if self.database:
            conn_str += f"/{self.database}"
            if self.schema:
                conn_str += f"/{self.schema}"
        
        # Add query parameters
        params = []
        if self.warehouse:
            params.append(f"warehouse={self.warehouse}")
        if self.role:
            params.append(f"role={self.role}")
        
        if params:
            conn_str += "?" + "&".join(params)
        
        logger.debug("Generated Snowflake connection string", database=self.database)
        return conn_str
