"""
Simple Model Callbacks Example for Students
This shows how to intercept and modify what goes TO and FROM the AI model.
Translated from Google ADK to Microsoft Agent Framework

In Microsoft Agent Framework, model-level interception is done via:
1. ChatCompletionClientMiddleware - intercepts model requests/responses
2. Or custom wrapper around the model client

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

from typing import Any, Callable, Awaitable, Optional
from dataclasses import dataclass

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.middleware import Middleware, MiddlewareContext
from agent_framework.models import (
    OpenAIChatCompletionClient,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)


@dataclass
class ModelInterceptResult:
    """Result from model interception - can block or allow the request."""
    blocked: bool = False
    custom_response: Optional[str] = None


class ModelCallbackMiddleware(Middleware):
    """
    Middleware that intercepts model-level requests and responses.
    
    This is the Microsoft Agent Framework equivalent of Google ADK's
    before_model_callback and after_model_callback.
    
    Google ADK Pattern:
    ┌─────────────────────────────────────────────────────────────┐
    │ before_model_callback(context, llm_request) -> LlmResponse? │
    │ [LLM API CALL]                                              │
    │ after_model_callback(context, llm_response) -> LlmResponse? │
    └─────────────────────────────────────────────────────────────┘
    
    Microsoft Agent Framework Pattern:
    ┌─────────────────────────────────────────────────────────────┐
    │ Middleware.invoke():                                        │
    │   - before_model_callback logic (can return early)          │
    │   - await next_handler(context) [LLM API CALL]              │
    │   - after_model_callback logic (can modify response)        │
    └─────────────────────────────────────────────────────────────┘
    """
    
    # Keywords to block (content filtering example)
    MATH_KEYWORDS = [
        "math",
        "calculate",
        "+",
        "-",
        "*",
        "/",
        "=",
        "plus",
        "minus",
        "times",
        "divided",
    ]
    
    def _before_model_callback(self, user_message: str) -> ModelInterceptResult:
        """
        Called BEFORE sending the request to the AI model.
        Perfect for: content filtering, request logging, blocking inappropriate content
        
        Equivalent to Google ADK's before_model_callback
        """
        print(f"📤 Sending to model: '{user_message}'")
        
        # Block math questions (as an example filter)
        if any(keyword in user_message.lower() for keyword in self.MATH_KEYWORDS):
            print("🚫 Blocking math-related content!")
            return ModelInterceptResult(
                blocked=True,
                custom_response=(
                    "Sorry, I'm not allowed to help with math problems right now. "
                    "Try asking about something else!"
                )
            )
        
        print("✅ Request approved - sending to model")
        return ModelInterceptResult(blocked=False)
    
    def _after_model_callback(self, response_text: str) -> str:
        """
        Called AFTER getting response from the AI model.
        Perfect for: response filtering, adding disclaimers, logging responses
        
        Equivalent to Google ADK's after_model_callback
        """
        # Truncate for logging
        preview = response_text[:50] if len(response_text) > 50 else response_text
        print(f"📥 Model responded: '{preview}...'")
        
        # Add a fun emoji to every response
        if response_text:
            modified_text = response_text + " 🤖"
            print("✨ Added robot emoji to response!")
            return modified_text
        
        return response_text
    
    async def invoke(
        self,
        context: MiddlewareContext,
        next_handler: Callable[[MiddlewareContext], Awaitable[Any]]
    ) -> Any:
        """
        Main middleware method - wraps the model call with before/after logic.
        """
        # ═══════════════════════════════════════════════════════════════
        # BEFORE MODEL CALLBACK
        # Extract user message and check if we should block
        # ═══════════════════════════════════════════════════════════════
        user_message = ""
        if context.input_message:
            user_message = context.input_message.content or ""
        
        # Run before_model_callback logic
        intercept_result = self._before_model_callback(user_message)
        
        # If blocked, return custom response without calling the model
        if intercept_result.blocked:
            # Create a mock response object
            # In Microsoft Agent Framework, we return without calling next_handler
            context.result = self._create_blocked_response(intercept_result.custom_response)
            return context.result
        
        # ═══════════════════════════════════════════════════════════════
        # CALL THE MODEL (equivalent to the actual LLM API call)
        # ═══════════════════════════════════════════════════════════════
        result = await next_handler(context)
        
        # ═══════════════════════════════════════════════════════════════
        # AFTER MODEL CALLBACK
        # Modify the response (add emoji, filter, etc.)
        # ═══════════════════════════════════════════════════════════════
        if result and hasattr(result, 'content'):
            original_text = result.content or ""
            modified_text = self._after_model_callback(original_text)
            result.content = modified_text
        
        return result
    
    def _create_blocked_response(self, message: str) -> Any:
        """Create a response object for blocked requests."""
        # Return a simple response-like object
        class BlockedResponse:
            def __init__(self, content: str):
                self.content = content
                self.role = "assistant"
        
        return BlockedResponse(message)


def create_filtered_chatbot() -> ChatCompletionAgent:
    """
    Create a chatbot with model-level callbacks for filtering.
    
    Mapping from Google ADK to Microsoft Agent Framework:
    ┌──────────────────────────┬─────────────────────────────────────┐
    │ Google ADK               │ Microsoft Agent Framework           │
    ├──────────────────────────┼─────────────────────────────────────┤
    │ LlmAgent                 │ ChatCompletionAgent                 │
    │ before_model_callback    │ Middleware - before next_handler()  │
    │ after_model_callback     │ Middleware - after next_handler()   │
    │ LlmRequest               │ ChatCompletionRequest / context     │
    │ LlmResponse              │ ChatCompletionResponse / result     │
    │ Return LlmResponse early │ Return without calling next_handler │
    │ Return None (continue)   │ Call await next_handler(context)    │
    └──────────────────────────┴─────────────────────────────────────┘
    """
    
    # Create the model client
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",  # OpenAI model name
    )
    
    # Create the model callback middleware
    model_callback_middleware = ModelCallbackMiddleware()
    
    # Create the agent with middleware
    agent = ChatCompletionAgent(
        name="filtered_chatbot",
        description="A chatbot that filters math questions and adds emojis",
        system_prompt="""
        You are a friendly chatbot. 
        - Be helpful and conversational
        - Keep responses short and friendly
        - Answer questions about various topics
        """,
        model_client=model_client,
        middleware=[model_callback_middleware],
    )
    
    return agent


# Create the root agent instance
root_agent = create_filtered_chatbot()


# ═══════════════════════════════════════════════════════════════════════════════
# Example usage demonstrating the model callbacks
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    """Example of how to use the agent with model callbacks."""
    
    print("=" * 60)
    print("Filtered Chatbot Demo")
    print("Try asking: 'What's the weather like?' or 'What's 2+2?'")
    print("=" * 60)
    
    agent = create_filtered_chatbot()
    thread = AgentThread()
    
    # Test 1: Normal question (should pass through)
    print("\n📝 Test 1: Normal question")
    print("-" * 40)
    user_message1 = "Hello, how are you?"
    print(f"User: {user_message1}\n")
    
    response1 = await agent.invoke(
        input_message=user_message1,
        thread=thread,
    )
    print(f"\n🤖 Response: {response1.content}")
    
    # Test 2: Math question (should be blocked)
    print("\n📝 Test 2: Math question (will be blocked)")
    print("-" * 40)
    user_message2 = "Can you help me calculate 15 + 25?"
    print(f"User: {user_message2}\n")
    
    response2 = await agent.invoke(
        input_message=user_message2,
        thread=thread,
    )
    print(f"\n🤖 Response: {response2.content}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
