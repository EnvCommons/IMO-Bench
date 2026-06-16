from pathlib import Path
import re
from typing import cast, List

from pydantic import BaseModel
import pandas as pd

from answer_verification import verify_math_answer
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

class IMOBenchAnswerBench(Environment):
    def __init__(self, task_spec: JSONObject, secrets: dict[str, str] = {}) -> None:
        super().__init__(task_spec)
        self.validated = TaskSpec.model_validate(task_spec)

    async def get_prompt(self) -> List[TextBlock]:
        return [TextBlock(text=f"Please reason step by step.\n{self.validated.problem}")]

    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        # verify_math_answer is deterministic and already falls back to string
        # comparison for unparseable answers, so no retry is needed here. Any
        # exception that still escapes is a genuine verifier defect and is left
        # to propagate (the SDK marks the call ToolFailed and ends the rollout)
        # rather than fabricating a reward.
        correct = verify_math_answer(params.answer, self.validated.answer)
        return ToolOutput(
            metadata={
                "correct": correct,
                "model_answer": params.answer,
                "solution": self.validated.answer,
            },
            blocks=[TextBlock(text=f"{'Correct!' if correct else 'Incorrect.'} Expected: {self.validated.answer}")],
            reward=1.0 if correct else 0.0,
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
