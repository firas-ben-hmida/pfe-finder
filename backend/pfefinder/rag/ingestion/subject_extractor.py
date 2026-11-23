"""Chaîne LCEL d'extraction : texte d'un PFE book -> sujets structurés (Pydantic)."""
from langchain_core.prompts import ChatPromptTemplate

from pfefinder.domain.models import ExtractedBook
from pfefinder.rag import prompts
from pfefinder.rag.chat_model import get_llm


def extract_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.EXTRACT_SYSTEM), ("human", prompts.EXTRACT_HUMAN)])
    return prompt | get_llm().with_structured_output(ExtractedBook)
