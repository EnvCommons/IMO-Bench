# IMO-Bench

[![OpenReward Environment](https://img.shields.io/badge/%E2%AD%90%20OpenReward-Environment-f7e6cc)](https://openreward.ai/GeneralReasoning/IMO-Bench)

## Description

**IMO-Bench** is an environment for evaluating agents on International Mathematical Olympiad (IMO) problems. It contains three sub-environments targeting different mathematical capabilities: **AnswerBench** (short-answer problem solving), **GradingBench** (solution grading), and **ProofBench** (proof generation). Problems span four IMO categories: Algebra, Combinatorics, Geometry, and Number Theory.

## Capabilities

- Solving mathematical olympiad problems requiring advanced reasoning
- Generating rigorous mathematical proofs
- Grading mathematical solutions for correctness
- Reasoning across Algebra, Combinatorics, Geometry, and Number Theory

## Compute Requirements

IMO-Bench does not require a sandbox. It has minimal compute requirements.

## License

[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Tasks

IMO-Bench contains three environment variants, each with 5 splits (all, Algebra, Combinatorics, Geometry, Number Theory). ProofBench has two more, **ProofBench-Basic** and **ProofBench-Advanced**. All splits are test-only. Total: 1,460 tasks.

- **AnswerBench** (400 tasks): Problems with short final answers — numbers, expressions or sets (100 per category). The agent solves the problem and submits an answer, which an LLM grader checks for mathematical equivalence with the reference answer (the paper's AnswerAutoGrader prompt; gpt-6-luna, high reasoning).
- **ProofBench** (60 tasks): Problems requiring full proof generation (30 basic + 30 advanced). The agent writes a proof that is graded on the IMO 0-7 scale by an LLM grader (gpt-6-luna, high reasoning). Its two extra splits are defined by `proofbench_splits.json` (split name -> Problem IDs) in the OpenReward file store, not in code:
  - `ProofBench-Basic` (30 tasks): PB-Basic-001..030, pre-IMO to IMO-medium, mostly modified competition problems.
  - `ProofBench-Advanced` (30 tasks): PB-Advanced-001..030, IMO-easy to IMO-hard, novel problems plus modified IMO 2024 and USAMO 2025 problems.
- **GradingBench** (1,000 tasks): Problems paired with a proposed solution and a ground-truth grade. The agent analyzes the solution and assigns a grade (incorrect, partial, almost, correct).

## Reward Structure

This is a sparse reward environment. In AnswerBench and GradingBench the agent's first plain reply is its answer and is graded once; in ProofBench the proof passed to `submit_proof` is graded once.

- **AnswerBench**: Binary reward. **1.0** if the LLM grader judges the answer equivalent to the reference, **0.0** otherwise. An LLM rather than a symbolic checker, as in the paper, so a correct answer in a different form (e.g. `\lceil \log_2(a+1) \rceil` for `\lfloor \log_2 a \rfloor + 1`) is not marked wrong.
- **GradingBench**: Binary reward. **1.0** if the extracted grade matches the expected grade, **0.0** otherwise. The grade is read from the last word of the response; only when that fails does the LLM grader (gpt-6-luna) extract it.
- **ProofBench**: Continuous reward on the IMO scale. The proof is graded by an LLM grader (gpt-6-luna, high reasoning) which assigns a score from {0, 1, 6, 7} out of 7. Reward is the score divided by 7 (0.0 to 1.0).

## Data

Problems are sourced from International Mathematical Olympiad competitions, stored as CSV files. Data files are stored on the OpenReward platform.

The data is the original IMO-Bench release (`answerbench.csv`, `proofbench.csv`, `gradingbench.csv`). Upstream has since deprecated the first two for `answerbench_v2.csv` (fixes ambiguous statements and incorrect answers) and `proofbench_v2.csv` (a typo fix and two clarified geometry statements); this environment has not moved to v2 yet.

## Tools

AnswerBench and GradingBench give agents no tools: their `answer` tool is marked `@terminal`, so the SDK hides it and the harness routes the agent's first plain (non-tool-call) reply into it. The agent simply writes its solution (the final answer for AnswerBench, or the grading analysis ending in a grade for GradingBench) and the grader reads that text.

| Tool | Variant | Description |
|------|---------|-------------|
| `submit_proof(proof)` | ProofBench | Submit the proof for grading. Ends the episode. Only the first submission is graded; a repeat submission gets reward -0.1 and is not re-graded. |

## Time Horizon

IMO-Bench consists of single-submission environments. The agent receives a math problem and submits once: its reply (AnswerBench, GradingBench) or its `submit_proof` call (ProofBench) is graded.

## Environment Difficulty

[Statistics on environment difficulty here]

## Other Environment Requirements

All three variants grade with `gpt-6-luna` at high reasoning effort through the OpenAI chat completions API, configured by environment variables: `KIMI_API_KEY` is the grader key (the `openai_api_key` session secret is used when it is unset) and `OPENAI_BASE_URL` the endpoint (any OpenAI-compatible server; OpenAI by default). The model is recorded in each result's metadata (`judge_model` for AnswerBench and ProofBench, with `judge_call` giving the model the endpoint reported and its reasoning tokens; `extraction_model` for GradingBench, set only when the fallback ran). Scores are not comparable with the paper's Gemini-graded results.

## Safety

Agents in IMO-Bench are asked to solve, grade, or prove mathematical problems. The environment does not present direct safety risks, as agents only provide text answers with no access to external systems, tools, or the internet.

## Citations

```bibtex
@inproceedings{luong2025imobench,
  title={Towards Robust Mathematical Reasoning},
  author={Luong, Thang and Hwang, Dawsen and Nguyen, Hoang H. and Ghiasi, Golnaz and Chervonyi, Yuri and Seo, Insuk and Kim, Junsu and Bingham, Garrett and Lee, Jonathan and Mishra, Swaroop and Zhai, Alex and Hu, Clara Huiyi and Michalewski, Henryk and Kim, Jimin and Ahn, Jeonghyun and Bae, Junhwi and Song, Xingyou and Trinh, Trieu H. and Le, Quoc V. and Jung, Junehyuk},
  booktitle={Proceedings of EMNLP},
  year={2025},
  url={https://arxiv.org/abs/2511.01846}
}
```
