#!/bin/sh
set -eu
lpc_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$lpc_directory"
if [ -n "${LPC_PYTHON:-}" ]; then
  lpc_python="$LPC_PYTHON"
elif [ -f "$lpc_directory/.local-dialog.json" ]; then
  lpc_python=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("python","python3.11"))' "$lpc_directory/.local-dialog.json")
elif [ -x "$lpc_directory/.venv-mlx/bin/python" ]; then
  lpc_python="$lpc_directory/.venv-mlx/bin/python"
else
  lpc_python=python3.11
fi
exec "$lpc_python" -m lean_proof_companion serve "$@"
