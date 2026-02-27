import asyncio
from pathlib import Path
import re
import traceback
from typing import List

from pydantic import BaseModel
import pandas as pd
from google import genai
from google.genai import types

from prompts import GRADING_PROMPT
from openreward.environments import Environment, tool, JSONObject, ToolOutput, TextBlock, Split

if Path("/orwd_data/").exists():
    DATA_PATH = Path("/orwd_data/")
else:
    DATA_PATH = Path(__file__).parent

PROOFBENCH_DF = pd.read_csv(DATA_PATH / "proofbench.csv")
VALID_SPLITS = [Split(name="all", type="test"), Split(name="Algebra", type="test"), Split(name="Combinatorics", type="test"), Split(name="Geometry", type="test"), Split(name="Number theory", type="test")]
VALID_SCORES = {0, 1, 6, 7}

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

        api_key = secrets.get("gemini_api_key")
        if not api_key:
            raise ValueError("Gemini API key must be provided via secrets parameter")

        self.client = genai.Client(api_key=api_key)

    async def get_prompt(self) -> List[TextBlock]:
        return [TextBlock(text=f"Please reason step by step.\n{self.validated.problem}")]

    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        try:
            prompt = GRADING_PROMPT.format(
                problem_statement=self.validated.problem,
                solution=self.validated.solution,
                guidelines=self.validated.guidelines,
                student_answer=params.proof_and_solution
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-2.5-pro",
                contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
                config=types.GenerateContentConfig(temperature=0),
            )

            assert response.candidates is not None
            assert response.candidates[0].content is not None
            assert response.candidates[0].content.parts is not None
            response_text = response.candidates[0].content.parts[0].text
            assert response_text is not None

            # Extract score from <points>N out of 7</points> format
            match = re.search(r"<points>(\d+) out of 7</points>", response_text)
            reward: float | None = None
            extracted_score: int | None = None
            if match:
                extracted_score = int(match.group(1))
                if extracted_score in VALID_SCORES:
                    reward = extracted_score / 7.0

            score_text = f"{extracted_score}/7" if extracted_score is not None else "N/A"
            return ToolOutput(
                metadata={
                    "grader_response": response_text,
                    "extracted_score": extracted_score,
                    "reward": reward,
                },
                blocks=[TextBlock(text=f"Score: {score_text} (Reward: {reward if reward is not None else 'N/A'})")],
                reward=reward,
                finished=True,
            )
        except Exception:
            return ToolOutput(
                metadata={"error": traceback.format_exc()},
                blocks=[TextBlock(text="Error occurred during proof grading")],
                reward=None,
                finished=True,
            )

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        if split not in [split.name for split in VALID_SPLITS]:
            raise ValueError(f"Unknown split: {split}")
        tasks = []
        for _, row in PROOFBENCH_DF.iterrows():
            if split != "all" and row["Category"] != split:
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
