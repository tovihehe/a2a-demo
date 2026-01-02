"""Trend Analyzer Agent Server."""

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search

# Add shared directory to path
# sys.path.append(str(Path(__file__).parent.parent / "shared"))
from base_executor import create_agent_a2a_server
from a2a.types import AgentSkill

# Load environment variables
load_dotenv('.env', override=True)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'

# Verify API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

print(f"✅ Google API Key loaded: {api_key[:-10]}...")

# Create the Trend Analyzer ADK Agent
analyzer_agent = Agent(
    model="gemini-1.5-flash",
    name="trend_analyzer_agent",
    instruction="""
    You are a data analyst specializing in trend analysis. When given a trending topic,
    perform deep research to find quantitative data and insights.

    For each trend you analyze:
    1. Search for statistics, numbers, and metrics related to the trend
    2. Look for:
       - Engagement metrics (views, shares, mentions)
       - Growth rates and timeline
       - Geographic distribution
       - Related hashtags or keywords
    3. Provide concrete numbers and data points

    Keep it somehow concise

    Always prioritize quantitative information over qualitative descriptions.
    """,
    tools=[google_search],
)

def create_analyzer_agent_server(host="0.0.0.0", port=10021):
    """Create A2A server for Analyzer Agent."""
    return create_agent_a2a_server(
        agent=analyzer_agent,
        name="Trend Analyzer Agent",
        description="Performs deep analysis of trends with quantitative data",
        skills=[
            AgentSkill(
                id="analyze_trend",
                name="Analyze Trend",
                description="Provides quantitative analysis of a specific trend",
                tags=["analysis", "data", "metrics", "statistics"],
                examples=[
                    "Analyze the #ClimateChange trend",
                    "Get metrics for the Taylor Swift trend",
                    "Provide data analysis for AI adoption trend",
                ],
            )
        ],
        host=host,
        port=port,
        status_message="Analyzing trend with quantitative data...",
        artifact_name="trend_analysis"
    )

async def main():
    """Run the analyzer agent server."""
    port = int(os.getenv('PORT', 10021))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Trend Analyzer Agent on {host}:{port}")
    
    app = create_analyzer_agent_server(host=host, port=port)
    
    config = uvicorn.Config(
        app.build(),
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
