# Session State Runner Translation Analysis
## Google ADK → Microsoft Agent Framework

This document analyzes the translation of the session-state-runner examples from Google's Agent Development Kit (ADK) to Microsoft's Agent Framework.

---

## 📋 Overview

This folder contains three examples demonstrating session and state management:

| File | Purpose | Key Features |
|------|---------|--------------|
| `agent.py` | Customer support with structured output | `output_schema`, `output_key`, state interpolation |
| `session_object.py` | Session properties demo | Session lifecycle, properties examination |
| `tester.py` | Full Study Buddy app | Persistent state, tools, interactive CLI |

---

## 🏗️ Architecture Comparison

### High-Level Architecture

```mermaid
flowchart TB
    subgraph Google ADK
        G_Service["SessionService<br/>(InMemory/Database)"]
        G_Session["Session Object"]
        G_State["session.state"]
        G_Runner["Runner"]
        G_Agent["Agent"]
        
        G_Service --> G_Session
        G_Session --> G_State
        G_Runner --> G_Agent
        G_Runner --> G_Service
    end
    
    subgraph Microsoft Agent Framework
        M_Service["Custom SessionService"]
        M_Session["Session Object"]
        M_State["StudyState dataclass"]
        M_Thread["AgentThread"]
        M_Agent["ChatCompletionAgent"]
        
        M_Service --> M_Session
        M_Session --> M_State
        M_Session --> M_Thread
        M_Agent --> M_Thread
    end
```

---

## 📊 Detailed Mapping

### Component Mapping

| Google ADK | Microsoft Agent Framework |
|------------|---------------------------|
| `InMemorySessionService` | Custom `InMemorySessionService` class |
| `DatabaseSessionService` | Custom `DatabaseSessionService` class |
| `session.state` | `StudyState` dataclass |
| `session.id` | `session.id` |
| `session.app_name` | `session.app_name` |
| `session.user_id` | `session.user_id` |
| `session.events` | `session.events` / `thread.messages` |
| `session.last_update_time` | `session.last_update_time` |
| `Runner` | Direct `agent.invoke()` |
| `output_schema` | Pydantic model + response parsing |
| `output_key` | Manual state storage |
| `tool_context.state` | Global state access |

---

## 🔄 Session Lifecycle Comparison

```mermaid
sequenceDiagram
    participant App as Application
    participant Svc as SessionService
    participant Sess as Session
    participant Agent as Agent
    
    rect rgb(230, 245, 255)
        Note over App,Agent: Google ADK Flow
        App->>Svc: create_session(app_name, user_id, state)
        Svc-->>Sess: Session object
        App->>Svc: Runner(agent, session_service)
        App->>Svc: runner.run_async(user_id, session_id, message)
        Svc->>Agent: Process with session context
        Agent-->>Svc: Response + state updates
        Svc->>Sess: Auto-persist state
    end
    
    rect rgb(255, 243, 224)
        Note over App,Agent: Microsoft Agent Framework Flow
        App->>Svc: create_session(app_name, user_id, state)
        Svc-->>Sess: Session object
        App->>Agent: agent.invoke(message, thread)
        Agent-->>App: Response
        App->>Svc: update_state(state)
    end
```

---

## 🔑 Key Differences

### 1. Session Services

```mermaid
flowchart LR
    subgraph Google["Google ADK"]
        G_IMem["InMemorySessionService"]
        G_DB["DatabaseSessionService"]
        G_Custom["Custom implementations"]
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M_Custom["Custom SessionService<br/>(build your own)"]
        M_Thread["AgentThread<br/>(conversation only)"]
    end
    
    G_IMem -.->|Translate to| M_Custom
    G_DB -.->|Translate to| M_Custom
```

**Google ADK** - Built-in services:
```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService

# Ready to use
service = InMemorySessionService()
service = DatabaseSessionService(db_url="sqlite:///./data.db")
```

**Microsoft Agent Framework** - Custom implementation:
```python
class InMemorySessionService:
    def __init__(self):
        self._sessions = {}
    
    async def create_session(self, ...): ...
    async def get_session(self, ...): ...
    async def delete_session(self, ...): ...
```

### 2. Structured Output (output_schema)

```mermaid
flowchart TD
    subgraph Google["Google ADK"]
        G_Schema["output_schema=CustomerStateOutput"]
        G_Key["output_key='state'"]
        G_Auto["Auto-stored in session.state['state']"]
        G_Schema --> G_Key --> G_Auto
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M_Schema["Pydantic model"]
        M_Prompt["Include JSON format in prompt"]
        M_Parse["Parse JSON from response"]
        M_Store["Manual storage in state"]
        M_Schema --> M_Prompt --> M_Parse --> M_Store
    end
```

