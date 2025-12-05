"""
Parallel Agent Content Creation System
This shows how to run multiple agents concurrently for parallel processing.
Translated from Google ADK to Microsoft Agent Framework

In Microsoft Agent Framework, parallel execution is done via:
1. ParallelWorkflow - Built-in parallel workflow pattern
2. asyncio.gather() - Python's native concurrent execution
3. Concurrent agent invocation with result aggregation

Reference: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
"""

import asyncio
from typing import Any, Dict, List
from dataclasses import dataclass

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.workflows import ParallelWorkflow
from agent_framework.models import OpenAIChatCompletionClient
from agent_framework.tools import WebSearchTool


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL CLIENT - Shared model client for all agents
# ═══════════════════════════════════════════════════════════════════════════════

def create_model_client():
    """Create the OpenAI model client."""
    return OpenAIChatCompletionClient(
        model="gpt-4o",  # OpenAI model name
        # Credentials from environment: OPENAI_API_KEY
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SUB-AGENTS - Specialized agents that run in parallel
# ═══════════════════════════════════════════════════════════════════════════════

def create_blog_writer_agent() -> ChatCompletionAgent:
    """
    Blog Content Writer Agent with Trend Analysis.
    
    Google ADK equivalent:
        Agent(
            name="TrendAwareBlogWriterAgent",
            tools=[google_search],
            output_key="blog_content",
            ...
        )
    """
    return ChatCompletionAgent(
        name="TrendAwareBlogWriterAgent",
        description="An agent that creates trend-aware blog content using comprehensive trend research",
        system_prompt="""
        You are a professional blog writer with expertise in trend analysis. Given a topic, you will:
        
        1. TREND RESEARCH PHASE:
           - Search for the topic + "trends 2025" to identify current trends
           - Search for the topic + "viral content social media" to find viral patterns
           - Search for the topic + "latest news industry updates" for recent developments
           - Search for the topic + "seasonal trends" to understand timing patterns
           - Search for the topic + "competitor campaigns" for competitive insights
        
        2. CONTENT ANALYSIS:
           - Identify trending keywords and topics from search results
           - Extract viral content patterns (what's getting high engagement)
           - Note recent industry news and developments
           - Understand seasonal trends and optimal timing
           - Analyze competitor strategies and campaigns
        
        3. BLOG CREATION:
           - Write a comprehensive, trend-aware blog post (800-1200 words)
           - Incorporate trending topics and keywords naturally
           - Reference recent industry developments
           - Include viral content insights and patterns
           - Structure for SEO with compelling headlines
           - Add current statistics and facts from research
        
        Always base your content on real trend data you discover through your searches.
        Make the content feel current, relevant, and backed by actual trending insights.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],
    )


def create_seo_specialist_agent() -> ChatCompletionAgent:
    """
    SEO Specialist Agent with Trend Research.
    
    Google ADK equivalent:
        Agent(
            name="TrendAwareSEOAgent",
            tools=[google_search],
            output_key="seo_strategy",
            ...
        )
    """
    return ChatCompletionAgent(
        name="TrendAwareSEOAgent",
        description="An agent that creates SEO strategies based on current trends and competitor analysis",
        system_prompt="""
        You are an SEO specialist who excels at trend-based keyword research. For the given topic, you will:
        
        1. KEYWORD TREND RESEARCH:
           - Search for the topic + "trending keywords 2025" 
           - Search for the topic + "popular search terms"
           - Search for the topic + "SEO keywords high volume"
           - Search for "what people search for" + the topic
        
        2. COMPETITOR ANALYSIS:
           - Search for the topic + "top performing content SEO"
           - Search for the topic + "competitor SEO strategies"
           - Analyze competitor content structures and keywords
        
        3. VIRAL CONTENT SEO:
           - Search for the topic + "viral content SEO analysis"
           - Identify content formats that rank well
           - Find trending long-tail keywords
        
        4. SEO STRATEGY CREATION:
           - High-value trending keywords and search terms
           - SEO-optimized titles and meta descriptions
           - Content structure recommendations based on top performers
           - Internal and external linking opportunities
           - Seasonal SEO timing recommendations
           - Competitor gap analysis and opportunities
        
        Focus on leveraging current search trends for maximum visibility.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],
    )


