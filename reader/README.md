# PC-01 · Lean Proof Companion reader

Self-contained RU/EN research reader. Open `dist/index.html` in a browser; its styles, scripts, author background, Lean capsule, seven recorded-check snapshots, release passport and all 106,496 Lean-exported reference transitions are embedded. Reading and local interactions do not require a server or network. Installing Lean or downloading model dependencies is a separate online step.

The page explains why a proof companion is useful, its trust boundaries, local installation, optional model generation and the published alpha release. It includes a small scorecard lab and four Lean-checked theorems. The lab does not claim to verify the complete MG-01 engine or model quality. Lean is not executed in the browser.

## Build and check

```sh
python3.11 build.py
node check.cjs
```

`model.js` is the actual finite browser implementation. `research/oracle.ndjson` contains 8192 rows × 13 results exported by Lean. `check.cjs` compares all transitions and checks the HTML anchors and standalone boundary. To regenerate the oracle, run `lake env lean --run research/Oracle.lean > research/oracle.ndjson` from the parent proof-companion checkout with its pinned toolchain, adjusting the file path. The `Oracle.lean` snapshot includes the capsule plus its output driver.

To recheck the four proof bodies, use the released companion on `research/Scorecard.lean` with each fully qualified theorem name and its body; the audit lists those names. The source contains no placeholders. `research/capsule-audit.json` records the original proof checks; `research/browser-checks.json` describes executed UI checks and limits. Hashes are unsigned local integrity records.

The embedded author artwork is inherited from the author's MI-01 reader without modifying the JPEG bytes. No new portrait or replacement art was generated. Layout uses the established green/gold palette, serif headings and monospaced technical notation. System fonts only; no CDN, iframe, fetch, external runtime or telemetry.

Published tool release: https://github.com/kernelpanic888/lean-proof-companion/releases/tag/v0.1.0-alpha.1 . This reader is a separately versioned documentation addition; it does not retroactively change that release's verifier checks. The parent R01–R18 remediation remains NEEDS_REWORK.
