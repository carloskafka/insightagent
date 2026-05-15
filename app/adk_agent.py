import os
import uuid
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.config import GOOGLE_API_KEY
from app.tools import web_search, safe_calculate, search_documents_rag

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

APP_NAME = "insightagent"
MODEL = "gemini-2.5-flash"

_session_service = InMemorySessionService()

_agent = LlmAgent(
    name="InsightAgent",
    model=MODEL,
    description="Helpful AI assistant with web search, math, and document analysis.",
    instruction="""You are InsightAgent, a helpful and intelligent AI assistant powered by Gemini 2.5 Flash.

You have access to the following tools — use them whenever they improve the quality of your answer:
- web_search: find current information on the web
- safe_calculate: evaluate mathematical expressions safely
- search_documents_rag: search through documents the user has uploaded

Guidelines:
- Be concise, accurate, and friendly.
- When answering factual or time-sensitive questions, prefer using web_search.
- For math questions, always use safe_calculate instead of computing manually.
- If the user asks about an uploaded document, use search_documents_rag first.""",
    tools=[
        FunctionTool(web_search),
        FunctionTool(safe_calculate),
        FunctionTool(search_documents_rag),
    ],
)

_runner = Runner(
    agent=_agent,
    app_name=APP_NAME,
    session_service=_session_service,
)


async def run_agent(
    message: str,
    history: Optional[list] = None,
    session_id: Optional[str] = None,
) -> str:
    """Run the ADK agent for a single turn.

    Args:
        message: The user's current message.
        history: Previous messages from PostgreSQL (for cross-restart memory).
        session_id: Stable ID tied to the conversation (e.g. 'conv_42').
    """
    user_id = "default"
    sid = session_id or str(uuid.uuid4())

    # Get or create ADK session (methods are async in ADK 1.x)
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=sid
    )
    if session is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=sid
        )

    # Inject PostgreSQL history so the agent has memory after restarts
    context = ""
    if history:
        lines = [f"{m['role'].upper()}: {m['content']}" for m in history[-8:]]
        context = "Previous conversation:\n" + "\n".join(lines) + "\n\nCurrent message: "

    full_message = (context + message) if context else message

    content = types.Content(
        role="user",
        parts=[types.Part(text=full_message)],
    )

    response_text = ""
    async for event in _runner.run_async(
        user_id=user_id,
        session_id=sid,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = "".join(
                    part.text
                    for part in event.content.parts
                    if hasattr(part, "text") and part.text
                )

    return response_text or "I could not generate a response. Please try again."
