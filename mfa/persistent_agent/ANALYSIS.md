# Persistent Agent Translation Analysis
## Google ADK → Microsoft Agent Framework

This document analyzes the translation of the persistent recipe assistant agent from Google's Agent Development Kit (ADK) to Microsoft's Agent Framework.

---

## 📋 Overview

This example demonstrates **persistent state management** - maintaining agent state across sessions using a SQLite database.

| Aspect | Google ADK | Microsoft Agent Framework |
|--------|------------|---------------------------|
| **Session Service** | `DatabaseSessionService` | Custom `RecipeStateStore` + `AgentThread` |
| **State Storage** | `session.state` | Custom state class + SQLite |
| **Persistence** | Automatic via events | Explicit `save()` calls |
| **Tool Context** | `tool_context.state` | Custom `ToolContext` class |
| **Runner** | `Runner` class | Direct agent invocation |

---

## 🏗️ Architecture Comparison

### High-Level Architecture

```mermaid
flowchart TB
    subgraph Google ADK
        G_User[User] --> G_Runner[Runner]
        G_Runner --> G_Agent[Agent]
        G_Agent --> G_Tools[Tools]
        G_Tools --> G_State["tool_context.state"]
        G_State --> G_Session[DatabaseSessionService]
        G_Session --> G_DB[(SQLite DB)]
    end
    
    subgraph Microsoft Agent Framework
        M_User[User] --> M_Assistant[RecipeAssistant]
        M_Assistant --> M_Agent[ChatCompletionAgent]
        M_Agent --> M_Tools[Tools]
        M_Tools --> M_Context[ToolContext]
        M_Context --> M_Store[RecipeStateStore]
        M_Store --> M_DB[(SQLite DB)]
    end
```

### State Flow Comparison

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant T as Tool
    participant S as State Store
    participant DB as SQLite DB
    
    rect rgb(230, 245, 255)
        Note over U,DB: Google ADK Flow
        U->>A: "Add pasta recipe"
        A->>T: add_recipe(...)
        T->>S: tool_context.state["recipes"].append()
        S->>DB: service.append_event(state_delta)
        DB-->>S: Persisted
        T-->>A: Result
        A-->>U: "Recipe added!"
    end
    
    rect rgb(255, 243, 224)
        Note over U,DB: Microsoft Agent Framework Flow
        U->>A: "Add pasta recipe"
        A->>T: add_recipe(...)
        T->>S: tool_context.state.recipes.append()
        T->>S: tool_context.save()
        S->>DB: INSERT/UPDATE state_json
        DB-->>S: Persisted
        T-->>A: Result
        A-->>U: "Recipe added!"
    end
```

---

## 📊 Detailed Mapping

### Component Mapping

| Google ADK | Microsoft Agent Framework |
|------------|---------------------------|
| `DatabaseSessionService` | `RecipeStateStore` (custom) |
| `session.state` | `RecipeState` dataclass |
| `service.create_session()` | `store.save_state()` (first time) |
| `service.get_session()` | `store.get_state()` |
| `service.list_sessions()` | `store.list_users()` |
| `service.append_event()` | `context.save()` |
| `tool_context.state` | `tool_context.state` (custom class) |
| `Runner` | `RecipeAssistant` (custom class) |
| `runner.run_async()` | `agent.invoke()` |

### Session Management

```mermaid
flowchart TD
    subgraph Google["Google ADK Session Management"]
        G_Start[Start] --> G_List["service.list_sessions()"]
        G_List --> G_Check{Sessions exist?}
        G_Check -->|Yes| G_Continue["SESSION_ID = sessions[0].id"]
        G_Check -->|No| G_Create["service.create_session()"]
        G_Create --> G_NewID["SESSION_ID = session.id"]
        G_Continue --> G_Ready[Ready]
        G_NewID --> G_Ready
    end
    
    subgraph Microsoft["Microsoft Agent Framework Session Management"]
        M_Start[Start] --> M_Get["store.get_state()"]
        M_Get --> M_Check{State exists?}
        M_Check -->|Yes| M_Load["Load existing state"]
        M_Check -->|No| M_Create["Create default state"]
        M_Create --> M_Save["store.save_state()"]
        M_Load --> M_Ready[Ready]
        M_Save --> M_Ready
    end
