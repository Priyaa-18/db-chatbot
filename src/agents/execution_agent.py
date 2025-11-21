"""
Execution Agent - Executes validated SQL queries on the database.
"""
import time
from typing import Optional
from src.models import AgentResult, SQLQuery, QueryResult
from src.database.base import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionAgent:
    """Agent responsible for executing SQL queries."""
    
    def __init__(self, db_connector: DatabaseConnector, timeout_seconds: int = 300):
        self.db_connector = db_connector
        self.timeout_seconds = timeout_seconds
    
    async def execute_query(
        self,
        sql_query: SQLQuery,
        max_rows: Optional[int] = None
    ) -> AgentResult:
        """
        Execute a validated SQL query.
        
        Args:
            sql_query: The SQL query to execute
            max_rows: Maximum number of rows to return
        
        Returns:
            AgentResult with QueryResult
        """
        start_time = time.time()
        
        try:
            sql = sql_query.sql
            
            logger.info("Executing query", sql=sql[:200])
            
            # Execute query
            rows = self.db_connector.execute_query(sql)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Check if we need to truncate
            truncated = False
            if max_rows and len(rows) > max_rows:
                rows = rows[:max_rows]
                truncated = True
                logger.warning(f"Results truncated to {max_rows} rows")
            
            # Get column names
            columns = list(rows[0].keys()) if rows else []
            
            query_result = QueryResult(
                data=rows,
                columns=columns,
                row_count=len(rows),
                execution_time_ms=execution_time,
                truncated=truncated
            )
            
            logger.info(
                "Query executed successfully",
                rows_returned=len(rows),
                truncated=truncated,
                execution_time_ms=execution_time
            )
            
            return AgentResult(
                success=True,
                data=query_result,
                metadata={
                    "row_count": len(rows),
                    "column_count": len(columns),
                    "truncated": truncated
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            logger.error(
                "Query execution failed",
                error=error_msg,
                sql=sql_query.sql[:200],
                execution_time_ms=execution_time
            )
            
            # Try to provide helpful error message
            helpful_error = self._parse_error_message(error_msg)
            
            return AgentResult(
                success=False,
                error=helpful_error,
                metadata={
                    "original_error": error_msg
                },
                execution_time_ms=execution_time
            )
    
    def _parse_error_message(self, error: str) -> str:
        """Parse database error and return user-friendly message."""
        error_lower = error.lower()
        
        # Common error patterns
        if "does not exist" in error_lower or "not found" in error_lower:
            return "Table or column not found. The query may reference non-existent database objects."
        
        if "syntax error" in error_lower or "invalid syntax" in error_lower:
            return "SQL syntax error. The query contains invalid SQL syntax."
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return f"Query execution timed out after {self.timeout_seconds} seconds. Try simplifying the query."
        
        if "permission" in error_lower or "access denied" in error_lower:
            return "Permission denied. You don't have access to query these tables."
        
        if "ambiguous" in error_lower:
            return "Ambiguous column reference. The query needs to specify which table columns belong to."
        
        if "divide by zero" in error_lower or "division by zero" in error_lower:
            return "Division by zero error. Check calculations in the query."
        
        # Return original error if no pattern matched
        return f"Database error: {error}"
