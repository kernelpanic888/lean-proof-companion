# Local dialogue preview validation · 2026-11-18

Code commit: `15e29574a63dadc31259f98b2496053a42b8b7b2` (later documentation-only commits do not change this tested code).

- Six Python unit tests passed, including periodic-repetition rejection.
- Sixteen model-free Lean negative/positive controls passed locally and in GitHub CI: https://github.com/kernelpanic888/lean-proof-companion/actions/runs/44208825347 .
- Independent reader checks passed: https://github.com/kernelpanic888/lean-proof-companion/actions/runs/44208825259 . All106496 finite reference transitions remain equal.
- Real local Qwen loading, chat-template rendering, startup generation and Lean process probe passed.
- Five small Russian dialogue checks exercised arithmetic, Lean explanation, the occupied-category question, acknowledgement of no Lean execution and a history recall question. They completed without the previous periodic loop. This is smoke coverage, not a language-model accuracy benchmark; proposed code remains unverified.
- API requests lacking local session authorization were rejected.
- A correct proof was accepted and a wrong proof was rejected through the local API. The reader UI also exercises a separate reviewed proof action.
- Independent direct Lean invocation outside the companion accepted a reflexivity proof, rejected a false proof and rejected sorry with warnings treated as errors.
- One real DeepSeek/LoRA UI proof-generation request exhausted its three attempts; all three candidates were rejected. This is not recorded as a model success. No adapter change or training was performed.
- Public reader profile omits network API code; local requests are enabled only in a loopback-served page with a per-launch session. Public profile and homepage publication checks passed.

The local MLX environment was reused. Fresh ML dependency restoration, independent model benchmarking and a hostile-input security audit are not certified. Dialogue logs and local model paths stay outside Git. The parent R01–R18 status remains NEEDS_REWORK.
