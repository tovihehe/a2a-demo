"""A2A Multi-Agent System Demo Client."""

import asyncio
import json
import uuid
from typing import Any, Dict
import os
import httpx
from a2a.client import A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest


class A2ADemoClient:
    """Demo client for A2A multi-agent system."""

    def __init__(self, default_timeout: float = 120.0):
        self._agent_info_cache: dict[str, dict[str, Any] | None] = {}
        self.default_timeout = default_timeout
        
        # Default agent URLs (can be overridden)
        self.trending_agent_url = "http://localhost:10020"
        self.analyzer_agent_url = "http://localhost:10021"
        self.host_agent_url = "http://localhost:10022"
        
        # Register agents
        self.add_remote_agent(self.trending_agent_url)
        self.add_remote_agent(self.analyzer_agent_url)
        self.add_remote_agent(self.host_agent_url)

    def add_remote_agent(self, agent_url: str):
        """Add agent to the list of available remote agents."""
        normalized_url = agent_url.rstrip('/')
        if normalized_url not in self._agent_info_cache:
            self._agent_info_cache[normalized_url] = None

    async def discover_agents(self) -> dict[str, dict[str, Any]]:
        """Discover and cache agent information."""
        print("🔍 Discovering agents...")
        
        remote_agents_info = {}
        for agent_url in self._agent_info_cache:
            try:
                timeout_config = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    response = await client.get(f"{agent_url}/.well-known/agent.json")
                    agent_data = response.json()
                    self._agent_info_cache[agent_url] = agent_data
                    remote_agents_info[agent_url] = agent_data
                    print(f"  ✅ {agent_data['name']} - {agent_url}")
            except Exception as e:
                print(f"  ❌ Failed to connect to {agent_url}: {e}")
        
        return remote_agents_info
    
    async def send_message(self, agent_url: str, message: str) -> str:
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
                            {"text": message}
                        ],
                    }
                }
            }
            response = await client.post(agent_url, json=payload)
            try:
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)
            except Exception as e:
                return f"Error in response: {e}\nResponse text: {response.text}"


    # async def send_message(self, agent_url: str, message: str) -> str:
    #     """Send a message to a specific agent."""
    #     timeout_config = httpx.Timeout(
    #         timeout=self.default_timeout,
    #         connect=10.0,
    #         read=self.default_timeout,
    #         write=10.0,
    #         pool=5.0
    #     )

    #     async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
    #         # Get agent card data
    #         if agent_url in self._agent_info_cache and self._agent_info_cache[agent_url] is not None:
    #             agent_card_data = self._agent_info_cache[agent_url]
    #         else:
    #             agent_card_response = await httpx_client.get(f"{agent_url}/.well-known/agent.json")
    #             agent_card_data = agent_card_response.json()

    #         # Create AgentCard from data
    #         agent_card = AgentCard(**agent_card_data)

    #         # Create A2A client
    #         client = A2AClient(
    #             httpx_client=httpx_client,
    #             agent_card=agent_card
    #         )

    #         # Build message payload
    #         send_message_payload = {
    #             'message': {
    #                 'role': 'user',
    #                 'parts': [
    #                     {'kind': 'text', 'text': message}
    #                 ],
    #                 'messageId': uuid.uuid4().hex,
    #             }
    #         }

    #         # Create request
    #         request = SendMessageRequest(
    #             id=str(uuid.uuid4()),
    #             params=MessageSendParams(**send_message_payload)
    #         )

    #         # Send message
    #         response = await client.send_message(request)

    #         # Extract response text
    #         try:
    #             response_dict = response.model_dump(mode='json', exclude_none=True)
    #             if 'result' in response_dict and 'artifacts' in response_dict['result']:
    #                 artifacts = response_dict['result']['artifacts']
    #                 for artifact in artifacts:
    #                     if 'parts' in artifact:
    #                         for part in artifact['parts']:
    #                             if 'text' in part:
    #                                 return part['text']
                
    #             return json.dumps(response_dict, indent=2)

    #         except Exception as e:
    #             print(f"Error parsing response: {e}")
    #             return str(response)

    def print_separator(self, title: str):
        """Print a separator with title."""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)

    async def run_demo_scenarios(self):
        """Run various demo scenarios."""
        
        self.print_separator("A2A MULTI-AGENT SYSTEM DEMO")
        
        # Discover agents
        agents = await self.discover_agents()
        if not agents:
            print("❌ No agents discovered. Make sure all services are running.")
            return

        print(f"\n📊 Discovered {len(agents)} agents")
        
        # # Scenario 1: Direct Trending Agent Call
        # self.print_separator("SCENARIO 1: Direct Trending Topics Request")
        # try:
        #     print("📡 Asking Trending Agent: What's trending today?")
        #     trending_response = await self.send_message(
        #         self.trending_agent_url, 
        #         "What's trending today?"
        #     )
        #     print("\n📝 Trending Topics Response:")
        #     print(trending_response)
        # except Exception as e:
        #     print(f"❌ Error in Scenario 1: {e}")

        # # Scenario 2: Direct Analyzer Agent Call
        # self.print_separator("SCENARIO 2: Direct Trend Analysis Request")
        # try:
        #     print("🔬 Asking Analyzer Agent: Analyze AI in social media trends")
        #     analysis_response = await self.send_message(
        #         self.analyzer_agent_url,
        #         "Analyze the AI trend in social media with quantitative data"
        #     )
        #     print("\n📊 Analysis Response:")
        #     print(analysis_response)
        # except Exception as e:
        #     print(f"❌ Error in Scenario 2: {e}")

        # Scenario 3: Host Agent Orchestration
        self.print_separator("SCENARIO 3: Host Agent Orchestration")
        try:
            print("🎯 Asking Host Agent to orchestrate full trend analysis")
            orchestrated_response = await self.send_message(
                self.host_agent_url,
                "Find the most relevant trends today, choose one of the top trends randomly, and give me a complete analysis with quantitative data"
            )
            print("\n🎭 Orchestrated Analysis:")
            print(orchestrated_response)
        except Exception as e:
            print(f"❌ Error in Scenario 3: {e}")

        # Scenario 4: Custom Query
        self.print_separator("SCENARIO 4: Custom Interactive Query")
        print("💬 You can now ask your own questions!")
        print("Available agents:")
        print(f"  - Trending Agent: {self.trending_agent_url}")
        print(f"  - Analyzer Agent: {self.analyzer_agent_url}")
        print(f"  - Host Agent: {self.host_agent_url}")
        
        while True:
            try:
                user_input = input("\n🤖 Enter your question (or 'quit' to exit): ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                agent_choice = input("Choose agent (1=Trending, 2=Analyzer, 3=Host, default=Host): ")
                
                if agent_choice == '1':
                    agent_url = self.trending_agent_url
                elif agent_choice == '2':
                    agent_url = self.analyzer_agent_url
                else:
                    agent_url = self.host_agent_url
                
                print(f"🚀 Sending to agent: {agent_url}")
                response = await self.send_message(agent_url, user_input)
                print("\n📋 Response:")
                print(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        self.print_separator("DEMO COMPLETED")
        print("Thank you for trying the A2A Multi-Agent System!")


async def main():
    """Run the demo."""
    client = A2ADemoClient()
    await client.run_demo_scenarios()


if __name__ == "__main__":
    print("🚀 Starting A2A Multi-Agent System Demo...")
    print("Make sure all agent services are running!")
    asyncio.run(main())