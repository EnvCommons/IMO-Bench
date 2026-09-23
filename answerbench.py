from pathlib import Path
import re
from typing import cast, List

from pydantic import BaseModel
import pandas as pd

from grading_utils import Grader
from prompts import ANSWER_GRADING_PROMPT
from openreward.environments import Environment, tool, JSONObject, ToolOutput, TextBlock, Split

if Path("/orwd_data/").exists():
    DATA_PATH = Path("/orwd_data/")
else:
    DATA_PATH = Path(__file__).parent

ANSWERBENCH_DF = pd.read_csv(DATA_PATH / "answerbench.csv")
VALID_SPLITS = [Split(name="all", type="test"), Split(name="Algebra", type="test"), Split(name="Combinatorics", type="test"), Split(name="Geometry", type="test"), Split(name="Number theory", type="test")]

class TaskSpec(BaseModel):
    problem: str
    answer: str

class AnswerParams(BaseModel):
    answer: str

# The last \boxed{Correct|Incorrect} is the verdict; earlier ones can appear in the analysis.
_VERDICT_RE = re.compile(r"\\boxed\{\s*(Correct|Incorrect)\s*\}", re.IGNORECASE)


class IMOBenchAnswerBench(Environment):
    def __init__(self, task_spec: JSONObject, secrets: dict[str, str] = {}) -> None:
        super().__init__(task_spec)
        self.validated = TaskSpec.model_validate(task_spec)
        self.grader = Grader(secrets)

    async def get_prompt(self) -> List[TextBlock]:
        return [TextBlock(text=f"Please reason step by step.\n{self.validated.problem}")]

    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        # Graded by an LLM (the paper's AnswerAutoGrader) rather than a symbolic checker, so
        # an equivalent answer in a different form is not marked wrong.
        prompt = (ANSWER_GRADING_PROMPT
                  .replace("{Problem_Statement}", self.validated.problem)
                  .replace("{Model_Solution}", params.answer)
                  .replace("{Golden_Answer}", self.validated.answer))
        response_text = await self.grader.generate("gemini-2.5-pro", prompt)

        verdicts = _VERDICT_RE.findall(response_text)
        correct: bool | None = verdicts[-1].lower() == "correct" if verdicts else None
        reward = None if correct is None else (1.0 if correct else 0.0)
        verdict_text = "Ungraded" if correct is None else ("Correct!" if correct else "Incorrect.")
        return ToolOutput(
            metadata={
                "correct": correct,
                "model_answer": params.answer,
                "solution": self.validated.answer,
                "grader_response": response_text,
                "judge_model": self.grader.model_for("gemini-2.5-pro"),
            },
            blocks=[TextBlock(text=f"{verdict_text} Expected: {self.validated.answer}")],
            reward=reward,
            finished=True,
        )

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        if split not in [split.name for split in VALID_SPLITS]:
            raise ValueError(f"Unknown split: {split}")
        tasks = []
        for _, row in ANSWERBENCH_DF.iterrows():
            if split != "all" and row["Category"] != split:
                continue
            tasks.append(TaskSpec(problem=str(row["Problem"]), answer=str(row["Short Answer"]).strip()))
        return [task.model_dump() for task in tasks]

    @classmethod
    def list_splits(cls) -> list[str]:
        return VALID_SPLITS
