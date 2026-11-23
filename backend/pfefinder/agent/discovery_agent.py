from langgraph.prebuilt import create_react_agent

from pfefinder.agent.discovery_tools import search_pfe_books, submit_source
from pfefinder.rag import prompts
from pfefinder.common.academic_year import target_year
from pfefinder.rag.chat_model import get_llm


def build_agent():
    """Agent ReAct LangGraph : il cherche et propose des sources, il n'écrit jamais en base lui-même."""
    system = prompts.AGENT_SYSTEM.format(year=target_year())
    return create_react_agent(get_llm(), [search_pfe_books, submit_source], prompt=system)
