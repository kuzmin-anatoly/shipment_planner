# AI Platform MVP Architecture

## MVP deployment choice

Start locally with direct Python execution and keep Docker Compose as the first deployment target.

Current local mode:

- `FastAPI` runs on the laptop at `http://127.0.0.1:8000`.
- LLM access goes through an OpenAI-compatible client.
- If LiteLLM/Ollama is offline, agents return a diagnostic fallback.

First container mode:

- `api` runs FastAPI.
- `litellm` exposes the LLM gateway.
- `ollama` hosts the local open-source model.
- `postgres` stores platform state and RAG data.
- `redis` is ready for async jobs, cache, and limits.

## Core contracts

The platform is split into simple contracts that can survive production hardening:

- Channels call only the `FastAPI` API.
- The API calls an intent router.
- The router selects one agent.
- Agents call tool services, not enterprise systems directly.
- All LLM calls go through `LLMClient`, backed by LiteLLM.
- RAG calls go through `rag_service`, currently simple in-memory search with pgvector schema prepared.

## MVP agents

- `Analytics Agent`: BI, DWH, SQL, metrics, reporting.
- `Knowledge Agent`: RAG over architecture notes now, Confluence/Jira later.
- `Dev Agent`: GitLab/Jira/Confluence engineering workflow assistant.

## Data integration plan

MS SQL:

- Use read-only service account.
- Expose allowlisted views or stored procedures.
- Add query validation, row limits, query logging, and result truncation before production.

Confluence and Jira:

- Start with REST API ingestion jobs.
- Store page/task chunks in `rag_documents`.
- Add embeddings once the ingestion path is stable.

GitLab:

- Start with REST API for projects, issues, merge requests, pipelines, and repository metadata.
- Later replace or complement with GitLab MCP.

## Vector layer decision

Use `PostgreSQL + pgvector` for MVP.

Reasons:

- One database to operate locally.
- Enough for early RAG validation.
- Easy to version schema and seed data.
- Can be replaced with `Qdrant` later behind the same `rag_service` contract.

Move to `Qdrant` when:

- RAG corpus grows significantly.
- Retrieval needs dedicated scaling.
- Hybrid/vector search tuning becomes a separate platform concern.
- Ingestion and search workloads start competing with platform state.

## Production direction

Keep these as architecture expansion points:

- `api-gateway`: AD/Entra auth, policy, audit, rate limits.
- `orchestrator`: LangGraph state graph, memory, HITL approvals.
- `agent-runtime`: isolated agent execution and tool permissions.
- `tool-services`: SQL, RAG, GitLab, Jira, Confluence, Fabric, 1C, WMS.
- `platform-services`: LiteLLM, PostgreSQL state, Redis, Langfuse, evals.
- `batch`: Airflow or another scheduler for ingestion, embeddings, and eval jobs.
