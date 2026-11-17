#!/bin/bash
# Installiert alles, was die Engine braucht: ffmpeg (mit rubberband), Blender, Python-Pakete,
# Piper + deutsche Stimmen (Offline-Fallback zu ElevenLabs). Idempotent: Fertiges wird übersprungen.
# Wird von .claude/settings.json bei jedem Sitzungsstart aufgerufen, geht aber auch von Hand: ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

BLENDER_VERSION="${BLENDER_VERSION:-5.1.2}"
BLENDER_DIR="/opt/blender-${BLENDER_VERSION}"
PIPER_DIR="${PIPER_DIR:-/opt/piper-voices}"
PIPER_VOICES=("de_DE-thorsten-high" "de_DE-kerstin-low")   # Kalle, Byte
log() { echo "[setup] $*" >&2; }

# ---------------------------------------------------------------- System-Pakete
need_apt=()
command -v ffmpeg >/dev/null || need_apt+=(ffmpeg)
command -v xz >/dev/null || need_apt+=(xz-utils)
command -v rubberband >/dev/null || need_apt+=(rubberband-cli)   # Tempo/Tonhöhe, falls ffmpeg ohne rubberband-Filter
for p in libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 libegl1; do
  dpkg -s "$p" >/dev/null 2>&1 || need_apt+=("$p")
done
if [ ${#need_apt[@]} -gt 0 ]; then
  log "apt: ${need_apt[*]}"
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${need_apt[@]}" >/dev/null
fi

# ---------------------------------------------------------------- Blender
if [ ! -x "$BLENDER_DIR/blender" ]; then
  mm="${BLENDER_VERSION%.*}"
  url="https://download.blender.org/release/Blender${mm}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"
  log "Blender ${BLENDER_VERSION} laden …"
  tmp="$(mktemp -d)"
  curl -fsSL --retry 4 "$url" -o "$tmp/b.tar.xz"
  mkdir -p "$BLENDER_DIR"
  tar -xJf "$tmp/b.tar.xz" -C "$BLENDER_DIR" --strip-components=1
  rm -rf "$tmp"
fi
ln -sf "$BLENDER_DIR/blender" /usr/local/bin/blender

# ---------------------------------------------------------------- Python
pyhashes="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.ki-staunen-setup.sha256"
if ! sha256sum --check --status "$pyhashes" 2>/dev/null; then
  rm -f "$pyhashes"
  log "pip install -r requirements.txt"
  python3 -m pip install -q --disable-pip-version-check -r requirements.txt
  sha256sum setup.sh requirements.txt > "$pyhashes"
fi

# ---------------------------------------------------------------- Piper-Stimmen (Fallback)
mkdir -p "$PIPER_DIR"
hf="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE"
for v in "${PIPER_VOICES[@]}"; do
  [ -s "$PIPER_DIR/$v.onnx" ] && continue
  name="${v#de_DE-}"; spk="${name%-*}"; q="${name##*-}"
  log "Piper-Stimme $v laden …"
  curl -fsSL --retry 4 "$hf/$spk/$q/$v.onnx" -o "$PIPER_DIR/$v.onnx.part" \
    && curl -fsSL --retry 4 "$hf/$spk/$q/$v.onnx.json" -o "$PIPER_DIR/$v.onnx.json" \
    && mv "$PIPER_DIR/$v.onnx.part" "$PIPER_DIR/$v.onnx" \
    || { rm -f "$PIPER_DIR/$v.onnx.part"; log "WARNUNG: $v nicht geladen (nur ElevenLabs verfügbar)"; }
done

# ---------------------------------------------------------------- Sitzung
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  { echo "export BLENDER=$BLENDER_DIR/blender"; echo "export PIPER_DIR=$PIPER_DIR"; } >> "$CLAUDE_ENV_FILE"
fi
log "fertig: $(blender --version 2>/dev/null | head -1), $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
