from dataclasses import dataclass

from app.schemas import KnowledgeDocument


@dataclass(frozen=True)
class RetrievedDocument:
    source: str
    title: str
    content: str
    score: int


class SimpleRagService:
    def __init__(self) -> None:
        self._documents: list[RetrievedDocument] = [
            RetrievedDocument(
                source="architecture-note",
                title="AI Platform MVP",
                content=(
                    "The MVP uses FastAPI, LangGraph-ready orchestration, LiteLLM, Ollama, "
                    "PostgreSQL with pgvector, Redis, and three agents: Analytics, Knowledge, Dev."
                ),
                score=0,
            ),
            RetrievedDocument(
                source="architecture-note",
                title="Production Direction",
                content=(
                    "Production should add AD/Entra auth, policy layer, audit, rate limits, "
                    "Langfuse observability, evals, HITL approvals, Airflow jobs, and stronger MCP adapters."
                ),
                score=0,
            ),
        ]

    def ingest_texts(self, source: str, documents: list[KnowledgeDocument]) -> int:
        for document in documents:
            self._documents.append(
                RetrievedDocument(
                    source=source,
                    title=document.title,
                    content=document.content,
                    score=0,
                )
            )
        return len(documents)

    def search(self, query: str, limit: int = 4) -> list[RetrievedDocument]:
        query_terms = {term.strip(".,:;!?()[]{}").lower() for term in query.split()}
        ranked = []
        for document in self._documents:
            haystack = f"{document.title} {document.content}".lower()
            score = sum(1 for term in query_terms if term and term in haystack)
            ranked.append(
                RetrievedDocument(
                    source=document.source,
                    title=document.title,
                    content=document.content,
                    score=score,
                )
            )
        ranked.sort(key=lambda document: document.score, reverse=True)
        return [document for document in ranked[:limit] if document.score > 0] or ranked[:limit]


rag_service = SimpleRagService()
