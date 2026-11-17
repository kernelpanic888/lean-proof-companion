# Release validation

Release: **0.1.0-alpha.1**, 2026-11-18.

The release validation report attached to the GitHub prerelease records the exact tested commit, executed commands, test results and artifact hashes. Consult that report and the GitHub workflow for actual outcomes; the presence of this document is not itself a successful check.

Required model-free controls:

- correct proof accepted, wrong proof rejected;
- changed theorem header and appended declarations rejected;
- `sorry`/`admit` rejected;
- user axiom classified as conditional, even with misleading candidate trace;
- old evidence survives later runs, modified evidence rejected;
- fixture repair receives diagnostics and succeeds on its second attempt;
- namespace/section/variable/inner `let` and intermediate definition preserved;
- empty target source rejected;
- valid and invalid documented examples have expected exit codes.

A local Base/LoRA generation smoke on one toy task was run in the existing MLX environment. Both exhausted 512 tokens; Base was rejected, and the extracted LoRA proof was accepted on standard axioms without warnings. This is not an independent benchmark.

Not run as part of this release: a fresh MLX environment install, independent model benchmark, training, full parent MG-01 acceptance, hostile-input security audit, Linux support. Historical parent results are not inherited as release results.

Local integrity hashes are not independently signed attestations. See [SECURITY](../SECURITY.md).
