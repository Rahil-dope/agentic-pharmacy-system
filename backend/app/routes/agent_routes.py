from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add the agent directory to sys.path so we can import agent.py correctly
agent_path = Path(__file__).parent.parent.parent.parent / "agent"
if str(agent_path) not in sys.path:
    sys.path.append(str(agent_path))

try:
    from agent import run_agent
except ImportError:
    # Fallback if the path logic is tricky in different environments
    # In a real production setup, this would be a proper package
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from agent.agent import run_agent

router = APIRouter(tags=["agent"])

class ChatRequest(BaseModel):
    customer_id: int
    message: str

class ChatResponse(BaseModel):
    response: Dict[str, Any]
    trace_url: str | None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Handle chat requests by calling the agent logic.
    """
    try:
        response, trace_url = run_agent(request.message, request.customer_id)
        return ChatResponse(response=response, trace_url=trace_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
