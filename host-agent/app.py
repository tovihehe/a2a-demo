"""Host Agent Server - Orchestrates other agents."""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

import httpx
import uvicorn
from dotenv import load_dotenv
from google.adk.agents import Agent

# Add shared directory to path
# sys.path.append(str(Path(__file__).parent.parent / "shared"))
from base_executor import create_agent_a2a_server
from a2a.types import AgentSkill, AgentCard, MessageSendParams, SendMessageRequest
from a2a.client import A2AClient

# Load environment variables
load_dotenv()
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'

# Verify API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

print(f"✅ Google API Key loaded: {api_key[:-10]}...")

class A2AToolClient:
    """A2A client for host agent with enhanced error handling."""

    def __init__(self, default_timeout: float = 160.0):
        self._agent_info_cache: dict[str, dict[str, Any] | None] = {}
        self.default_timeout = default_timeout
        
        # Pre-register agents using environment variables with validation
        self.trending_url = self._get_validated_url('TRENDING_AGENT_URL', 'http://localhost:10020/')
        self.analyzer_url = self._get_validated_url('ANALYZER_AGENT_URL', 'http://localhost:10021/')
        
        print(f"🔌 Trending Agent URL: {self.trending_url}")
        print(f"🔌 Analyzer Agent URL: {self.analyzer_url}")
        
        self.add_remote_agent(self.trending_url)
        self.add_remote_agent(self.analyzer_url)

    def _get_validated_url(self, env_var: str, default: str) -> str:
        """Get and validate URL from environment variable."""
        url = os.getenv(env_var, default).rstrip('/')
        if not url.startswith('http'):
            url = 'http://' + url
        return url

    def add_remote_agent(self, agent_url: str):
        """Add agent to the list of available remote agents."""
        normalized_url = agent_url.rstrip('/')
        if normalized_url not in self._agent_info_cache:
            self._agent_info_cache[normalized_url] = None

    async def list_remote_agents(self) -> dict[str, dict[str, Any]]:
        """List available remote agents with caching and async support."""
        if not self._agent_info_cache:
            return {}

        remote_agents_info = {}
        for agent_url in list(self._agent_info_cache.keys()):
            try:
                timeout_config = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.get(f"{agent_url}/.well-known/agent.json")
                    response.raise_for_status()
                    agent_data = response.json()
                    self._agent_info_cache[agent_url] = agent_data
                    remote_agents_info[agent_url] = agent_data
                    print(f"  ✅ Discovered: {agent_data['name']} at {agent_url}")
                    print(agent_data)
                    print(type(agent_data))
            except httpx.HTTPStatusError as e:
                print(f"  ❌ HTTP error from {agent_url}: {e.response.status_code}")
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                print(f"  ❌ Connection failed to {agent_url}: {str(e)}")
            except Exception as e:
                print(f"  ❌ Unexpected error with {agent_url}: {str(e)}")

        return remote_agents_info
    
    async def _send_message(self, agent_url: str, message: str) -> str:
        timeout_config = httpx.Timeout(
            timeout=self.default_timeout,
            connect=10.0,
            read=self.default_timeout,
            write=10.0,
            pool=5.0
        )
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": str(uuid.uuid4()),
                        "role": "user",
                        "parts": [
                            {"text": str(message)}
                        ],
                    }
                }
            }
            print(agent_url)
            response = await client.post(agent_url, json=payload)
            
            try:
                response.raise_for_status()
                print("RESPONSE")
                print(response.json())
                return json.dumps(response.json(), indent=2)
            except Exception as e:
                print("THERE IS AN ERROR")
                print(e)
                return f"Error in response: {e}\nResponse text: {response.text}"


    async def create_task(self, agent_url: str, message: str) -> str:
        """Send a message with comprehensive error handling."""
        try:
            return await self._send_message(agent_url, message)
        except Exception as e:
            return f"Agent communication error: {str(e)}"

    def _extract_response_text(self, response_dict: dict) -> str:
        """Extract text from response artifacts."""
        if 'result' in response_dict and 'artifacts' in response_dict['result']:
            artifacts = response_dict['result']['artifacts']
            text_parts = []
            for artifact in artifacts:
                if 'parts' in artifact:
                    for part in artifact['parts']:
                        if 'text' in part:
                            text_parts.append(part['text'])
            if text_parts:
                return "\n\n".join(text_parts)
        
        return json.dumps(response_dict, indent=2)

# Initialize A2A client
a2a_client = A2AToolClient()

# Create the Host ADK Agent
host_agent = Agent(
    model="gemini-2.5-flash",
    name="trend_analysis_host",
    instruction="""
You are an expert AI Orchestrator. Your responsibilities include:
1. Understanding user requests and determining if they require single or multi-agent workflows
2. Using `list_remote_agents` to discover available agents and their capabilities
3. For single-step requests: Select the most appropriate agent and use `create_task`
4. For multi-step requests: 
   - Identify necessary agents and execution order
   - Execute tasks sequentially, passing outputs between agents as needed
5. Clearly communicate to users which agents are handling each task and their results

Important Guidelines:
- ALWAYS call `list_remote_agents` before planning agent interactions
- For multi-step workflows: 
  1. Start with the Trending Agent to get current trends
  2. Select a relevant trend to analyze
  3. Pass the trend to the Analyzer Agent for detailed analysis
- If agent communication fails, inform the user and suggest alternatives
- Present comprehensive results from all agents without over-summarizing
""",
    tools=[a2a_client.list_remote_agents, a2a_client.create_task]
)

def create_host_agent_server(host="0.0.0.0", port=10022):
    """Create A2A server for Host Agent."""
    endpoint_url = os.getenv("AGENT_ENDPOINT_URL", f"http://{host}:{port}")
    print(f"🌐 Host Agent endpoint: {endpoint_url}")
    return create_agent_a2a_server(
        agent=host_agent,
        name="Trend Analysis Host",
        description="Orchestrates trend discovery and analysis using specialized agents",
        endpoint_url=endpoint_url,
        skills=[
            AgentSkill(
                id="comprehensive_trend_analysis",
                name="Comprehensive Trend Analysis",
                description="Finds trending topics and provides deep analysis of the most relevant one",
                tags=["trends", "analysis", "orchestration", "insights"],
                examples=[
                    "Analyze current trends",
                    "What's trending and why is it important?",
                    "Give me a comprehensive trend report",
                ],
            )
        ],
        host=host,
        port=port,
        status_message="Orchestrating trend analysis...",
        artifact_name="trend_report"
    )

async def main():
    """Run the host agent server."""
    port = int(os.getenv('PORT', 10022))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Host Agent on {host}:{port}")
    
    app = create_host_agent_server(host=host, port=port)
    
    config = uvicorn.Config(
        app.build(),
        host=host,
        port=port,
        log_level="info",
        timeout_keep_alive=600  # Increase keep-alive timeout
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())