from langgraph.prebuilt import create_react_agent

from pfefinder.agent.tools import search_pfe_books, submit_source
from pfefinder.core import prompts
from pfefinder.core.dates import target_year
from pfefinder.core.llm import get_llm


def build_agent():
    """Agent ReAct LangGraph : il cherche et propose des sources, il n'écrit jamais en base lui-même."""
    system = prompts.AGENT_SYSTEM.format(year=target_year())
    return create_react_agent(get_llm(), [search_pfe_books, submit_source], prompt=system)
