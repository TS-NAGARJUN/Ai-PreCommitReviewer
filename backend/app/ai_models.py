import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=False)

logger = logging.getLogger("ai_models")

class AIModelError(Exception):
    pass


def _extract_json(raw_text: str) -> str:
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("Empty response text")

    # Attempt to extract the first JSON object or array from the response.
    start = raw_text.find("{")
    if start == -1:
        start = raw_text.find("[")
        if start == -1:
            raise ValueError("No JSON object or array found")
        opening = "["
        closing = "]"
    else:
        opening = "{"
        closing = "}"

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(raw_text[start:], start):
        if char == "\\" and not escape:
            escape = True
            continue

        if char == '"' and not escape:
            in_string = not in_string

        if not in_string:
            if char == opening:
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0:
                    return raw_text[start:index + 1]

        escape = False

    raise ValueError("Could not extract balanced JSON payload")


def _parse_json(raw_text: str) -> Any:
    payload = _extract_json(raw_text)
    return json.loads(payload)


def _normalize_severity(value: Optional[str]) -> str:
    if not value:
        return "low"
    normalized = value.strip().lower()
    if normalized in {"high", "critical", "error"}:
        return "high"
    if normalized in {"medium", "moderate", "warn", "warning"}:
        return "medium"
    return "low"


def _normalize_category(value: Optional[str]) -> str:
    if not value:
        return "other"
    normalized = value.strip().lower()
    if "security" in normalized:
        return "security"
    if "bug" in normalized or "error" in normalized or "crash" in normalized:
        return "bug"
    if "style" in normalized or "format" in normalized or "lint" in normalized:
        return "style"
    if "performance" in normalized or "efficiency" in normalized:
        return "performance"
    if "docs" in normalized or "documentation" in normalized:
        return "documentation"
    return "other"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class GeminiClient:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def review(self, prompt: str) -> str:
        if not self.api_key:
            raise AIModelError("Gemini API key is missing")

        url = f"{self.BASE_URL}/{self.MODEL_NAME}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code >= 400:
                message = response.text or response.reason_phrase
                raise AIModelError(f"Gemini API error {response.status_code}: {message}")
            body = response.json()
            return self._extract_text(body)

    @staticmethod
    def _extract_text(body: Any) -> str:
        if isinstance(body, dict):
            candidates = body.get("candidates") or []
            if candidates:
                first_candidate = candidates[0]
                if isinstance(first_candidate, dict):
                    content = first_candidate.get("content") or {}
                    parts = content.get("parts") or []
                    if parts:
                        texts = []
                        for part in parts:
                            if isinstance(part, dict) and isinstance(part.get("text"), str):
                                texts.append(part["text"])
                        if texts:
                            return "\n".join(texts)
            if "text" in body:
                return str(body["text"])
            if "output_text" in body:
                return str(body["output_text"])
        return str(body)


