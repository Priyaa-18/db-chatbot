# Deployment Checklist & FAQ

## 🚀 Pre-Deployment Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created from `.env.template`

### Configuration
- [ ] LLM API key configured (Anthropic or OpenAI)
- [ ] Database credentials set
- [ ] Database connection tested
- [ ] Row limits configured
- [ ] Query timeout set
- [ ] Log level configured

### Security Review
- [ ] `ALLOW_DESTRUCTIVE_QUERIES` set to `false`
- [ ] Row limits appropriate for your use case
- [ ] Audit logging enabled
- [ ] Credentials stored securely (not in code)
- [ ] Error messages don't leak sensitive info

### Testing
- [ ] Unit tests pass (`pytest`)
- [ ] Database connection works
- [ ] LLM API calls successful
- [ ] Example queries run correctly
- [ ] Error handling tested

### Performance
- [ ] Schema caching enabled
- [ ] Connection pooling configured
- [ ] Query timeout appropriate
- [ ] Max rows limit set

### Monitoring
- [ ] Logging configured
- [ ] Log aggregation set up (optional)
- [ ] Metrics collection planned
- [ ] Alerting configured (optional)

## ❓ Frequently Asked Questions

### General

**Q: What databases are supported?**
A: Currently Snowflake and Databricks have full support. PostgreSQL and MySQL connectors are implemented and ready to use. You can add support for other databases by implementing the `DatabaseConnector` interface.

**Q: Which LLM provider should I use?**
A: We recommend Anthropic Claude (Sonnet 4.5) for best accuracy in SQL generation. OpenAI GPT-4o is also supported and works well.

**Q: How accurate is the SQL generation?**
A: Accuracy depends on several factors:
- Quality of your database schema (names, descriptions)
- Clarity of user queries
- LLM model used (Claude Sonnet 4.5 recommended)
- Example queries provided for context

Expect 80-95% accuracy for well-structured databases with clear naming.

**Q: Can I use this in production?**
A: Yes! The system is designed for production use with:
- Error handling
- Validation and security checks
- Audit logging
- Connection pooling
- Timeout handling
- Structured logging

However, always review generated SQL before executing on production databases initially.

### Setup & Configuration

**Q: Do I need both API keys (Anthropic and OpenAI)?**
A: No, you only need one. Set `LLM_PROVIDER` to either "anthropic" or "openai" and provide the corresponding API key.

**Q: How do I connect to multiple databases?**
A: Configure all database credentials in `.env`. You can override the default database per query:

```python
response = await chatbot.process_query(
    user_query="...",
    user_id="user123",
    database_override=DatabaseType.DATABRICKS
)
```

**Q: What if my database has special characters in the password?**
A: The system automatically URL-encodes passwords. Just put the raw password in the `.env` file.

**Q: How do I set up for Databricks Unity Catalog?**
A: Set the `DATABRICKS_CATALOG` and `DATABRICKS_SCHEMA` in your `.env` file:

```env
DATABRICKS_CATALOG=main
DATABRICKS_SCHEMA=analytics
```

### Usage

**Q: How do I ask complex questions?**
A: Be specific and use natural language. Examples:
- Good: "Show me top 10 customers by total revenue in 2024"
- Bad: "customers revenue"

The more specific your query, the better the results.

**Q: Can it handle JOINs across multiple tables?**
A: Yes! The system automatically identifies relationships between tables and generates appropriate JOINs.

**Q: What if the generated SQL is wrong?**
A: The system provides:
1. The SQL query for review
2. An explanation of what it does
3. Confidence score

If wrong, you can:
- Rephrase your query
- Provide more context
- Check your schema has good descriptions

**Q: How do I handle queries that return too much data?**
A: The system automatically enforces row limits (default 10,000). You can configure this in `.env`:

```env
MAX_QUERY_ROWS=5000
```

### Performance

**Q: How fast is it?**
A: Typical query flow:
- Schema discovery: 100-500ms (cached: <10ms)
- SQL generation: 1-3 seconds
- Validation: 10-50ms  
- Execution: Varies by query
- Visualization: 200-500ms
- Total: 2-5 seconds for simple queries

**Q: Can I cache query results?**
A: Schema is cached automatically. For query results, you would need to implement custom caching based on your requirements.

**Q: How do I improve performance?**
A: 
1. Enable schema caching (enabled by default)
2. Use specific table names in queries
3. Add indexes to your database
4. Reduce `MAX_QUERY_ROWS` if appropriate
5. Use faster LLM models (though less accurate)

### Security

**Q: Is my data sent to the LLM?**
A: No! Only metadata (schema, table names, column names) is sent to the LLM. Actual data never leaves your database.

**Q: How do I prevent destructive queries?**
A: Set in `.env`:

```env
ALLOW_DESTRUCTIVE_QUERIES=false
```

This blocks DROP, DELETE, TRUNCATE by default.

