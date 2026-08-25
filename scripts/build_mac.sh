#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/pick_python.sh
source "$ROOT/scripts/pick_python.sh"
PY="$(pick_python)"

VERSION="$(node -p "require('./package.json').version")"
RELEASE_DIR="$ROOT/release"
PYI_WORK="$ROOT/build/pyinstaller"
PYI_CACHE="$ROOT/build/pyinstaller-cache"
export PYINSTALLER_CONFIG_DIR="$PYI_CACHE"
mkdir -p "$PYI_CACHE"

echo "==> Checking dictionary database..."
if [[ ! -f "$ROOT/data/dictionary.db" ]]; then
  echo "Missing data/dictionary.db. Run: npm run db:download" >&2
  exit 1
fi

echo "==> Building frontend..."
npm run build

echo "==> Using Python: $PY ($("$PY" --version))"
echo "==> Installing build dependencies..."
"$PY" -m pip install -q -r requirements-build.txt

echo "==> Packaging macOS app (this may take a few minutes)..."
rm -rf "$RELEASE_DIR" "$PYI_WORK"
"$PY" -m PyInstaller packaging/enword.spec \
  --distpath "$RELEASE_DIR" \
  --workpath "$PYI_WORK" \
  --noconfirm

APP="$RELEASE_DIR/EnWord.app"
DMG="$RELEASE_DIR/EnWord-${VERSION}-mac.dmg"

if [[ ! -d "$APP" ]]; then
  echo "Expected app bundle not found: $APP" >&2
  exit 1
fi

echo "==> Creating DMG..."
rm -f "$DMG"
hdiutil create \
  -volname "离线背单词" \
  -srcfolder "$APP" \
  -ov \
  -format UDZO \
  "$DMG" >/dev/null

echo
echo "Done."
echo "  App: $APP"
echo "  DMG: $DMG"
echo
echo "Install: open the DMG and drag EnWord.app to Applications."
