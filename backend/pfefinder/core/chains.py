"""Chaînes LCEL : extraction de profil, justification du matching, extraction d'un PFE book."""
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from pfefinder.core import prompts
from pfefinder.core.llm import get_llm
from pfefinder.core.schemas import ExtractedBook, Profile


class SubjectReason(BaseModel):
    id: int
    raison: str = Field(description="Une phrase expliquant pourquoi ce sujet correspond au profil")


class Reasons(BaseModel):
    raisons: list[SubjectReason] = Field(default_factory=list)


def profile_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.PROFILE_SYSTEM), ("human", prompts.PROFILE_HUMAN)])
    return prompt | get_llm().with_structured_output(Profile)


def reason_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.REASON_SYSTEM), ("human", prompts.REASON_HUMAN)])
    return prompt | get_llm().with_structured_output(Reasons)


def extract_chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.EXTRACT_SYSTEM), ("human", prompts.EXTRACT_HUMAN)])
    return prompt | get_llm().with_structured_output(ExtractedBook)
