"""
Simple Agent Callbacks Example for Students
This example shows how to use middleware to monitor agent interactions.
Translated from Google ADK to Microsoft Agent Framework

Microsoft Agent Framework is the successor to both Semantic Kernel and AutoGen,
combining their strengths into a unified foundation for building AI agents.

Installation: pip install agent-framework

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

from datetime import datetime
from typing import Any, Callable, Awaitable

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.middleware import Middleware, MiddlewareContext
from agent_framework.models import AzureOpenAIChatCompletionClient


class TimingMiddleware(Middleware):
    """
    Middleware that monitors agent interactions - equivalent to Google ADK callbacks.
    
    In Microsoft Agent Framework:
    - Middleware intercepts agent actions (before/after processing)
    - Similar to Google ADK's before_agent_callback and after_agent_callback
    
    In Google ADK, you had:
    - before_agent_callback: Called BEFORE processing
    - after_agent_callback: Called AFTER processing
    
    In Microsoft Agent Framework:
    - Middleware.invoke(): Wraps the agent call with before/after logic
    """
    
    def __init__(self):
        self.state: dict[str, Any] = {}
    
    async def invoke(
        self,
        context: MiddlewareContext,
        next_handler: Callable[[MiddlewareContext], Awaitable[Any]]
    ) -> Any:
        """
        Called when the agent processes a message.
        Code before next_handler() = before callback
        Code after next_handler() = after callback
        """
        # ═══════════════════════════════════════════════════════════════
        # BEFORE AGENT CALLBACK (equivalent to Google ADK before_agent_callback)
        # Great for: logging, authentication, input validation
        # ═══════════════════════════════════════════════════════════════
        user_content = context.input_message.content if context.input_message else ""
        print(f"🚀 Starting to process: '{user_content}'")
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Store start time in state (equivalent to callback_context.state)
        self.state["start_time"] = datetime.now()
        
        # ═══════════════════════════════════════════════════════════════
        # AGENT PROCESSING - Call the next handler (the actual agent)
        # ═══════════════════════════════════════════════════════════════
        result = await next_handler(context)
        
        # ═══════════════════════════════════════════════════════════════
        # AFTER AGENT CALLBACK (equivalent to Google ADK after_agent_callback)
        # Great for: logging responses, analytics, post-processing
        # ═══════════════════════════════════════════════════════════════
        if "start_time" in self.state:
            duration = datetime.now() - self.state["start_time"]
            print(f"⚡ Response generated in {duration.total_seconds():.1f} seconds")
        
        print(f"✅ Agent responded. State: '{self.state}'...")
        
        return result  # Don't modify the response


def create_math_tutor_agent() -> ChatCompletionAgent:
    """
    Create a math tutor agent with middleware callbacks.
    
    Mapping from Google ADK to Microsoft Agent Framework:
    ┌─────────────────────────┬─────────────────────────────────────┐
    │ Google ADK              │ Microsoft Agent Framework           │
    ├─────────────────────────┼─────────────────────────────────────┤
    │ LlmAgent                │ ChatCompletionAgent                 │
    │ before_agent_callback   │ Middleware.invoke() - before next() │
    │ after_agent_callback    │ Middleware.invoke() - after next()  │
    │ CallbackContext.state   │ Middleware state / AgentThread      │
    │ model="gemini-2.0-flash"│ AzureOpenAIChatCompletionClient     │
    │ instruction             │ system_prompt                       │
    └─────────────────────────┴─────────────────────────────────────┘
    """
    
    # Create the model client
    # Azure OpenAI credentials loaded from environment variables:
    # AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT
    model_client = AzureOpenAIChatCompletionClient(
        deployment="gpt-4o",  # Your Azure OpenAI deployment name
    )
    
    # Create the timing middleware (our callback equivalent)
    timing_middleware = TimingMiddleware()
    
    # Create the agent with middleware
    agent = ChatCompletionAgent(
        name="math_tutor",
        description="A friendly math tutor for students",
        system_prompt="""
        You are a helpful math tutor. 
        - Give clear, step-by-step explanations
        - Be encouraging and patient
        - Keep answers concise but complete
        """,
        model_client=model_client,
        middleware=[timing_middleware],  # Attach middleware (callbacks)
    )
    
    return agent


# Create the root agent instance
root_agent = create_math_tutor_agent()


# ═══════════════════════════════════════════════════════════════════════════════
# Example usage demonstrating the middleware callbacks
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    """Example of how to use the agent with middleware callbacks."""
    
    agent = create_math_tutor_agent()
    
    # Create a thread for state management
    # AgentThread maintains conversation history and state
    thread = AgentThread()
    
    # User message
    user_message = "What is 2 + 2?"
    print(f"\n📝 User: {user_message}\n")
    print("=" * 50)
    
    # Invoke the agent - middleware will be called automatically
    # The timing middleware will:
    # 1. Log "Starting to process" (before callback)
    # 2. Let the agent generate response
    # 3. Log response time (after callback)
    response = await agent.invoke(
        input_message=user_message,
        thread=thread,
    )
    
    print("=" * 50)
    print(f"\n🤖 Math Tutor: {response.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
