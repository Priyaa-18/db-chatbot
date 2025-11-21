"""
Schema Agent - Discovers and manages database schema information.
"""
import time
from typing import List, Optional
from src.models import AgentResult, SchemaContext, TableMetadata
from src.database.base import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SchemaAgent:
    """Agent responsible for schema discovery and management."""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
    
    async def get_schema_context(
        self,
        user_query: str,
        schema: Optional[str] = None,
        use_cache: bool = True
    ) -> AgentResult:
        """
        Get relevant schema context for a user query.
        
        Args:
            user_query: The user's natural language query
            schema: Optional specific schema to search
            use_cache: Whether to use cached schema information
        
        Returns:
            AgentResult with SchemaContext
        """
        start_time = time.time()
        
        try:
            # Get all table metadata
            all_tables = self.db_connector.get_all_table_metadata(schema=schema, use_cache=use_cache)
            
            # Filter relevant tables based on query keywords
            relevant_tables = self._filter_relevant_tables(user_query, all_tables)
            
            # Build schema context
            schema_context = SchemaContext(
                tables=relevant_tables,
                relationships=self._infer_relationships(relevant_tables),
                common_queries=[],  # Could be populated from history
                business_terms={}   # Could be loaded from config
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                "Schema context retrieved",
                total_tables=len(all_tables),
                relevant_tables=len(relevant_tables),
                execution_time_ms=execution_time
            )
            
            return AgentResult(
                success=True,
                data=schema_context,
                metadata={
                    "total_tables": len(all_tables),
                    "relevant_tables": len(relevant_tables),
                    "schema": schema
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error("Failed to get schema context", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _filter_relevant_tables(
        self,
        user_query: str,
        all_tables: List[TableMetadata]
    ) -> List[TableMetadata]:
        """
        Filter tables that are likely relevant to the user query.
        
        Uses keyword matching on table names and column names.
        """
        query_lower = user_query.lower()
        query_words = set(query_lower.split())
        
        relevant_tables = []
        
        for table in all_tables:
            # Check table name
            table_name_lower = table.name.lower()
            
            # Check if any query word appears in table name
            if any(word in table_name_lower for word in query_words):
                relevant_tables.append(table)
                continue
            
            # Check column names
            column_names = [col["name"].lower() for col in table.columns]
            if any(any(word in col_name for word in query_words) for col_name in column_names):
                relevant_tables.append(table)
                continue
        
        # If no tables matched, return all tables (let LLM decide)
        if not relevant_tables:
            logger.warning("No tables matched query keywords, returning all tables")
            return all_tables[:20]  # Limit to first 20 tables to avoid overwhelming LLM
        
        logger.info(f"Filtered {len(relevant_tables)} relevant tables from {len(all_tables)} total")
        return relevant_tables
    
    def _infer_relationships(self, tables: List[TableMetadata]) -> List[dict]:
        """
        Infer relationships between tables based on column names.
        
        This is a simple heuristic - looks for foreign key patterns.
        """
        relationships = []
        
        for table in tables:
            for column in table.columns:
                col_name = column["name"].lower()
                
                # Look for common FK patterns: table_id, tableid, table_fk
                if col_name.endswith("_id") or col_name.endswith("id"):
                    # Try to find referenced table
                    potential_table = col_name.replace("_id", "").replace("id", "")
                    
                    for other_table in tables:
                        if other_table.name.lower() == potential_table:
                            relationships.append({
                                "from_table": table.name,
                                "from_column": column["name"],
                                "to_table": other_table.name,
                                "to_column": "id"  # Assume primary key is 'id'
                            })
        
        return relationships
