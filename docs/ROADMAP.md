# Roadmap and parent-project boundary

This standalone release publishes the companion verifier and its documentation. It is not acceptance of the full DeepSeek/MG-01 project.

| Area | This release | Remaining work |
| --- | --- | --- |
| Fixed statement, axiom audit | Implemented; negative controls in selftest | Independent review, broader syntax cases and adversarial tests |
| Evidence | Unique runs, hashes and replay | Signed evidence, complete dependency/toolchain provenance |
| Context extraction | Lean AST theorem extraction | Training corpus migration and verification of every example |
| Generation and repair | Optional MLX path, tested with fixture | Broader real-model coverage and a fresh locked ML environment (one local Base/LoRA smoke was run) |
| Evaluation leakage | No reference proof in current target prompt | Thirty fresh held-out tasks, frozen adapter and fair Base/LoRA evaluation |
| Candidate training | Not shipped | Reproducible training, save/reload and separate promotion review |
| Mathlib | External trusted project option | Parent experiment/core final synchronized build acceptance |
| MG-01 | Not part of companion distribution | Complete transition invariants, 50000 games, browser tests and canonical reader |
| Parent passport | Historical status stays NEEDS_REWORK | Final R01–R18 evidence-backed acceptance |
| Platform | macOS fail-closed restriction | Reviewed Linux isolation backend and real hostile-input testing |

No claim of balanced classes, optimal game strategy, complete game verification or 10/10 model performance is made. Publishing this prerelease does not change any working adapter or deployed site.