**Google ADK:**
```python
class CustomerStateOutput(BaseModel):
    customer_name: str
    loyalty_points: int

agent = Agent(
    output_schema=CustomerStateOutput,
    output_key="state",  # Auto-stored here
)

# After agent runs:
structured = session.state["state"]  # Automatically populated
```

**Microsoft Agent Framework:**
```python
class CustomerStateOutput(BaseModel):
    customer_name: str
    loyalty_points: int

# Include format in prompt
system_prompt = """
...
Output JSON: {"customer_name": "...", "loyalty_points": ...}
"""

# Parse manually
response = await agent.invoke(message)
json_data = extract_json(response.content)
session.state["state"] = json_data
```

### 3. State Interpolation in Instructions

**Google ADK** - Automatic variable substitution:
```python
agent = Agent(
    instruction="Hello {customer_name}, you have {loyalty_points} points."
)
# Variables auto-filled from session.state
```

**Microsoft Agent Framework** - Manual string formatting:
```python
system_prompt = f"""Hello {state.customer_name}, you have {state.loyalty_points} points."""

agent = ChatCompletionAgent(system_prompt=system_prompt)
```

### 4. Runner vs Direct Invocation

```mermaid
flowchart LR
    subgraph Google["Google ADK"]
        G_Runner["Runner"]
        G_Stream["run_async() → events"]
        G_Final["event.is_final_response()"]
        G_Runner --> G_Stream --> G_Final
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M_Agent["ChatCompletionAgent"]
        M_Invoke["invoke()"]
        M_Response["response.content"]
        M_Agent --> M_Invoke --> M_Response
    end
```

**Google ADK:**
```python
runner = Runner(agent=agent, app_name=APP_NAME, session_service=service)

async for event in runner.run_async(user_id, session_id, message):
    if event.is_final_response():
        print(event.content.parts[0].text)
```

**Microsoft Agent Framework:**
```python
response = await agent.invoke(
    input_message=message,
    thread=thread,
)
print(response.content)
```

### 5. Tool Context State Access

```mermaid
flowchart TD
    subgraph Google["Google ADK"]
        G_Tool["def my_tool(arg, tool_context=None)"]
        G_Check["if tool_context and hasattr(tool_context, 'state')"]
        G_Access["tool_context.state['key']"]
        G_Tool --> G_Check --> G_Access
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M_Tool["@tool\ndef my_tool(arg)"]
        M_Global["global current_state"]
        M_Access["current_state.attribute"]
        M_Tool --> M_Global --> M_Access
    end
```

**Google ADK:**
```python
def add_course(name: str, tool_context=None) -> dict:
    if tool_context and hasattr(tool_context, "state"):
        courses = tool_context.state.get("courses", [])
        courses.append({"name": name})
        tool_context.state["courses"] = courses
```

**Microsoft Agent Framework:**
```python
current_state: Optional[StudyState] = None

@tool
def add_course(name: str) -> dict:
    global current_state
    if current_state:
        current_state.courses.append({"name": name})
        asyncio.create_task(_save_state())
```

---

## 🗄️ Study Buddy Data Model

```mermaid
classDiagram
    class StudyState {
        +str student_name
        +str learning_style
        +List~Course~ courses
        +List~Assignment~ assignments
        +List~StudySession~ study_sessions
        +int total_study_minutes
        +to_dict() Dict
        +from_dict(data) StudyState
    }
    
    class Course {
        +str id
        +str name
        +str instructor
        +str added_date
    }
    
    class Assignment {
        +str id
        +str course_name
        +str title
        +str due_date
        +str status
        +str added_date
        +str completed_date
    }
    
    class StudySession {
        +str id
        +str subject
        +int duration_minutes
        +str notes
        +str date
        +str time
    }
    
    StudyState "1" *-- "*" Course
    StudyState "1" *-- "*" Assignment
    StudyState "1" *-- "*" StudySession
```

---

## ⚡ Execution Flow - Study Buddy

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI Interface
    participant Svc as DatabaseSessionService
    participant Agent as ChatCompletionAgent
    participant Tools as Tool Functions
    participant State as StudyState
    participant DB as SQLite
    
    U->>CLI: Run application
    CLI->>CLI: setup_student()
    CLI->>Svc: initialize_session()
    Svc->>DB: list_sessions()
    
    alt Existing session
        DB-->>Svc: Session data
        Svc->>State: StudyState.from_dict()
    else New session
        Svc->>State: Create default state
        Svc->>DB: INSERT session
    end
    
    CLI->>Agent: create_study_agent(state)
    
    loop Chat Loop
        U->>CLI: "Add course Math with Dr. Smith"
        CLI->>Agent: invoke(message, thread)
        Agent->>Tools: add_course("Math", "Dr. Smith")
        Tools->>State: state.courses.append()
        Tools->>Svc: _save_state()
        Svc->>DB: UPDATE state_json
        Tools-->>Agent: {"action": "add_course", ...}
        Agent-->>CLI: Response
        CLI-->>U: Display response
    end
