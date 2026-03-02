# IMO-Bench

[![OpenReward Environment](https://img.shields.io/badge/%E2%AD%90%20OpenReward-Environment-f7e6cc)](https://openreward.ai/GeneralReasoning/IMO-Bench)

## Description

**IMO-Bench** is an environment for evaluating agents on International Mathematical Olympiad (IMO) problems. It contains three sub-environments targeting different mathematical capabilities: **AnswerBench** (numerical answer extraction), **GradingBench** (solution grading), and **ProofBench** (proof generation). Problems span four IMO categories: Algebra, Combinatorics, Geometry, and Number Theory.

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

IMO-Bench contains three sub-environments, each with 5 splits (all, Algebra, Combinatorics, Geometry, Number Theory). All splits are test-only. Total: 1,460 tasks.

- **AnswerBench** (400 tasks): Problems with short numerical answers (100 per category). The agent solves the problem and submits an answer verified by the `math_verify` library.
- **ProofBench** (60 tasks): Problems requiring full proof generation (30 basic + 30 advanced). The agent writes a proof that is graded on the IMO 0-7 scale by an LLM grader (gemini-2.5-pro).
- **GradingBench** (1,000 tasks): Problems paired with a proposed solution and a ground-truth grade. The agent analyzes the solution and assigns a grade (incorrect, partial, almost, correct).

## Reward Structure

This is a sparse reward environment. Each task requires exactly one tool call to the `answer` tool.

- **AnswerBench**: Binary reward. **1.0** for a correct answer (verified by `math_verify`), **0.0** otherwise. No LLM graders.
- **GradingBench**: Binary reward. **1.0** if the extracted grade matches the expected grade, **0.0** otherwise. A Gemini LLM (gemini-2.5-flash) is used as a fallback to extract the grade from the agent's response when direct parsing fails.
- **ProofBench**: Continuous reward on the IMO scale. The proof is graded by an LLM grader (gemini-2.5-pro) which assigns a score from {0, 1, 6, 7} out of 7. Reward is the score divided by 7 (0.0 to 1.0).

## Data

Problems are sourced from International Mathematical Olympiad competitions, stored as CSV files. Data files are stored on the OpenReward platform.

## Tools

Agents are given a single tool across all three sub-environments:

- `answer`: Submit an answer (numerical answer for AnswerBench, grading analysis for GradingBench, or proof for ProofBench). Returns the grade and score. This tool can only be called once per task.

## Time Horizon

IMO-Bench is a single-turn environment. The agent receives a math problem and submits one answer. Each task requires exactly one tool call.

## Environment Difficulty

[Statistics on environment difficulty here]

## Other Environment Requirements

GradingBench and ProofBench require a Google Gemini API key (`GEMINI_API_KEY` secret) for LLM-based grading. AnswerBench has no additional requirements.

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
