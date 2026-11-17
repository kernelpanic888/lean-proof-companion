# CLI reference and integration

`lean-proof-companion` and `python -m lean_proof_companion` expose the same commands. Run `--help` or `COMMAND --help` for arguments.

| Command | Purpose |
| --- | --- |
| `doctor [--project PATH]` | Check Python, Lean version and actual restricted worker startup |
| `verify --source FILE --name NAME --proof FILE` | Check a saved proof term against one trusted source theorem |
| `prove --source FILE --name NAME --model DIR [--adapter DIR] [--attempts 1..3]` | Generate and check candidates; experimental MLX integration |
| `replay DIRECTORY` | Verify saved file and result hashes, without invoking Lean |
| `selftest [--runs DIR]` | Run model-free integration regressions and negative controls |

`verify` and `prove` accept `--project PATH` and `--runs PATH`. Default project: the source checkout. Default evidence location: `./runs` relative to your working directory. A target must be a fully qualified theorem name. Only supported simple `:=` theorem bodies are extracted; unsupported input fails explicitly. The entire trusted source must elaborate successfully. A reference body or a `by sorry` placeholder is allowed in the trusted source, but no placeholder is accepted in a candidate.

## Proof files

Supply a complete term:

```lean
by
  rfl
```

`verify` deliberately does not strip prose or markdown. The experimental model path can extract an outer fence or a matching complete declaration, then checks only its proof in the original header. Ambiguous fences or changed headers fail.

## Automation

Capture stdout as JSON and check the exit code. `verify` prints a result object including `directory`, `task_id`, `task_name`, `status`, `accepted`, `lean_version`, `axioms`, diagnostics and file hashes. Some infrastructure errors go to stderr as a JSON object. Do not decide acceptance by searching for `PASS` in logs. For a successful proof, require exit code 0 and `accepted == true`.

`prove` writes an `evaluation-*.json` report and prints its contents with its path. The report separates `first_attempt_pass` and `repaired_pass`. Each attempt also has a separate run and generation metadata: budget, observed tokens, finish reason, elapsed time, mode and model-manifest digest. `length` means the budget was exhausted, not that a proof was complete.

Exit 0 for `replay` means the supplied manifest matched its files; it does not mean the saved result was accepted. Read the saved `accepted` field. Similarly, `selftest` means the harness controls passed, not that every intentional invalid candidate was accepted.

## Evidence layout

```text
runs/
  latest.json                 # convenience pointer, not the evidence itself
  <timestamp>-<uuid>/
    task.json                 # fixed task, including trusted context/header
    generation.json
    raw.txt
    proof.txt
    Candidate.lean
    Expected.lean             # isolated expected-type stub
    term/
    compile/
    inspection/audit.json     # exists after successful compilation/inspection
    result.json
    seal.json
```

Failed candidates may have no compile or inspection artifact. That never yields acceptance. Parsing and model manifests live alongside attempt directories. `latest.json` changes with each run and is not an archive. Keep the referenced directory and the model manifest when exporting evidence.

The saved TaskSpec can include a reference field; it is local provenance, not part of task identity and not sent to the generator. Avoid exporting private theorem sources without reviewing them.
