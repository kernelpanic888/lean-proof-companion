# Changelog

## Unreleased · 0.2.0.dev0

- Local reader chat with a separate Qwen dialogue model, explicit NOT_RUN metadata, history and periodic-repetition detection.
- Loopback service with startup probes, Host/Origin/session checks, reviewed Lean verification and DeepSeek generation.
- Separate local/public reader profiles; public pages do not contact local services automatically.
- Foreground launcher and pinned model setup instructions. DeepSeek weights and working LoRA unchanged.


## 0.1.0-alpha.1 — 2026-11-18

Initial standalone research prerelease.

- Fixed TaskSpec context and Lean-syntax theorem extraction.
- Separate Lean type/axiom inspection and strict warning policy.
- Restricted macOS workers with separate write directories and process-group cleanup.
- Per-attempt records, SHA-256 manifests, integrity replay and raw diagnostics.
- Model-free CLI, examples and negative-control selftests.
- Experimental local MLX generation and three-attempt repair with explicit Base/LoRA configuration.
- Installation, deployment, architecture, trust limits, Russian guide and release procedure.

Model GPU validation, training and the parent 18-item remediation are not certified by this release.
