"""Shared helpers for the LLM-backed graders (gradingbench, proofbench)."""
import asyncio

from google import genai
from google.genai import types

# Number of times to call the grader model before giving up. The SDK does not
# retry env-server failures (it raises ToolFailed and ends the rollout), so the
# tool owns its own retrying; a persistent failure then re-raises and the
# platform terminates the session cleanly rather than the env fabricating a reward.
GRADER_MAX_ATTEMPTS = 4
GRADER_BACKOFF_CAP_S = 30


async def generate_with_retry(
    client: genai.Client,
    model: str,
    prompt: str,
    *,
    max_attempts: int = GRADER_MAX_ATTEMPTS,
) -> str:
    """Call the Gemini API with exponential backoff and return the response text.

    Transient failures (network blips, rate limits, empty/blocked candidates) are
    retried. After ``max_attempts`` the last exception is re-raised so the tool
    fails loudly (the SDK turns the raise into ToolFailed -> terminal) instead of
    swallowing the error into a fabricated reward.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            res = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(temperature=0),
            )
            assert res.candidates is not None
            assert res.candidates[0].content is not None
            assert res.candidates[0].content.parts is not None
            text = res.candidates[0].content.parts[0].text
            assert text is not None
            return text
        except Exception as e:
            last_exc = e
            if attempt < max_attempts - 1:
                wait = min(2 ** attempt, GRADER_BACKOFF_CAP_S)
                print(f"GRADER API ERROR: {model} | {e} | retry in {wait}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(wait)
    assert last_exc is not None
    raise last_exc
