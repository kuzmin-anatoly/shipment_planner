from app.core.language import response_language_for


def test_detects_russian() -> None:
    assert response_language_for("Что входит в MVP?") == "Russian"


def test_defaults_to_user_language() -> None:
    assert response_language_for("What is in the MVP?") == "same language as the user"
