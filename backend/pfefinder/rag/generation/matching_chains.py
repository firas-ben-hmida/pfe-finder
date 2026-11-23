"""Chaînes LCEL du matching : CV -> profil, puis justification des sujets récupérés."""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from pfefinder.domain.models import Profile
from pfefinder.rag import prompts
from pfefinder.rag.chat_model import resilient


class SubjectReason(BaseModel):
    id: int
    raison: str = Field(description="Une phrase expliquant pourquoi ce sujet correspond au profil")


class Reasons(BaseModel):
    raisons: list[SubjectReason] = Field(default_factory=list)


def profile_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.PROFILE_SYSTEM), ("human", prompts.PROFILE_HUMAN)])
    return resilient(lambda llm: prompt | llm.with_structured_output(Profile), allow_local=False)


def reason_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.REASON_SYSTEM), ("human", prompts.REASON_HUMAN)])
    return resilient(lambda llm: prompt | llm.with_structured_output(Reasons), allow_local=False)
