from app.agents.base import BaseAgent
from app.core.language import response_language_for
from app.schemas import AgentResponse, ChatRequest
from app.services.dev_tools import dev_tools_service


class DevAgent(BaseAgent):
    name = "dev"

    async def run(self, request: ChatRequest) -> AgentResponse:
        context = dev_tools_service.describe_capabilities()
        language = response_language_for(request.message)
        answer = await self.llm.chat(
            system_prompt=(
                "You are a Dev Agent for GitLab, Jira, Confluence, CI/CD, and engineering workflows. "
                "Answer in the same language as the user. "
                "Use only connected tool capabilities. If integrations are missing, describe the next setup step."
            ),
            user_prompt=(
                f"Required response language: {language}\n"
                f"Question: {request.message}\n\nDev tools context:\n{context}"
            ),
        )
        return AgentResponse(answer=answer, sources=["dev-tools-service"])
