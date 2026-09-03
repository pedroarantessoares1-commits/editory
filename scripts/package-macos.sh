#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Este empacotador precisa rodar em macOS ou no runner macOS do GitHub Actions." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js nao encontrado. Instale Node 22 antes de empacotar." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 nao encontrado. Instale Python 3.11+ antes de empacotar." >&2
  exit 1
fi

VERSION="$(node -p "require('./package.json').version")"
RELEASE_DIR="releases/v${VERSION}"
DIST_DIR="${DIST_DIR:-dist}"
STAGE_DIR="${DIST_DIR}/macos-arm64-share"
PACKAGE_PATH="${DIST_DIR}/Editory-${VERSION}-macos-arm64-share.zip"
CHECKSUMS_PATH="${DIST_DIR}/SHA256SUMS-macos-arm64.txt"

if [[ ! -f "${RELEASE_DIR}/release-notes.md" ]]; then
  echo "Notas de release nao encontradas: ${RELEASE_DIR}/release-notes.md" >&2
  exit 1
fi

if [[ ! -f "${RELEASE_DIR}/manifest.json" ]]; then
  echo "Manifesto de release nao encontrado: ${RELEASE_DIR}/manifest.json" >&2
  exit 1
fi

echo "== Instalando dependencias desktop =="
npm ci

echo "== Preparando runtime Python =="
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "== Limpando caches do runtime Python =="
find .venv -type d -name "__pycache__" -prune -exec rm -rf {} +
find .venv -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

echo "== Checando arquivos desktop/web =="
npm run check:web
npm run check:desktop

echo "== Gerando DMG e ZIP macOS arm64 =="
CSC_IDENTITY_AUTO_DISCOVERY=false npm run build:mac

echo "== Montando pacote compartilhavel =="
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

find "$DIST_DIR" -maxdepth 1 -type f \( \
  -name "*.dmg" -o \
  -name "*.zip" -o \
  -name "*.blockmap" -o \
  -name "latest*.yml" \
\) ! -name "*macos-arm64-share.zip" -print0 | while IFS= read -r -d '' artifact; do
  cp "$artifact" "$STAGE_DIR/"
done

cp "${RELEASE_DIR}/release-notes.md" "$STAGE_DIR/RELEASE-NOTES.md"
cp "${RELEASE_DIR}/manifest.json" "$STAGE_DIR/manifest.json"

(
  cd "$STAGE_DIR"
  shasum -a 256 * > "../$(basename "$CHECKSUMS_PATH")"
)
cp "$CHECKSUMS_PATH" "$STAGE_DIR/"

rm -f "$PACKAGE_PATH"
(
  cd "$STAGE_DIR"
  /usr/bin/zip -r "../$(basename "$PACKAGE_PATH")" .
)

echo "Pacote pronto: ${PACKAGE_PATH}"
echo "Checksums: ${CHECKSUMS_PATH}"
