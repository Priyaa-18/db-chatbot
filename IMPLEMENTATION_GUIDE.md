# Enterprise Database Chatbot - Complete Implementation Guide

## Project Overview

This is a **production-ready** LLM-based chatbot system for querying enterprise databases using natural language. The system supports Snowflake, Databricks, PostgreSQL, MySQL, and can be extended to other databases.

## Key Features

✅ **Multi-Agent Architecture** - Modular design with specialized agents
✅ **Database Agnostic** - Works with major enterprise databases
✅ **LLM Providers** - Support for Anthropic Claude and OpenAI GPT
✅ **Security First** - Query validation, safety checks, audit logging
✅ **Auto Visualization** - Intelligent chart generation from results
✅ **Schema Discovery** - Automatic database introspection
✅ **Production Ready** - Error handling, logging, monitoring

## Architecture Components

### 1. Agents

**SchemaAgent** (`src/agents/schema_agent.py`)
- Discovers database schema
- Filters relevant tables based on query
- Infers relationships between tables
- Caches schema for performance

**SQLAgent** (`src/agents/sql_agent.py`)
- Generates SQL from natural language
- Uses LLM with schema context
- Provides explanations and confidence scores
- Supports complex queries (JOINs, aggregations, etc.)

**ValidationAgent** (`src/agents/validation_agent.py`)
- Validates SQL syntax
- Checks for destructive operations
- Enforces row limits
- Estimates query cost
- Prevents SQL injection

**ExecutionAgent** (`src/agents/execution_agent.py`)
- Executes validated queries
- Handles timeouts
- Provides helpful error messages
- Manages database connections

**VisualizationAgent** (`src/agents/visualization_agent.py`)
- Determines best chart type
- Generates interactive Plotly charts
- Handles large datasets
- Provides table fallback

### 2. Database Connectors

**Base Connector** (`src/database/base.py`)
- Abstract interface for all databases
- Connection pooling
- Schema introspection
- Query execution
- Caching

**Snowflake** (`src/database/snowflake_db.py`)
- Snowflake-specific connection handling
- Authentication support
- Warehouse management

**Databricks** (`src/database/databricks_db.py`)
- Databricks SQL endpoint connection
- Unity Catalog support
- Token authentication

### 3. LLM Providers

**Anthropic Claude** (`src/llm/anthropic_provider.py`)
- Claude Sonnet 4.5 (recommended)
- Structured JSON output
- High accuracy for SQL generation

**OpenAI GPT** (`src/llm/openai_provider.py`)
- GPT-4o support
- JSON mode
- Alternative to Claude

### 4. Orchestrator

**ChatbotOrchestrator** (`src/orchestrator.py`)
- Coordinates all agents
- Manages execution flow
- Error handling
- Logging and metrics
- Context management

## Installation & Setup

### Prerequisites

- Python 3.8+
- Database credentials (Snowflake or Databricks)
- LLM API key (Anthropic or OpenAI)

### Step 1: Install Dependencies

```bash
cd enterprise-db-chatbot
pip install -r requirements.txt
```

### Step 2: Configure Environment

Copy `.env.template` to `.env` and fill in your credentials:

```bash
cp .env.template .env
```

Edit `.env` with your actual credentials:

```env
# Choose your LLM provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Configure your database
DEFAULT_DATABASE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=mycompany
SNOWFLAKE_USER=myuser
SNOWFLAKE_PASSWORD=mypassword
SNOWFLAKE_DATABASE=ANALYTICS
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

### Step 3: Test Connection

```bash
python examples/run_chatbot.py
```

## Usage Examples

### Basic Usage

```python
from src.config import Settings
from src.orchestrator import ChatbotOrchestrator
import asyncio

async def main():
    settings = Settings()
    chatbot = ChatbotOrchestrator(settings)
    
    response = await chatbot.process_query(
        user_query="Show me top 10 customers by revenue",
        user_id="user123"
    )
    
    print(f"SQL: {response.sql.sql}")
    print(f"Results: {response.result.row_count} rows")

asyncio.run(main())
```

### Interactive Mode

```bash
python examples/run_chatbot.py --interactive
```

### With Visualization

```python
response = await chatbot.process_query(
    user_query="Show monthly sales trends",
    user_id="user123",
    include_visualization=True
)

# Save chart
with open("chart.html", "w") as f:
    f.write(response.chart_html)
