"""Trending Topics Agent Server."""

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
load_dotenv()
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'

# Verify API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

print(f"✅ Google API Key loaded: {api_key[:-10]}...")

# Create the Trending Topics ADK Agent
trending_agent = Agent(
    model="gemini-2.5-flash",
    name="trending_topics_agent",
    instruction="""
    You are a social media trends analyst. Your job is to search the web for current trending topics,
    particularly from social platforms.

    When asked about trends:
    1. Search for "trending topics today" or similar queries
    2. Extract the top 3 trending topics
    3. Return them in a JSON format

    Focus on current, real-time trends from the last 24 hours.

    You MUST return your response in the following JSON format:
    {
        "trends": [
            {
                "topic": "Topic name",
                "description": "Brief description (1-2 sentences)",
                "reason": "Why it's trending"
            },
            {
                "topic": "Topic name",
                "description": "Brief description (1-2 sentences)",
                "reason": "Why it's trending"
            },
            {
                "topic": "Topic name",
                "description": "Brief description (1-2 sentences)",
                "reason": "Why it's trending"
            }
        ]
    }

    Only return the JSON object, no additional text.
    """,
    tools=[google_search],
)

def create_trending_agent_server(host="0.0.0.0", port=10020):
    """Create A2A server for Trending Agent."""
    endpoint_url = os.getenv("AGENT_ENDPOINT_URL", f"http://{host}:{port}")

    return create_agent_a2a_server(
        agent=trending_agent,
        name="Trending Topics Agent",
        description="Searches the web for current trending topics from social media",
        endpoint_url=endpoint_url,
        skills=[
            AgentSkill(
                id="find_trends",
                name="Find Trending Topics",
                description="Searches for current trending topics on social media",
                endpoint_url=endpoint_url,
                tags=["trends", "social media", "twitter", "current events"],
                examples=[
                    "What's trending today?",
                    "Show me current Twitter trends",
                    "What are people talking about on social media?",
                ],
            )
        ],
        host=host,
        port=port,
        status_message="Searching for trending topics...",
        artifact_name="trending_topics"
    )

async def main():
    """Run the trending agent server."""
    port = int(os.getenv('PORT', 10020))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Trending Topics Agent on {host}:{port}")
    
    app = create_trending_agent_server(host=host, port=port)
    
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