def create_visual_creator_agent() -> ChatCompletionAgent:
    """
    Visual Content Creator Agent with Viral Pattern Analysis.
    
    Google ADK equivalent:
        Agent(
            name="TrendAwareVisualAgent",
            tools=[google_search],
            output_key="visual_content",
            ...
        )
    """
    return ChatCompletionAgent(
        name="TrendAwareVisualAgent",
        description="An agent that creates visual content strategies based on viral patterns and visual trends",
        system_prompt="""
        You are a visual content strategist who identifies viral visual patterns. For the given topic, you will:
        
        1. VIRAL VISUAL RESEARCH:
           - Search for the topic + "viral videos trending formats"
           - Search for the topic + "popular social media visuals"
           - Search for the topic + "Instagram TikTok viral content"
           - Search for the topic + "infographic trending designs"
        
        2. PLATFORM-SPECIFIC TRENDS:
           - Search for the topic + "YouTube trending video styles"
           - Search for the topic + "Pinterest popular pins"
           - Search for the topic + "LinkedIn visual content trends"
        
        3. SEASONAL VISUAL PATTERNS:
           - Search for the topic + "seasonal visual content ideas"
           - Search for the topic + "holiday themed visuals"
        
        4. VISUAL STRATEGY CREATION:
           - Trending visual formats and styles for each platform
           - Specific image and video concepts based on viral patterns
           - Color schemes and design trends currently popular
           - Platform-optimized visual content recommendations
           - Seasonal visual themes and timing
           - Visual content calendar suggestions
        
        Base all recommendations on actual viral patterns you discover through research.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],
    )


def create_social_media_agent() -> ChatCompletionAgent:
    """
    Social Media Manager Agent with Engagement Analysis.
    
    Google ADK equivalent:
        Agent(
            name="TrendAwareSocialAgent",
            tools=[google_search],
            output_key="social_strategy",
            ...
        )
    """
    return ChatCompletionAgent(
        name="TrendAwareSocialAgent",
        description="An agent that creates social media strategies based on viral patterns and engagement trends",
        system_prompt="""
        You are a social media expert who analyzes viral content patterns. For the given topic, you will:
        
        1. VIRAL CONTENT RESEARCH:
           - Search for the topic + "viral social media posts 2025"
           - Search for the topic + "trending hashtags Instagram Twitter"
           - Search for the topic + "TikTok viral content ideas"
           - Search for the topic + "LinkedIn engagement strategies"
        
        2. PLATFORM TREND ANALYSIS:
           - Search for the topic + "Instagram trending formats"
           - Search for the topic + "Twitter viral tweets examples"
           - Search for the topic + "TikTok trending challenges"
           - Search for the topic + "YouTube Shorts popular content"
        
        3. ENGAGEMENT PATTERN RESEARCH:
           - Search for the topic + "high engagement social posts"
           - Search for the topic + "viral marketing campaigns social"
           - Search for the topic + "influencer collaboration trends"
        
        4. SOCIAL STRATEGY CREATION:
           - Platform-specific content based on viral patterns
           - Trending hashtags and optimal posting times
           - Content formats that drive highest engagement
           - Viral content techniques and strategies
           - Influencer collaboration opportunities
           - Community engagement and growth tactics
        
        Create strategies that leverage proven viral patterns and engagement techniques.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],
    )


