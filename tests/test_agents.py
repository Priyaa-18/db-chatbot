"""
Unit tests for agent implementations.
"""
import pytest
from src.models import SQLQuery, ValidationResult, QueryResult, TableMetadata, SchemaContext
from src.agents.validation_agent import ValidationAgent
from src.utils.security import QuerySafetyChecker, RowLimitEnforcer


class TestQuerySafetyChecker:
    """Tests for QuerySafetyChecker."""
    
    def test_destructive_query_detection(self):
        """Test detection of destructive queries."""
        # Test DROP TABLE
        is_destructive, issues = QuerySafetyChecker.is_destructive("DROP TABLE users")
        assert is_destructive
        assert len(issues) > 0
        
        # Test DELETE
        is_destructive, issues = QuerySafetyChecker.is_destructive("DELETE FROM users WHERE id = 1")
        assert is_destructive
        
        # Test safe query
        is_destructive, issues = QuerySafetyChecker.is_destructive("SELECT * FROM users")
        assert not is_destructive
    
    def test_dangerous_patterns(self):
        """Test detection of dangerous patterns."""
        # Test SQL comment
        has_dangerous, warnings = QuerySafetyChecker.check_dangerous_patterns("SELECT * FROM users -- comment")
        assert has_dangerous
        
        # Test safe query
        has_dangerous, warnings = QuerySafetyChecker.check_dangerous_patterns("SELECT * FROM users")
        assert not has_dangerous
    
    def test_validate_query(self):
        """Test full query validation."""
        # Safe query
        is_safe, errors, warnings = QuerySafetyChecker.validate_query(
            "SELECT * FROM users LIMIT 10",
            allow_destructive=False
        )
        assert is_safe
        assert len(errors) == 0
        
        # Destructive query
        is_safe, errors, warnings = QuerySafetyChecker.validate_query(
            "DROP TABLE users",
            allow_destructive=False
        )
        assert not is_safe
        assert len(errors) > 0


class TestRowLimitEnforcer:
    """Tests for RowLimitEnforcer."""
    
    def test_add_limit_clause(self):
        """Test adding LIMIT clause to queries."""
        # Query without LIMIT
        sql = "SELECT * FROM users"
        result = RowLimitEnforcer.add_limit_clause(sql, 1000)
        assert "LIMIT 1000" in result
        
        # Query with existing LIMIT (lower)
        sql = "SELECT * FROM users LIMIT 100"
        result = RowLimitEnforcer.add_limit_clause(sql, 1000)
        assert "LIMIT 100" in result
        
        # Query with existing LIMIT (higher)
        sql = "SELECT * FROM users LIMIT 5000"
        result = RowLimitEnforcer.add_limit_clause(sql, 1000)
        assert "LIMIT 1000" in result
    
    def test_estimate_result_size(self):
        """Test result size estimation."""
        # With LIMIT
        sql = "SELECT * FROM users LIMIT 50"
        size = RowLimitEnforcer.estimate_result_size(sql)
        assert size == 50
        
        # Without LIMIT
        sql = "SELECT * FROM users"
        size = RowLimitEnforcer.estimate_result_size(sql)
        assert size == -1


@pytest.mark.asyncio
class TestValidationAgent:
    """Tests for ValidationAgent."""
    
    async def test_validate_safe_query(self):
        """Test validation of safe query."""
        agent = ValidationAgent(allow_destructive=False, max_rows=10000)
        
        sql_query = SQLQuery(
            sql="SELECT * FROM users WHERE status = 'active' LIMIT 100",
            confidence_score=0.9
        )
        
        result = await agent.validate_query(sql_query, "Get active users")
        
        assert result.success
        assert result.data.is_valid
        assert result.data.safe_to_execute
        assert len(result.data.errors) == 0
    
    async def test_validate_destructive_query(self):
        """Test validation rejects destructive query."""
        agent = ValidationAgent(allow_destructive=False, max_rows=10000)
        
        sql_query = SQLQuery(
            sql="DROP TABLE users",
            confidence_score=0.5
        )
        
        result = await agent.validate_query(sql_query, "Delete users table")
        
        assert result.success
        assert not result.data.is_valid
        assert not result.data.safe_to_execute
        assert len(result.data.errors) > 0
    
    async def test_validate_adds_limit(self):
        """Test that validation adds LIMIT clause when needed."""
        agent = ValidationAgent(allow_destructive=False, max_rows=1000)
        
        sql_query = SQLQuery(
            sql="SELECT * FROM users",
            confidence_score=0.8
        )
        
        result = await agent.validate_query(sql_query, "Get all users")
        
        assert result.success
        assert "LIMIT" in sql_query.sql.upper()


class TestSchemaFiltering:
    """Tests for schema filtering logic."""
    
    def test_filter_relevant_tables(self):
        """Test filtering relevant tables based on query."""
        # Mock data
        tables = [
            TableMetadata(
                name="users",
                schema="public",
                columns=[{"name": "id", "type": "int", "nullable": False}]
            ),
            TableMetadata(
                name="orders",
                schema="public",
                columns=[{"name": "id", "type": "int", "nullable": False}]
            ),
            TableMetadata(
                name="products",
                schema="public",
                columns=[{"name": "id", "type": "int", "nullable": False}]
            ),
        ]
        
        # This is a simplified version - the actual agent has more sophisticated logic
        query = "show me all users"
        query_words = query.lower().split()
        
        relevant = [t for t in tables if any(word in t.name.lower() for word in query_words)]
        
        assert len(relevant) == 1
        assert relevant[0].name == "users"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
