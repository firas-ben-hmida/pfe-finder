"""Chaînes LCEL du matching : CV -> profil, puis notation et justification des sujets candidats."""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from pfefinder.domain.models import Profile
from pfefinder.rag import prompts
from pfefinder.rag.chat_model import resilient


class SubjectJudgement(BaseModel):
    id: int
    pertinence: int = Field(ge=0, le=10, description="Note de pertinence du sujet pour ce profil, de 0 à 10")
    raison: str = Field(description="Une phrase expliquant la note")


class Judgements(BaseModel):
    sujets: list[SubjectJudgement] = Field(default_factory=list)


def profile_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.PROFILE_SYSTEM), ("human", prompts.PROFILE_HUMAN)])
    return resilient(lambda llm: prompt | llm.with_structured_output(Profile), allow_local=False)


def rerank_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.RERANK_SYSTEM), ("human", prompts.RERANK_HUMAN)])
    return resilient(lambda llm: prompt | llm.with_structured_output(Judgements), allow_local=False)