```

---

## 🔑 Key Differences

### 1. Session/State Service Pattern

**Google ADK** - Built-in service:
```python
from google.adk.sessions import DatabaseSessionService

service = DatabaseSessionService(db_url="sqlite:///./recipe_data.db")

# Create session
session = await service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    state=initial_state,
)

# Get session
session = service.get_session(app_name, user_id, session_id)
```

**Microsoft Agent Framework** - Custom implementation:
```python
class RecipeStateStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def get_state(self, user_id: str, app_name: str) -> RecipeState:
        # Query SQLite and return state
        ...
    
    def save_state(self, user_id: str, app_name: str, state: RecipeState):
        # Insert/update in SQLite
        ...
```

### 2. State Access in Tools

```mermaid
flowchart LR
    subgraph Google["Google ADK"]
        G_Tool[Tool Function]
        G_Param["tool_context parameter"]
        G_State["tool_context.state"]
        G_Tool --> G_Param --> G_State
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M_Tool[Tool Function]
        M_Global["Global tool_context"]
        M_State["tool_context.state"]
        M_Tool --> M_Global --> M_State
    end
```

**Google ADK:**
```python
def add_recipe(name: str, tool_context=None) -> dict:
    if tool_context and hasattr(tool_context, "state"):
        recipes = tool_context.state.get("recipes", [])
        recipes.append(recipe)
        tool_context.state["recipes"] = recipes
    return {"message": "Added"}
```

**Microsoft Agent Framework:**
```python
# Global context set before invocation
tool_context: Optional[ToolContext] = None

@tool
def add_recipe(name: str) -> dict:
    global tool_context
    if tool_context:
        tool_context.state.recipes.append(recipe)
        tool_context.save()  # Explicit persistence
    return {"message": "Added"}
```

### 3. State Persistence

```mermaid
flowchart TD
    subgraph Google["Google ADK - Event-Based"]
        G_Change[State Change] --> G_Event["Create Event with state_delta"]
        G_Event --> G_Append["service.append_event()"]
        G_Append --> G_Auto["Auto-persisted"]
    end
    
    subgraph Microsoft["Microsoft Agent Framework - Explicit"]
        M_Change[State Change] --> M_Modify["Modify state object"]
        M_Modify --> M_Save["context.save()"]
        M_Save --> M_SQL["INSERT/UPDATE SQL"]
    end
```

**Google ADK** - Automatic via events:
```python
event = Event(
    id=str(uuid.uuid4()),
    author="user",
    content=types.Content(...),
    actions=session_types.Actions(state_delta={"recipes": recipes}),
    timestamp=time.time(),
)
service.append_event(session=session, event=event)
```

**Microsoft Agent Framework** - Explicit save:
```python
tool_context.state.recipes.append(recipe)
tool_context.save()  # Must call explicitly
```

### 4. Runner Pattern

**Google ADK:**
```python
runner = Runner(
    agent=recipe_agent,
    app_name=APP_NAME,
    session_service=service
)

# Run with streaming events
async for ev in runner.run_async(user_id, session_id, new_message):
    if ev.is_final_response():
        print(ev.content.parts[0].text)
```

**Microsoft Agent Framework:**
```python
class RecipeAssistant:
    def __init__(self, user_id, app_name):
        self.agent = create_recipe_agent()
        self.thread = AgentThread()
        self.context = ToolContext(user_id, app_name, state_store)
    
    async def ask(self, user_input: str) -> str:
        response = await self.agent.invoke(
            input_message=user_input,
            thread=self.thread,
        )
        return response.content
