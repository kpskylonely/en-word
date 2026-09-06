#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMAGE="${ENWORD_KYLIN_IMAGE:-enword-kylin-builder}"
ARCH="${ARCH:-amd64}"
case "$ARCH" in
  arm64) PLATFORM="${ENWORD_DOCKER_PLATFORM:-linux/arm64}" ;;
  *) PLATFORM="${ENWORD_DOCKER_PLATFORM:-linux/amd64}" ;;
esac

if [[ ! -f "$ROOT/data/dictionary.db" ]]; then
  echo "Missing data/dictionary.db. Run: npm run db:download" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop for Mac first." >&2
  exit 1
fi

echo "==> Building Linux ${ARCH} builder image (${PLATFORM})..."
docker build --platform "$PLATFORM" \
  -f "$ROOT/packaging/docker/Dockerfile.kylin-build" \
  -t "$IMAGE" \
  "$ROOT"

echo "==> Building Kylin/Ubuntu .deb inside Docker (${PLATFORM}, ${ARCH})..."
docker run --rm --platform "$PLATFORM" \
  -v "$ROOT:/app" \
  -w /app \
  -e ARCH="$ARCH" \
  "$IMAGE" \
  bash -lc '
    set -euo pipefail
    export PYINSTALLER_CONFIG_DIR=/app/build/pyinstaller-cache
    mkdir -p "$PYINSTALLER_CONFIG_DIR"

    # Mac node_modules are not compatible with Linux containers.
    rm -rf node_modules
    npm ci

    rm -rf release/EnWord build/pyinstaller build/deb-root
    bash scripts/build_kylin.sh
  '

echo
echo "Done. Debian package:"
ls -lh "$ROOT"/release/*.deb
