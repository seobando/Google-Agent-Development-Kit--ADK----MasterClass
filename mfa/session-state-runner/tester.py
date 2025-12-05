#!/usr/bin/env python3
"""
Simple Study Buddy - Interactive CLI Application
A streamlined AI-powered study assistant using Microsoft Agent Framework
Translated from Google ADK

Features:
- Single AI agent with multiple tools
- Persistent state management with SQLite
- Interactive command-line interface
- Course and assignment tracking
- Study session logging
- Natural language interaction

Installation:
pip install agent-framework python-dotenv

Usage:
python tester.py
"""

import asyncio
import uuid
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

from agent_framework import ChatCompletionAgent, AgentThread
from agent_framework.models import OpenAIChatCompletionClient
from agent_framework.tools import tool


load_dotenv()

# Configuration
DB_PATH = Path(__file__).parent / "simple_study_buddy.db"
APP_NAME = "SimpleStudyBuddy"
USER_ID = "student"


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StudyState:
    """
    Persistent state for the study buddy.
    
    Google ADK equivalent:
        initial_state = {
            "student_name": student_name,
            "learning_style": learning_style,
            "courses": [],
            "assignments": [],
            "study_sessions": [],
            "total_study_minutes": 0,
        }
    """
    student_name: str = "Student"
    learning_style: str = "visual"
    courses: List[Dict[str, Any]] = field(default_factory=list)
    assignments: List[Dict[str, Any]] = field(default_factory=list)
    study_sessions: List[Dict[str, Any]] = field(default_factory=list)
    total_study_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudyState":
        return cls(**data)


class DatabaseSessionService:
    """
    SQLite-based session service for persistent storage.
    
    Google ADK equivalent:
        from google.adk.sessions import DatabaseSessionService
        service = DatabaseSessionService(db_url="sqlite:///./simple_study_buddy.db")
    
    In Microsoft Agent Framework:
    - Custom implementation for state persistence
    - SQLite database for storage
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                app_name TEXT,
                user_id TEXT,
                state_json TEXT,
                created_at REAL,
                updated_at REAL,
                UNIQUE(app_name, user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def list_sessions(self, app_name: str, user_id: str) -> List[Dict]:
        """
        List existing sessions.
        
        Google ADK equivalent:
            resp = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, state_json FROM sessions WHERE app_name = ? AND user_id = ?",
            (app_name, user_id)
        )
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row[0],
                "state": json.loads(row[1]) if row[1] else {},
            })
        
        conn.close()
        return sessions
    
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Create a new session.
        
        Google ADK equivalent:
            session = await service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                state=initial_state
            )
        """
        session_id = str(uuid.uuid4())
        now = time.time()
        state_json = json.dumps(state or {})
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (id, app_name, user_id, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, app_name, user_id, state_json, now, now))
        
        conn.commit()
        conn.close()
        
        return {"id": session_id, "state": state or {}}
    
    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> Optional[Dict]:
        """
        Get an existing session.
        
        Google ADK equivalent:
            session = await service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=session_id
            )
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT state_json FROM sessions WHERE app_name = ? AND user_id = ?",
            (app_name, user_id)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {"id": session_id, "state": json.loads(row[0]) if row[0] else {}}
        return None
    
    async def update_state(
        self,
        app_name: str,
        user_id: str,
        state: Dict[str, Any],
    ):
        """Update session state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET state_json = ?, updated_at = ?
            WHERE app_name = ? AND user_id = ?
        """, (json.dumps(state), time.time(), app_name, user_id))
        
        conn.commit()
        conn.close()


# Global service and state
service: Optional[DatabaseSessionService] = None
session_id: Optional[str] = None
current_state: Optional[StudyState] = None
agent: Optional[ChatCompletionAgent] = None
thread: Optional[AgentThread] = None


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

@tool
def add_course(name: str, instructor: str) -> dict:
    """Add a new course to your schedule.
    
    Args:
        name: The name of the course (e.g., "Calculus I", "Physics")
        instructor: The instructor's name (e.g., "Dr. Smith")
    """
    global current_state
    
    if current_state:
        course = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "instructor": instructor,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        current_state.courses.append(course)
        asyncio.create_task(_save_state())
        
        print(f"✅ Added course: {name} with {instructor}")
        print_courses(current_state.courses)
        return {"action": "add_course", "message": f"Added course: {name}"}
    
    return {"action": "add_course", "error": "Could not add course"}


@tool
def view_courses() -> dict:
    """View all enrolled courses."""
    global current_state
    
    if current_state:
        print_courses(current_state.courses)
        return {"action": "view_courses", "count": len(current_state.courses)}
    
    return {"action": "view_courses", "error": "Could not access courses"}


