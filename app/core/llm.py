import httpx

from app.core.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower()
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.headers = {"Authorization": f"Bearer {settings.llm_api_key}"} if settings.llm_api_key else {}

    async def health(self) -> dict:
        if self.provider == "ollama":
            return await self._ollama_health()

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/models", headers=self.headers)
                return {"available": response.is_success, "status_code": response.status_code}
        except httpx.HTTPError:
            return {"available": False, "error": "LLM health check failed."}

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "ollama":
            return await self._ollama_chat(system_prompt, user_prompt)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            if settings.llm_offline_fallback:
                return "Local LLM is not available yet."
            raise

    async def _ollama_health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                return {
                    "available": True,
                    "provider": "ollama",
                    "model": self.model,
                    "model_loaded": self.model in model_names,
                }
        except httpx.HTTPError:
            return {"available": False, "provider": "ollama", "error": "Ollama health check failed."}

    async def _ollama_chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception:
            if settings.llm_offline_fallback:
                return "Ollama is not available yet, or the model is not downloaded."
            raise
