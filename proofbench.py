import json
from pathlib import Path
import re
from typing import List

from pydantic import BaseModel
import pandas as pd
from grading_utils import Grader
from prompts import GRADING_PROMPT
from openreward.environments import Environment, tool, terminal, JSONObject, ToolOutput, TextBlock, Split

if Path("/orwd_data/").exists():
    DATA_PATH = Path("/orwd_data/")
else:
    DATA_PATH = Path(__file__).parent

PROOFBENCH_DF = pd.read_csv(DATA_PATH / "proofbench.csv")
# Extra splits (e.g. proofbench-basic / proofbench-advanced) are data, not code: an optional
# proofbench_splits.json in the data directory maps each split name to its Problem IDs.
_SPLITS_FILE = DATA_PATH / "proofbench_splits.json"
ID_SPLITS: dict[str, set[str]] = (
    {name: set(ids) for name, ids in json.loads(_SPLITS_FILE.read_text()).items()}
    if _SPLITS_FILE.exists() else {}
)
_unknown_ids = set().union(*ID_SPLITS.values()) - set(PROOFBENCH_DF["Problem ID"].astype(str))
if _unknown_ids:
    raise ValueError(f"proofbench_splits.json names unknown Problem IDs: {sorted(_unknown_ids)}")
VALID_SPLITS = [Split(name="all", type="test"), *(Split(name=name, type="test") for name in ID_SPLITS), Split(name="Algebra", type="test"), Split(name="Combinatorics", type="test"), Split(name="Geometry", type="test"), Split(name="Number theory", type="test")]
VALID_SCORES = {0, 1, 6, 7}
# Tags that frame the proof (<proof>) or carry the grader's score (<answer>). Escaped inside the
# submission, so it can neither close its <proof> block nor plant a score the grader might echo.
_TAG_RE = re.compile(r"<\s*(/?)\s*(proof|answer)\s*>", re.IGNORECASE)
# The grader ends with <answer>N</answer>; tolerate "N out of 7" and whitespace inside the tag.
_SCORE_RE = re.compile(r"<answer>\s*(\d+)(?:\s*out\s+of\s+7)?\s*</answer>", re.IGNORECASE)

class TaskSpec(BaseModel):
    problem: str
    solution: str
    guidelines: str

class AnswerParams(BaseModel):
    proof_and_solution: str

class IMOBenchProofBench(Environment):
    def __init__(self, task_spec: JSONObject, secrets: dict[str, str] = {}) -> None:
        super().__init__(task_spec)
        self.validated = TaskSpec.model_validate(task_spec)

        self.grader = Grader(secrets)

    async def get_prompt(self) -> List[TextBlock]:
        return [TextBlock(text=(
            f"Please reason step by step.\n{self.validated.problem}\n\n"
            "Your reply must be a complete and rigorous proof: justify every step. It is graded on "
            "the IMO 0-7 scale against a reference solution, and a correct final answer without a "
            "full proof earns no credit."
        ))]

    @terminal
    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        prompt = GRADING_PROMPT.format(
            problem_statement=self.validated.problem,
            solution=self.validated.solution,
            guidelines=self.validated.guidelines,
            student_answer=_TAG_RE.sub(r"&lt;\1\2&gt;", params.proof_and_solution),
        )

        response_text = await self.grader.generate(prompt)

        # Score from the grader's <answer>N</answer>. Take the LAST one: the reasoning may quote
        # the option list before the verdict at the end. Reward = N / 7 for N in VALID_SCORES.
        matches = _SCORE_RE.findall(response_text)
        reward: float | None = None
        extracted_score: int | None = None
        if matches:
            extracted_score = int(matches[-1])
            if extracted_score in VALID_SCORES:
                reward = extracted_score / 7.0

        score_text = f"{extracted_score}/7" if extracted_score is not None else "N/A"
        return ToolOutput(
            metadata={
                "grader_response": response_text,
                "judge_model": self.grader.model,
                "extracted_score": extracted_score,
                "reward": reward,
            },
            blocks=[TextBlock(text=f"Score: {score_text} (Reward: {reward if reward is not None else 'N/A'})")],
            reward=reward,
            finished=True,
        )

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        if split not in [split.name for split in VALID_SPLITS]:
            raise ValueError(f"Unknown split: {split}")
        tasks = []
        for _, row in PROOFBENCH_DF.iterrows():
            if split in ID_SPLITS:
                if str(row["Problem ID"]) not in ID_SPLITS[split]:
                    continue
            elif split != "all" and row["Category"] != split:
                continue
            tasks.append(TaskSpec(
                problem=str(row["Problem"]),
                solution=str(row["Solution"]),
                guidelines=str(row["Grading guidelines"]),
            ))
        return [task.model_dump() for task in tasks]

    @classmethod
    def list_splits(cls) -> list[str]:
        return VALID_SPLITS
