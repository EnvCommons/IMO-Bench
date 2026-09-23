import os

import pytest

from openreward.environments import ToolOutput, JSONObject

from answerbench import IMOBenchAnswerBench, AnswerParams as AnswerParams1
from gradingbench import IMOBenchGradingBench, AnswerParams as AnswerParams2
from proofbench import IMOBenchProofBench, AnswerParams as AnswerParams3

def grader_secrets() -> dict[str, str]:
    """Grader credentials from the environment: GEMINI_API_KEY, or OPENAI_API_KEY (with
    OPENAI_BASE_URL / JUDGE_MODEL) for an OpenAI-compatible grader. Skips when neither is set."""
    if os.getenv("OPENAI_API_KEY"):
        return {"openai_api_key": os.environ["OPENAI_API_KEY"]}
    if os.getenv("GEMINI_API_KEY"):
        return {"gemini_api_key": os.environ["GEMINI_API_KEY"]}
    pytest.skip("no grader key: set GEMINI_API_KEY or OPENAI_API_KEY")

# ===== AnswerBench Tests =====

ANSWER_TASKS = IMOBenchAnswerBench.list_tasks("all")

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("task", ANSWER_TASKS)
async def test_answerbench_gold(task: JSONObject):
    """Test that correct answers get reward=1.0"""
    env = IMOBenchAnswerBench(task_spec=task, secrets=grader_secrets())

    result: ToolOutput = await env.answer(AnswerParams1(answer=env.validated.answer))
    assert result.reward == 1.0
    assert result.finished is True

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("task", ANSWER_TASKS)
async def test_answerbench_xfail(task: JSONObject):
    """Test that incorrect answers get reward=0.0"""
    env = IMOBenchAnswerBench(task_spec=task, secrets=grader_secrets())

    incorrect_answer = "definitely_wrong_answer_123456789"
    result: ToolOutput = await env.answer(AnswerParams1(answer=incorrect_answer))
    assert result.reward == 0.0
    assert result.finished is True

# ===== GradingBench Tests =====

GRADING_TASKS = IMOBenchGradingBench.list_tasks("all")

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("task", GRADING_TASKS)
async def test_gradingbench_xfail(task: JSONObject):
    """Test that incorrect grading gets reward=0.0 (requires Gemini API key)"""
    env = IMOBenchGradingBench(task_spec=task, secrets=grader_secrets())

    incorrect_answer = "definitely_wrong_answer_123456789"
    result: ToolOutput = await env.answer(AnswerParams2(grading_analysis_and_score=incorrect_answer))
    assert result.reward == 0.0
    assert result.finished is True

# ===== ProofBench Tests =====

PROOF_TASKS = IMOBenchProofBench.list_tasks("all")

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("task", PROOF_TASKS)
async def test_proofbench_xfail(task: JSONObject):
    """Test that incorrect proofs get reward=0.0 (requires Gemini API key)"""
    env = IMOBenchProofBench(task_spec=task, secrets=grader_secrets())

    incorrect_answer = "definitely_wrong_answer_123456789"
    result: ToolOutput = await env.answer(AnswerParams3(proof_and_solution=incorrect_answer))
    # Proofbench may return reward=None or reward=0.0 for errors
    assert result.reward is not None
    assert result.reward <= 0.0
    assert result.finished is True
