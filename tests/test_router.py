from app.core.router import IntentRouter


def test_routes_analytics_questions() -> None:
    router = IntentRouter()
    decision = router.route("Сделай SQL отчет по продажам")
    assert decision.agent == "analytics"


def test_routes_dev_questions() -> None:
    router = IntentRouter()
    decision = router.route("Проверь GitLab pipeline и Jira issue")
    assert decision.agent == "dev"


def test_routes_knowledge_by_default() -> None:
    router = IntentRouter()
    decision = router.route("Что входит в MVP платформы?")
    assert decision.agent == "knowledge"
