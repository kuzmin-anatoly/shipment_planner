from app.agents.base import BaseAgent
from app.core.language import response_language_for
from app.schemas import AgentResponse, ChatRequest


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    async def run(self, request: ChatRequest) -> AgentResponse:
        language = response_language_for(request.message)
        answer = await self.llm.chat(
            system_prompt=(
                "You are an Analytics Agent for a corporate AI platform MVP. "
                "Help with BI, SQL, DWH, metrics, and report questions. "
                "Answer in the same language as the user. "
                "Do not invent database values; explain limits clearly when external data is unavailable."
            ),
            user_prompt=f"Required response language: {language}\nQuestion: {request.message}",
        )
        return AgentResponse(answer=answer, sources=["analytics"])
