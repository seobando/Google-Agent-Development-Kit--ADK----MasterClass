"""
Session State Runner - Customer Support Example
Demonstrates structured output and session state management.
Translated from Google ADK to Microsoft Agent Framework

Key features demonstrated:
1. InMemorySessionService → InMemoryThreadStore
2. output_schema with Pydantic → Structured output handling
3. output_key → State storage
4. Runner with session → Direct agent invocation with thread
5. State interpolation in instructions

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import asyncio
import uuid
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.threads import InMemoryThreadStore
from agent_framework.models import AzureOpenAIChatCompletionClient
from agent_framework.output import StructuredOutputParser


load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURED OUTPUT SCHEMA
# ═══════════════════════════════════════════════════════════════════════════════

class CustomerStateOutput(BaseModel):
    """
    Pydantic schema for structured customer state output.
    
    Google ADK equivalent:
        class CustomerStateOutput(BaseModel):
            customer_name: str = Field(...)
            ...
        
        Agent(output_schema=CustomerStateOutput, output_key="state")
    
    In Microsoft Agent Framework:
    - Use Pydantic models for structured output
    - Parse response with StructuredOutputParser
    - Store in session state manually
    """
    customer_name: str = Field(description="Full name of the customer.")
    favorite_category: str = Field(
        description="Customer's preferred product category for shopping."
    )
    recent_order: str = Field(
        description="Details of the customer's most recent order including product, order number, and status."
    )
    loyalty_points: int = Field(
        description="Current number of loyalty/reward points the customer has earned.",
        ge=0,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY SESSION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class InMemorySessionService:
    """
    In-memory session service for storing session state.
    
    Google ADK equivalent:
        from google.adk.sessions import InMemorySessionService
        session_service = InMemorySessionService()
    
    In Microsoft Agent Framework:
    - Use InMemoryThreadStore for thread storage
    - Custom session state management
    
    Mapping:
    ┌───────────────────────────┬─────────────────────────────────────┐
    │ Google ADK                │ Microsoft Agent Framework           │
    ├───────────────────────────┼─────────────────────────────────────┤
    │ InMemorySessionService    │ InMemorySessionService (custom)     │
    │ create_session()          │ create_session()                    │
    │ get_session()             │ get_session()                       │
    │ session.state             │ session.state                       │
    └───────────────────────────┴─────────────────────────────────────┘
    """
    
    def __init__(self):
        self._sessions: Dict[str, "Session"] = {}
    
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> "Session":
        """Create a new session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
        )
        
        key = f"{app_name}:{user_id}:{session_id}"
        self._sessions[key] = session
        return session
    
    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> Optional["Session"]:
        """Get an existing session."""
        key = f"{app_name}:{user_id}:{session_id}"
        return self._sessions.get(key)


class Session:
    """Session object holding state and metadata."""
    
    def __init__(
        self,
        id: str,
        app_name: str,
        user_id: str,
        state: Dict[str, Any],
    ):
        self.id = id
        self.app_name = app_name
        self.user_id = user_id
        self.state = state
        self.thread = AgentThread()


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER SUPPORT AGENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_customer_support_agent(customer_data: Dict[str, Any]) -> ChatCompletionAgent:
    """
    Create a customer support agent with state interpolation.
    
    Google ADK equivalent:
        Agent(
            name="CustomerSupport",
            model="gemini-2.0-flash",
            output_schema=CustomerStateOutput,
            output_key="state",
            instruction="... {customer_name} ... {favorite_category} ..."
        )
    
    In Microsoft Agent Framework:
    - State interpolation done manually in system_prompt
    - Structured output via response_format or parsing
    """
    # Interpolate state into system prompt (equivalent to Google ADK's {variable} syntax)
    system_prompt = f"""You are a friendly customer support agent for TechStore.

Customer Information:
- Name: {customer_data.get('customer_name', 'Unknown')}
- Favorite Category: {customer_data.get('favorite_category', 'General')}
- Recent Order: {customer_data.get('recent_order', 'None')}
- Loyalty Points: {customer_data.get('loyalty_points', 0)}

Help the customer with their inquiries. Be friendly and personalized.
Reference their order status, favorite categories, and loyalty points when relevant.

When responding, also output a JSON with the customer's current state:
{{
    "customer_name": "<name>",
    "favorite_category": "<category>",
    "recent_order": "<order details>",
    "loyalty_points": <points>
}}
"""
    
    model_client = AzureOpenAIChatCompletionClient(
        deployment="gpt-4o",
    )
    
    return ChatCompletionAgent(
        name="CustomerSupport",
        description="Customer support agent for TechStore",
        system_prompt=system_prompt,
        model_client=model_client,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """
    Main example demonstrating session state and structured output.
    
    Google ADK equivalent flow:
        1. Create InMemorySessionService
        2. Create session with state
        3. Create Agent with output_schema
        4. Create Runner
        5. Run agent and get response
        6. Access structured output from session.state["state"]
    """
    
    # Create session service to store customer data
    # Equivalent to: session_service = InMemorySessionService()
    session_service = InMemorySessionService()
    
    # Simple customer profile
    customer_data = {
        "customer_name": "Sarah Johnson",
        "favorite_category": "Electronics",
        "recent_order": "iPhone 15 Pro - Order #12345 - Shipped",
        "loyalty_points": 500,
    }
    
    # Create session
    # Equivalent to: await session_service.create_session(...)
    APP_NAME = "TechStore"
    CUSTOMER_ID = "sarah_j"
    SESSION_ID = str(uuid.uuid4())
    
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=CUSTOMER_ID,
        session_id=SESSION_ID,
        state=customer_data,
    )
    
    print(f"🛒 Customer: {customer_data['customer_name']}")
    print(f"📱 Favorite: {customer_data['favorite_category']}")
    print(f"📦 Recent Order: {customer_data['recent_order']}")
    print(f"⭐ Points: {customer_data['loyalty_points']}")
    
    # Create the customer support agent
    # Equivalent to: Agent(output_schema=CustomerStateOutput, output_key="state", ...)
    support_agent = create_customer_support_agent(customer_data)
    
    # Customer asks a question
    customer_message = "Hi! Can you check my recent order status?"
    
    print(f"\n💬 Customer: {customer_message}")
    print("🤖 Support Agent: ", end="")
    
    # Get response from agent
    # Equivalent to: runner.run_async(user_id, session_id, new_message)
    response = await support_agent.invoke(
        input_message=customer_message,
        thread=session.thread,
    )
    
    if response:
        print(response.content)
    
    # Parse structured output from response
    # In Google ADK, this would be automatically stored in session.state["state"]
    # In Microsoft Agent Framework, we parse manually
    try:
        import json
        import re
        
        # Try to extract JSON from response
        response_text = response.content if response else ""
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        
        if json_match:
            structured_data = json.loads(json_match.group())
            session.state["state"] = structured_data
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Show final session state
    # Equivalent to: session = await session_service.get_session(...)
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=CUSTOMER_ID, session_id=SESSION_ID
    )
    
    # Check if structured output exists in session state under the output_key
    # Equivalent to Google ADK's output_key mechanism
    if session and "state" in session.state:
        structured_data = session.state["state"]
        print(f"\n{structured_data}")
        print("✅ Updating session state:")
        
        for key, value in structured_data.items():
            session.state[key] = value
            print(f"  - {key} updated to: {value}")
        
        del session.state["state"]
    else:
        print("\nNo structured output found in session state.")
    
    print(f"\n📊 Session Data:")
    if session:
        for key, value in session.state.items():
            print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
