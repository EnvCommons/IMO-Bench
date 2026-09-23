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

IMO-Bench contains three environment variants, each with 5 splits (all, Algebra, Combinatorics, Geometry, Number Theory). All splits are test-only. Total: 1,460 tasks.

- **AnswerBench** (400 tasks): Problems with short final answers — numbers, expressions or sets (100 per category). The agent solves the problem and submits an answer, which an LLM grader checks for mathematical equivalence with the reference answer (the paper's AnswerAutoGrader prompt; gemini-2.5-pro by default).
- **ProofBench** (60 tasks): Problems requiring full proof generation (30 basic + 30 advanced). The agent writes a proof that is graded on the IMO 0-7 scale by an LLM grader (gemini-2.5-pro by default).
- **GradingBench** (1,000 tasks): Problems paired with a proposed solution and a ground-truth grade. The agent analyzes the solution and assigns a grade (incorrect, partial, almost, correct).

## Reward Structure

This is a sparse reward environment. Each task requires exactly one tool call to the `answer` tool.

- **AnswerBench**: Binary reward. **1.0** if the LLM grader judges the answer equivalent to the reference, **0.0** otherwise. An LLM rather than a symbolic checker, as in the paper, so a correct answer in a different form (e.g. `\lceil \log_2(a+1) \rceil` for `\lfloor \log_2 a \rfloor + 1`) is not marked wrong.
- **GradingBench**: Binary reward. **1.0** if the extracted grade matches the expected grade, **0.0** otherwise. The grade is read from the last word of the response; only when that fails does the LLM grader (gemini-2.5-flash by default) extract it.
- **ProofBench**: Continuous reward on the IMO scale. The proof is graded by an LLM grader (gemini-2.5-pro by default) which assigns a score from {0, 1, 6, 7} out of 7. Reward is the score divided by 7 (0.0 to 1.0).

## Data

Problems are sourced from International Mathematical Olympiad competitions, stored as CSV files. Data files are stored on the OpenReward platform.

The data is the original IMO-Bench release (`answerbench.csv`, `proofbench.csv`, `gradingbench.csv`). Upstream has since deprecated the first two for `answerbench_v2.csv` (fixes ambiguous statements and incorrect answers) and `proofbench_v2.csv` (a typo fix and two clarified geometry statements); this environment has not moved to v2 yet.

## Tools

Agents are given a single tool across all three sub-environments:

- `answer`: Submit an answer (final answer for AnswerBench, grading analysis for GradingBench, or proof for ProofBench). Returns the grade and score. This tool can only be called once per task.

## Time Horizon

IMO-Bench consists of single-turn environments. The agent receives a math problem and submits one answer. Each task requires exactly one tool call.

## Environment Difficulty

[Statistics on environment difficulty here]

## Other Environment Requirements

All three variants need an LLM grader, configured through session secrets.

- `gemini_api_key`: grade with Gemini, using the models above (the benchmark's reference setup).
- `openai_api_key`: grade with any OpenAI-compatible chat endpoint instead. `OPENAI_BASE_URL` redirects it to another provider, and `JUDGE_MODEL` names the model (default `gpt-5-mini`). The model used is recorded in each result's metadata (`judge_model` for AnswerBench and ProofBench, `extraction_model` for GradingBench, set only when the fallback ran). Scores graded this way are not comparable with results graded by Gemini.

If both are given, `openai_api_key` wins.

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
