from app.agents.base import BaseAgent
from app.core.language import response_language_for
from app.schemas import AgentResponse, ChatRequest
from app.services.sql import sql_service


class AnalyticsAgent(BaseAgent):
    name = "analytics"

    async def run(self, request: ChatRequest) -> AgentResponse:
        sql_context = sql_service.describe_capabilities()
        language = response_language_for(request.message)
        answer = await self.llm.chat(
            system_prompt=(
                "You are an Analytics Agent for a corporate AI platform MVP. "
                "Help with BI, SQL, DWH, metrics, and report questions. "
                "Answer in the same language as the user. "
                "Never invent database values. If data access is not configured, explain what is needed."
            ),
            user_prompt=(
                f"Required response language: {language}\n"
                f"Question: {request.message}\n\nSQL service context:\n{sql_context}"
            ),
        )
        return AgentResponse(answer=answer, sources=["sql-query-service"])
