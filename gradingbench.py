from pathlib import Path
import re
from typing import Literal, cast, List

from pydantic import BaseModel
import pandas as pd
from google import genai

from grading_utils import generate_with_retry
from openreward.environments import Environment, tool, JSONObject, ToolOutput, TextBlock, Split

if Path("/orwd_data/").exists():
    DATA_PATH = Path("/orwd_data/")
else:
    DATA_PATH = Path(__file__).parent

GRADINGBENCH_DF = pd.read_csv(DATA_PATH / "gradingbench.csv")
VALID_SPLITS = [Split(name="all", type="test"), Split(name="Algebra", type="test"), Split(name="Combinatorics", type="test"), Split(name="Geometry", type="test"), Split(name="Number theory", type="test")]

class TaskSpec(BaseModel):
    problem: str
    solution: str
    score_assigned: str

class AnswerParams(BaseModel):
    grading_analysis_and_score: str

class IMOBenchGradingBench(Environment):
    def __init__(self, task_spec: JSONObject, secrets: dict[str, str] = {}) -> None:
        super().__init__(task_spec)
        self.validated = TaskSpec.model_validate(task_spec)

        api_key = secrets.get("gemini_api_key")
        if not api_key:
            raise ValueError("Gemini API key must be provided via secrets parameter")

        self.client = genai.Client(api_key=api_key)

    async def get_prompt(self) -> List[TextBlock]:
        prompt = f"""Carefully analyze the given problem statement and the proposed solution, and then write out your analysis regarding the correctness of the proposed solution.
After the analysis, you must provide a score based on the following criteria:
- incorrect: The solution is completely incorrect or irrelevant.
- partial: The solution is partially correct but has significant errors or omissions.
- almost: The solution is almost correct but contains minor errors or inaccuracies.
- correct: The solution is fully correct and complete.
The very last part of your response must be only one of the following words: incorrect, partial, almost, or correct.
Problem:
{self.validated.problem}
Solution:
{self.validated.solution}"""
        return [TextBlock(text=prompt)]

    @tool
    async def answer(self, params: AnswerParams) -> ToolOutput:
        # First, try to extract the grade from the last word of the response
        response_text = params.grading_analysis_and_score.strip()
        words = response_text.split()
        extracted_grade: str | None = None

        if words:
            last_word = words[-1].lower().rstrip('.,!?;:')
            valid_grades = {"incorrect", "partial", "almost", "correct"}
            if last_word in valid_grades:
                extracted_grade = last_word

        # If extraction failed, use Gemini API to extract the grade
        if extracted_grade is None:
            prompt = f"""## Instructions for Extracting Final Scores
**Objective:** Given an response of an evaluation prompt, extract the final score presented within the response and format it specifically.
**Process:**
1. **Analyze the response:** Scan the response to identify the final score provided by the evaluator.
2. **Extract and format the final answer:** Present the extracted score on a new line, preceded exactly by "Final answer: ".
**Formatting Rules:**
* **Evaluation Categories:** The expected output must be one of the following categories: 'correct', 'partial', 'almost', 'incorrect', or 'not found'.
* **Score Identification:** The extraction is based on identifying the keyword used by the evaluator to summarize their conclusion. The criteria associated with these keywords are:
* **incorrect:** The evaluator concluded that the solution is completely incorrect or irrelevant.
* **partial:** The evaluator concluded that the solution is partially correct but has significant errors or omissions.
* **almost:** The evaluator concluded that the solution is almost correct but contains minor errors or inaccuracies.
* **correct:** The evaluator concluded that the solution is fully correct and complete.
* **not_found:** The evaluation response does not clearly contain one of the four explicit scores listed above.
* **Extraction:** Determine the provided score from the response and extract the category ('correct', 'partial', 'almost', or 'incorrect'). If a score cannot be reliably identified within the text, the output must be 'not_found'.
**Note:** No additional markings or explanations are needed beyond "Final answer: " and the extracted answer.
Below is the response:
{params.grading_analysis_and_score}"""

            api_response = await generate_with_retry(self.client, "gemini-2.5-flash", prompt)
            # Extract the grade from the API response
            # Look for "Final answer: " pattern
            match = re.search(r"Final answer:\s*(\w+)", api_response, re.IGNORECASE)
            if match:
                extracted_grade = match.group(1).lower()
            else:
                # Fallback: try to find one of the valid grades in the response
                valid_grades = {"incorrect", "partial", "almost", "correct"}
                for grade in valid_grades:
                    if grade in api_response.lower():
                        extracted_grade = grade
                        break

                if extracted_grade is None:
                    extracted_grade = "not_found"

        # Compare extracted grade with expected response
        expected_grade = self.validated.score_assigned.strip().lower()
        correct = extracted_grade == expected_grade

        return ToolOutput(
            metadata={
                "correct": correct,
                "extracted_grade": extracted_grade,
                "expected_grade": expected_grade,
                "grading_analysis_and_score": params.grading_analysis_and_score,
            },
            blocks=[TextBlock(text=f"Grade: {extracted_grade} (Expected: {expected_grade}) - {'Correct' if correct else 'Incorrect'}")],
            reward=1.0 if correct else 0.0,
            finished=True,
        )

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        if split not in [split.name for split in VALID_SPLITS]:
            raise ValueError(f"Unknown split: {split}")
        tasks = []
        for _, row in GRADINGBENCH_DF.iterrows():
            if split != "all" and row["Category"] != split:
                continue
            tasks.append(TaskSpec(
                problem=str(row["Problem"]),
                solution=str(row["Solution"]),
                score_assigned=str(row["Reward"]))
            )
        return [task.model_dump() for task in tasks]

    @classmethod
    def list_splits(cls) -> list[str]:
        return VALID_SPLITS
