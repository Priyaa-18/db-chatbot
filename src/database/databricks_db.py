"""
Databricks database connector implementation.
"""
from typing import Dict, Any
from src.database.base import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabricksConnector(DatabaseConnector):
    """Databricks database connector."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.server_hostname = config.get("server_hostname")
        self.http_path = config.get("http_path")
        self.token = config.get("token")
        self.catalog = config.get("catalog")
        self.schema = config.get("schema")
        
        # Validate required fields
        if not all([self.server_hostname, self.http_path, self.token]):
            raise ValueError("Missing required Databricks configuration")
    
    def get_connection_string(self) -> str:
        """Get Databricks connection string."""
        # Build connection string for databricks-sqlalchemy
        # Format: databricks://token:<token>@<hostname>?http_path=<path>&catalog=<catalog>&schema=<schema>
        
        conn_str = f"databricks://token:{self.token}@{self.server_hostname}"
        
        # Add query parameters
        params = [f"http_path={self.http_path}"]
        
        if self.catalog:
            params.append(f"catalog={self.catalog}")
        if self.schema:
            params.append(f"schema={self.schema}")
        
        conn_str += "?" + "&".join(params)
        
        logger.debug("Generated Databricks connection string", catalog=self.catalog)
        return conn_str
