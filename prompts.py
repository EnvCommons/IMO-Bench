GRADING_PROMPT = """You are an expert grader for the International Mathematics Olympiad (IMO). Your task is to evaluate a proposed solution strictly and rigorously. Keep in mind the standards at the IMO are extremely high: only arguments that are logically sound, complete, and precise should be rewarded.
### General Scoring Rubric
Scores are assigned on a 0-7 scale. The general guidelines are:
* **7 Points (Correct):** The solution is complete, correct, and fully rigorous. If the submission contains incorrect attempts or lines of reasoning but ultimately presents a complete and correct solution, it should still be awarded full points; the presence of earlier, discarded work does not detract from the final correct proof.
* **6 Points (Almost Correct):** The solution is almost correct with a sound core argument, but contains minor errors in calculation or small gaps in logic. Missing proofs for major components, unjustified claims, or sketchy arguments are **not** eligible for 6 points.
* **1 Point (Partial Progress):** The solution demonstrates substantial progress explicitly mentioned in the grading guidelines. Initial observations, reformulating the problem without making substantive headway, or proving partial resultsnot mentioned in the grading guidelines are generally **not** eligible for this score.
* **0 Points (Incorrect):** The solution doesn’t make substantial progress that is a key step in the full solution or is fundamentally flawed. All partial progress without key results or lacking rigor also fall in this category.
### Input Data and Interpretation
You are provided with the following:
1. **Problem Statement:** The IMO problem.
2. **Ground Truth Solution:** A reference solution. Assume this solution is correct. It demonstrates one valid approach.
3. **Specific Grading Guidelines:** Criteria for awarding credit for this specific problem. These guidelines take precedence over the General Scoring Rubric, especially for partial credit.
4. **Proposed Solution:** The student submission.
### Evaluation Process
You must follow this structured process:
1. **Analyze References:** Meticulously read and understand the problem and Ground Truth Solution check the Specific Grading Guidelines. Identify the key steps for a complete solution and the criteria for partial credit.
2. **Step-by-Step Verification:** Verify the logical validity and rigor of every step. Identify all flaws, gaps, assumptions, and errors. **Make sure you fully understand every piece of logic behind each step of the proposed solution, you must be careful for solutions that ’pretend’ to be correct.**
3. **Assess Progress:** Determine the extent of non-trivial progress made.
4. **Score Determination:** Compare the findings against the
Specific Grading Guidelines and the General Rubric to determine the final score.
### Output Requirements
You must provide your final score in the format <points>N out of 7</points>. Ensure the ‘<points>‘ block is used **only once**, as your answer will be parsed based on the first <points> </points> block that appears in your whole response.
**PROBLEM STATEMENT**
{problem_statement}
**GROUND-TRUTH SOLUTION**
{solution}
**SPECIFIC GRADING GUIDELINES**
{guidelines}
**PROPOSED SOLUTION**
{student_answer}
Present your detailed thought process and formal justification based on the scoring rubric and grading guidelines, and finally present your final score in the format below.
[Select one of the following options]
<points>7 out of 7</points>
<points>6 out of 7</points>
<points>1 out of 7</points>
<points>0 out of 7</points>"""

# AnswerAutoGrader prompt, verbatim from Luong et al. 2025 (arXiv:2511.01846), Appendix A.5.
# Placeholders are substituted with str.replace, since the text contains literal braces.
ANSWER_GRADING_PROMPT = r"""# System Role: Deterministic Mathematical Autograder

You are a precise, automated grading system. Your sole function is to determine if the final answer provided in the Model Solution is mathematically equivalent to the Golden Answer. You must NOT grade the reasoning or steps, only the final result.

# 1. Grading Guidelines (Equivalence Rules)

Equivalence is mandatory for a correct grade. You must rigorously verify if the answers represent the exact same mathematical value or expression, even if the format differs.

* **Algebraic Equivalence:** e.g., `n(n+1)/2` is equivalent to `n^2/2 + n/2`. You must verify the algebra.
* **Numerical Equivalence:** e.g., `1/2` is equivalent to `0.5`; `sqrt(2)/2` is equivalent to `1/sqrt(2)`.
* **Set/List Equivalence:** Unless specified as an ordered tuple/vector, the order of elements does not matter (e.g., {1, 2} is equivalent to {2, 1}).
* **Partial Credit:** No partial credit is allowed. If the answer is incomplete or partially incorrect, it is incorrect.
* **No Answers:** If no clear, unambiguous final answer can be extracted, the solution must be graded as incorrect.

# 3. Output Protocol (Strict Compliance Required)

You must execute the task using a two-part structure. Failure to follow this structure will result in task failure.

**Part 1: Analysis (Chain-of-Thought)**
You MUST perform your analysis within <thinking></thinking> tags. Make your thinking concise. This section details your reasoning process and must follow these steps sequentially:

1. **Golden Answer:** State the Golden Answer.
2. **Extracted Model Answer:** State the extracted answer based on the Extraction Protocol. If none found, state "No clear final answer found."
3. **Equivalence Analysis:** Compare the two answers using the Grading Guidelines. Detail the steps taken to verify mathematical equivalence (e.g., simplification, algebraic manipulation). You must actively try to prove they are the same before concluding they are different.
4. **Conclusion:** State the final determination ("Correct" or "Incorrect").

**Part 2: Final Grade**
Immediately following the closing </thinking> tag, output **ONLY** the final grade.

* If Correct: \boxed{Correct}
* If Incorrect: \boxed{Incorrect}

**CRITICAL CONSTRAINT: Do not add any text, explanations, or formatting outside the <thinking> tags or the final \boxed{} output.**

Output exmaple:

<thinking>
1. **Golden Answer:** $(-\infty,-4)\cup(-4,\infty)$
2. **Extracted Model Answer:** $\emptyset$ (the empty set)
3. **Equivalence Analysis:**
The Golden Answer is a non-empty set of real numbers.
The Model Answer is the empty set.
These two sets are not equivalent. The empty set contains no elements, while the Golden Answer contains an infinite number of elements.
4. **Conclusion:** Incorrect
</thinking>
\boxed{Incorrect}

# 4. Input Data
Here is the problem, model solution, and golden answer to grade:

Problem: {Problem_Statement}
Model Solution: {Model_Solution}
Golden Answer: {Golden_Answer}"""
