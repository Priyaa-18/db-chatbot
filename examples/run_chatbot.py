"""
Example usage of the Enterprise Database Chatbot.

Run this script to test the chatbot with sample queries.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings
from src.orchestrator import ChatbotOrchestrator
from src.utils.logger import setup_logging, get_logger
from src.models import DatabaseType

logger = get_logger(__name__)


async def main():
    """Main function to run example queries."""
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    logger.info("=" * 80)
    logger.info("Enterprise Database Chatbot - Example Usage")
    logger.info("=" * 80)
    
    try:
        # Load settings
        settings = Settings()
        logger.info(f"Loaded settings - Database: {settings.default_database_type}, LLM: {settings.llm_provider}")
        
        # Initialize chatbot
        chatbot = ChatbotOrchestrator(settings)
        logger.info("Chatbot initialized successfully")
        
        # Test connection
        logger.info("\nTesting database connection...")
        if not chatbot.test_connection():
            logger.error("Database connection test failed!")
            return
        logger.info("✓ Database connection successful")
        
        # Example queries
        queries = [
            "Show me the top 10 customers by total revenue",
            "What were the sales by region for last quarter?",
            "Count the number of orders by status",
            "Find products with inventory below 100 units",
            "Show me monthly revenue trends for 2024",
        ]
        
        print("\n" + "=" * 80)
        print("Running Example Queries")
        print("=" * 80)
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'─' * 80}")
            print(f"Query {i}: {query}")
            print(f"{'─' * 80}")
            
            # Process query
            response = await chatbot.process_query(
                user_query=query,
                user_id="demo_user",
                include_visualization=True
            )
            
            # Display results
            print(f"\nStatus: {response.status.value}")
            
            if response.sql:
                print(f"\nGenerated SQL:")
                print(f"  {response.sql.sql}")
                if response.sql.explanation:
                    print(f"\nExplanation: {response.sql.explanation}")
                if response.sql.confidence_score:
                    print(f"Confidence: {response.sql.confidence_score:.2%}")
            
            if response.validation:
                if response.validation.warnings:
                    print(f"\nWarnings:")
                    for warning in response.validation.warnings:
                        print(f"  ⚠ {warning}")
                if response.validation.errors:
                    print(f"\nErrors:")
                    for error in response.validation.errors:
                        print(f"  ✗ {error}")
            
            if response.result:
                print(f"\nResults:")
                print(f"  Rows: {response.result.row_count}")
                print(f"  Columns: {', '.join(response.result.columns)}")
                print(f"  Execution time: {response.result.execution_time_ms:.2f}ms")
                
                # Show first few rows
                if response.result.data:
                    print(f"\n  Sample data (first 5 rows):")
                    for idx, row in enumerate(response.result.data[:5], 1):
                        print(f"    {idx}. {row}")
            
            if response.chart_html:
                print(f"\n  ✓ Visualization generated")
                # Save chart to file
                chart_file = f"example_chart_{i}.html"
                with open(chart_file, 'w') as f:
                    f.write(response.chart_html)
                print(f"  Saved to: {chart_file}")
            
            if response.error_message:
                print(f"\n✗ Error: {response.error_message}")
            
            print(f"\nTotal execution time: {response.execution_time_ms:.2f}ms")
            
            # Pause between queries
            await asyncio.sleep(1)
        
        print("\n" + "=" * 80)
        print("Example queries completed!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


def interactive_mode():
    """Run chatbot in interactive mode."""
    
    setup_logging(log_level="INFO")
    
    print("\n" + "=" * 80)
    print("Enterprise Database Chatbot - Interactive Mode")
    print("=" * 80)
    print("Type your queries below. Type 'exit' or 'quit' to stop.\n")
    
    try:
        settings = Settings()
        chatbot = ChatbotOrchestrator(settings)
        
        # Test connection
        if not chatbot.test_connection():
            print("✗ Database connection failed!")
            return
        print("✓ Connected to database\n")
        
        while True:
            try:
                # Get user input
                query = input("Your query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                # Process query
                print("\nProcessing...")
                response = asyncio.run(chatbot.process_query(
                    user_query=query,
                    user_id="interactive_user",
                    include_visualization=True
                ))
                
                # Display results
                print(f"\n{'─' * 80}")
                print(f"Status: {response.status.value}")
                
                if response.sql:
                    print(f"\nSQL: {response.sql.sql}")
                
                if response.result:
                    print(f"\nResults: {response.result.row_count} rows")
                    if response.result.data:
                        print("\nFirst 10 rows:")
                        for idx, row in enumerate(response.result.data[:10], 1):
                            print(f"{idx}. {row}")
                
                if response.error_message:
                    print(f"\nError: {response.error_message}")
                
                print(f"\nExecution time: {response.execution_time_ms:.2f}ms")
                print(f"{'─' * 80}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")
    
    except Exception as e:
        print(f"Failed to initialize: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enterprise Database Chatbot Example")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--database",
        "-d",
        choices=["snowflake", "databricks"],
        help="Override default database"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        asyncio.run(main())
