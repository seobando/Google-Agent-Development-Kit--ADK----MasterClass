"""
Persistent Recipe Assistant Agent
This shows how to persist agent state across sessions using a database.
Translated from Google ADK to Microsoft Agent Framework

In Microsoft Agent Framework, persistence is handled via:
1. AgentThread - Maintains conversation history and state
2. ThreadStore / DatabaseThreadStore - Persists threads to database
3. Context providers - Inject state into agent context
4. Checkpointing - Save/restore workflow state

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import asyncio
import time
import uuid
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.threads import ThreadStore, DatabaseThreadStore
from agent_framework.models import AzureOpenAIChatCompletionClient
from agent_framework.tools import tool
from agent_framework.context import ContextProvider


load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent / "recipe_data.db"
APP_NAME = "Personal Recipe Assistant"
USER_ID = "alice"


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT - Persistent State Store
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RecipeState:
    """
    Persistent state for the recipe assistant.
    
    Google ADK equivalent:
        session.state = {
            "chef_name": "Alice",
            "total_recipes": 0,
            "recipes": []
        }
    
    In Microsoft Agent Framework, state is managed via:
    - AgentThread for conversation state
    - Custom state store for application data
    """
    chef_name: str = "Alice"
    total_recipes: int = 0
    recipes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RecipeStateStore:
    """
    Persistent state store using SQLite.
    
    Google ADK equivalent:
        DatabaseSessionService(db_url="sqlite:///./recipe_data.db")
    
    In Microsoft Agent Framework:
    - ThreadStore / DatabaseThreadStore for thread persistence
    - Custom state stores for application-specific data
    
    Mapping:
    ┌─────────────────────────────┬─────────────────────────────────────┐
    │ Google ADK                  │ Microsoft Agent Framework           │
    ├─────────────────────────────┼─────────────────────────────────────┤
    │ DatabaseSessionService      │ DatabaseThreadStore + custom store  │
    │ session.state               │ Thread state + custom state         │
    │ service.create_session()    │ store.create_thread()               │
    │ service.get_session()       │ store.get_thread()                  │
    │ service.list_sessions()     │ store.list_threads()                │
    │ service.append_event()      │ Automatic with thread updates       │
    └─────────────────────────────┴─────────────────────────────────────┘
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database for state persistence."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for state persistence
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_state (
                user_id TEXT PRIMARY KEY,
                app_name TEXT,
                state_json TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                app_name TEXT,
                role TEXT,
                content TEXT,
                timestamp REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_state(self, user_id: str, app_name: str) -> RecipeState:
        """
        Get state for a user/app combination.
        
        Equivalent to Google ADK's:
            session = service.get_session(app_name, user_id, session_id)
            state = session.state
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT state_json FROM user_state WHERE user_id = ? AND app_name = ?",
            (user_id, app_name)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            state_dict = json.loads(row[0])
            return RecipeState(**state_dict)
        
        return RecipeState()
    
    def save_state(self, user_id: str, app_name: str, state: RecipeState):
        """
        Save state for a user/app combination.
        
        Equivalent to Google ADK's:
            service.append_event(session, event_with_state_delta)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        state_json = json.dumps(state.to_dict())
        now = time.time()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_state (user_id, app_name, state_json, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE((SELECT created_at FROM user_state WHERE user_id = ? AND app_name = ?), ?), ?)
        """, (user_id, app_name, state_json, user_id, app_name, now, now))
        
        conn.commit()
        conn.close()
    
    def list_users(self, app_name: str) -> List[str]:
        """
        List all users with state for an app.
        
        Equivalent to Google ADK's:
            service.list_sessions(app_name, user_id)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT DISTINCT user_id FROM user_state WHERE app_name = ?",
            (app_name,)
        )
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return users


# Global state store instance
state_store = RecipeStateStore(DB_PATH)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS - Recipe management functions
# ═══════════════════════════════════════════════════════════════════════════════

# We'll pass state through a context object
class ToolContext:
    """
    Context passed to tools for state access.
    
    Google ADK equivalent: tool_context parameter with state attribute
    """
    def __init__(self, user_id: str, app_name: str, store: RecipeStateStore):
        self.user_id = user_id
        self.app_name = app_name
        self.store = store
        self._state: Optional[RecipeState] = None
    
    @property
    def state(self) -> RecipeState:
        if self._state is None:
            self._state = self.store.get_state(self.user_id, self.app_name)
        return self._state
    
    def save(self):
        """Persist state changes to database."""
        if self._state:
            self._state.total_recipes = len(self._state.recipes)
            self.store.save_state(self.user_id, self.app_name, self._state)


# Global context (will be set before agent invocation)
tool_context: Optional[ToolContext] = None


