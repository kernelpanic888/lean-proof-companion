# Release procedure

1. Update version in `pyproject.toml`, `lean_proof_companion/__init__.py`, changelog and release notes.
2. Install into a new Python environment from a clean source checkout.
3. Run `./scripts/check.sh`; retain full evidence locally and publish a scrubbed validation summary.
4. Check documentation links, wheel contents, dependency declarations and tracked files for private paths, credentials, weights and archives.
5. Commit, push and wait for the macOS CI workflow on that exact commit. An unrun or failed workflow is not a pass.
6. Create a prerelease tag and attach the source distribution, wheel, SHA256SUMS and validation summary. Bind the validation summary to the exact source commit. Treat these archives as unsigned artifacts unless signatures are explicitly provided.
7. Confirm the published tag resolves to the tested commit and assets can be downloaded and match their hashes.

Use a prerelease until the roadmap items required for a stable release have their own evidence. Never carry historical model scores into new release acceptance. Documentation-only follow-ups should state which evidence remains applicable.
