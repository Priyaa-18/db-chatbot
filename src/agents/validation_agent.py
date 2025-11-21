"""
Validation Agent - Validates SQL queries for safety and correctness.
"""
import time
import re
from typing import Optional
from src.models import AgentResult, SQLQuery, ValidationResult
from src.utils.security import QuerySafetyChecker, RowLimitEnforcer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationAgent:
    """Agent responsible for validating SQL queries."""
    
    def __init__(self, allow_destructive: bool = False, max_rows: int = 10000):
        self.allow_destructive = allow_destructive
        self.max_rows = max_rows
    
    async def validate_query(
        self,
        sql_query: SQLQuery,
        user_query: str
    ) -> AgentResult:
        """
        Validate a SQL query for safety and correctness.
        
        Args:
            sql_query: The SQL query to validate
            user_query: Original user query for context
        
        Returns:
            AgentResult with ValidationResult
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        try:
            sql = sql_query.sql
            
            # 1. Basic SQL syntax check
            syntax_valid = self._check_syntax(sql)
            if not syntax_valid:
                errors.append("SQL syntax appears invalid")
            
            # 2. Safety checks
            is_safe, safety_errors, safety_warnings = QuerySafetyChecker.validate_query(
                sql,
                allow_destructive=self.allow_destructive
            )
            errors.extend(safety_errors)
            warnings.extend(safety_warnings)
            
            # 3. Check for row limits
            estimated_rows = RowLimitEnforcer.estimate_result_size(sql)
            if estimated_rows == -1 or estimated_rows > self.max_rows:
                warnings.append(f"Query may return many rows. Limit will be enforced ({self.max_rows} rows)")
                # Enforce limit
                sql_query.sql = RowLimitEnforcer.add_limit_clause(sql, self.max_rows)
            
            # 4. Estimate query cost (simple heuristic)
            estimated_cost = self._estimate_cost(sql, sql_query.tables_used)
            
            # 5. Check confidence score
            if sql_query.confidence_score and sql_query.confidence_score < 0.6:
                warnings.append(f"Low confidence score ({sql_query.confidence_score:.2f}). Query may not be accurate.")
            
            # Determine if safe to execute
            safe_to_execute = len(errors) == 0
            
            validation_result = ValidationResult(
                is_valid=safe_to_execute,
                errors=errors,
                warnings=warnings,
                estimated_cost=estimated_cost,
                safe_to_execute=safe_to_execute
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                "Query validated",
                is_valid=validation_result.is_valid,
                errors=len(errors),
                warnings=len(warnings),
                safe_to_execute=safe_to_execute,
                execution_time_ms=execution_time
            )
            
            return AgentResult(
                success=True,
                data=validation_result,
                metadata={
                    "errors": errors,
                    "warnings": warnings,
                    "estimated_cost": estimated_cost
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error("Failed to validate query", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _check_syntax(self, sql: str) -> bool:
        """
        Basic SQL syntax check.
        
        This is a simple check - real validation happens at execution.
        """
        sql_upper = sql.upper().strip()
        
        # Check for common SQL keywords
        valid_starts = ["SELECT", "WITH"]
        if not any(sql_upper.startswith(keyword) for keyword in valid_starts):
            return False
        
        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            return False
        
        # Check for FROM clause (required for SELECT)
        if sql_upper.startswith("SELECT") and "FROM" not in sql_upper:
            return False
        
        return True
    
    def _estimate_cost(self, sql: str, tables_used: list) -> float:
        """
        Estimate query cost (simple heuristic).
        
        Returns a cost score between 0 and 1.
        """
        cost = 0.0
        sql_upper = sql.upper()
        
        # Number of tables (joins are expensive)
        cost += len(tables_used) * 0.1
        
        # JOINs
        join_count = sql_upper.count("JOIN")
        cost += join_count * 0.15
        
        # Subqueries
        subquery_count = sql_upper.count("SELECT") - 1  # Subtract main SELECT
        cost += subquery_count * 0.2
        
        # GROUP BY (aggregations can be expensive)
        if "GROUP BY" in sql_upper:
            cost += 0.15
        
        # ORDER BY without LIMIT (can be expensive)
        if "ORDER BY" in sql_upper and "LIMIT" not in sql_upper:
            cost += 0.1
        
        # DISTINCT (can be expensive)
        if "DISTINCT" in sql_upper:
            cost += 0.1
        
        # Window functions
        window_functions = ["ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD"]
        for func in window_functions:
            if func in sql_upper:
                cost += 0.15
                break
        
        # Cap at 1.0
        return min(cost, 1.0)
