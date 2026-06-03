def response_language_for(text: str) -> str:
    has_cyrillic = any("\u0400" <= character <= "\u04ff" for character in text)
    return "Russian" if has_cyrillic else "same language as the user"
