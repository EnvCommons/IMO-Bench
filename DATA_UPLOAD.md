# Data Upload Requirements for IMOBench

## Overview
This environment requires the following CSV datasets to be uploaded to OpenReward cloud storage.

## Directory Structure
```
/orwd_data/imobench/
├── answerbench.csv       (170 KB, 400 rows)
├── gradingbench.csv      (11 MB, 1000 rows)
├── proofbench.csv        (188 KB, 60 rows)
└── proofbench_splits.json (2 KB, optional: ProofBench split name -> Problem IDs)
```

## File Descriptions
- **answerbench.csv**: Math problems with short answers for direct answer verification (Algebra, Combinatorics, Geometry, Number Theory)
- **gradingbench.csv**: Problems with solutions, grading guidelines, and example responses for grading evaluation
- **proofbench.csv**: Problems with solutions and grading guidelines for proof verification
- **proofbench_splits.json**: Extra ProofBench splits as `{"split name": ["PB-Basic-001", ...]}`; currently `proofbench-basic` and `proofbench-advanced`. Kept off GitHub (gitignored).

## Upload Instructions
Upload the three CSV files to the `imobench/` directory in your OpenReward namespace at https://openreward.ai.
