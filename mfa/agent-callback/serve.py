"""
Serve the Math Tutor Agent with a Web UI
Similar to Google ADK's `adk web` command

Run with: python serve.py
Then open: http://127.0.0.1:8080
"""

from agent_framework.devui import serve
from agent import root_agent

if __name__ == "__main__":
    print("🚀 Starting Agent Framework Dev UI...")
    print("📍 Open http://127.0.0.1:8080 in your browser")
    print("Press Ctrl+C to stop\n")
    
    serve(
        entities=[root_agent],
        port=8080,
        auto_open=True,  # Automatically open browser
        ui_enabled=True,
    )