```

## Query Examples

The chatbot can handle various types of queries:

1. **Simple Selection**
   - "Show me all active users"
   - "Get the top 10 products"

2. **Aggregations**
   - "Count orders by status"
   - "Sum revenue by region"
   - "Average order value by month"

3. **Filtering**
   - "Users who joined in the last 30 days"
   - "Products with stock below 100"
   - "Orders over $1000"

4. **Joins**
   - "Show me customers and their orders"
   - "Products with their categories"

5. **Time Series**
   - "Daily sales for last week"
   - "Monthly revenue trends for 2024"

6. **Rankings**
   - "Top 5 customers by lifetime value"
   - "Best selling products this quarter"

## Security Features

### 1. Query Validation

- **Syntax checking** - Validates SQL before execution
- **Destructive operations** - Blocks DROP, DELETE, TRUNCATE by default
- **SQL injection** - Prevents injection attacks
- **Row limits** - Enforces maximum result size

### 2. Access Control

- **User-based permissions** - Respects database permissions
- **Audit logging** - Tracks all queries
- **Error messages** - Safe error handling

### 3. Configuration

```python
# Enable/disable destructive queries
ALLOW_DESTRUCTIVE_QUERIES=false

# Set row limit
MAX_QUERY_ROWS=10000

# Query timeout
QUERY_TIMEOUT_SECONDS=300
```

## Performance Optimization

### 1. Caching

- **Schema cache** - Reduces database round trips
- **TTL configuration** - Configurable cache expiration

```python
SCHEMA_CACHE_TTL_SECONDS=3600  # 1 hour
```

### 2. Connection Pooling

- Automatic connection pool management
- Configurable pool size
- Connection health checks

### 3. Async Execution

- All agents run asynchronously
- Non-blocking I/O operations
- Parallel processing where possible

## Monitoring & Logging

### Structured Logging

All operations logged with:
- Timestamp
- User ID
- Query details
- Execution time
- Error details

### Metrics Tracked

- Query success/failure rates
- Average execution time
- LLM token usage
- Database connection metrics

### Log Levels

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Extending the System

### Add New Database

1. Create connector in `src/database/`:

```python
from src.database.base import DatabaseConnector

class MyDBConnector(DatabaseConnector):
    def get_connection_string(self) -> str:
        return f"mydb://{self.config['host']}/{self.config['database']}"
```

2. Update `config.py` with new database type
3. Add to orchestrator initialization

### Add Custom Validation Rules

```python
class CustomValidationAgent(ValidationAgent):
    async def validate_query(self, sql_query, user_query):
        result = await super().validate_query(sql_query, user_query)
        
        # Add custom validation
        if "sensitive_table" in sql_query.sql.lower():
            result.data.errors.append("Cannot query sensitive tables")
            result.data.safe_to_execute = False
        
        return result
```

### Customize LLM Prompts

Edit prompts in `src/agents/sql_agent.py`:

```python
def _build_system_prompt(self) -> str:
    return """Your custom system prompt..."""
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```
Solution: Check credentials in .env file
Verify network access to database
Test with native client first
```

**2. LLM API Errors**
```
Solution: Verify API key is correct
Check API quota/limits
Review error message for details
```

**3. SQL Generation Errors**
```
Solution: Improve schema context
Add example queries
Use lower temperature (0.0-0.2)
```

**4. Performance Issues**
```
Solution: Enable schema caching
Reduce max_query_rows
Add database indexes
```

## Best Practices

### 1. Schema Design
- Add table and column descriptions
- Use clear, descriptive names
- Document relationships
- Maintain metadata

### 2. Query Optimization
- Start with simple queries
- Provide example queries for training
- Use specific table/column names
- Include business context

### 3. Security
- Never store credentials in code
- Use environment variables
- Enable audit logging
- Review generated SQL before execution
- Set appropriate row limits

### 4. Production Deployment
- Use connection pooling
- Enable caching
- Set appropriate timeouts
- Monitor LLM costs
- Log all queries
- Set up alerts

## API Reference

### ChatbotOrchestrator

```python
class ChatbotOrchestrator:
    async def process_query(
        user_query: str,
        user_id: str,
        context: Optional[ConversationContext] = None,
        database_override: Optional[DatabaseType] = None,
        max_rows: Optional[int] = None,
        include_visualization: bool = True
    ) -> ChatbotResponse
```

### ChatbotResponse

```python
class ChatbotResponse:
    status: QueryStatus  # PENDING, SUCCESS, FAILED
    sql: SQLQuery  # Generated SQL
    validation: ValidationResult  # Validation results
    result: QueryResult  # Query results
    chart_html: str  # Visualization HTML
    error_message: str  # Error if any
    execution_time_ms: float  # Total time
```

## Testing

Run tests:

```bash
# All tests
pytest

# Specific test file
pytest tests/test_agents.py

# With coverage
pytest --cov=src tests/
```

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- GitHub Issues
- Email: support@example.com
- Documentation: https://docs.example.com

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Changelog

### v1.0.0 (2024-11-20)
- Initial release
- Multi-agent architecture
- Snowflake and Databricks support
- Claude and GPT support
- Auto visualization
- Comprehensive security features

---

Built with ❤️ for data teams everywhere.
