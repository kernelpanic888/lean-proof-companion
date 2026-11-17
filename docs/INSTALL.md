# Installation and local deployment

## Supported profile

- macOS with `/usr/bin/sandbox-exec`; model-free validation also runs on macOS GitHub runners.
- Python 3.11 or newer. Release checks use Python 3.11.
- Elan and Lake; `lean-toolchain` pins `leanprover/lean4:v4.31.0-rc1`.
- Model assistance additionally requires Apple Silicon and MLX-compatible local weights.

The Python verifier has no runtime package dependencies. Installation uses setuptools as a build dependency. All commands below run from the repository root. No old virtual environment is needed.

## Install Elan

Follow the upstream [Elan installation instructions](https://github.com/leanprover/elan#installation). Ensure `lake` is available on PATH, then run:

```sh
lake env lean --version
```

Elan installs the pinned toolchain if it is missing. Installation needs network access. Verification workers themselves deny network access. This repository's default Lake package has no external Lean dependencies.

## Create a fresh Python environment

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
lean-proof-companion doctor
./scripts/check.sh
```

A successful `doctor` actually starts the restricted Lean worker and parses a small theorem. It does not infer health from a directory's existence. Evidence goes into `runs/`, which is ignored by Git.

For a wheel installation, pass `--project /path/to/this-checkout` to Lean commands: the wheel contains the inspector but does not bundle a root Lake project. A source checkout with editable installation is the supported deployment.

## Optional MLX generation

Create a second environment to keep the model-free checker installation simple:

```sh
python3.11 -m venv .venv-mlx
. .venv-mlx/bin/activate
python -m pip install -e .
python -m pip install -r requirements-mlx.txt
python -m pip freeze > local-mlx-environment.txt
```

`requirements-mlx.txt` pins the two directly used MLX packages to the historical development environment. Transitive resolution and fresh GPU execution are **not release-validated**. This is not a reproducible ML environment lock. Do not interpret successful installation as a model smoke test.

Obtain an MLX-compatible model separately, observe its model license, and store it outside Git. No download command or particular weight revision is implied by this release. You may use a locally converted DeepSeek-Prover-V2 model; its weights and license are independent of this repository.

```sh
lean-proof-companion prove --source examples/Tasks.lean \
  --name CompanionExample.add_zero --model /absolute/path/to/model
```

The entire selected model directory is hashed before generation. Keep it stable during a run. An adapter is optional and explicit:

```sh
lean-proof-companion prove --source examples/Tasks.lean \
  --name CompanionExample.add_zero --model /absolute/path/to/model \
  --adapter /absolute/path/to/adapter
```

This release has no training or adapter promotion command.

## Service integration and CI

Use the CLI as a local worker and consume its JSON and exit code. See [CLI](CLI.md). Do not expose it as an unauthenticated web service: Lean contexts and plugins can execute code, and the current isolation allows host reads. Use a dedicated machine/account with only the files needed for the job. A Linux container is not supported by this release and no unisolated fallback is provided.

The included GitHub workflow installs the pinned Lean toolchain, runs Python tests and model-free Lean regressions, and uploads the run evidence as an artifact. It does not install MLX, download weights, train, or measure model accuracy.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `lake` missing | Install Elan and add its bin directory to PATH |
| Sandbox initialization denied | Run in a macOS environment that permits `sandbox-exec`; do not bypass isolation |
| Unknown import | Build the trusted external project with `lake build`, then pass `--project` |
| No matching target | Use the exact qualified theorem name and valid Lean source |
| `CONDITIONAL` | Read `axioms`; prove the assumptions or accept the result as conditional |
| `VERIFIED_STANDARD` but not accepted | Read compiler warnings; strict acceptance rejects them |
| `INFRA_ERROR` | Inspect the run's stderr and reason; never count it as a negative model result |
| MLX import/Metal failure | Use Apple Silicon and a separate MLX environment; model-free verification remains available |
| Corrupt evidence | Keep the damaged record; rerun into a fresh directory rather than editing its hashes |

## Removal

Remove the dedicated environment and checkout when no longer needed. Preserve or export `runs/` first if you need its evidence. No background service, scheduled task, account setting or published site is installed.