@tool
def add_recipe(
    name: str,
    ingredients: str,
    instructions: str,
    cook_time: str = "30 minutes",
) -> dict:
    """Add a new recipe to your collection.
    
    Args:
        name: The name of the recipe
        ingredients: List of ingredients needed
        instructions: Step-by-step cooking instructions
        cook_time: How long the recipe takes to cook (default: 30 minutes)
    """
    global tool_context
    
    recipe = {
        "name": name,
        "ingredients": ingredients,
        "instructions": instructions,
        "cook_time": cook_time,
        "date_added": time.strftime("%Y-%m-%d"),
    }
    
    if tool_context:
        tool_context.state.recipes.append(recipe)
        tool_context.save()  # Persist to database
        
        print(f"[Recipes] Added recipe: {name}")
        print_recipe_summary(tool_context.state.recipes)
        
        return {
            "action": "add_recipe",
            "recipe": name,
            "message": f"Added recipe: {name}",
        }
    
    return {"action": "add_recipe", "error": "No context available"}


@tool
def view_recipes() -> dict:
    """View all saved recipes in your collection."""
    global tool_context
    
    if tool_context:
        recipes = tool_context.state.recipes
        print_all_recipes(recipes)
        return {
            "action": "view_recipes",
            "count": len(recipes),
            "message": "Here are all your saved recipes",
        }
    
    return {"action": "view_recipes", "error": "No context available"}


@tool
def get_recipe(name: str) -> dict:
    """Get details of a specific recipe by name.
    
    Args:
        name: The name of the recipe to retrieve
    """
    global tool_context
    
    if tool_context:
        recipes = tool_context.state.recipes
        
        # Find recipe (case insensitive)
        for recipe in recipes:
            if recipe["name"].lower() == name.lower():
                print_recipe_details(recipe)
                return {
                    "action": "get_recipe",
                    "recipe": name,
                    "found": True,
                    "message": f"Found recipe: {name}",
                }
        
        print(f"[Recipes] Recipe '{name}' not found")
        return {
            "action": "get_recipe",
            "recipe": name,
            "found": False,
            "message": f"Recipe '{name}' not found",
        }
    
    return {"action": "get_recipe", "error": "No context available"}


@tool
def delete_recipe(name: str) -> dict:
    """Delete a recipe by name.
    
    Args:
        name: The name of the recipe to delete
    """
    global tool_context
    
    if tool_context:
        recipes = tool_context.state.recipes
        
        # Find and remove recipe
        for i, recipe in enumerate(recipes):
            if recipe["name"].lower() == name.lower():
                recipes.pop(i)
                tool_context.save()  # Persist to database
                
                print(f"[Recipes] Deleted recipe: {name}")
                print_recipe_summary(recipes)
                return {
                    "action": "delete_recipe",
                    "recipe": name,
                    "deleted": True,
                    "message": f"Deleted recipe: {name}",
                }
        
        print(f"[Recipes] Recipe '{name}' not found")
        return {
            "action": "delete_recipe",
            "recipe": name,
            "deleted": False,
            "message": f"Recipe '{name}' not found",
        }
    
    return {"action": "delete_recipe", "error": "No context available"}


@tool
def search_recipes(ingredient: str) -> dict:
    """Search for recipes containing a specific ingredient.
    
    Args:
        ingredient: The ingredient to search for
    """
    global tool_context
    
    if tool_context:
        recipes = tool_context.state.recipes
        
        # Find recipes containing the ingredient
        matching_recipes = []
        for recipe in recipes:
            if ingredient.lower() in recipe["ingredients"].lower():
                matching_recipes.append(recipe["name"])
        
        if matching_recipes:
            print(f"[Search] Found {len(matching_recipes)} recipe(s) with '{ingredient}':")
            for name in matching_recipes:
                print(f"  • {name}")
        else:
            print(f"[Search] No recipes found with ingredient '{ingredient}'")
        
        return {
            "action": "search_recipes",
            "ingredient": ingredient,
            "found": len(matching_recipes),
            "recipes": matching_recipes,
        }
    
    return {"action": "search_recipes", "error": "No context available"}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS - For debugging and display
# ═══════════════════════════════════════════════════════════════════════════════

def print_recipe_summary(recipes: List[Dict]):
    if not recipes:
        print("[Recipes] No recipes saved yet")
    else:
        print(f"[Recipes] Total: {len(recipes)} recipe(s)")
        for recipe in recipes:
            print(f"  • {recipe['name']} ({recipe['cook_time']}) - added {recipe['date_added']}")


