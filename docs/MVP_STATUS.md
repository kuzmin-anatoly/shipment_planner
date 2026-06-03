# MVP AI Platform Status

Last updated: 2026-05-04

## C4 Context

```mermaid
C4Context
  title AI Platform MVP - Current Local Context

  Person(user, "Internal User", "Tests agents through Web Chat and IDE workflows")

  System_Boundary(platform, "AI Platform MVP - Local Laptop") {
    System(web, "Web Chat", "Static UI served by FastAPI")
    System(api, "FastAPI Backend", "API, router, agent runtime")
    System(agents, "MVP Agents", "Analytics, Knowledge, Dev")
    System(llm, "Ollama", "Local open-source LLM runtime")
    System(rag, "Simple RAG Service", "In-memory documents for current sandbox")
  }

  System_Ext(mssql, "MS SQL DWH", "Planned read-only analytics source")
  System_Ext(confluence, "Confluence", "Planned knowledge source")
  System_Ext(jira, "Jira", "Planned knowledge/dev source")
  System_Ext(gitlab, "GitLab", "Planned dev source")

  Rel(user, web, "Uses", "Browser")
  Rel(web, api, "Calls", "HTTP /api/chat")
  Rel(api, agents, "Routes requests to", "Simple intent router")
  Rel(agents, llm, "Generates answers with", "Ollama API")
  Rel(agents, rag, "Retrieves context from", "Python service")

  Rel(agents, mssql, "Not connected yet", "Planned SQL service")
  Rel(rag, confluence, "Not connected yet", "Planned ingestion")
  Rel(rag, jira, "Not connected yet", "Planned ingestion")
  Rel(agents, gitlab, "Not connected yet", "Planned API/MCP adapter")
```

## C4 Container

```mermaid
C4Container
  title AI Platform MVP - Current Containers/Runtime

  Person(user, "Internal User")

  Container_Boundary(local, "Local Laptop Runtime") {
    Container(web, "Web Chat", "HTML/CSS/JS", "Local browser chat UI")
    Container(api, "FastAPI App", "Python + FastAPI", "Routes requests and runs agents")
    Container(router, "Intent Router", "Python", "Selects analytics, knowledge, or dev agent")
    Container(analytics, "Analytics Agent", "Python", "SQL/DWH assistant shell")
    Container(knowledge, "Knowledge Agent", "Python", "RAG assistant shell")
    Container(dev, "Dev Agent", "Python", "GitLab/Jira/Confluence assistant shell")
    Container(ollama, "Ollama", "Local service", "Runs qwen2.5:3b")
    ContainerDb(rag, "Simple RAG Store", "In-memory Python list", "Seed architecture notes")
  }

  ContainerDb(pg, "PostgreSQL + pgvector", "Docker planned", "State and vector store")
  Container(redis, "Redis", "Docker planned", "Queue/cache/rate limit foundation")
  Container(litellm, "LiteLLM", "Docker planned", "Future model gateway")

  Rel(user, web, "Uses")
  Rel(web, api, "POST /api/chat")
  Rel(api, router, "Classifies intent")
  Rel(router, analytics, "analytics intent")
  Rel(router, knowledge, "default/knowledge intent")
  Rel(router, dev, "dev intent")
  Rel(analytics, ollama, "LLM calls")
  Rel(knowledge, ollama, "LLM calls")
  Rel(dev, ollama, "LLM calls")
  Rel(knowledge, rag, "Searches context")

  Rel(api, pg, "Not active yet")
  Rel(api, redis, "Not active yet")
  Rel(api, litellm, "Not active yet")
```

## Current Component State

| Component | State | Current details |
| --- | --- | --- |
| Web Chat | Active | `http://127.0.0.1:8000/` |
| FastAPI backend | Active | `http://127.0.0.1:8000/api` |
| Intent Router | Active | Keyword-based routing |
| Analytics Agent | Active shell | No MS SQL connection yet |
| Knowledge Agent | Active shell | Uses simple in-memory RAG notes |
| Dev Agent | Active shell | No GitLab/Jira/Confluence API connection yet |
| Ollama | Active | Local runtime at `http://127.0.0.1:11434` |
| Current chat LLM | Active | `qwen2.5:3b`, model id `357c53fb659c`, size `1.9 GB` |
| Additional local LLM | Available | `llama3.2:3b`, model id `a80c4f17acd5`, size `2.0 GB` |
| LiteLLM | Planned | Compose config exists, not active locally |
| PostgreSQL + pgvector | Planned | Compose/schema exists, not active locally |
| Redis | Planned | Compose config exists, not active locally |
| Docker Compose deployment | Prepared | Docker CLI not available in current PATH |

## Data Access State

| Source | State | Notes |
| --- | --- | --- |
| MS SQL DWH | Not connected | Need read-only DSN/service account and allowlisted queries/views |
| Confluence | Not connected | Need base URL/token and ingestion job |
| Jira | Not connected | Need base URL/token and ingestion/dev adapter |
| GitLab | Not connected | Need base URL/token and project access |
| Local architecture notes | Active | Seeded in `SimpleRagService` |

## Next MVP Work

1. Replace in-memory RAG with persistent `PostgreSQL + pgvector`.
2. Add ingestion pipeline for local files first, then Confluence/Jira.
3. Add MS SQL read-only query service with allowlist, row limits, and audit log.
4. Add GitLab/Jira adapter for Dev Agent.
5. Add LiteLLM as the model gateway once Docker/local server deployment is ready.
6. Add minimal observability: request id, agent id, selected model, latency, tool calls.
