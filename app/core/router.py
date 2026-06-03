from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    intent: str
    agent: str


class IntentRouter:
    analytics_keywords = {
        "sql",
        "dwh",
        "dashboard",
        "metric",
        "metrics",
        "report",
        "sales",
        "revenue",
        "query",
        "analytics",
        "аналит",
        "отчет",
        "отчёт",
        "метрик",
        "продаж",
        "выруч",
    }
    dev_keywords = {
        "gitlab",
        "jira",
        "merge",
        "pull request",
        "issue",
        "commit",
        "code",
        "repo",
        "pipeline",
        "dev",
        "задач",
        "репозитор",
        "код",
        "пайплайн",
    }

    def route(self, message: str) -> RouteDecision:
        normalized = message.lower()
        if any(keyword in normalized for keyword in self.analytics_keywords):
            return RouteDecision(intent="analytics", agent="analytics")
        if any(keyword in normalized for keyword in self.dev_keywords):
            return RouteDecision(intent="dev", agent="dev")
        return RouteDecision(intent="knowledge", agent="knowledge")
