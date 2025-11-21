"""
Data models for the enterprise database chatbot.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatabaseType(str, Enum):
    """Supported database types."""
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class QueryStatus(str, Enum):
    """Query execution status."""
    PENDING = "pending"
    VALIDATING = "validating"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TableMetadata(BaseModel):
    """Metadata for a database table."""
    name: str
    schema: str
    columns: List[Dict[str, str]]  # [{name: str, type: str, nullable: bool}]
    row_count: Optional[int] = None
    description: Optional[str] = None


class SchemaContext(BaseModel):
    """Database schema context for LLM."""
    tables: List[TableMetadata]
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    common_queries: List[str] = Field(default_factory=list)
    business_terms: Dict[str, str] = Field(default_factory=dict)


class SQLQuery(BaseModel):
    """Generated SQL query."""
    sql: str
    explanation: Optional[str] = None
    tables_used: List[str] = Field(default_factory=list)
    estimated_rows: Optional[int] = None
    confidence_score: Optional[float] = None


class ValidationResult(BaseModel):
    """Result of query validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    estimated_cost: Optional[float] = None
    safe_to_execute: bool = True


class QueryResult(BaseModel):
    """Result of query execution."""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class ChartConfig(BaseModel):
    """Configuration for chart generation."""
    chart_type: str  # bar, line, scatter, pie, etc.
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    title: Optional[str] = None
    color_column: Optional[str] = None


class ConversationContext(BaseModel):
    """Context for multi-turn conversations."""
    user_id: str
    session_id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    query_history: List[Dict[str, Any]] = Field(default_factory=list)
    schema_cache: Optional[SchemaContext] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ChatbotRequest(BaseModel):
    """Request to the chatbot."""
    user_query: str
    user_id: str
    context: Optional[ConversationContext] = None
    database_override: Optional[DatabaseType] = None
    max_rows: Optional[int] = None
    include_visualization: bool = True


class ChatbotResponse(BaseModel):
    """Response from the chatbot."""
    query_id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: QueryStatus
    user_query: str
    sql: Optional[SQLQuery] = None
    validation: Optional[ValidationResult] = None
    result: Optional[QueryResult] = None
    chart_html: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentResult(BaseModel):
    """Generic result from an agent."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0
