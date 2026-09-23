"""Shared helpers for the LLM-backed graders (gradingbench, proofbench)."""
import asyncio
import os
import re

from google import genai
from google.genai import types
import openai

# Number of times to call the grader model before giving up. The SDK does not
# retry env-server failures (it raises ToolFailed and ends the rollout), so the
# tool owns its own retrying; a persistent failure then re-raises and the
# platform terminates the session cleanly rather than the env fabricating a reward.
GRADER_MAX_ATTEMPTS = 4
GRADER_BACKOFF_CAP_S = 30

# Used when an OpenAI-compatible grader is configured without JUDGE_MODEL.
DEFAULT_OPENAI_JUDGE_MODEL = "gpt-5-mini"

# A reasoning model served without a reasoning parser returns its thinking inline,
# and the <points> regex would match a score it considered rather than the one it gave.
_THINK_RE = re.compile(r"^\s*<think>.*?</think>", re.DOTALL)


class Grader:
    """One grader backend: Gemini, or any OpenAI-compatible chat endpoint.

    `openai_api_key` in secrets selects the OpenAI-compatible backend, which
    honours OPENAI_BASE_URL (so grading can be redirected to another endpoint)
    and JUDGE_MODEL. Otherwise `gemini_api_key` selects Gemini with the
    per-call model the benchmark specifies.
    """

    def __init__(self, secrets: dict[str, str]) -> None:
        openai_key = secrets.get("openai_api_key")
        gemini_key = secrets.get("gemini_api_key")
        if openai_key:
            self.backend = "openai"
            self._openai = openai.AsyncOpenAI(
                api_key=openai_key, base_url=os.environ.get("OPENAI_BASE_URL") or None
            )
            self._openai_model = os.environ.get("JUDGE_MODEL") or DEFAULT_OPENAI_JUDGE_MODEL
        elif gemini_key:
            self.backend = "gemini"
            self._gemini = genai.Client(api_key=gemini_key)
        else:
            raise ValueError(
                "A grader API key must be provided via secrets: "
                "gemini_api_key, or openai_api_key for an OpenAI-compatible endpoint"
            )

    def model_for(self, gemini_model: str) -> str:
        return gemini_model if self.backend == "gemini" else self._openai_model

    async def _generate_once(self, gemini_model: str, prompt: str) -> str:
        if self.backend == "gemini":
            res = await asyncio.to_thread(
                self._gemini.models.generate_content,
                model=gemini_model,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(temperature=0),
            )
            assert res.candidates is not None
            assert res.candidates[0].content is not None
            assert res.candidates[0].content.parts is not None
            text = res.candidates[0].content.parts[0].text
        else:
            chat = await self._openai.chat.completions.create(
                model=self._openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = chat.choices[0].message.content
            if text is not None:
                text = _THINK_RE.sub("", text).strip()
        assert text, "grader returned an empty response"
        return text

    async def generate(
        self, gemini_model: str, prompt: str, *, max_attempts: int = GRADER_MAX_ATTEMPTS
    ) -> str:
        """Call the grader with exponential backoff and return the response text.

        Transient failures (network blips, rate limits, empty/blocked candidates) are
        retried. After ``max_attempts`` the last exception is re-raised so the tool
        fails loudly (the SDK turns the raise into ToolFailed -> terminal) instead of
        swallowing the error into a fabricated reward.
        """
        model = self.model_for(gemini_model)
        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                return await self._generate_once(gemini_model, prompt)
            except Exception as e:
                last_exc = e
                if attempt < max_attempts - 1:
                    wait = min(2 ** attempt, GRADER_BACKOFF_CAP_S)
                    print(f"GRADER API ERROR: {model} | {e} | retry in {wait}s (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(wait)
        assert last_exc is not None
        raise last_exc
