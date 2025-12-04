"""
Session Object Example
Demonstrates session properties and lifecycle.
Translated from Google ADK to Microsoft Agent Framework

This example shows how to:
1. Create a session with initial state
2. Examine session properties
3. Delete a session

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from agent_framework import AgentThread


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Session:
    """
    Session object that mirrors Google ADK's session structure.
    
    Google ADK session properties:
        - id: Unique session identifier
        - app_name: Application name
        - user_id: User identifier
        - state: Dictionary of session state
        - events: List of events in the session
        - last_update_time: Timestamp of last update
    
    Microsoft Agent Framework equivalent:
        - AgentThread handles conversation history
        - Custom Session class for additional metadata
    """
    id: str
    app_name: str
    user_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    events: List[Any] = field(default_factory=list)
    last_update_time: float = field(default_factory=time.time)
    thread: AgentThread = field(default_factory=AgentThread)


# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY SESSION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class InMemorySessionService:
    """
    In-memory session service for demonstration.
    
    Google ADK equivalent:
        from google.adk.sessions import InMemorySessionService
        temp_service = InMemorySessionService()
    
    In Microsoft Agent Framework:
    - No built-in equivalent
    - Implement custom session management
    - Or use AgentThread for conversation state
    
    Mapping:
    ┌───────────────────────────┬─────────────────────────────────────┐
    │ Google ADK                │ Microsoft Agent Framework           │
    ├───────────────────────────┼─────────────────────────────────────┤
    │ InMemorySessionService    │ Custom InMemorySessionService       │
    │ session.id                │ session.id                          │
    │ session.app_name          │ session.app_name                    │
    │ session.user_id           │ session.user_id                     │
    │ session.state             │ session.state                       │
    │ session.events            │ session.events / thread.messages    │
    │ session.last_update_time  │ session.last_update_time            │
    │ create_session()          │ create_session()                    │
    │ delete_session()          │ delete_session()                    │
    └───────────────────────────┴─────────────────────────────────────┘
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """
        Create a new session.
        
        Google ADK equivalent:
            session = await temp_service.create_session(
                app_name="my_app",
                user_id="user123",
                state={"initial_key": "value"}
            )
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            events=[],
            last_update_time=time.time(),
        )
        
        key = f"{app_name}:{user_id}:{session_id}"
        self._sessions[key] = session
        
        return session
    
    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        """Get an existing session."""
        key = f"{app_name}:{user_id}:{session_id}"
        return self._sessions.get(key)
    
    async def delete_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> bool:
        """
        Delete a session.
        
        Google ADK equivalent:
            await temp_service.delete_session(
                app_name=session.app_name,
                user_id=session.user_id,
                session_id=session.id
            )
        """
        key = f"{app_name}:{user_id}:{session_id}"
        if key in self._sessions:
            del self._sessions[key]
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """
    Demonstrate session object properties.
    
    Google ADK equivalent:
        temp_service = InMemorySessionService()
        example_session = await temp_service.create_session(...)
        print(example_session.id, example_session.state, ...)
        await temp_service.delete_session(...)
    """
    
    # Create session service
    # Equivalent to: temp_service = InMemorySessionService()
    temp_service = InMemorySessionService()
    
    # Create a session with initial state
    # Equivalent to: await temp_service.create_session(...)
    example_session = await temp_service.create_session(
        app_name="my_app",
        user_id=f"user{uuid.uuid4()}",
        state={"initial_key": "Hello World for State!"},  # State can be initialized
    )
    
    # Examine session properties
    # These are equivalent to Google ADK's session properties
    print(f"--- Examining Session Properties ---")
    print(f"ID (`id`):                    {example_session.id}")
    print(f"Application Name (`app_name`): {example_session.app_name}")
    print(f"User ID (`user_id`):          {example_session.user_id}")
    print(f"State (`state`):              {example_session.state}")
    print(f"Events (`events`):            {example_session.events}")  # Initially empty
    print(f"Last Update (`last_update_time`): {example_session.last_update_time:.2f}")
    print(f"Thread (`thread`):            {type(example_session.thread).__name__}")
    print(f"---------------------------------")
    
    # Clean up - delete the session
    # Equivalent to: await temp_service.delete_session(...)
    deleted = await temp_service.delete_session(
        app_name=example_session.app_name,
        user_id=example_session.user_id,
        session_id=example_session.id,
    )
    print(f"Session deleted: {deleted}")


if __name__ == "__main__":
    asyncio.run(main())
