# Trust boundary and security limitations

This is an experimental local research tool, not a hardened executor for arbitrary hostile Lean code.

## Trusted inputs

The Lake project, imports, native plugins, source context and task header are trusted. Source extraction elaborates the supplied Lean file, including reference bodies. Do not point it at an untrusted file or package. The model receives the prefix before the target and its header, never the target's saved reference body; prior permitted declarations may include their proofs.

## Candidate handling

The candidate is parsed as one term. Appended commands, `sorry`, `admit` and `run_tac` syntax are rejected. This is a policy filter, not a proof that every possible effectful Lean feature is eliminated. Compilation and inspection run in separate OS-restricted processes. Each process can write only its own work directory; network access is denied. Process groups are killed after completion or timeout. No fallback executes Lean without the OS restriction.

The profile permits file reads, process operations and Mach lookup. It does **not** prevent reading user files or guarantee protection against resource exhaustion or malicious native dependencies. Do not run with secrets accessible when accepting potentially hostile input. A dedicated machine or disposable macOS VM with only the required files is the appropriate boundary for that use case. The profile has not undergone independent security review.

## Verification decision

Candidate stdout is diagnostic only. A separate Lean inspector imports the compiled module, compares the resulting theorem type with the trusted expected type, and calls `Lean.collectAxioms`. Expected placeholders do not enter the compiled candidate. `sorryAx`, a type mismatch or missing inspection never yields acceptance. User axioms produce `CONDITIONAL`; compiler warnings prevent strict acceptance.

This relies on Lean's kernel, native runtime, the inspector and the integrity of the host toolchain and imported environment. The term-only parser uses the built-in Lean grammar; project-specific syntax extensions may be rejected before compilation.

## Evidence

UUID directories avoid accidental overwrite. SHA-256 manifests and a result seal detect missing or changed files when the seal remains trusted. They are not cryptographic signatures, append-only storage or protection from an attacker who can modify both evidence and hashes. Protect evidence with normal host permissions; externally sign/archive it if stronger provenance is required.

`replay` validates these hashes. It does not recompile or reestablish the truth of a proof. A new `verify` run is needed for a fresh Lean check.

## Reporting

Report non-sensitive issues in the repository issue tracker. For a vulnerability that could expose local data, use GitHub's private vulnerability reporting if enabled; otherwise request a private contact without posting exploit data or credentials. No response-time or production support guarantee is provided.
