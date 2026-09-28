"""Shared helpers for the LLM-backed graders (answerbench, gradingbench, proofbench)."""
import asyncio
import os
import re
from typing import Any

import openai

# Number of times to call the grader model before giving up. The SDK does not
# retry env-server failures (it raises ToolFailed and ends the rollout), so the
# tool owns its own retrying; a persistent failure then re-raises and the
# platform terminates the session cleanly rather than the env fabricating a reward.
GRADER_MAX_ATTEMPTS = 4
GRADER_BACKOFF_CAP_S = 30

GRADER_MODEL = "gpt-6-luna"
GRADER_REASONING_EFFORT = "high"

# A reasoning model served without a reasoning parser returns its thinking inline; strip it so a
# score it considered while thinking cannot reach the parse.
_THINK_RE = re.compile(r"^\s*<think>.*?</think>", re.DOTALL)


class Grader:
    """gpt-6-luna with high reasoning effort, through the OpenAI chat completions API.

    Chat completions rather than the Responses API, since every OpenAI-compatible endpoint
    serves it the same way.

    The key comes from the KIMI_API_KEY environment variable, falling back to
    `openai_api_key` in secrets; OPENAI_BASE_URL sets the endpoint (any
    OpenAI-compatible server), defaulting to OpenAI.
    """

    def __init__(self, secrets: dict[str, str]) -> None:
        api_key = os.environ.get("KIMI_API_KEY") or secrets.get("openai_api_key")
        if not api_key:
            raise ValueError(
                "A grader API key must be provided: KIMI_API_KEY env var or openai_api_key secret"
            )
        self._client = openai.AsyncOpenAI(
            api_key=api_key, base_url=os.environ.get("OPENAI_BASE_URL") or None
        )
        self.model = GRADER_MODEL
        # What the endpoint reported for the last successful call: the served model name and how
        # much it reasoned. Recorded in each result so a non-reasoning judge is visible.
        self.last_call: dict[str, Any] = {}

    async def _generate_once(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self.model,
            reasoning_effort=GRADER_REASONING_EFFORT,
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.choices[0].message
        text = _THINK_RE.sub("", message.content or "").strip()
        assert text, "grader returned an empty response"
        usage = response.usage
        details = getattr(usage, "completion_tokens_details", None)
        self.last_call = {
            "served_model": response.model,
            # OpenAI reports reasoning tokens under completion_tokens_details; some compatible
            # servers put them at the top level of usage.
            "reasoning_tokens": getattr(details, "reasoning_tokens", None) or getattr(usage, "reasoning_tokens", None),
            "reasoning_chars": len(getattr(message, "reasoning_content", None) or ""),
        }
        return text

    async def generate(self, prompt: str, *, max_attempts: int = GRADER_MAX_ATTEMPTS) -> str:
        """Call the grader with exponential backoff and return the response text.

        Transient failures (network blips, rate limits, empty responses) are
        retried. After ``max_attempts`` the last exception is re-raised so the tool
        fails loudly (the SDK turns the raise into ToolFailed -> terminal) instead of
        swallowing the error into a fabricated reward.
        """
        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                return await self._generate_once(prompt)
            except Exception as e:
                last_exc = e
                if attempt < max_attempts - 1:
                    wait = min(2 ** attempt, GRADER_BACKOFF_CAP_S)
                    print(f"GRADER API ERROR: {self.model} | {e} | retry in {wait}s (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(wait)
        assert last_exc is not None
        raise last_exc
