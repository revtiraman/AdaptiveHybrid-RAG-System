from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


class LLMClient:
    def __init__(self, provider: str, model: str, api_key: str, base_url: str, timeout_seconds: float) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete_json(self, instructions: str, prompt: str) -> dict[str, object]:
        if not self.api_key:
            raise RuntimeError("LLM provider is not configured")

        if self.provider == "openai":
            body = self._openai_complete(instructions=instructions, prompt=prompt)
            text = self._extract_openai_text(body)
        elif self.provider == "gemini":
            body = self._gemini_complete(instructions=instructions, prompt=prompt)
            text = self._extract_gemini_text(body)
        else:
            raise RuntimeError(f"Unsupported LLM provider: {self.provider}")

        text = text.strip()
        if not text:
            raise RuntimeError("LLM returned empty content")
        return self._parse_json_lenient(text)

    def _openai_complete(self, instructions: str, prompt: str) -> dict[str, object]:

        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": prompt,
            "temperature": 0.1,
            "max_output_tokens": 900,
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

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request could not be completed: {exc}") from exc

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
            },
        }

        request = urllib.request.Request(
            url=f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request could not be completed: {exc}") from exc

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

    @staticmethod
    def _parse_json_lenient(text: str) -> dict[str, object]:
        raw = text.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Handle markdown fenced JSON responses.
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r"```$", "", raw).strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise RuntimeError("LLM returned non-JSON content")