```

---

## 📁 File-by-File Analysis

### agent.py - Customer Support

```mermaid
flowchart TD
    Start[Start] --> CreateService["Create InMemorySessionService"]
    CreateService --> CreateSession["Create session with customer data"]
    CreateSession --> CreateAgent["Create agent with state interpolation"]
    CreateAgent --> SendMessage["Send customer message"]
    SendMessage --> GetResponse["Get agent response"]
    GetResponse --> ParseJSON["Parse structured output from response"]
    ParseJSON --> UpdateState["Update session state"]
    UpdateState --> Display["Display final state"]
```

| Feature | Google ADK | Microsoft Agent Framework |
|---------|------------|---------------------------|
| Structured output | `output_schema=Pydantic` | Parse JSON from response |
| State interpolation | `{variable}` in instruction | f-string in system_prompt |
| Auto-storage | `output_key="state"` | Manual `state["state"] = data` |

### session_object.py - Session Properties

```mermaid
flowchart TD
    Start[Start] --> Create["create_session()"]
    Create --> Examine["Examine properties"]
    Examine --> ID["session.id"]
    Examine --> AppName["session.app_name"]
    Examine --> UserID["session.user_id"]
    Examine --> State["session.state"]
    Examine --> Events["session.events"]
    Examine --> LastUpdate["session.last_update_time"]
    ID & AppName & UserID & State & Events & LastUpdate --> Delete["delete_session()"]
```

### tester.py - Study Buddy

```mermaid
mindmap
  root((Study Buddy))
    Session Management
      DatabaseSessionService
      Session resume
      State persistence
    Tools
      add_course
      view_courses
      add_assignment
      view_assignments
      complete_assignment
      log_study_session
      view_study_stats
    CLI Interface
      Setup wizard
      Help command
      Status display
      Special commands
    State
      StudyState dataclass
      SQLite storage
      Auto-save on changes
```

---

## ✅ Advantages & Trade-offs

```mermaid
quadrantChart
    title Session Management Comparison
    x-axis Manual Control --> Automatic
    y-axis Simple --> Feature-Rich
    quadrant-1 Automatic & Feature-Rich
    quadrant-2 Manual & Feature-Rich
    quadrant-3 Manual & Simple
    quadrant-4 Automatic & Simple
    Google ADK: [0.75, 0.8]
    Microsoft Agent Framework: [0.3, 0.6]
```

### Google ADK Advantages
- ✅ Built-in `InMemorySessionService` and `DatabaseSessionService`
- ✅ Automatic state interpolation in instructions
- ✅ `output_schema` for structured output
- ✅ `output_key` for automatic state storage
- ✅ Event-based streaming with `run_async()`
- ✅ `tool_context.state` auto-injection

### Microsoft Agent Framework Advantages
- ✅ Full control over session implementation
- ✅ Custom database schema design
- ✅ Flexible state structures (dataclasses)
- ✅ Direct agent invocation (simpler for basic cases)
- ✅ Can use any storage backend
- ✅ More explicit state management

### Trade-offs

| Aspect | Google ADK | Microsoft Agent Framework |
|--------|------------|---------------------------|
| **Session services** | Built-in | DIY |
| **Structured output** | Automatic | Manual parsing |
| **State interpolation** | `{variable}` | f-strings |
| **Tool context** | Auto-injected | Global state |
| **Streaming** | Event-based | Response object |
| **Boilerplate** | Less | More |

---

## 🌐 Environment Configuration

### Google ADK
```bash
GOOGLE_API_KEY=your-google-api-key
```

### Microsoft Agent Framework
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

---

## 📝 Summary

```mermaid
flowchart TB
    subgraph Google["Google ADK Approach"]
        G1["Built-in SessionService"]
        G2["Automatic state interpolation"]
        G3["output_schema + output_key"]
        G4["Runner with events"]
        G5["tool_context.state"]
    end
    
    subgraph Microsoft["Microsoft Agent Framework Approach"]
        M1["Custom SessionService"]
        M2["Manual f-string formatting"]
        M3["Parse JSON + manual storage"]
        M4["Direct invoke()"]
        M5["Global state object"]
    end
    
    G1 -.->|Translate| M1
    G2 -.->|Translate| M2
    G3 -.->|Translate| M3
    G4 -.->|Translate| M4
    G5 -.->|Translate| M5
```

The key insight is that Google ADK provides **comprehensive built-in session management** while Microsoft Agent Framework requires **custom implementation** but offers complete flexibility in designing your session and state architecture.

---

## 🔗 References

- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Microsoft Agent Framework Thread Management](https://learn.microsoft.com/en-us/agent-framework/threads)
- [Google ADK Sessions Documentation](https://google.github.io/adk-docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