@tool
def add_assignment(course_name: str, title: str, due_date: str) -> dict:
    """Add a new assignment.
    
    Args:
        course_name: The course this assignment belongs to
        title: The title/name of the assignment
        due_date: Due date in format YYYY-MM-DD
    """
    global current_state
    
    if current_state:
        assignment = {
            "id": str(uuid.uuid4())[:8],
            "course_name": course_name,
            "title": title,
            "due_date": due_date,
            "status": "Pending",
            "added_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        current_state.assignments.append(assignment)
        asyncio.create_task(_save_state())
        
        print(f"✅ Added assignment: {title} for {course_name} (Due: {due_date})")
        print_assignments(current_state.assignments)
        return {"action": "add_assignment", "message": f"Added assignment: {title}"}
    
    return {"action": "add_assignment", "error": "Could not add assignment"}


@tool
def view_assignments(status_filter: str = "all") -> dict:
    """View all assignments.
    
    Args:
        status_filter: Filter by status - "all", "pending", or "completed"
    """
    global current_state
    
    if current_state:
        assignments = current_state.assignments
        
        if status_filter.lower() != "all":
            assignments = [
                a for a in assignments if a["status"].lower() == status_filter.lower()
            ]
        
        print_assignments(assignments, status_filter)
        return {"action": "view_assignments", "count": len(assignments)}
    
    return {"action": "view_assignments", "error": "Could not access assignments"}


@tool
def complete_assignment(title: str) -> dict:
    """Mark an assignment as completed.
    
    Args:
        title: The title of the assignment to mark as complete
    """
    global current_state
    
    if current_state:
        for assignment in current_state.assignments:
            if assignment["title"].lower() == title.lower():
                assignment["status"] = "Completed"
                assignment["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                asyncio.create_task(_save_state())
                
                print(f"✅ Completed assignment: {title}")
                print_assignments(current_state.assignments)
                return {"action": "complete_assignment", "message": f"Completed: {title}"}
        
        print(f"❌ Assignment '{title}' not found")
        return {"action": "complete_assignment", "error": f"Assignment '{title}' not found"}
    
    return {"action": "complete_assignment", "error": "Could not complete assignment"}


@tool
def log_study_session(subject: str, duration_minutes: int, notes: str = "") -> dict:
    """Log a study session.
    
    Args:
        subject: What you studied (e.g., "calculus", "physics")
        duration_minutes: How many minutes you studied
        notes: Optional notes about what you covered
    """
    global current_state
    
    if current_state:
        session = {
            "id": str(uuid.uuid4())[:8],
            "subject": subject,
            "duration_minutes": duration_minutes,
            "notes": notes,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
        }
        
        current_state.study_sessions.append(session)
        current_state.total_study_minutes += duration_minutes
        asyncio.create_task(_save_state())
        
        print(f"✅ Logged {duration_minutes} minute study session on {subject}")
        if notes:
            print(f"   Notes: {notes}")
        print_study_stats(current_state)
        return {"action": "log_study_session", "message": f"Logged study session: {subject}"}
    
    return {"action": "log_study_session", "error": "Could not log session"}


@tool
def view_study_stats() -> dict:
    """View your study statistics and recent sessions."""
    global current_state
    
    if current_state:
        print_study_stats(current_state)
        return {"action": "view_study_stats", "message": "Study stats displayed"}
    
    return {"action": "view_study_stats", "error": "Could not access stats"}


async def _save_state():
    """Save current state to database."""
    global service, current_state
    if service and current_state:
        await service.update_state(APP_NAME, USER_ID, current_state.to_dict())


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def print_courses(courses: List[Dict]):
    """Display courses in a formatted way."""
    if not courses:
        print("📚 No courses enrolled yet")
    else:
        print(f"\n📚 Your Courses ({len(courses)}):")
        print("-" * 40)
        for i, course in enumerate(courses, 1):
            print(f"  {i}. {course['name']}")
            print(f"     Instructor: {course['instructor']}")
            print(f"     Added: {course['added_date']}")
        print("-" * 40)


def print_assignments(assignments: List[Dict], status_filter: str = "all"):
    """Display assignments in a formatted way."""
    if not assignments:
        print(f"📋 No assignments found (filter: {status_filter})")
    else:
        print(f"\n📋 Your Assignments - {status_filter.title()} ({len(assignments)}):")
        print("-" * 50)
        for i, assignment in enumerate(assignments, 1):
            status_icon = "✅" if assignment["status"] == "Completed" else "⏳"
            print(f"  {status_icon} {i}. {assignment['title']}")
            print(f"     Course: {assignment['course_name']}")
            print(f"     Due: {assignment['due_date']} | Status: {assignment['status']}")
            if assignment.get("completed_date"):
                print(f"     Completed: {assignment['completed_date']}")
        print("-" * 50)


def print_study_stats(state: StudyState):
    """Display study statistics."""
    sessions = state.study_sessions
    total_minutes = state.total_study_minutes
    total_hours = total_minutes / 60
    
    print(f"\n📊 Study Statistics:")
    print("-" * 30)
    print(f"  Total Sessions: {len(sessions)}")
    print(f"  Total Hours: {total_hours:.1f}h")
    if sessions:
        avg_session = total_minutes / len(sessions)
        print(f"  Avg Session: {avg_session:.0f} minutes")
        
        print(f"\n  Recent Sessions:")
        for session in sessions[-5:]:
            print(f"    • {session['subject']} - {session['duration_minutes']}min ({session['date']})")
    print("-" * 30)


def print_header():
    """Print application header."""
    print("=" * 60)
    print("🎓 SIMPLE STUDY BUDDY - Your AI Academic Assistant")
    print("=" * 60)
    print("Powered by Microsoft Agent Framework | Type 'help' for commands")
    print()


def print_help():
    """Print help information."""
    print("\n📖 Available Commands:")
    print("-" * 40)
    print("COURSE MANAGEMENT:")
    print("  • 'add course Math with Dr. Smith'")
    print("  • 'show my courses' or 'view courses'")
    print()
    print("ASSIGNMENT TRACKING:")
    print("  • 'add assignment homework for Math due 2024-12-20'")
    print("  • 'view assignments' or 'show assignments'")
    print("  • 'complete homework'")
    print()
    print("STUDY LOGGING:")
    print("  • 'log 30 minute study session on calculus'")
    print("  • 'show study stats' or 'view stats'")
    print()
    print("GENERAL:")
    print("  • 'help' - Show this help")
    print("  • 'status' - Show current status")
    print("  • 'clear' - Clear screen")
    print("  • 'quit' or 'exit' - Exit application")
    print("-" * 40)


def print_status(state: StudyState):
    """Print current status."""
    pending_assignments = len([a for a in state.assignments if a["status"] == "Pending"])
    
    print(f"\n📊 Current Status:")
    print("-" * 30)
    print(f"  Student: {state.student_name}")
    print(f"  Learning Style: {state.learning_style}")
    print(f"  Enrolled Courses: {len(state.courses)}")
    print(f"  Pending Assignments: {pending_assignments}")
    print(f"  Study Sessions: {len(state.study_sessions)}")
    print(f"  Total Study Time: {state.total_study_minutes / 60:.1f} hours")
    print("-" * 30)


# ═══════════════════════════════════════════════════════════════════════════════
# AI AGENT DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

def create_study_agent(state: StudyState) -> ChatCompletionAgent:
    """
    Create the study buddy agent.
    
    Google ADK equivalent:
        study_agent = Agent(
            name="StudyBuddy",
            model="gemini-2.0-flash",
            instruction="...",
            tools=[...],
        )
    """
    system_prompt = f"""You are a friendly study assistant helping {state.student_name} manage their academic life.

Current Status:
- Student: {state.student_name}
- Learning Style: {state.learning_style}
- Total Study Time: {state.total_study_minutes} minutes

You can help with:
• Course management: add_course(name, instructor), view_courses()
• Assignment tracking: add_assignment(course_name, title, due_date), view_assignments(), complete_assignment(title)
• Study logging: log_study_session(subject, duration_minutes, notes), view_study_stats()

When users ask to:
- "Add course Math with Dr. Smith" → call add_course("Math", "Dr. Smith")
- "Show my courses" → call view_courses()
- "Add assignment homework for Math due tomorrow" → call add_assignment("Math", "homework", "2024-12-15")
- "View assignments" → call view_assignments()
- "Complete homework" → call complete_assignment("homework")
- "Log 30 minute study session on calculus" → call log_study_session("calculus", 30)
- "Show study stats" → call view_study_stats()

Always be encouraging and help them stay organized! Provide brief, helpful responses.
"""
    
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o",
    )
    
    return ChatCompletionAgent(
        name="StudyBuddy",
        description="Personal study assistant",
        system_prompt=system_prompt,
        model_client=model_client,
        tools=[
            add_course,
            view_courses,
            add_assignment,
            view_assignments,
            complete_assignment,
            log_study_session,
            view_study_stats,
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

async def initialize_session(student_name: str = "Student", learning_style: str = "visual"):
    """
    Initialize session.
    
    Google ADK equivalent:
        service = DatabaseSessionService(db_url=DB_URL)
        resp = await service.list_sessions(...)
        runner = Runner(agent=study_agent, app_name=APP_NAME, session_service=service)
    """
    global service, session_id, current_state, agent, thread
    
    try:
        print("🔄 Initializing Study Buddy...")
        
        # Create database service
        service = DatabaseSessionService(DB_PATH)
        
        # Check for existing session
        sessions = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)
        
        if sessions:
            session_id = sessions[0]["id"]
            current_state = StudyState.from_dict(sessions[0]["state"])
            print(f"✅ Resuming existing session: {session_id[:8]}...")
        else:
            # Create new session
            initial_state = StudyState(
                student_name=student_name,
                learning_style=learning_style,
            )
            
            session = await service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                state=initial_state.to_dict(),
            )
            session_id = session["id"]
            current_state = initial_state
            print(f"✅ Created new session: {session_id[:8]}...")
        
        # Create agent and thread
        agent = create_study_agent(current_state)
        thread = AgentThread()
        
        print("✅ Study Buddy initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Study Buddy: {str(e)}")
        return False


async def chat_with_agent(message: str) -> str:
    """
    Send message to agent and get response.
    
    Google ADK equivalent:
        async for event in runner.run_async(user_id, session_id, new_message):
            if event.is_final_response():
                print(event.content.parts[0].text)
    """
    global agent, thread
    
    try:
        response = await agent.invoke(
            input_message=message,
            thread=thread,
        )
        
        return response.content if response else "I'm having trouble understanding. Can you rephrase?"
        
    except Exception as e:
        return f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def setup_student():
    """Initial student setup."""
    print("\n🎓 Welcome to Study Buddy!")
    print("Let's set up your profile...")
    
    student_name = input("Enter your name (or press Enter for 'Student'): ").strip()
    if not student_name:
        student_name = "Student"
    
    print("\nChoose your learning style:")
    print("1. Visual (charts, diagrams, images)")
    print("2. Auditory (discussions, lectures)")
    print("3. Kinesthetic (hands-on, practice)")
    print("4. Reading/Writing (notes, text)")
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        styles = {"1": "visual", "2": "auditory", "3": "kinesthetic", "4": "reading"}
        if choice in styles:
            learning_style = styles[choice]
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    return student_name, learning_style


def handle_special_commands(user_input: str, state: StudyState) -> bool:
    """Handle special CLI commands that don't need AI."""
    command = user_input.lower().strip()
    
    if command in ["help", "?"]:
        print_help()
        return True
    
    elif command in ["status", "info"]:
        print_status(state)
        return True
    
    elif command in ["clear", "cls"]:
        import os
        os.system("cls" if os.name == "nt" else "clear")
        print_header()
        return True
    
    elif command in ["quit", "exit", "q"]:
        print("\n👋 Thanks for using Study Buddy! Keep studying hard!")
        return True
    
    return False


async def main_loop():
    """Main interactive loop."""
    global current_state
    
    print_header()
    
    # Setup student profile
    student_name, learning_style = setup_student()
    
    # Initialize session
    success = await initialize_session(student_name, learning_style)
    if not success:
        print("❌ Failed to initialize. Exiting...")
        return
    
    # Show initial status
    print_status(current_state)
    
    print(f"\n💬 Hi {student_name}! I'm ready to help you manage your studies.")
    print("Type 'help' for commands or just tell me what you need!")
    
    # Main chat loop
    while True:
        try:
            print("\n" + "-" * 60)
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if handle_special_commands(user_input, current_state):
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                continue
            
            # Send to AI agent
            print("🤖 Study Buddy: ", end="", flush=True)
            response = await chat_with_agent(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Caught Ctrl+C. Thanks for using Study Buddy!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Type 'help' if you need assistance.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main function."""
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════════
"""
EXAMPLE COMMANDS TO TRY:

Setup:
- Run: python tester.py
- Follow setup prompts for name and learning style

Course Management:
- "Add course Calculus I with Dr. Smith"
- "Add course Physics with Dr. Johnson"
- "Show my courses"

Assignment Tracking:
- "Add assignment Problem Set 1 for Calculus I due 2024-12-20"
- "Add assignment Lab Report for Physics due 2024-12-25"
- "View my assignments"
- "Complete Problem Set 1"

Study Logging:
- "Log 45 minute study session on derivatives"
- "Log 60 minute study session on kinematics with notes solved 10 problems"
- "Show my study stats"

Special Commands:
- "help" - Show all commands
- "status" - Show current overview
- "clear" - Clear screen
- "quit" - Exit application

The AI agent understands natural language and will call the appropriate tools
to help you manage your academic life!
"""
