from abc import ABC, abstractmethod

from app.core.llm import LLMClient
from app.schemas import AgentResponse, ChatRequest


class BaseAgent(ABC):
    name: str

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    @abstractmethod
    async def run(self, request: ChatRequest) -> AgentResponse:
        raise NotImplementedError