class GroqClient:
    BASE_URL = "https://api.groq.com"
    DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def __init__(self, api_key: str, model_name: Optional[str] = None):
        self.api_key = (api_key or "").strip()
        self.model_name = (model_name or os.getenv("GROQ_MODEL") or self.DEFAULT_MODEL).strip()

    async def review(self, prompt: str) -> str:
        if not self.api_key:
            raise AIModelError("Groq API key is missing")

        url = f"{self.BASE_URL}/openai/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start_time = asyncio.get_running_loop().time()
        logger.debug("Groq request URL=%s model=%s", url, self.model_name)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            elapsed = asyncio.get_running_loop().time() - start_time
            logger.warning("Groq request timed out after %.2fs", elapsed)
            raise AIModelError(f"Groq request timed out after {elapsed:.2f}s") from exc
        except httpx.ConnectError as exc:
            logger.warning("Groq connection failed: %s", exc)
            raise AIModelError(f"Groq network error: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            body = exc.response.text if exc.response is not None else ""
            logger.warning("Groq request failed with status %s: %s", status_code, body)
            if status_code == 401:
                raise AIModelError("Groq 401 Unauthorized: invalid or missing API key") from exc
            if status_code == 403:
                raise AIModelError("Groq 403 Forbidden: access denied") from exc
            if status_code == 404:
                raise AIModelError(f"Groq 404 Not Found: invalid endpoint or model '{self.model_name}'") from exc
            if status_code == 429:
                raise AIModelError("Groq 429 Rate limit exceeded") from exc
            if status_code >= 500:
                raise AIModelError(f"Groq 500+ server error: {body}") from exc
            raise AIModelError(f"Groq API error {status_code}: {body}") from exc
        except httpx.RequestError as exc:
            logger.warning("Groq request failed: %s", exc)
            raise AIModelError(f"Groq request failed: {exc}") from exc

        elapsed = asyncio.get_running_loop().time() - start_time
        logger.debug("Groq response status=%s duration=%.2fs body=%s", response.status_code, elapsed, response.text)

        if response.status_code == 401:
            raise AIModelError("Groq 401 Unauthorized: invalid or missing API key")
        if response.status_code == 403:
            raise AIModelError("Groq 403 Forbidden: access denied")
        if response.status_code == 404:
            raise AIModelError(f"Groq 404 Not Found: invalid endpoint or model '{self.model_name}'")
        if response.status_code == 429:
            raise AIModelError("Groq 429 Rate limit exceeded")
        if response.status_code >= 500:
            raise AIModelError(f"Groq 500+ server error: {response.text}")
        if response.status_code >= 400:
            raise AIModelError(f"Groq API error {response.status_code}: {response.text}")

        try:
            body = response.json()
        except ValueError as exc:
            raise AIModelError("Groq response was not valid JSON") from exc

        return self._extract_text(body)

    @staticmethod
    def _extract_text(body: Any) -> str:
        if not isinstance(body, dict):
            raise AIModelError("Groq response was malformed")

        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AIModelError("Groq response was malformed: empty choices array")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise AIModelError("Groq response was malformed")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise AIModelError("Groq response was malformed")

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "\n".join(parts)

        raise AIModelError("Groq response was malformed: missing message content")


class HuggingFaceClient:
    BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, token: str, model_name: str = "Qwen2.5-Coder-7B-Instruct"):
        self.token = token
        self.model_name = model_name

    async def review(self, prompt: str) -> str:
        if not self.token:
            raise AIModelError("HuggingFace token is missing")

        url = f"{self.BASE_URL}/{self.model_name}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.2,
                "return_full_text": False,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code >= 400:
                message = response.text or response.reason_phrase
                raise AIModelError(f"HuggingFace API error {response.status_code}: {message}")
            body = response.json()
            return self._extract_text(body)

    @staticmethod
    def _extract_text(body: Any) -> str:
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, dict) and "generated_text" in first:
                return str(first["generated_text"])
            return str(first)
        if isinstance(body, dict):
            if "generated_text" in body:
                return str(body["generated_text"])
            if "text" in body:
                return str(body["text"])
        return str(body)


