from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


class LLMClient:
    """
    Unified LLM client supporting OpenAI Responses API, Gemini REST API,
    and OpenRouter (Chat Completions format) with multi-key rotation.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        extra_api_keys: list[str] | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        # Build key pool: primary key + any extras, deduped, non-empty
        pool = [k.strip() for k in ([api_key] + (extra_api_keys or [])) if k.strip()]
        self._key_pool: list[str] = list(dict.fromkeys(pool))  # preserve order, dedupe
        self._key_index = 0

    @property
    def api_key(self) -> str:
        """Current active key."""
        if not self._key_pool:
            return ""
        return self._key_pool[self._key_index % len(self._key_pool)]

    def _rotate_key(self) -> bool:
        """Advance to the next key. Returns True if a new key is available."""
        if len(self._key_pool) <= 1:
            return False
        self._key_index = (self._key_index + 1) % len(self._key_pool)
        return True

    def complete_json(self, instructions: str, prompt: str) -> dict[str, object]:
        if not self._key_pool:
            raise RuntimeError("LLM provider is not configured — no API key supplied")

        last_error: Exception | None = None
        # Try every key in the pool before giving up
        for attempt in range(len(self._key_pool)):
            try:
                return self._complete_once(instructions=instructions, prompt=prompt)
            except RuntimeError as exc:
                last_error = exc
                detail = str(exc).lower()
                _rotatable = [
                    "429", "rate limit", "quota", "resource_exhausted",
                    "too many requests", "billing", "insufficient_quota",
                ]
                if any(token in detail for token in _rotatable):
                    if self._rotate_key():
                        continue  # try next key
                break  # non-rotatable error, fail fast

        raise last_error or RuntimeError("All LLM keys exhausted")

    def _complete_once(self, instructions: str, prompt: str) -> dict[str, object]:
        if self.provider == "openai":
            body = self._openai_complete(instructions=instructions, prompt=prompt)
            text = self._extract_openai_text(body)
        elif self.provider == "gemini":
            body = self._gemini_complete(instructions=instructions, prompt=prompt)
            text = self._extract_gemini_text(body)
        elif self.provider == "openrouter":
            body = self._openrouter_complete(instructions=instructions, prompt=prompt)
            text = self._extract_chat_text(body)
        elif self.provider == "mistral":
            body = self._mistral_complete(instructions=instructions, prompt=prompt)
            text = self._extract_chat_text(body)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

        text = text.strip()
        if not text:
            raise RuntimeError("LLM returned empty content")
        return self._parse_json_lenient(text)

    # ------------------------------------------------------------------ #
    #  Provider implementations
    # ------------------------------------------------------------------ #

    def _openrouter_complete(self, instructions: str, prompt: str) -> dict[str, object]:
        """OpenRouter uses the OpenAI Chat Completions format."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Research RAG",
            },
        )
        return self._http_post(request, label="OpenRouter")

    def _mistral_complete(self, instructions: str, prompt: str) -> dict[str, object]:
        """Mistral uses the standard OpenAI Chat Completions format."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        return self._http_post(request, label="Mistral")

    def _openai_complete(self, instructions: str, prompt: str) -> dict[str, object]:
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": prompt,
            "temperature": 0.1,
            "max_output_tokens": 1500,
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/responses",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        return self._http_post(request, label="OpenAI")

    def _gemini_complete(self, instructions: str, prompt: str) -> dict[str, object]:
        model_name = self.model.removeprefix("models/")
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Return ONLY valid JSON with no markdown fences.\n\n"
                                f"System instructions:\n{instructions}\n\n"
                                f"User prompt:\n{prompt}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
                "maxOutputTokens": 1500,
            },
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        return self._http_post(request, label="Gemini")

    def _http_post(self, request: urllib.request.Request, label: str) -> dict[str, object]:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{label} request failed [{exc.code}]: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{label} request could not be completed: {exc}") from exc

    # ------------------------------------------------------------------ #
    #  Response extractors
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_chat_text(body: dict[str, object]) -> str:
        """Extract content from OpenAI-compatible Chat Completions response."""
        choices = body.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message", {})
        if not isinstance(message, dict):
            return ""
        content = message.get("content", "")
        return str(content) if content else ""

    @staticmethod
    def _extract_openai_text(body: dict[str, object]) -> str:
        output_text = body.get("output_text")
        if isinstance(output_text, str):
            return output_text
        parts: list[str] = []
        for output in body.get("output", []):
            if not isinstance(output, dict):
                continue
            for content in output.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif isinstance(text, dict) and isinstance(text.get("value"), str):
                    parts.append(text["value"])
        return "\n".join(parts)

    @staticmethod
    def _extract_gemini_text(body: dict[str, object]) -> str:
        candidates = body.get("candidates", [])
        if not isinstance(candidates, list):
            return ""
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content", {})
            if not isinstance(content, dict):
                continue
            parts = content.get("parts", [])
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text
        return ""

    # ------------------------------------------------------------------ #
    #  JSON parsing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_json_lenient(text: str) -> dict[str, object]:
        raw = text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Strip markdown fences
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r"```$", "", raw).strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

        # Extract first {...} block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise RuntimeError("LLM returned non-JSON content")
