# Contributing

Start with the model-free installation in README and run `./scripts/check.sh`. Include a minimal trusted Lean source and candidate term for a bug report; remove private data from evidence first.

Changes to acceptance policy need a negative control demonstrating the previous false acceptance and a positive control preserving a legitimate proof. Do not replace the fixed theorem with a model-proposed statement, trust candidate stdout for audits, or silently execute without the OS restriction.

Document platform/toolchain requirements and distinguish executed checks from intended checks. Model or training changes require their own provenance and evaluation; verifier tests do not measure model quality. Do not commit weights, adapters, chat archives, tokens, virtual environments, build caches or private run evidence.

Contributions are under Apache-2.0. The project currently has no production support or release schedule guarantee.
