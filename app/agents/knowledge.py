from app.agents.base import BaseAgent
from app.core.language import response_language_for
from app.schemas import AgentResponse, ChatRequest
from app.services.rag import rag_service


class KnowledgeAgent(BaseAgent):
    name = "knowledge"

    async def run(self, request: ChatRequest) -> AgentResponse:
        documents = rag_service.search(request.message, limit=4)
        language = response_language_for(request.message)
        context = "\n\n".join(
            f"[{index}] {document.title}\n{document.content}"
            for index, document in enumerate(documents, start=1)
        )
        answer = await self.llm.chat(
            system_prompt=(
                "You are a Knowledge Agent. Answer using the provided context first. "
                "Answer in the same language as the user. "
                "When context is present, summarize it directly and cite only the listed sources. "
                "If the context is insufficient, say what source should be connected next."
            ),
            user_prompt=(
                f"Required response language: {language}\n"
                f"Question: {request.message}\n\nContext:\n{context or 'No indexed context yet.'}"
            ),
        )
        return AgentResponse(answer=answer, sources=[document.source for document in documents])
