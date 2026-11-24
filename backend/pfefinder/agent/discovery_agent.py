from langgraph.prebuilt import create_react_agent

from pfefinder.agent.guardrails import SEED_URLS
from pfefinder.agent.discovery_tools import explore_page, submit_source
from pfefinder.rag import prompts
from pfefinder.common.academic_year import target_year
from pfefinder.rag.chat_model import get_llm


def build_agent():
    """Agent ReAct LangGraph : il explore les sites de confiance et propose des sources, il n'écrit jamais en base lui-même."""
    system = prompts.AGENT_SYSTEM.format(year=target_year(), seeds=", ".join(SEED_URLS))
    return create_react_agent(get_llm(), [explore_page, submit_source], prompt=system)