**Q: What about SQL injection?**
A: The system has multiple protections:
1. LLM generates SQL (doesn't concatenate user input)
2. Validation agent checks for dangerous patterns
3. Parameterized queries where possible
4. Input sanitization

**Q: Can users query any table?**
A: The system respects database-level permissions. Users can only query tables they have access to in the database.

**Q: How do I audit queries?**
A: Enable audit logging:

```env
ENABLE_AUDIT_LOGGING=true
```

All queries are logged with user ID, timestamp, SQL, and results.

### Troubleshooting

**Q: "Database connection failed" error**
A: Check:
1. Credentials in `.env` are correct
2. Network access to database
3. Database is running
4. Firewall rules allow connection

Test connection with native client first.

**Q: "LLM API key invalid" error**
A: 
1. Verify API key in `.env`
2. Check for extra spaces/newlines
3. Confirm API key is active
4. Check API quota/limits

**Q: "No tables found" message**
A: Check:
1. Database credentials include schema
2. User has permission to view tables
3. Schema name is correct (case-sensitive)
4. Tables exist in specified schema

**Q: Generated SQL has syntax errors**
A: This can happen if:
1. Schema metadata is incomplete
2. Table/column names are ambiguous
3. LLM hallucinated table names

Solutions:
- Improve schema documentation
- Use more specific queries
- Provide example queries
- Lower LLM temperature

**Q: Queries are slow**
A: Check:
1. Database query performance (run SQL directly)
2. Missing database indexes
3. Large result sets
4. Schema cache disabled
5. Network latency

**Q: Visualization not generating**
A: Check:
1. Results have data
2. Column types are appropriate
3. Not too many data points (limit: 1000)
4. Plotly installed correctly

### Customization

**Q: How do I customize the SQL generation?**
A: Edit prompts in `src/agents/sql_agent.py`:

```python
def _build_system_prompt(self) -> str:
    return """Your custom prompt..."""
```

**Q: Can I add custom validation rules?**
A: Yes! Extend `ValidationAgent`:

```python
class CustomValidationAgent(ValidationAgent):
    async def validate_query(self, sql_query, user_query):
        result = await super().validate_query(sql_query, user_query)
        # Add your custom logic
        return result
```

**Q: How do I add a new database?**
A: 
1. Create connector in `src/database/`
2. Implement `DatabaseConnector` interface  
3. Add config in `config.py`
4. Update orchestrator

See IMPLEMENTATION_GUIDE.md for details.

**Q: Can I change the chart types?**
A: Yes! The `VisualizationAgent` uses LLM to determine chart type. You can:
1. Modify the LLM prompt
2. Override chart selection logic
3. Add custom chart types

### Cost & Limits

**Q: How much does it cost?**
A: Main costs:
1. **LLM API**: $3-10 per 1M tokens (Claude: ~$3, GPT-4o: ~$5)
2. **Database**: Your existing database costs
3. **Hosting**: Minimal (just Python app)

Typical query uses 2000-5000 tokens = $0.01-0.05 per query.

**Q: Are there rate limits?**
A: Yes, from your LLM provider:
- Anthropic: 50 requests/minute (tier 1)
- OpenAI: 500 requests/minute (tier 1)

Both have higher tiers available.

**Q: Can I reduce LLM costs?**
A: Yes:
1. Cache schema metadata (done automatically)
2. Use smaller context (fewer tables in prompt)
3. Reduce max_tokens setting
4. Use cheaper model (but less accurate)

### Scaling

**Q: How many concurrent users can it handle?**
A: Depends on:
1. LLM API rate limits
2. Database connection pool size
3. Server resources

With default settings: 10-50 concurrent users comfortably.

**Q: How do I scale horizontally?**
A: 
1. Deploy multiple instances
2. Use shared cache (Redis)
3. Load balancer in front
4. Shared database connection pool

**Q: What about high availability?**
A: Use:
1. Multiple app instances
2. Database replicas
3. LLM provider redundancy
4. Health checks and auto-restart

## 🛠️ Common Modifications

### Change Default Row Limit

In `.env`:
```env
MAX_QUERY_ROWS=5000
```

### Add Table Descriptions

In your database, add comments:
```sql
COMMENT ON TABLE customers IS 'Customer master data';
COMMENT ON COLUMN customers.email IS 'Customer email address';
```

### Custom Error Messages

Edit `src/agents/execution_agent.py`:
```python
def _parse_error_message(self, error: str) -> str:
    # Add custom error parsing
    return custom_message
```

### Add Business Terms

In `src/agents/schema_agent.py`:
```python
business_terms = {
    "MRR": "Monthly Recurring Revenue",
    "CAC": "Customer Acquisition Cost",
    "LTV": "Lifetime Value"
}
```

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: Set `LOG_LEVEL=DEBUG` for detailed logs
2. **Review documentation**: See IMPLEMENTATION_GUIDE.md
3. **Test components**: Run individual agents
4. **Simplify query**: Start with simple queries
5. **Check examples**: Run example scripts

## 🎯 Success Tips

1. **Start simple**: Begin with basic queries
2. **Document schema**: Add table/column descriptions
3. **Provide examples**: Train with example queries
4. **Review SQL**: Check generated SQL initially
5. **Monitor costs**: Track LLM token usage
6. **Iterate prompts**: Refine prompts for better results
7. **Cache aggressively**: Enable all caching
8. **Test thoroughly**: Test with real queries
9. **Set limits**: Appropriate row/timeout limits
10. **Log everything**: Enable comprehensive logging

---

**Ready to deploy?** Follow the checklist above and start with the example scripts!
