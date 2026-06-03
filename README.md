# AI Platform MVP

Локальный MVP мультиагентской AI-платформы на `Python + FastAPI`.

## Что внутри

- `FastAPI` API и простой Web Chat.
- `LiteLLM` как единый gateway к локальным LLM.
- `Ollama` с моделью `llama3.1:8b` для offline-first режима.
- `PostgreSQL + pgvector` как стартовый state/RAG слой.
- `Redis` под будущие очереди, rate limits и фоновые задачи.
- 3 MVP-агента: `Analytics`, `Knowledge`, `Dev`.
- Simple Intent Router, который выбирает агента по тексту запроса.

## Почему pgvector для MVP

Для первой проверки проще держать state и RAG в одном `PostgreSQL`. Когда платформа дойдет до production-ветки, Knowledge storage можно вынести в `Qdrant`, сохранив контракт `rag_service`.

## Быстрый старт локально

### Вариант A: Python без Docker

Подходит для первой проверки API и Web Chat. По умолчанию backend ходит напрямую в локальный Ollama API: `http://localhost:11434`.

Установите Ollama, затем скачайте модель:

```powershell
ollama pull qwen2.5:3b
```

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Откройте:

```text
http://127.0.0.1:8000
```

Для OpenCode-интеграции Ollama:

```powershell
ollama launch opencode --model qwen2.5:3b
```

### Вариант B: Docker Compose

1. Создайте `.env` из примера:

```powershell
Copy-Item .env.example .env
```

2. Поднимите сервисы:

```powershell
docker compose up --build
```

3. Скачайте локальную модель в контейнер Ollama:

```powershell
docker exec -it ai-platform-ollama ollama pull llama3.1:8b
```

4. Откройте Web Chat:

```text
http://localhost:8000
```

API healthcheck:

```text
http://localhost:8000/api/health
```

## Проверка без модели

Если модель еще не скачана, API и router все равно работают. Ответ агента будет содержать диагностическое сообщение `Ollama is not available yet`.

## Примеры запросов

- `Что входит в MVP платформы?`
- `Какие компоненты нужны для production direction?`
- `Сделай SQL отчет по продажам за месяц`
- `Проверь задачи Jira и статус GitLab pipeline`

## Интеграции

Пока интеграции работают в sandbox-режиме и описывают, что нужно настроить.

Для MS SQL:

```env
MSSQL_DSN=
```

Для Confluence/Jira/GitLab:

```env
CONFLUENCE_BASE_URL=
CONFLUENCE_API_TOKEN=
JIRA_BASE_URL=
JIRA_API_TOKEN=
GITLAB_BASE_URL=
GITLAB_TOKEN=
```

## Production-вектор

Этот MVP уже разложен так, чтобы дальше добавить:

- AD/Entra auth.
- Policy layer.
- Audit и rate limit.
- Langfuse observability.
- Evals.
- HITL approvals.
- Airflow jobs для ingestion, embeddings и evals.
- MCP adapters для GitLab, Atlassian, Fabric.
- Qdrant вместо pgvector, если RAG слой начнет расти отдельно от Postgres.

Подробнее: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Текущий статус инфраструктуры и компонентов: [docs/MVP_STATUS.md](docs/MVP_STATUS.md).
