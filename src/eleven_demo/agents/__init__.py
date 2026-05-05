"""ElevenAgents helper surface: factory, tool schemas, knowledge base, simulation."""

from eleven_demo.agents.conversation_sim import Analysis, SimulationResult, ToolCall, Turn, simulate
from eleven_demo.agents.factory import (
    create_agent,
    delete_agent,
    find_agent_by_name,
    list_agents,
    update_agent,
    upsert_agent,
)
from eleven_demo.agents.kb import (
    RagIndex,
    compute_rag,
    list_kb_documents,
    upload_kb_file,
    upload_kb_text,
)
from eleven_demo.agents.tools import TOOLS_REGISTRY

__all__ = [
    "TOOLS_REGISTRY",
    "Analysis",
    "RagIndex",
    "SimulationResult",
    "ToolCall",
    "Turn",
    "compute_rag",
    "create_agent",
    "delete_agent",
    "find_agent_by_name",
    "list_agents",
    "list_kb_documents",
    "simulate",
    "update_agent",
    "upload_kb_file",
    "upload_kb_text",
    "upsert_agent",
]
