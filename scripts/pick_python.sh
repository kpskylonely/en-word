#!/usr/bin/env bash
# Resolve a Python 3.9+ interpreter for packaging.
pick_python() {
  if [[ -n "${PYTHON:-}" ]] && command -v "$PYTHON" >/dev/null 2>&1 \
    && "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "$PYTHON"
    return 0
  fi
  for candidate in python3.12 python3.11 python3.10 python3.9 /usr/bin/python3 /usr/local/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
      echo "$candidate"
      return 0
    fi
  done
  echo "Python 3.9+ is required for packaging. Set PYTHON=/path/to/python3.9+" >&2
  exit 1
}
