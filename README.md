# Lean Proof Companion

**Keep the statement fixed. Generate a candidate. Let Lean check it. Save the evidence.**

A local companion for people learning Lean, building formal specifications, or testing proof-generating models. It separates the model's suggestion from the verifier's decision and reports which axioms a proof depends on.

**Status: v0.1.0-alpha.1 — research prerelease.** The verifier and model-free examples have release checks. Base and LoRA generation were smoke-tested locally on one toy target; the MLX integration remains experimental; training and independent model benchmarking are outside this release. This release does not close the parent project's 18-item remediation plan.

[Русская документация и назначение](docs/README_RU.md) · [Install and deployment](docs/INSTALL.md) · [CLI reference](docs/CLI.md) · [Architecture](docs/ARCHITECTURE.md) · [Trust and limitations](SECURITY.md) · [Release evidence](docs/VALIDATION.md) · [Roadmap](docs/ROADMAP.md)

## Why use it?

A convincing-looking answer can prove the wrong statement, use an undeclared assumption, or fail to compile. This companion keeps the original theorem header, submits only a proof term, compiles it with Lean, audits the resulting theorem with `Lean.collectAxioms`, and saves each attempt in a separate directory.

Use it to:

- check a proof received from a person or model against your exact theorem;
- learn from Lean diagnostics and compare a first attempt with a repaired attempt;
- distinguish proofs on standard Lean axioms from proofs relying on your own assumptions;
- retain the input, output, diagnostics, tool version and hashes for later inspection.

It checks the formal statement you supplied. It does not establish that your specification matches the real world, that a model is reliable on unseen problems, or that a game is balanced.

## Quick start: no model required

Requirements: **macOS**, Python 3.11+, and [Elan](https://github.com/leanprover/elan) with Lake on PATH. The checked Lean toolchain is pinned in `lean-toolchain`.

```sh
git clone https://github.com/kernelpanic888/lean-proof-companion.git
cd lean-proof-companion
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
lake env lean --version
lean-proof-companion doctor
lean-proof-companion verify \
  --source examples/Tasks.lean \
  --name CompanionExample.twice_zero \
  --proof examples/valid.proof
lean-proof-companion selftest
```

The example should report `VERIFIED_STANDARD` and `accepted: true`. Try `examples/invalid.proof`: it must return a rejection and exit code 1.

## A specification example

`examples/NoDoubleWrite.lean` states a practical rule: a scorecard category already marked as used cannot be recorded again. The model uses `Fin 13` for category bounds. Check the saved proof with:

```sh
lean-proof-companion verify --source examples/NoDoubleWrite.lean \
  --name Scorecard.no_double_write --proof examples/no-double-write.proof
```

This verifies a rule of the small specification; it does not verify an external JavaScript game or the complete MG-01 engine.

## Optional model assistance

On Apple Silicon, install the optional MLX environment described in [INSTALL](docs/INSTALL.md). Supply your own local MLX-compatible model and, optionally, adapter. Model weights are not redistributed.

```sh
lean-proof-companion prove \
  --source examples/Tasks.lean \
  --name CompanionExample.add_zero \
  --model /path/to/local-mlx-model \
  --attempts 3
```

The budgets are 512, 1024, 1024 tokens. The original statement stays fixed; later attempts receive the previous answer and Lean diagnostics. A LoRA run requires an explicit `--adapter /path/to/adapter`. There is no automatic fallback claiming LoRA while using Base.

## Reading the result

| Status | Meaning | Strict acceptance |
| --- | --- | --- |
| `VERIFIED_STANDARD` | Kernel-checked theorem, matching type, dependencies limited to `propext`, `Classical.choice`, `Quot.sound` | Yes, only without warnings |
| `CONDITIONAL` | Kernel-checked theorem with additional user axioms | No |
| `REJECTED` | Invalid term, compilation failure, changed type, placeholder, or non-theorem | No |
| `INFRA_ERROR` | Required tool, sandbox, inspector, or file operation failed | No |

A warning may accompany `VERIFIED_STANDARD`; `accepted` remains false under the strict policy. Read both fields. Exit codes: 0 accepted / successful inspection, 1 rejected or conditional, 2 infrastructure failure. `replay` checks evidence integrity, not proof validity anew.

Each attempt saves `task.json`, `raw.txt`, `proof.txt`, generated Lean source, compiler diagnostics, a structured inspector result, `result.json`, and `seal.json`. No previous run directory is reused. Hashes detect accidental or partial modification; they are not signatures against an attacker who can rewrite the entire directory.

## Bring your own Lean project

```sh
lean-proof-companion verify --project /path/to/trusted-lake-project \
  --source /path/to/Tasks.lean --name MyNamespace.myTheorem \
  --proof /path/to/proof.txt --runs ./runs
```

Build that project's imports with `lake build` first. The project's context, dependencies and plugins must be trusted. Only the pinned toolchain in this repository is included in release acceptance; other Lean versions may require changes to the inspector API.

## Development

```sh
. .venv/bin/activate
./scripts/check.sh
```

See [CONTRIBUTING](CONTRIBUTING.md), [CHANGELOG](CHANGELOG.md) and [release procedure](docs/RELEASING.md). Source is Apache-2.0; Lean and optional model dependencies retain their own licenses. No hosting, model download, adapter promotion or site deployment occurs automatically.
