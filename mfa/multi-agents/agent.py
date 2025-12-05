"""
Multi-Agent Travel Planning System
This shows how to create sequential multi-agent workflows.
Translated from Google ADK to Microsoft Agent Framework

In Microsoft Agent Framework, multi-agent orchestration is done via:
1. Workflows - Graph-based execution with explicit control
2. AgentGroupChat - For conversational multi-agent scenarios
3. Sequential pattern - Agents run one after another

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import datetime
from zoneinfo import ZoneInfo
from typing import Any, Callable

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.workflows import Workflow, SequentialWorkflow
from agent_framework.models import OpenAIChatCompletionClient
from agent_framework.tools import tool, WebSearchTool


# Model configuration
AGENT_MODEL = "gpt-4o"  # OpenAI model name


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS - Function tools that agents can use
# ═══════════════════════════════════════════════════════════════════════════════

@tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_normalized = city.lower().replace(" ", "")

    # Mock weather data
    mock_weather_db = {
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25°C.",
        },
        "london": {
            "status": "success",
            "report": "It's cloudy in London with a temperature of 15°C.",
        },
        "tokyo": {
            "status": "success",
            "report": "Tokyo is experiencing light rain and a temperature of 18°C.",
        },
        "paris": {
            "status": "success",
            "report": "The weather in Paris is sunny with a temperature of 22°C.",
        },
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have weather information for '{city}'.",
        }


@tool
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    return {"status": "success", "report": report}


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL CLIENT - Shared model client for all agents
# ═══════════════════════════════════════════════════════════════════════════════

def create_model_client():
    """Create the OpenAI model client."""
    return OpenAIChatCompletionClient(
        model=AGENT_MODEL,
        # Credentials from environment: OPENAI_API_KEY
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-AGENTS - Individual specialized agents
# ═══════════════════════════════════════════════════════════════════════════════

def create_destination_research_agent() -> ChatCompletionAgent:
    """
    Destination Research Agent - Researches location information.
    
    Google ADK equivalent:
        Agent(
            name="DestinationResearchAgent",
            tools=[google_search],
            output_key="destination_research",
            ...
        )
    
    In Microsoft Agent Framework:
    - Tools are added via the tools parameter
    - output_key is handled via workflow state management
    """
    return ChatCompletionAgent(
        name="DestinationResearchAgent",
        description="An agent that researches travel destinations and gathers essential information",
        system_prompt="""
        You are a travel researcher. You will be given a destination and travel preferences, and you will research:
        - Best time to visit and weather patterns
        - Top attractions and must-see locations
        - Local culture, customs, and etiquette tips
        - Transportation options within the destination
        - Safety considerations and travel requirements
        Provide comprehensive destination insights for trip planning.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],  # Equivalent to google_search
    )


def create_itinerary_builder_agent() -> ChatCompletionAgent:
    """
    Itinerary Builder Agent - Creates detailed travel schedule.
    
    This agent receives the research from the previous agent via workflow state.
    """
    return ChatCompletionAgent(
        name="ItineraryBuilderAgent",
        description="An agent that creates structured travel itineraries with daily schedules",
        system_prompt="""
        You are a professional travel planner. Using the destination research provided, create a detailed itinerary that includes:
        - Day-by-day schedule with recommended activities
        - Suggested accommodation areas or districts
        - Estimated time requirements for each activity
        - Meal recommendations and dining suggestions
        - Budget estimates for major expenses
        Structure it logically for easy following during the trip.
        """,
        model_client=create_model_client(),
    )