def create_email_marketing_agent() -> ChatCompletionAgent:
    """
    Email Marketing Agent with Industry Trend Analysis.
    
    Google ADK equivalent:
        Agent(
            name="TrendAwareEmailAgent",
            tools=[google_search],
            output_key="email_campaigns",
            ...
        )
    """
    return ChatCompletionAgent(
        name="TrendAwareEmailAgent",
        description="An agent that creates email marketing campaigns based on industry trends and best practices",
        system_prompt="""
        You are an email marketing specialist who stays current with industry trends. For the given topic, you will:
        
        1. EMAIL TREND RESEARCH:
           - Search for the topic + "email marketing trends 2025"
           - Search for the topic + "newsletter best practices current"
           - Search for the topic + "email subject lines high open rates"
           - Search for "email marketing" + the topic + "successful campaigns"
        
        2. INDUSTRY NEWS RESEARCH:
           - Search for the topic + "industry news latest developments"
           - Search for the topic + "market trends email content"
           - Search for the topic + "customer behavior email preferences"
        
        3. CAMPAIGN PERFORMANCE ANALYSIS:
           - Search for the topic + "email campaign examples successful"
           - Search for the topic + "email automation trends"
           - Search for the topic + "lead magnet ideas trending"
        
        4. EMAIL STRATEGY CREATION:
           - Subject lines incorporating trending topics and industry news
           - Email content based on current market developments
           - Newsletter themes that align with industry trends
           - Lead magnets based on trending interests
           - Email sequence strategies using viral content patterns
           - Segmentation strategies based on current behavior trends
        
        Create email campaigns that feel timely, relevant, and based on current industry insights.
        """,
        model_client=create_model_client(),
        tools=[WebSearchTool()],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PARALLEL WORKFLOW - Orchestrates agents concurrently
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ParallelResults:
    """Container for results from all parallel agents."""
    blog_content: str
    seo_strategy: str
    visual_content: str
    social_strategy: str
    email_campaigns: str


class TrendAwareContentCreationSystem(ParallelWorkflow):
    """
    Parallel workflow that runs all content creation agents concurrently.
    
    Google ADK equivalent:
        ParallelAgent(
            name="TrendAwareContentCreationSystem",
            sub_agents=[agent1, agent2, agent3, agent4, agent5],
        )
    
    Microsoft Agent Framework uses ParallelWorkflow or asyncio.gather():
    - All agents receive the same input
    - All agents run concurrently (in parallel)
    - Results are collected after all complete
    
    Mapping:
    ┌─────────────────────────┬─────────────────────────────────────┐
    │ Google ADK              │ Microsoft Agent Framework           │
    ├─────────────────────────┼─────────────────────────────────────┤
    │ ParallelAgent           │ ParallelWorkflow / asyncio.gather() │
    │ sub_agents=[]           │ agents list + concurrent invoke     │
    │ output_key              │ Results dataclass / dict            │
    │ Automatic parallel      │ Explicit asyncio.gather()           │
    └─────────────────────────┴─────────────────────────────────────┘
    """
    
    def __init__(self):
        super().__init__(
            name="TrendAwareContentCreationSystem",
            description="A comprehensive content creation system that uses real-time trend monitoring to create data-driven, current content across all channels",
        )
        
        # Create all sub-agents
        self.blog_writer = create_blog_writer_agent()
        self.seo_specialist = create_seo_specialist_agent()
        self.visual_creator = create_visual_creator_agent()
        self.social_media = create_social_media_agent()
        self.email_marketing = create_email_marketing_agent()
        
        # Register agents for parallel execution
        self.agents = [
            self.blog_writer,
            self.seo_specialist,
            self.visual_creator,
            self.social_media,
            self.email_marketing,
        ]
    
    async def run(self, user_input: str) -> ParallelResults:
        """
        Execute all agents in parallel.
        
        In Google ADK, ParallelAgent automatically runs all sub_agents concurrently.
        In Microsoft Agent Framework, we use asyncio.gather() for parallel execution.
        """
        print("=" * 70)
        print("🚀 PARALLEL CONTENT CREATION SYSTEM STARTED")
        print("=" * 70)
        print(f"\n📝 Topic: {user_input}")
        print(f"\n⚡ Running {len(self.agents)} agents in PARALLEL...")
        print("-" * 70)
        
        # Create tasks for parallel execution
        # Each agent gets the same input and runs concurrently
        tasks = [
            self._run_agent(self.blog_writer, user_input, "blog_content"),
            self._run_agent(self.seo_specialist, user_input, "seo_strategy"),
            self._run_agent(self.visual_creator, user_input, "visual_content"),
            self._run_agent(self.social_media, user_input, "social_strategy"),
            self._run_agent(self.email_marketing, user_input, "email_campaigns"),
        ]
        
        # Run all agents in parallel using asyncio.gather()
        # This is the Microsoft Agent Framework equivalent of ParallelAgent
        results = await asyncio.gather(*tasks)
        
        # Collect results into structured output
        # Equivalent to Google ADK's output_key mechanism
        results_dict = {r["key"]: r["content"] for r in results}
        
        print("\n" + "=" * 70)
        print("✅ ALL PARALLEL AGENTS COMPLETED")
        print("=" * 70)
        
        return ParallelResults(
            blog_content=results_dict.get("blog_content", ""),
            seo_strategy=results_dict.get("seo_strategy", ""),
            visual_content=results_dict.get("visual_content", ""),
            social_strategy=results_dict.get("social_strategy", ""),
            email_campaigns=results_dict.get("email_campaigns", ""),
        )
    
    async def _run_agent(
        self, 
        agent: ChatCompletionAgent, 
        user_input: str, 
        output_key: str
    ) -> Dict[str, Any]:
        """
        Run a single agent and return its result with the output key.
        This simulates Google ADK's output_key behavior.
        """
        print(f"  🔄 Starting: {agent.name}")
        
        response = await agent.invoke(
            input_message=user_input,
            thread=AgentThread(),
        )
        
        print(f"  ✅ Completed: {agent.name}")
        
        return {
            "key": output_key,
            "agent": agent.name,
            "content": response.content,
        }


# Create the root agent (workflow) instance
root_agent = TrendAwareContentCreationSystem()


# ═══════════════════════════════════════════════════════════════════════════════
# Example usage
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Example of how to use the parallel content creation system."""
    
    workflow = TrendAwareContentCreationSystem()
    
    # User request - all agents will work on this topic in parallel
    topic = "sustainable fashion for millennials"
    
    print(f"\n📝 Creating content for: '{topic}'")
    print("   All 5 agents will run in PARALLEL!\n")
    
    # Run the parallel workflow
    results = await workflow.run(topic)
    
    # Display results from each agent
    print("\n" + "=" * 70)
    print("📊 CONTENT CREATION RESULTS")
    print("=" * 70)
    
    print("\n📝 BLOG CONTENT:")
    print("-" * 40)
    print(results.blog_content[:500] + "..." if len(results.blog_content) > 500 else results.blog_content)
    
    print("\n🔍 SEO STRATEGY:")
    print("-" * 40)
    print(results.seo_strategy[:500] + "..." if len(results.seo_strategy) > 500 else results.seo_strategy)
    
    print("\n🎨 VISUAL CONTENT:")
    print("-" * 40)
    print(results.visual_content[:500] + "..." if len(results.visual_content) > 500 else results.visual_content)
    
    print("\n📱 SOCIAL STRATEGY:")
    print("-" * 40)
    print(results.social_strategy[:500] + "..." if len(results.social_strategy) > 500 else results.social_strategy)
    
    print("\n📧 EMAIL CAMPAIGNS:")
    print("-" * 40)
    print(results.email_campaigns[:500] + "..." if len(results.email_campaigns) > 500 else results.email_campaigns)


if __name__ == "__main__":
    asyncio.run(main())
