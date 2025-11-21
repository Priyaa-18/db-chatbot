# Enterprise Database Chatbot

A production-ready LLM-based chatbot for querying enterprise databases (Snowflake, Databricks, etc.) using natural language.

## Features

- 🔍 **Schema Discovery**: Automatic database schema introspection
- 🤖 **AI-Powered SQL Generation**: Natural language to SQL using LLMs
- ✅ **Query Validation**: Syntax checking and cost estimation
- 🚀 **Multi-Database Support**: Snowflake, Databricks, PostgreSQL, MySQL, and more
- 📊 **Visualization**: Automatic chart generation from query results
- 🔒 **Security**: Role-based access control and query safety checks
- 📝 **Audit Logging**: Full query history and user tracking

## Architecture

```
User Query → Orchestrator
              ↓
         State Manager
              ↓
    [Schema Agent] → Get relevant tables/columns
              ↓
    [SQL Generation Agent] → Generate SQL with LLM
              ↓
    [Validation Agent] → Check syntax & safety
              ↓
    [Execution Agent] → Run query on database
              ↓
    [Visualization Agent] → Generate charts
              ↓
         Response
```

## Installation

### 1. Clone and Setup
```bash
cd enterprise-db-chatbot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
LLM_PROVIDER=anthropic  # or 'openai'
LLM_MODEL=claude-sonnet-4-20250514

# Database Configuration - Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_ROLE=your_role

# Database Configuration - Databricks
DATABRICKS_SERVER_HOSTNAME=your_host.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/endpoints/xxxxx
DATABRICKS_TOKEN=your_token
DATABRICKS_CATALOG=your_catalog
DATABRICKS_SCHEMA=your_schema

# Application Settings
MAX_QUERY_ROWS=10000
QUERY_TIMEOUT_SECONDS=300
LOG_LEVEL=INFO
```

### 3. Run Examples
```bash
# Run example chatbot
python examples/run_chatbot.py

# Run with specific database
python examples/run_chatbot.py --database snowflake
python examples/run_chatbot.py --database databricks
```

## Usage

### Basic Usage

```python
from src.orchestrator import ChatbotOrchestrator
from src.config import Settings

# Initialize
settings = Settings()
chatbot = ChatbotOrchestrator(settings)

# Query database
response = await chatbot.process_query(
    user_query="Show me top 10 customers by revenue",
    user_id="user123"
)

print(f"SQL: {response.sql}")
print(f"Results: {response.data}")
print(f"Visualization: {response.chart_html}")
```

### Advanced Usage with Context

```python
# Multi-turn conversation with context
context = ConversationContext(user_id="user123")

response1 = await chatbot.process_query(
    "Show me sales by region",
    context=context
)

# Follow-up query uses context
response2 = await chatbot.process_query(
    "Now filter for last quarter",
    context=context
)
```

## Project Structure

```
enterprise-db-chatbot/
├── src/
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models (Pydantic)
│   ├── orchestrator.py        # Main orchestration logic
│   ├── agents/
│   │   ├── schema_agent.py    # Schema discovery
│   │   ├── sql_agent.py       # SQL generation
│   │   ├── validation_agent.py # Query validation
│   │   ├── execution_agent.py # Query execution
│   │   └── visualization_agent.py # Chart generation
│   ├── llm/
│   │   ├── base.py            # LLM base interface
│   │   ├── openai_provider.py # OpenAI implementation
│   │   └── anthropic_provider.py # Anthropic implementation
│   ├── database/
│   │   ├── base.py            # Database base interface
│   │   ├── snowflake_db.py    # Snowflake connector
│   │   └── databricks_db.py   # Databricks connector
│   └── utils/
│       ├── logger.py          # Structured logging
│       └── security.py        # Security utilities
├── tests/
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   └── test_integration.py
├── examples/
│   └── run_chatbot.py         # Example usage
├── requirements.txt
└── README.md
```

## Security Considerations

1. **Query Safety**
   - Automatic row limits
   - Timeout enforcement
   - No DROP/DELETE/TRUNCATE allowed by default
   - SQL injection prevention

2. **Access Control**
   - User-based permissions
   - Database-level authentication
   - Audit logging of all queries

3. **Data Privacy**
   - Schema metadata only sent to LLM
   - No actual data sent to LLM
   - Results filtered by user permissions

## Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src tests/
```

## Performance Optimization

- Connection pooling for databases
- Schema caching with TTL
- Query result pagination
- Async execution for I/O operations

## Monitoring

All operations are logged with structured logging:
- Query execution time
- LLM token usage
- Database connection metrics
- Error rates and types

## Extending

### Add New Database
1. Create connector in `src/database/`
2. Implement `DatabaseConnector` interface
3. Add configuration in `config.py`

### Add New LLM Provider
1. Create provider in `src/llm/`
2. Implement `LLMProvider` interface
3. Add to provider factory

### Custom Validation Rules
1. Extend `ValidationAgent`
2. Add custom rules in `validate_query()`

## License

MIT License

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: [Link to repo]
- Documentation: [Link to docs]
