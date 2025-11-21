"""
Visualization Agent - Generates charts and visualizations from query results.
"""
import time
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any
from src.models import AgentResult, QueryResult, ChartConfig
from src.llm.base import LLMProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisualizationAgent:
    """Agent responsible for generating visualizations."""
    
    def __init__(self, llm_provider: LLMProvider, max_chart_points: int = 1000):
        self.llm = llm_provider
        self.max_chart_points = max_chart_points
    
    async def generate_visualization(
        self,
        query_result: QueryResult,
        user_query: str
    ) -> AgentResult:
        """
        Generate visualization from query results.
        
        Args:
            query_result: Results from query execution
            user_query: Original user query for context
        
        Returns:
            AgentResult with HTML chart
        """
        start_time = time.time()
        
        try:
            # Check if data is suitable for visualization
            if not query_result.data:
                logger.info("No data to visualize")
                return AgentResult(
                    success=True,
                    data=None,
                    metadata={"message": "No data to visualize"},
                    execution_time_ms=(time.time() - start_time) * 1000
                )
            
            if len(query_result.data) > self.max_chart_points:
                logger.warning(f"Too many data points ({len(query_result.data)}), limiting to {self.max_chart_points}")
                query_result.data = query_result.data[:self.max_chart_points]
            
            # Determine best chart type using LLM
            chart_config = await self._determine_chart_type(query_result, user_query)
            
            # Generate chart
            chart_html = self._create_chart(query_result.data, chart_config)
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(
                "Visualization generated",
                chart_type=chart_config.chart_type,
                data_points=len(query_result.data),
                execution_time_ms=execution_time
            )
            
            return AgentResult(
                success=True,
                data=chart_html,
                metadata={
                    "chart_type": chart_config.chart_type,
                    "data_points": len(query_result.data)
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error("Failed to generate visualization", error=str(e))
            return AgentResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
    
    async def _determine_chart_type(
        self,
        query_result: QueryResult,
        user_query: str
    ) -> ChartConfig:
        """Use LLM to determine best chart type and configuration."""
        
        # Analyze columns
        columns = query_result.columns
        sample_data = query_result.data[:5]  # First 5 rows as sample
        
        prompt = f"""Based on the user's query and the data structure, determine the best chart type and configuration.

User Query: {user_query}

Data Structure:
Columns: {', '.join(columns)}
Sample Data: {sample_data}

Choose the most appropriate chart type and specify the axes:
- bar: For comparing categories
- line: For trends over time or ordered data
- scatter: For relationships between two numeric variables
- pie: For showing proportions (only if suitable)
- table: If data is not suitable for charts

Respond with JSON only."""
        
        system_prompt = "You are a data visualization expert. Recommend the best chart type and configuration for the given data."
        
        try:
            response = await self.llm.generate_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format={
                    "chart_type": "string (bar, line, scatter, pie, or table)",
                    "x_axis": "string (column name for x-axis)",
                    "y_axis": "string (column name for y-axis)",
                    "title": "string (suggested chart title)",
                    "color_column": "string or null (column for color coding)"
                }
            )
            
            return ChartConfig(
                chart_type=response.get("chart_type", "bar"),
                x_axis=response.get("x_axis"),
                y_axis=response.get("y_axis"),
                title=response.get("title", "Query Results"),
                color_column=response.get("color_column")
            )
            
        except Exception as e:
            logger.warning(f"Failed to determine chart type with LLM: {e}, using defaults")
            # Fallback to simple heuristic
            return self._simple_chart_heuristic(query_result)
    
    def _simple_chart_heuristic(self, query_result: QueryResult) -> ChartConfig:
        """Simple heuristic for chart type when LLM fails."""
        columns = query_result.columns
        
        # Default to bar chart with first two columns
        if len(columns) >= 2:
            return ChartConfig(
                chart_type="bar",
                x_axis=columns[0],
                y_axis=columns[1],
                title="Query Results"
            )
        else:
            return ChartConfig(
                chart_type="table",
                title="Query Results"
            )
    
    def _create_chart(self, data: List[Dict[str, Any]], config: ChartConfig) -> str:
        """Create chart using Plotly."""
        
        import pandas as pd
        df = pd.DataFrame(data)
        
        # Handle table display
        if config.chart_type == "table" or not config.x_axis or not config.y_axis:
            fig = go.Figure(data=[go.Table(
                header=dict(values=list(df.columns),
                           fill_color='paleturquoise',
                           align='left'),
                cells=dict(values=[df[col] for col in df.columns],
                          fill_color='lavender',
                          align='left'))
            ])
        
        # Bar chart
        elif config.chart_type == "bar":
            fig = px.bar(
                df,
                x=config.x_axis,
                y=config.y_axis,
                color=config.color_column,
                title=config.title
            )
        
        # Line chart
        elif config.chart_type == "line":
            fig = px.line(
                df,
                x=config.x_axis,
                y=config.y_axis,
                color=config.color_column,
                title=config.title
            )
        
        # Scatter plot
        elif config.chart_type == "scatter":
            fig = px.scatter(
                df,
                x=config.x_axis,
                y=config.y_axis,
                color=config.color_column,
                title=config.title
            )
        
        # Pie chart
        elif config.chart_type == "pie":
            fig = px.pie(
                df,
                names=config.x_axis,
                values=config.y_axis,
                title=config.title
            )
        
        else:
            # Default to bar
            fig = px.bar(df, x=config.x_axis, y=config.y_axis, title=config.title)
        
        # Update layout for better appearance
        fig.update_layout(
            template="plotly_white",
            height=500,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Convert to HTML
        return fig.to_html(include_plotlyjs='cdn', div_id="chart")
