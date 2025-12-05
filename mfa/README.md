# Microsoft Agent Framework Examples

This folder contains translations of Google ADK examples to **Microsoft Agent Framework**.

## 📦 Installation

```bash
pip install uv
uv sync
```

## 🔐 Environment Variables

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## 📁 Examples

| Example | Description | Run Command |
|---------|-------------|-------------|
| **agent-callback** | Middleware for agent lifecycle | `uv run python agent-callback/agent.py` |
| **model-callback** | Model-level request/response interception | `uv run python model-callback/agent.py` |
| **multi-agents** | Sequential workflow (Travel Planner) | `uv run python multi-agents/agent.py` |
| **parallel-agent** | Parallel execution (Content Creation) | `uv run python parallel-agent/agent.py` |
| **persistent_agent** | SQLite state persistence (Recipe App) | `uv run python persistent_agent/agent.py` |
| **session-state-runner** | Session management (Study Buddy) | `uv run python session-state-runner/tester.py` |

## 📖 Analysis Documents

Each example includes an `ANALYSIS.md` with:
- Component mapping from Google ADK
- Mermaid architecture diagrams
- Code comparison examples
- Trade-offs analysis

## 🔗 References

- [Microsoft Agent Framework Docs](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Original Google ADK Course](https://github.com/pdichone/adk-course)