def print_all_recipes(recipes: List[Dict]):
    if not recipes:
        print("[Recipes] No recipes saved yet")
    else:
        print(f"\n[Recipe Collection] {len(recipes)} recipe(s):")
        for i, recipe in enumerate(recipes, 1):
            print(f"\n{i}. {recipe['name']}")
            print(f"   Cook time: {recipe['cook_time']}")
            print(f"   Added: {recipe['date_added']}")


def print_recipe_details(recipe: Dict):
    print(f"\n[Recipe Details] {recipe['name']}")
    print(f"Cook time: {recipe['cook_time']}")
    print(f"Added: {recipe['date_added']}")
    print(f"\nIngredients:\n{recipe['ingredients']}")
    print(f"\nInstructions:\n{recipe['instructions']}")


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

def create_recipe_agent() -> ChatCompletionAgent:
    """
    Create the recipe assistant agent.
    
    Google ADK equivalent:
        Agent(
            name="recipe_agent",
            model="gemini-2.0-flash",
            tools=[add_recipe, view_recipes, ...],
            instruction="...",
        )
    
    In Microsoft Agent Framework:
    - ChatCompletionAgent for LLM-based agent
    - Tools decorated with @tool
    - system_prompt instead of instruction
    """
    model_client = AzureOpenAIChatCompletionClient(
        deployment="gpt-4o",
    )
    
    return ChatCompletionAgent(
        name="recipe_agent",
        description="Personal recipe collection assistant",
        system_prompt="""
You help users manage their personal recipe collection. You can add, view, search, and delete recipes.

When the user wants to:
  • Add a recipe      → call add_recipe(name, ingredients, instructions, cook_time)
  • View all recipes  → call view_recipes()
  • Get specific recipe → call get_recipe(name)
  • Delete a recipe   → call delete_recipe(name)
  • Search by ingredient → call search_recipes(ingredient)

Always be friendly and helpful. Suggest recipe ideas if asked. Confirm actions taken.

Example commands you understand:
- "Add my pasta recipe"
- "Show me the chocolate cake recipe"
- "What recipes use chicken?"
- "Delete the old soup recipe"
""",
        model_client=model_client,
        tools=[add_recipe, view_recipes, get_recipe, delete_recipe, search_recipes],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class RecipeAssistant:
    """
    Main assistant class that manages sessions and state.
    
    Google ADK equivalent:
        service = DatabaseSessionService(db_url=DB_URL)
        runner = Runner(agent=recipe_agent, app_name=APP_NAME, session_service=service)
    
    In Microsoft Agent Framework:
    - AgentThread for conversation history
    - Custom state store for persistent data
    - Direct agent invocation
    """
    
    def __init__(self, user_id: str, app_name: str):
        self.user_id = user_id
        self.app_name = app_name
        self.agent = create_recipe_agent()
        self.thread = AgentThread()
        self.context = ToolContext(user_id, app_name, state_store)
    
    async def initialize(self):
        """
        Initialize the session.
        
        Google ADK equivalent:
            resp = await service.list_sessions(app_name, user_id)
            if resp.sessions:
                SESSION_ID = resp.sessions[0].id
            else:
                session = await service.create_session(...)
        """
        global tool_context
        tool_context = self.context
        
        # Load existing state
        state = self.context.state
        
        if state.recipes:
            print(f"Continuing session for {state.chef_name}")
            print(f"  You have {len(state.recipes)} recipe(s) saved")
        else:
            print(f"New session created for {state.chef_name}")
            # Save initial state
            self.context.save()
    
    async def ask(self, user_input: str) -> str:
        """
        Send a message to the agent.
        
        Google ADK equivalent:
            async for ev in runner.run_async(user_id, session_id, new_message):
                if ev.is_final_response():
                    print(ev.content.parts[0].text)
        """
        global tool_context
        tool_context = self.context  # Ensure context is set
        
        response = await self.agent.invoke(
            input_message=user_input,
            thread=self.thread,
        )
        
        return response.content if response else "I couldn't process that request."


# Create root agent instance for module compatibility
root_agent = create_recipe_agent()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """
    Main chat loop.
    
    Google ADK equivalent:
        async def main():
            await initialize_session()
            while True:
                q = input("You: ")
                await ask_agent(q)
    """
    assistant = RecipeAssistant(USER_ID, APP_NAME)
    await assistant.initialize()
    
    print("\n🍳 Personal Recipe Assistant ready! (type 'quit' to exit)")
    print("Try: 'add pasta recipe', 'view recipes', 'search chicken', 'get pasta recipe'\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ("quit", "exit"):
                print("Recipe collection saved. Happy cooking! 👋")
                break
            
            response = await assistant.ask(user_input)
            print(f"\n👩‍🍳 Recipe Assistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nRecipe collection saved. Happy cooking! 👋")
            break


if __name__ == "__main__":
    asyncio.run(main())
