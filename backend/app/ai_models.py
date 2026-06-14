import json
import os
import re
import logging
from typing import Any, Dict, List, Optional

import httpx

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


class GroqClient:
    BASE_URL = "https://api.groq.com/v1/models"
    MODEL_NAME = "llama-3.1-70b"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def review(self, prompt: str) -> str:
        if not self.api_key:
            raise AIModelError("Groq API key is missing")

        payloads = [
            {"input": prompt, "max_output_tokens": 1024, "temperature": 0.2},
            {"prompt": prompt, "max_output_tokens": 1024, "temperature": 0.2},
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            for payload in payloads:
                for endpoint in ("infer", "generate"):
                    url = f"{self.BASE_URL}/{self.MODEL_NAME}/{endpoint}"
                    response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                        json=payload,
                    )
                    if response.status_code == 404:
                        continue
                    if response.status_code >= 400:
                        logger.warning("Groq %s returned %s: %s", url, response.status_code, response.text)
                        continue
                    return self._extract_text(response.json())

        raise AIModelError("Groq API did not return a usable response")

    @staticmethod
    def _extract_text(body: Any) -> str:
        if isinstance(body, dict):
            if "results" in body and isinstance(body["results"], list) and body["results"]:
                result = body["results"][0]
                if isinstance(result, dict) and "output" in result:
                    output = result["output"]
                    if isinstance(output, list) and output:
                        return str(output[0])
                    return str(output)
            if "output" in body:
                output = body["output"]
                if isinstance(output, list) and output:
                    return str(output[0])
                return str(output)
            if "text" in body:
                return str(body["text"])
            if "generated_text" in body:
                return str(body["generated_text"])
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, dict) and "generated_text" in first:
                return str(first["generated_text"])
            return str(first)
        return str(body)


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
    def __init__(self, groq_key: str, hf_token: str):
        self.groq_key = groq_key
        self.hf_token = hf_token
        self.groq = GroqClient(groq_key)
        self.hf = HuggingFaceClient(hf_token)

    async def analyze(self, repo_path: str, branch: str, staged_diff: str, changed_files: List[str]) -> Dict[str, Any]:
        prompt = self._build_prompt(repo_path, branch, staged_diff, changed_files)

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
                    "summary": "AI review unavailable due to model API access failure.",
                    "commitMsg": "AI review could not run because the external model API could not be reached.",
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
    return AIReviewService(groq_key, hf_token)
