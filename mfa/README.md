# Microsoft Agent Framework Examples

This folder contains translations of Google ADK examples to **Microsoft Agent Framework**.

## 📦 Installation

```bash
pip install uv
uv sync
```

## 🔐 Environment Variables

Create a `.env` file in the `mfa` folder with:

```bash
OPENAI_API_KEY=sk-your-openai-api-key
```

> **Note**: These examples use regular OpenAI API. If you prefer Azure OpenAI, you can modify the imports to use `AzureOpenAIChatCompletionClient` instead.

---

## 📁 Examples & Use Cases

### 🔔 agent-callback — Lifecycle Monitoring with Middleware

| | |
|---|---|
| **Problem** | How do you monitor agent performance, log requests, and track execution time without modifying the core agent logic? |
| **Solution** | Use middleware callbacks to intercept agent lifecycle events (before/after processing) for logging, timing, and analytics. |
| **Use Case** | A **Math Tutor Agent** that logs when each request starts, measures response time, and confirms successful responses—all transparently via middleware. |
| **Run** | `uv run python agent-callback/agent.py` |

**Key Concepts:**
- `before_agent_callback` → Middleware logic before `next_handler()`
- `after_agent_callback` → Middleware logic after `next_handler()`
- Useful for: authentication, request logging, performance monitoring

---

### 🛡️ model-callback — Request/Response Filtering

| | |
|---|---|
| **Problem** | How do you filter, block, or modify content going TO and FROM the AI model without changing agent logic? |
| **Solution** | Use model-level middleware to intercept requests before they reach the LLM and modify responses before they're returned. |
| **Use Case** | A **Filtered Chatbot** that blocks math-related questions (content filtering) and automatically appends a robot emoji 🤖 to all responses. |
| **Run** | `uv run python model-callback/agent.py` |

**Key Concepts:**
- Block requests by returning early without calling `next_handler()`
- Modify responses after the model call
- Useful for: content moderation, adding disclaimers, response formatting

---

### 🌍 multi-agents — Sequential Workflow (Travel Planner)

| | |
|---|---|
| **Problem** | How do you orchestrate multiple specialized agents to work together in a step-by-step pipeline, where each agent's output feeds into the next? |
| **Solution** | Use a sequential workflow that chains agents together—each agent receives the previous agent's output as context. |
| **Use Case** | A **Travel Planning System** with 3 specialized agents working in sequence: |
| | 1. **DestinationResearchAgent** — Researches the destination (attractions, culture, weather) |
| | 2. **ItineraryBuilderAgent** — Creates a day-by-day travel schedule from the research |
| | 3. **TravelOptimizerAgent** — Adds money-saving tips, packing lists, and backup plans |
| **Run** | `uv run python multi-agents/agent.py` |

**Key Concepts:**
- `SequentialWorkflow` orchestrates agents in order
- Output from Agent 1 → Input for Agent 2 → Input for Agent 3
- Each agent has specialized expertise (research → planning → optimization)

---

### ⚡ parallel-agent — Concurrent Execution (Content Creation)

| | |
|---|---|
| **Problem** | How do you run multiple independent agents simultaneously to reduce total execution time when they don't depend on each other? |
| **Solution** | Use parallel execution with `asyncio.gather()` to run all agents concurrently, then aggregate their results. |
| **Use Case** | A **Trend-Aware Content Creation System** with 5 agents running in parallel: |
| | 1. **TrendAwareBlogWriterAgent** — Creates SEO-optimized blog posts with trend research |
| | 2. **TrendAwareSEOAgent** — Generates keyword strategies and competitor analysis |
| | 3. **TrendAwareVisualAgent** — Creates visual content recommendations for each platform |
| | 4. **TrendAwareSocialAgent** — Develops social media strategies with viral patterns |
| | 5. **TrendAwareEmailAgent** — Creates email marketing campaigns based on trends |
| **Run** | `uv run python parallel-agent/agent.py` |

**Key Concepts:**
- All agents receive the same topic/input
- All agents execute concurrently (not sequentially)
- Results are collected after all agents complete
- 5x faster than running sequentially!

---

### 💾 persistent_agent — SQLite State Persistence (Recipe App)

| | |
|---|---|
| **Problem** | How do you maintain agent state (data, preferences, history) across sessions so users can continue where they left off? |
| **Solution** | Use a database-backed state store (SQLite) to persist user data between sessions, with tools that read/write to the database. |
| **Use Case** | A **Personal Recipe Assistant** that remembers your recipe collection across sessions: |
| | - **Add recipes** with ingredients, instructions, and cook time |
| | - **View all recipes** in your collection |
| | - **Search recipes** by ingredient |
| | - **Get/Delete recipes** by name |
| | - All data persists to SQLite and survives restarts |
| **Run** | `uv run python persistent_agent/agent.py` |

**Key Concepts:**
- `RecipeStateStore` wraps SQLite for persistence
- `ToolContext` provides state access to tools
- State is loaded at session start and saved after each tool call
- Works across app restarts—your recipes are never lost

---

### 🎓 session-state-runner — Session Management (Customer Support)

| | |
|---|---|
| **Problem** | How do you maintain in-memory session state with structured data, interpolate state into prompts, and parse structured outputs? |
| **Solution** | Use an in-memory session service with Pydantic schemas for structured output and state interpolation in system prompts. |
| **Use Case** | A **TechStore Customer Support Agent** that: |
| | - Maintains customer profile (name, preferences, orders, loyalty points) |
| | - Personalizes responses using customer data in the system prompt |
| | - Returns structured JSON with customer state |
| | - Stores parsed state back into the session |
| **Run** | `uv run python session-state-runner/tester.py` |

**Key Concepts:**
- `InMemorySessionService` stores sessions in memory
- State interpolation: `{customer_name}` in prompts becomes actual data
- Structured output with Pydantic models
- `output_key` pattern for storing structured responses in state

---

## 📖 Analysis Documents

Each example includes an `ANALYSIS.md` with:
- Component mapping from Google ADK
- Mermaid architecture diagrams
- Code comparison examples
- Trade-offs analysis

## 🔗 References

- [Microsoft Agent Framework Docs](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Original Google ADK Course](https://github.com/pdichone/adk-course)
