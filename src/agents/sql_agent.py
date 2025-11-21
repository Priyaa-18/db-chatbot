"""
SQL Agent - Generates SQL queries from natural language using LLM.
"""
import time
import json
from typing import Optional
from src.models import AgentResult, SQLQuery, SchemaContext
from src.llm.base import LLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SQLAgent:
    """Agent responsible for generating SQL from natural language."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    async def generate_sql(
        self,
        user_query: str,
        schema_context: SchemaContext
    ) -> AgentResult:
        """
        Generate SQL query from natural language.
        
        Args:
            user_query: The user's natural language query
            schema_context: Database schema context
        
        Returns:
            AgentResult with SQLQuery
        """
        start_time = time.time()
        
        try:
            # Build prompt with schema context
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(user_query, schema_context)
            
            # Generate structured SQL response
            response = await self.llm.generate_structured(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format={
                    "sql": "string - the SQL query",
                    "explanation": "string - explanation of what the query does",
                    "tables_used": ["list of table names used"],
                    "confidence_score": "float between 0 and 1"
                }
            )
            
            # Parse response into SQLQuery model
            sql_query = SQLQuery(
                sql=response["sql"],
                explanation=response.get("explanation"),
                tables_used=response.get("tables_used", []),
                confidence_score=response.get("confidence_score")
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                "SQL generated",
                sql_length=len(sql_query.sql),
                tables_used=len(sql_query.tables_used),
                confidence=sql_query.confidence_score,
                execution_time_ms=execution_time
            )
            
            return AgentResult(
                success=True,
                data=sql_query,
                metadata={
                    "tables_used": sql_query.tables_used,
                    "confidence": sql_query.confidence_score
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error("Failed to generate SQL", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for SQL generation."""
        return """You are an expert SQL query generator. Your task is to convert natural language questions into accurate SQL queries.

Guidelines:
1. Generate syntactically correct SQL queries
2. Use proper JOINs when querying multiple tables
3. Always use explicit column names (avoid SELECT *)
4. Include appropriate WHERE clauses for filtering
5. Use aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
6. Add ORDER BY for ranking/sorting queries
7. Use LIMIT to prevent returning too many rows
8. Be case-insensitive in comparisons using LOWER() or UPPER()
9. Handle NULL values appropriately
10. Write queries that are optimized for performance

You must respond with valid JSON containing:
- sql: The SQL query string
- explanation: Brief explanation of what the query does
- tables_used: List of table names used in the query
- confidence_score: Your confidence in the query (0.0 to 1.0)

Important: Only use tables and columns that are provided in the schema context."""
    
    def _build_user_prompt(self, user_query: str, schema_context: SchemaContext) -> str:
        """Build user prompt with query and schema context."""
        # Format schema information
        schema_text = self._format_schema_context(schema_context)
        
        prompt = f"""User Question: {user_query}

Database Schema:
{schema_text}

Generate a SQL query that answers the user's question using the provided schema.
Remember to:
- Only use tables and columns that exist in the schema
- Write clean, readable SQL
- Include your confidence score based on schema completeness and query complexity

Respond with JSON only."""
        
        return prompt
    
    def _format_schema_context(self, schema_context: SchemaContext) -> str:
        """Format schema context for prompt."""
        schema_lines = []
        
        for table in schema_context.tables:
            schema_lines.append(f"\nTable: {table.schema}.{table.name}")
            if table.description:
                schema_lines.append(f"  Description: {table.description}")
            
            schema_lines.append("  Columns:")
            for col in table.columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                schema_lines.append(f"    - {col['name']} ({col['type']}) {nullable}")
            
            if table.row_count:
                schema_lines.append(f"  Approximate rows: {table.row_count:,}")
        
        # Add relationships if available
        if schema_context.relationships:
            schema_lines.append("\nTable Relationships:")
            for rel in schema_context.relationships:
                schema_lines.append(
                    f"  {rel['from_table']}.{rel['from_column']} -> "
                    f"{rel['to_table']}.{rel['to_column']}"
                )
        
        # Add business terms if available
        if schema_context.business_terms:
            schema_lines.append("\nBusiness Terms:")
            for term, definition in schema_context.business_terms.items():
                schema_lines.append(f"  {term}: {definition}")
        
        return "\n".join(schema_lines)