class AIReviewService:
    def __init__(self, groq_key: str, hf_token: str, gemini_key: str = ""):
        self.groq_key = groq_key
        self.hf_token = hf_token
        self.gemini_key = gemini_key
        self.gemini = GeminiClient(gemini_key)
        self.groq = GroqClient(groq_key)
        self.hf = HuggingFaceClient(hf_token)

    async def check_models(self) -> Dict[str, Any]:
        prompts = {
            "gemini": "You are the Gemini model. Reply with a short confirmation that you are available and identify yourself as Gemini.",
            "groq": "You are the Groq model. Reply with a short confirmation that you are available and identify yourself as Groq.",
            "huggingface": "You are the Hugging Face model. Reply with a short confirmation that you are available and identify yourself as Hugging Face.",
        }

        results: Dict[str, Any] = {}
        for name, prompt in prompts.items():
            try:
                if name == "gemini":
                    response_text = await self.gemini.review(prompt)
                elif name == "groq":
                    response_text = await self.groq.review(prompt)
                else:
                    response_text = await self.hf.review(prompt)

                results[name] = {
                    "status": "ok",
                    "response": _clean_string(response_text) or "ready",
                }
            except Exception as exc:
                logger.warning("Model check failed for %s: %s", name, exc, exc_info=True)
                error_text = str(exc)
                if not error_text:
                    error_text = repr(exc)
                results[name] = {
                    "status": "error",
                    "response": error_text,
                }

        overall_status = "ok"
        if any(item.get("status") != "ok" for item in results.values()):
            overall_status = "partial_error"

        return {
            "status": overall_status,
            "models": results,
        }

    async def analyze(self, repo_path: str, branch: str, staged_diff: str, changed_files: List[str]) -> Dict[str, Any]:
        prompt = self._build_prompt(repo_path, branch, staged_diff, changed_files)

        try:
            review_text = await self.gemini.review(prompt)
            logger.info("Gemini review completed")
        except Exception as gemini_error:
            logger.warning("Gemini review failed: %s", gemini_error)
            try:
                review_text = await self.groq.review(prompt)
                logger.info("Groq review completed")
            except Exception as groq_error:
                logger.warning("Groq review failed: %s", groq_error)
                try:
                    review_text = await self.hf.review(prompt)
                    logger.info("HuggingFace review completed")
                except Exception as hf_error:
                    logger.error("HuggingFace review failed: %s", hf_error)
                    return {
                        "riskScore": 0.0,
                        "summary": "AI review unavailable due to model API access failure. Check GEMINI_API_KEY, GROQ_API_KEY, or HF_TOKEN.",
                        "commitMsg": "AI review could not run because the configured model APIs could not be reached.",
                        "findings": [],
                    }

        return self._build_response(review_text)

    @staticmethod
    def _build_prompt(repo_path: str, branch: str, staged_diff: str, changed_files: List[str]) -> str:
        changed_files_text = "\n".join(changed_files) if changed_files else "(no changed files detected)"
        return (
            "You are an expert code reviewer. Analyze the staged Git diff and changed files for security, reliability, maintainability, style, and bug risk. "
            "Return only valid JSON with the following schema:\n"
            "{\n"
            "  \"riskScore\": number,\n"
            "  \"summary\": string,\n"
            "  \"commitMsg\": string,\n"
            "  \"findings\": [\n"
            "    {\n"
            "      \"file\": string,\n"
            "      \"line\": number|null,\n"
            "      \"severity\": \"high\"|\"medium\"|\"low\",\n"
            "      \"category\": string,\n"
            "      \"message\": string\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "If there are no problems, return riskScore 0.0, findings: [], summary: \"No issues found in staged changes.\", and a helpful commitMsg.\n"
            "Do not include any markdown or explanations outside the JSON object.\n"
            f"Repository: {repo_path}\n"
            f"Branch: {branch}\n"
            f"Changed files:\n{changed_files_text}\n"
            f"Staged diff:\n{staged_diff}\n"
        )

    def _build_response(self, raw_text: str) -> Dict[str, Any]:
        try:
            parsed = _parse_json(raw_text)
        except Exception as parse_error:
            logger.warning("Failed to parse model JSON output: %s", parse_error)
            return {
                "riskScore": 0.0,
                "summary": "Unable to parse AI model response.",
                "commitMsg": "Review failed: invalid model response.",
                "findings": [],
            }

        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
            return {
                "riskScore": _safe_float(parsed.get("riskScore", 0.0)),
                "summary": _clean_string(parsed.get("summary", "No summary provided.")),
                "commitMsg": _clean_string(parsed.get("commitMsg", "AI review complete.")),
                "findings": [
                    {
                        "file": _clean_string(item.get("file", "unknown")),
                        "line": item.get("line") if isinstance(item.get("line"), int) else None,
                        "severity": _normalize_severity(item.get("severity")),
                        "category": _normalize_category(item.get("category")),
                        "message": _clean_string(item.get("message", "")),
                    }
                    for item in findings
                    if isinstance(item, dict)
                ],
            }

        return {
            "riskScore": 0.0,
            "summary": "AI response was not a JSON object.",
            "commitMsg": "AI review failed to return structured output.",
            "findings": [],
        }


def get_review_service() -> AIReviewService:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    hf_token = os.getenv("HF_TOKEN", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    return AIReviewService(groq_key, hf_token, gemini_key)
