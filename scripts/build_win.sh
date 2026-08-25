#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN* | *_NT*)
    ;;
  *)
    echo "Windows packages must be built on Windows." >&2
    echo "Push to GitHub to build .exe via Actions, or run on a Windows machine." >&2
    exit 1
    ;;
esac

if [[ -n "${PYTHON:-}" ]] && command -v "$PYTHON" >/dev/null 2>&1; then
  PY="$PYTHON"
elif command -v python >/dev/null 2>&1; then
  PY="python"
elif command -v py >/dev/null 2>&1; then
  PY="py"
  PY_ARGS=(-3)
else
  echo "Python 3.9+ is required. Set PYTHON=/path/to/python" >&2
  exit 1
fi

run_python() {
  if [[ -n "${PY_ARGS:-}" ]]; then
    "$PY" "${PY_ARGS[@]}" "$@"
  else
    "$PY" "$@"
  fi
}

VERSION="$(node -p "require('./package.json').version")"
RELEASE_DIR="$ROOT/release"
PYI_WORK="$ROOT/build/pyinstaller"
PYI_CACHE="$ROOT/build/pyinstaller-cache"
export PYINSTALLER_CONFIG_DIR="$PYI_CACHE"
mkdir -p "$PYI_CACHE"

ZIP="$RELEASE_DIR/EnWord-${VERSION}-win.zip"
EXE="$RELEASE_DIR/EnWord/EnWord.exe"

echo "==> Checking dictionary database..."
if [[ ! -f "$ROOT/data/dictionary.db" ]]; then
  echo "Missing data/dictionary.db. Run: npm run db:download" >&2
  exit 1
fi

echo "==> Building frontend..."
npm run build

echo "==> Using Python: $PY ($(run_python --version))"
echo "==> Installing build dependencies..."
run_python -m pip install -q -r requirements-build.txt

echo "==> Packaging Windows app (this may take a few minutes)..."
rm -rf "$RELEASE_DIR/EnWord" "$PYI_WORK"
run_python -m PyInstaller packaging/enword.spec \
  --distpath "$RELEASE_DIR" \
  --workpath "$PYI_WORK" \
  --noconfirm

if [[ ! -f "$EXE" ]]; then
  echo "Expected binary not found: $EXE" >&2
  exit 1
fi

echo "==> Creating zip archive..."
rm -f "$ZIP"
(
  cd "$RELEASE_DIR"
  tar -a -c -f "EnWord-${VERSION}-win.zip" EnWord
)

echo
echo "Done."
echo "  App dir: $RELEASE_DIR/EnWord"
echo "  Exe:     $EXE"
echo "  Zip:     $ZIP"
echo
echo "Install: unzip and run EnWord.exe (requires WebView2 runtime on Windows)."
