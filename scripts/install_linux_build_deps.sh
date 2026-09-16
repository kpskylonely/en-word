#!/usr/bin/env bash
# Install Python build deps inside Linux/Kylin builder (Docker or native).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Python not found: $PY" >&2
  exit 1
fi

echo "==> Python: $("$PY" --version)"
echo "==> Upgrading pip..."
"$PY" -m pip install --quiet --upgrade pip wheel

echo "==> Installing Linux build requirements..."
"$PY" -m pip install --quiet -r requirements-build-linux.txt

echo "==> Verifying pywebview GTK import..."
"$PY" - <<'PY'
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: F401
import webview  # noqa: F401
print("pywebview/gi OK")
PY