def create_travel_optimizer_agent() -> ChatCompletionAgent:
    """
    Travel Optimizer Agent - Adds practical tips and optimizations.
    
    This is the final agent that produces the optimized travel plan.
    """
    return ChatCompletionAgent(
        name="TravelOptimizerAgent",
        description="An agent that optimizes travel plans with practical advice and alternatives",
        system_prompt="""
        You are a seasoned travel consultant. Using the itinerary provided, optimize it by adding:
        - Money-saving tips and budget alternatives
        - Packing recommendations specific to the destination
        - Backup plans for weather or unexpected situations
        - Local apps, websites, or resources to download
        - Cultural do's and don'ts for respectful travel
        
        Format the final output as:
        
        ITINERARY: [the detailed itinerary]
        
        OPTIMIZATION TIPS: [your money-saving and practical tips here]
        
        TRAVEL ESSENTIALS: [packing and preparation advice here]
        
        BACKUP PLANS: [alternative options and contingencies here]
        """,
        model_client=create_model_client(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SEQUENTIAL WORKFLOW - Orchestrates agents in sequence
# ═══════════════════════════════════════════════════════════════════════════════

class TravelPlanningWorkflow(SequentialWorkflow):
    """
    Sequential workflow that orchestrates the travel planning agents.
    
    Google ADK equivalent:
        SequentialAgent(
            name="TravelPlanningSystem",
            sub_agents=[agent1, agent2, agent3],
        )
    
    Microsoft Agent Framework uses Workflows for multi-agent orchestration:
    - SequentialWorkflow: Runs agents one after another
    - Each agent's output is passed to the next agent
    - State is managed via the workflow context
    
    Mapping:
    ┌─────────────────────────┬─────────────────────────────────────┐
    │ Google ADK              │ Microsoft Agent Framework           │
    ├─────────────────────────┼─────────────────────────────────────┤
    │ SequentialAgent         │ SequentialWorkflow                  │
    │ sub_agents=[]           │ agents=[] / add_agent()             │
    │ output_key              │ Workflow state / context            │
    │ Agent                   │ ChatCompletionAgent                 │
    │ tools=[google_search]   │ tools=[WebSearchTool()]             │
    └─────────────────────────┴─────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__(
            name="TravelPlanningSystem",
            description="A comprehensive system that researches destinations, builds itineraries, and optimizes travel plans",
        )
        
        # Create the sub-agents
        self.destination_agent = create_destination_research_agent()
        self.itinerary_agent = create_itinerary_builder_agent()
        self.optimizer_agent = create_travel_optimizer_agent()
        
        # Add agents to the sequential workflow
        # They will run in the order they are added
        self.add_agent(self.destination_agent)
        self.add_agent(self.itinerary_agent)
        self.add_agent(self.optimizer_agent)
    
    async def run(self, user_input: str) -> str:
        """
        Execute the sequential workflow.
        
        Flow:
        1. DestinationResearchAgent researches the destination
        2. ItineraryBuilderAgent creates itinerary from research
        3. TravelOptimizerAgent optimizes with practical tips
        """
        # Workflow state to pass data between agents
        # This is equivalent to Google ADK's output_key mechanism
        state = {
            "user_request": user_input,
            "destination_research": "",
            "travel_itinerary": "",
        }
        
        print("=" * 60)
        print("🌍 TRAVEL PLANNING WORKFLOW STARTED")
        print("=" * 60)
        
        # Step 1: Destination Research
        print("\n📍 Step 1: Researching destination...")
        print("-" * 40)
        research_result = await self.destination_agent.invoke(
            input_message=user_input,
            thread=AgentThread(),
        )
        state["destination_research"] = research_result.content
        print(f"✅ Research complete: {len(state['destination_research'])} chars")
        
        # Step 2: Build Itinerary (using research from step 1)
        print("\n📅 Step 2: Building itinerary...")
        print("-" * 40)
        itinerary_prompt = f"""
        Based on this destination research:
        
        {state['destination_research']}
        
        Create a detailed travel itinerary for: {user_input}
        """
        itinerary_result = await self.itinerary_agent.invoke(
            input_message=itinerary_prompt,
            thread=AgentThread(),
        )
        state["travel_itinerary"] = itinerary_result.content
        print(f"✅ Itinerary complete: {len(state['travel_itinerary'])} chars")
        
        # Step 3: Optimize (using itinerary from step 2)
        print("\n⚡ Step 3: Optimizing travel plan...")
        print("-" * 40)
        optimizer_prompt = f"""
        Based on this travel itinerary:
        
        {state['travel_itinerary']}
        
        Optimize this travel plan with practical tips and recommendations.
        """
        final_result = await self.optimizer_agent.invoke(
            input_message=optimizer_prompt,
            thread=AgentThread(),
        )
        
        print("\n" + "=" * 60)
        print("✅ TRAVEL PLANNING WORKFLOW COMPLETE")
        print("=" * 60)
        
        return final_result.content


# Create the root agent (workflow) instance
root_agent = TravelPlanningWorkflow()


# ═══════════════════════════════════════════════════════════════════════════════
# Example usage
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Example of how to use the multi-agent travel planning system."""
    
    workflow = TravelPlanningWorkflow()
    
    # User request
    user_request = "Plan a 5-day trip to Tokyo, Japan for a family with kids"
    
    print("\n📝 User Request:")
    print(f"   {user_request}")
    print()
    
    # Run the sequential workflow
    result = await workflow.run(user_request)
    
    print("\n🎯 FINAL TRAVEL PLAN:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
