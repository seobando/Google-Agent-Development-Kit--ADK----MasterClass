"""
Simple Agent Callbacks Example for Students
This example shows how to use middleware to monitor agent interactions.
Translated from Google ADK to Microsoft Agent Framework

Microsoft Agent Framework is the successor to both Semantic Kernel and AutoGen,
combining their strengths into a unified foundation for building AI agents.

Installation: pip install agent-framework

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Awaitable

from agent_framework import ChatAgent, AgentThread, AgentMiddleware, AgentRunContext
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv

load_dotenv()


async def timing_middleware(
    context: AgentRunContext,
    next_handler: Callable[[AgentRunContext], Awaitable[None]]
) -> None:
    """
    Middleware that monitors agent interactions - equivalent to Google ADK callbacks.
    
    In Microsoft Agent Framework:
    - Middleware intercepts agent actions (before/after processing)
    - Similar to Google ADK's before_agent_callback and after_agent_callback
    
    In Google ADK, you had:
    - before_agent_callback: Called BEFORE processing
    - after_agent_callback: Called AFTER processing
    
    In Microsoft Agent Framework:
    - Middleware function wraps the agent call with before/after logic
    """
    # ═══════════════════════════════════════════════════════════════
    # BEFORE AGENT CALLBACK (equivalent to Google ADK before_agent_callback)
    # Great for: logging, authentication, input validation
    # ═══════════════════════════════════════════════════════════════
    print(f"🚀 Starting to process request...")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = datetime.now()
    
    # ═══════════════════════════════════════════════════════════════
    # AGENT PROCESSING - Call the next handler (the actual agent)
    # ═══════════════════════════════════════════════════════════════
    await next_handler(context)
    
    # ═══════════════════════════════════════════════════════════════
    # AFTER AGENT CALLBACK (equivalent to Google ADK after_agent_callback)
    # Great for: logging responses, analytics, post-processing
    # ═══════════════════════════════════════════════════════════════
    duration = datetime.now() - start_time
    print(f"⚡ Response generated in {duration.total_seconds():.1f} seconds")
    print(f"✅ Agent responded successfully!")


def create_math_tutor_agent() -> ChatAgent:
    """
    Create a math tutor agent with middleware callbacks.
    
    Mapping from Google ADK to Microsoft Agent Framework:
    ┌─────────────────────────┬─────────────────────────────────────┐
    │ Google ADK              │ Microsoft Agent Framework           │
    ├─────────────────────────┼─────────────────────────────────────┤
    │ LlmAgent                │ ChatAgent                           │
    │ before_agent_callback   │ Middleware - before next_handler()  │
    │ after_agent_callback    │ Middleware - after next_handler()   │
    │ CallbackContext.state   │ AgentRunContext / AgentThread       │
    │ model="gemini-2.0-flash"│ OpenAIChatClient(model_id="gpt-4o") │
    │ instruction             │ instructions                        │
    └─────────────────────────┴─────────────────────────────────────┘
    """
    
    # Create the model client
    # OpenAI credentials loaded from environment variable: OPENAI_API_KEY
    chat_client = OpenAIChatClient(model_id="gpt-4o")
    
    # Create the agent with middleware
    agent = ChatAgent(
        chat_client=chat_client,
        name="math_tutor",
        description="A friendly math tutor for students",
        instructions="""
        You are a helpful math tutor. 
        - Give clear, step-by-step explanations
        - Be encouraging and patient
        - Keep answers concise but complete
        """,
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
    
    # Run the agent - middleware will be called automatically
    # The timing middleware will:
    # 1. Log "Starting to process" (before callback)
    # 2. Let the agent generate response
    # 3. Log response time (after callback)
    response = await agent.run(
        messages=user_message,
        thread=thread,
    )
    
    print("=" * 50)
    print(f"\n🤖 Math Tutor: {response.text}")


async def interactive():
    """Interactive chat loop - like Google ADK CLI mode."""
    
    agent = create_math_tutor_agent()
    thread = AgentThread()
    
    print("\n" + "=" * 50)
    print("🎓 MATH TUTOR - Interactive Mode")
    print("=" * 50)
    print("Type your math questions, or 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("📝 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Keep learning!")
                break
            
            print("\n" + "-" * 40)
            response = await agent.run(messages=user_input, thread=thread)
            print("-" * 40)
            print(f"\n🤖 Math Tutor: {response.text}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        # Run web UI: python agent.py web
        from agent_framework.devui import serve
        print("🚀 Starting Web UI at http://127.0.0.1:8080")
        serve(entities=[root_agent], port=8080, auto_open=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "once":
        # Run single question: python agent.py once
        asyncio.run(main())
    else:
        # Interactive CLI mode (default)
        asyncio.run(interactive())
