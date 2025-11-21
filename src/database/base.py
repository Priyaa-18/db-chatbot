"""
Base interface for database connectors.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from src.models import TableMetadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnector(ABC):
    """Base class for database connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine: Optional[Engine] = None
        self._schema_cache: Optional[List[TableMetadata]] = None
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        pass
    
    def connect(self) -> Engine:
        """Create database connection."""
        if self.engine is None:
            connection_string = self.get_connection_string()
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10
            )
            logger.info("Connected to database", db_type=self.__class__.__name__)
        return self.engine
    
    def disconnect(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Disconnected from database")
    
    def get_schemas(self) -> List[str]:
        """Get list of schemas in the database."""
        engine = self.connect()
        inspector = inspect(engine)
        return inspector.get_schema_names()
    
    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """Get list of tables in a schema."""
        engine = self.connect()
        inspector = inspect(engine)
        return inspector.get_table_names(schema=schema)
    
    def get_table_metadata(self, table_name: str, schema: Optional[str] = None) -> TableMetadata:
        """Get metadata for a specific table."""
        engine = self.connect()
        inspector = inspect(engine)
        
        columns = []
        for col in inspector.get_columns(table_name, schema=schema):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True)
            })
        
        # Try to get row count (may not be available for all databases)
        row_count = None
        try:
            with engine.connect() as conn:
                full_name = f"{schema}.{table_name}" if schema else table_name
                result = conn.execute(text(f"SELECT COUNT(*) FROM {full_name}"))
                row_count = result.scalar()
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}", error=str(e))
        
        return TableMetadata(
            name=table_name,
            schema=schema or "default",
            columns=columns,
            row_count=row_count
        )
    
    def get_all_table_metadata(self, schema: Optional[str] = None, use_cache: bool = True) -> List[TableMetadata]:
        """Get metadata for all tables in a schema."""
        if use_cache and self._schema_cache is not None:
            logger.info("Using cached schema metadata")
            return self._schema_cache
        
        logger.info("Fetching schema metadata from database")
        tables = self.get_tables(schema)
        metadata_list = []
        
        for table in tables:
            try:
                metadata = self.get_table_metadata(table, schema)
                metadata_list.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to get metadata for table {table}", error=str(e))
        
        self._schema_cache = metadata_list
        logger.info(f"Fetched metadata for {len(metadata_list)} tables")
        return metadata_list
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        engine = self.connect()
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                
                # Convert to list of dicts
                columns = result.keys()
                rows = []
                for row in result:
                    rows.append(dict(zip(columns, row)))
                
                logger.info(f"Executed query, returned {len(rows)} rows")
                return rows
                
        except Exception as e:
            logger.error("Failed to execute query", error=str(e), sql=sql[:200])
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            engine = self.connect()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            return False
    
    def clear_cache(self):
        """Clear the schema cache."""
        self._schema_cache = None
        logger.info("Cleared schema cache")