```

---

## 🗄️ Database Schema Comparison

### Google ADK

```mermaid
erDiagram
    SESSIONS {
        string id PK
        string app_name
        string user_id
        json state
        timestamp created_at
        timestamp updated_at
    }
    
    EVENTS {
        string id PK
        string session_id FK
        string author
        json content
        json actions
        timestamp timestamp
    }
    
    SESSIONS ||--o{ EVENTS : has
```

### Microsoft Agent Framework (Custom)

```mermaid
erDiagram
    USER_STATE {
        string user_id PK
        string app_name PK
        json state_json
        real created_at
        real updated_at
    }
    
    CONVERSATION_HISTORY {
        string id PK
        string user_id FK
        string app_name
        string role
        text content
        real timestamp
    }
    
    USER_STATE ||--o{ CONVERSATION_HISTORY : has
```

---

## 🏢 Recipe Assistant Components

### Tools Available

```mermaid
mindmap
  root((Recipe Assistant))
    add_recipe
      name
      ingredients
      instructions
      cook_time
    view_recipes
      List all recipes
    get_recipe
      Search by name
    delete_recipe
      Remove by name
    search_recipes
      Find by ingredient
```

### State Structure

```mermaid
classDiagram
    class RecipeState {
        +str chef_name
        +int total_recipes
        +List~Recipe~ recipes
        +to_dict() Dict
    }
    
    class Recipe {
        +str name
        +str ingredients
        +str instructions
        +str cook_time
        +str date_added
    }
    
    RecipeState "1" *-- "*" Recipe : contains
```

---

## ⚡ Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant M as Main Loop
    participant A as RecipeAssistant
    participant AG as ChatCompletionAgent
    participant T as Tools
    participant S as StateStore
    participant DB as SQLite
    
    M->>A: initialize()
    A->>S: get_state(user_id, app_name)
    S->>DB: SELECT state_json
    DB-->>S: state data
    S-->>A: RecipeState
    A-->>M: Ready
    
    loop Chat Loop
        U->>M: "Add pasta recipe"
        M->>A: ask(user_input)
        A->>AG: invoke(input, thread)
        AG->>T: add_recipe(name, ...)
        T->>S: state.recipes.append()
        T->>S: save()
        S->>DB: INSERT/UPDATE
        DB-->>S: OK
        T-->>AG: {"action": "add_recipe"}
        AG-->>A: response
        A-->>M: "Recipe added!"
        M-->>U: Display response
    end
```

---

## ✅ Advantages & Trade-offs

```mermaid
quadrantChart
    title State Management Comparison
    x-axis Manual Control --> Automatic
    y-axis Simple --> Complex
    quadrant-1 Automatic & Complex
    quadrant-2 Manual & Complex
    quadrant-3 Manual & Simple
    quadrant-4 Automatic & Simple
    Google ADK: [0.8, 0.6]
    Microsoft Agent Framework: [0.3, 0.5]
```

### Google ADK Advantages
- ✅ Built-in `DatabaseSessionService`
- ✅ Automatic state persistence via events
- ✅ Event sourcing pattern built-in
- ✅ Session management handled by framework
- ✅ `tool_context` automatically injected

### Microsoft Agent Framework Advantages
- ✅ Full control over state structure
- ✅ Custom database schema design
- ✅ Explicit persistence (predictable)
- ✅ Flexible state store implementation
- ✅ Can use any database/storage backend
- ✅ Better for complex state requirements

### Trade-offs

| Aspect | Google ADK | Microsoft Agent Framework |
|--------|------------|---------------------------|
| **Built-in Support** | Comprehensive | Minimal (build your own) |
| **Flexibility** | Moderate | High |
| **Boilerplate** | Less | More |
| **Control** | Limited | Full |
| **Event Sourcing** | Built-in | DIY |
| **Schema Control** | Framework-defined | Custom |

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
flowchart LR
    subgraph Google["Google ADK"]
        G1["DatabaseSessionService"]
        G2["session.state"]
        G3["tool_context.state"]
        G4["append_event()"]
        G1 --> G2 --> G3 --> G4
    end
    
    subgraph Microsoft["Microsoft Agent Framework"]
        M1["Custom StateStore"]
        M2["RecipeState dataclass"]
        M3["ToolContext.state"]
        M4["context.save()"]
        M1 --> M2 --> M3 --> M4
    end
```

| Feature | Google ADK | Microsoft Agent Framework |
|---------|------------|---------------------------|
| **Session service** | `DatabaseSessionService` | Custom `RecipeStateStore` |
| **State access** | `session.state` dict | `RecipeState` dataclass |
| **Tool context** | Auto-injected `tool_context` | Global `ToolContext` |
| **Persistence** | Event-based (automatic) | Explicit `save()` |
| **Runner** | `Runner` class | Custom `RecipeAssistant` |

The key insight is that Google ADK provides **built-in persistence infrastructure** while Microsoft Agent Framework requires **custom implementation** but offers more flexibility in designing your state management architecture.

---

## 🔗 References

- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Microsoft Agent Framework Thread Management](https://learn.microsoft.com/en-us/agent-framework/threads)
- [Google ADK Sessions Documentation](https://google.github.io/adk-docs/)

