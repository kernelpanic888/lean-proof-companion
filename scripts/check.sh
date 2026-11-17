#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python -m unittest discover -s tests -v
python -m lean_proof_companion doctor
python -m lean_proof_companion selftest
python -m lean_proof_companion verify --source examples/Tasks.lean --name CompanionExample.twice_zero --proof examples/valid.proof
set +e
python -m lean_proof_companion verify --source examples/Tasks.lean --name CompanionExample.twice_zero --proof examples/invalid.proof
code=$?
set -e
[ "$code" -eq 1 ] || exit 1
python -m lean_proof_companion verify --source examples/NoDoubleWrite.lean --name Scorecard.no_double_write --proof examples/no-double-write.proof
