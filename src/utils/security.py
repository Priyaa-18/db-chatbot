"""
Security utilities for query validation and safety.
"""
import re
from typing import List, Tuple


class QuerySafetyChecker:
    """Check SQL queries for safety concerns."""
    
    # Destructive operations
    DESTRUCTIVE_KEYWORDS = [
        r"\bDROP\s+TABLE\b",
        r"\bDROP\s+DATABASE\b",
        r"\bDROP\s+SCHEMA\b",
        r"\bTRUNCATE\b",
        r"\bDELETE\s+FROM\b",
        r"\bUPDATE\s+.*\s+SET\b",
    ]
    
    # Potentially dangerous patterns
    DANGEROUS_PATTERNS = [
        r"--",  # SQL comments (potential injection)
        r"/\*.*\*/",  # Block comments
        r";\s*DROP",  # Multiple statements
        r"EXEC\s+",  # Execute statements
        r"xp_cmdshell",  # Command execution
    ]
    
    @staticmethod
    def is_destructive(sql: str) -> Tuple[bool, List[str]]:
        """Check if query contains destructive operations."""
        issues = []
        sql_upper = sql.upper()
        
        for pattern in QuerySafetyChecker.DESTRUCTIVE_KEYWORDS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                issues.append(f"Destructive operation detected: {pattern}")
        
        return len(issues) > 0, issues
    
    @staticmethod
    def check_dangerous_patterns(sql: str) -> Tuple[bool, List[str]]:
        """Check for potentially dangerous SQL patterns."""
        warnings = []
        
        for pattern in QuerySafetyChecker.DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                warnings.append(f"Potentially dangerous pattern: {pattern}")
        
        return len(warnings) > 0, warnings
    
    @staticmethod
    def validate_query(sql: str, allow_destructive: bool = False) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a SQL query for safety.
        
        Returns:
            Tuple of (is_safe, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check for destructive operations
        is_destructive, destructive_issues = QuerySafetyChecker.is_destructive(sql)
        if is_destructive and not allow_destructive:
            errors.extend(destructive_issues)
        
        # Check for dangerous patterns
        has_dangerous, dangerous_warnings = QuerySafetyChecker.check_dangerous_patterns(sql)
        if has_dangerous:
            warnings.extend(dangerous_warnings)
        
        # Check for empty query
        if not sql.strip():
            errors.append("Empty SQL query")
        
        # Check for multiple statements (simple check)
        if sql.count(';') > 1:
            errors.append("Multiple SQL statements not allowed")
        
        is_safe = len(errors) == 0
        return is_safe, errors, warnings


class RowLimitEnforcer:
    """Enforce row limits on queries."""
    
    @staticmethod
    def add_limit_clause(sql: str, max_rows: int) -> str:
        """Add LIMIT clause to SQL query if not present."""
        sql_upper = sql.upper()
        
        # Check if LIMIT already exists
        if "LIMIT" in sql_upper:
            # Extract existing limit
            limit_match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                if existing_limit <= max_rows:
                    return sql
                else:
                    # Replace with max_rows
                    return re.sub(
                        r"LIMIT\s+\d+",
                        f"LIMIT {max_rows}",
                        sql,
                        flags=re.IGNORECASE
                    )
        
        # Add LIMIT clause
        sql = sql.rstrip(';')
        return f"{sql}\nLIMIT {max_rows}"
    
    @staticmethod
    def estimate_result_size(sql: str) -> int:
        """Estimate the number of rows that will be returned."""
        # Simple heuristic - if there's a LIMIT, use that
        limit_match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
        if limit_match:
            return int(limit_match.group(1))
        
        # If no LIMIT, assume potentially large result
        return -1  # Unknown


def sanitize_user_input(user_input: str) -> str:
    """Sanitize user input to prevent injection."""
    # Remove potentially dangerous characters
    sanitized = user_input.replace("'", "''")  # Escape single quotes
    sanitized = sanitized.replace(";", "")  # Remove semicolons
    sanitized = sanitized.replace("--", "")  # Remove SQL comments
    
    return sanitized
