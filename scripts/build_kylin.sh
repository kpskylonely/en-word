#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=scripts/pick_python.sh
source "$ROOT/scripts/pick_python.sh"
PY="$(pick_python)"

VERSION="$(node -p "require('./package.json').version")"
ARCH="${ARCH:-amd64}"
RELEASE_DIR="$ROOT/release"
PYI_WORK="$ROOT/build/pyinstaller"
PYI_CACHE="$ROOT/build/pyinstaller-cache"
export PYINSTALLER_CONFIG_DIR="$PYI_CACHE"
mkdir -p "$PYI_CACHE"
DEB_ROOT="$ROOT/build/deb-root"
DEB_FILE="$RELEASE_DIR/en-word_${VERSION}_${ARCH}.deb"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Kylin/Linux packages must be built on Linux (Kylin/Ubuntu)." >&2
  echo "Copy this project to a Kylin machine and run: npm run pack:kylin" >&2
  exit 1
fi

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

echo "==> Packaging Linux app..."
rm -rf "$RELEASE_DIR/EnWord" "$PYI_WORK"
"$PY" -m PyInstaller packaging/enword.spec \
  --distpath "$RELEASE_DIR" \
  --workpath "$PYI_WORK" \
  --noconfirm

if [[ ! -x "$RELEASE_DIR/EnWord/EnWord" ]]; then
  echo "Expected binary not found: $RELEASE_DIR/EnWord/EnWord" >&2
  exit 1
fi

echo "==> Building .deb package..."
rm -rf "$DEB_ROOT"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/share/en-word"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps"

cp -R "$RELEASE_DIR/EnWord" "$DEB_ROOT/usr/share/en-word/"
install -m 755 packaging/en-word.sh "$DEB_ROOT/usr/bin/en-word"
install -m 644 packaging/en-word.desktop "$DEB_ROOT/usr/share/applications/en-word.desktop"

if [[ -f "$ROOT/packaging/en-word.svg" ]]; then
  install -m 644 "$ROOT/packaging/en-word.svg" \
    "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps/en-word.svg"
fi

cat > "$DEB_ROOT/DEBIAN/control" <<EOF
Package: en-word
Version: ${VERSION}
Section: education
Priority: optional
Architecture: ${ARCH}
Maintainer: EnWord <local@enword>
Depends: libwebkit2gtk-4.1-0 | libwebkit2gtk-4.0-37, libgtk-3-0, libnotify4
Description: Offline vocabulary learning app
 Fully offline English vocabulary trainer with flashcards, quizzes,
 spelling, and wrong-word review. Based on DictionaryData.
EOF

cat > "$DEB_ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications || true
fi
EOF
chmod 755 "$DEB_ROOT/DEBIAN/postinst"

mkdir -p "$RELEASE_DIR"
rm -f "$DEB_FILE"
dpkg-deb --build --root-owner-group "$DEB_ROOT" "$DEB_FILE"

echo
echo "Done."
echo "  Binary dir: $RELEASE_DIR/EnWord"
echo "  Debian pkg: $DEB_FILE"
echo
echo "Install: sudo dpkg -i '$DEB_FILE'"
echo "If dependencies are missing: sudo apt -f install"
