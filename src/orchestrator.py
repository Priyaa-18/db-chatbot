"""
Main Orchestrator - Coordinates all agents to process user queries.
"""
import time
from typing import Optional
from src.models import (
    ChatbotRequest, ChatbotResponse, QueryStatus, DatabaseType,
    ConversationContext
)
from src.config import Settings
from src.agents.schema_agent import SchemaAgent
from src.agents.sql_agent import SQLAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.execution_agent import ExecutionAgent
from src.agents.visualization_agent import VisualizationAgent
from src.database.base import DatabaseConnector
from src.database.snowflake_db import SnowflakeConnector
from src.database.databricks_db import DatabricksConnector
from src.llm.base import LLMProvider
from src.llm.anthropic_provider import AnthropicProvider
from src.llm.openai_provider import OpenAIProvider
from src.utils.logger import get_logger, LogContext

logger = get_logger(__name__)


class ChatbotOrchestrator:
    """Main orchestrator for the enterprise database chatbot."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize LLM provider
        self.llm_provider = self._initialize_llm()
        
        # Initialize database connector
        self.db_connector = self._initialize_database()
        
        # Initialize agents
        self.schema_agent = SchemaAgent(self.db_connector)
        self.sql_agent = SQLAgent(self.llm_provider)
        self.validation_agent = ValidationAgent(
            allow_destructive=settings.allow_destructive_queries,
            max_rows=settings.max_query_rows
        )
        self.execution_agent = ExecutionAgent(
            self.db_connector,
            timeout_seconds=settings.query_timeout_seconds
        )
        self.visualization_agent = VisualizationAgent(
            self.llm_provider,
            max_chart_points=settings.max_chart_points
        )
        
        logger.info("ChatbotOrchestrator initialized successfully")
    
    def _initialize_llm(self) -> LLMProvider:
        """Initialize LLM provider based on configuration."""
        if self.settings.llm_provider.value == "anthropic":
            if not self.settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return AnthropicProvider(
                api_key=self.settings.anthropic_api_key,
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens
            )
        elif self.settings.llm_provider.value == "openai":
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return OpenAIProvider(
                api_key=self.settings.openai_api_key,
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                max_tokens=self.settings.llm_max_tokens
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")
    
    def _initialize_database(self, db_type: Optional[DatabaseType] = None) -> DatabaseConnector:
        """Initialize database connector based on configuration."""
        if db_type is None:
            db_type = self.settings.default_database_type
        
        # Validate configuration
        if not self.settings.validate_config(db_type):
            raise ValueError(f"Invalid configuration for database type: {db_type}")
        
        config = self.settings.get_database_config(db_type)
        
        if db_type == DatabaseType.SNOWFLAKE:
            return SnowflakeConnector(config)
        elif db_type == DatabaseType.DATABRICKS:
            return DatabricksConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    async def process_query(
        self,
        user_query: str,
        user_id: str,
        context: Optional[ConversationContext] = None,
        database_override: Optional[DatabaseType] = None,
        max_rows: Optional[int] = None,
        include_visualization: bool = True
    ) -> ChatbotResponse:
        """
        Process a user query through the entire pipeline.
        
        Args:
            user_query: Natural language query from user
            user_id: User identifier
            context: Optional conversation context
            database_override: Override default database
            max_rows: Maximum rows to return
            include_visualization: Whether to generate visualization
        
        Returns:
            ChatbotResponse with results
        """
        start_time = time.time()
        
        # Create request
        request = ChatbotRequest(
            user_query=user_query,
            user_id=user_id,
            context=context,
            database_override=database_override,
            max_rows=max_rows or self.settings.max_query_rows,
            include_visualization=include_visualization
        )
        
        # Add logging context
        with LogContext(user_id=user_id, query=user_query[:100]):
            logger.info("Processing query started")
            
            # Initialize response
            response = ChatbotResponse(
                status=QueryStatus.PENDING,
                user_query=user_query
            )
            
            try:
                # Step 1: Get schema context
                logger.info("Step 1: Getting schema context")
                schema_result = await self.schema_agent.get_schema_context(
                    user_query=user_query,
                    use_cache=True
                )
                
                if not schema_result.success:
                    response.status = QueryStatus.FAILED
                    response.error_message = f"Failed to get schema: {schema_result.error}"
                    return response
                
                schema_context = schema_result.data
                
                # Step 2: Generate SQL
                logger.info("Step 2: Generating SQL")
                sql_result = await self.sql_agent.generate_sql(
                    user_query=user_query,
                    schema_context=schema_context
                )
                
                if not sql_result.success:
                    response.status = QueryStatus.FAILED
                    response.error_message = f"Failed to generate SQL: {sql_result.error}"
                    return response
                
                response.sql = sql_result.data
                
                # Step 3: Validate SQL
                logger.info("Step 3: Validating SQL")
                response.status = QueryStatus.VALIDATING
                
                validation_result = await self.validation_agent.validate_query(
                    sql_query=response.sql,
                    user_query=user_query
                )
                
                if not validation_result.success:
                    response.status = QueryStatus.FAILED
                    response.error_message = f"Validation failed: {validation_result.error}"
                    return response
                
                response.validation = validation_result.data
                
                if not response.validation.safe_to_execute:
                    response.status = QueryStatus.FAILED
                    response.error_message = "Query failed safety validation: " + "; ".join(response.validation.errors)
                    return response
                
                # Step 4: Execute query
                logger.info("Step 4: Executing query")
                response.status = QueryStatus.EXECUTING
                
                execution_result = await self.execution_agent.execute_query(
                    sql_query=response.sql,
                    max_rows=request.max_rows
                )
                
                if not execution_result.success:
                    response.status = QueryStatus.FAILED
                    response.error_message = f"Execution failed: {execution_result.error}"
                    return response
                
                response.result = execution_result.data
                
                # Step 5: Generate visualization (optional)
                if include_visualization and response.result.row_count > 0:
                    logger.info("Step 5: Generating visualization")
                    
                    viz_result = await self.visualization_agent.generate_visualization(
                        query_result=response.result,
                        user_query=user_query
                    )
                    
                    if viz_result.success and viz_result.data:
                        response.chart_html = viz_result.data
                
                # Success!
                response.status = QueryStatus.SUCCESS
                execution_time = (time.time() - start_time) * 1000
                response.execution_time_ms = execution_time
                
                logger.info(
                    "Query processing completed",
                    status="success",
                    execution_time_ms=execution_time,
                    rows_returned=response.result.row_count if response.result else 0
                )
                
                return response
                
            except Exception as e:
                logger.error("Unexpected error processing query", error=str(e))
                response.status = QueryStatus.FAILED
                response.error_message = f"Unexpected error: {str(e)}"
                response.execution_time_ms = (time.time() - start_time) * 1000
                return response
    
    def test_connection(self) -> bool:
        """Test database connection."""
        return self.db_connector.test_connection()
    
    def clear_cache(self):
        """Clear all caches."""
        self.db_connector.clear_cache()
        logger.info("Caches cleared")
