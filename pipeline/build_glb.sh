#!/usr/bin/env bash
# FreeCAD συναρμολόγηση → spot.glb
#
#   ./build_glb.sh                       # προεπιλογή: SPOT_assembly_auto.FCStd (αυτόματη συναρμολόγηση)
#   ./build_glb.sh /path/αρχείο.FCStd    # άλλο αρχείο
#   ./build_glb.sh "" --budget 250000    # επιπλέον επιλογές για το Blender
#                                        # (--budget N, --no-draco, --no-blend)
# Έξοδος: out/spot.glb, out/spot.blend, out/spot_report.json
# και, αν υπάρχει το site δίπλα, αντίγραφο στο ../public/models/spot.glb
# μαζί με εικόνα ../public/projects/spot/render.png
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FCSTD="${1:-$HOME/Spot_NTUA/3D Design/full-assembly/SPOT_assembly_auto.FCStd}"
[ -z "$FCSTD" ] && FCSTD="$HOME/Spot_NTUA/3D Design/full-assembly/SPOT_assembly_auto.FCStd"
shift || true
BUILD="$HERE/build"
OUT="${SPOT_OUT:-$HERE/out/spot.glb}"

command -v freecad.cmd >/dev/null || { echo "Δεν βρέθηκε το freecad.cmd (sudo snap install freecad)"; exit 1; }
command -v blender >/dev/null     || { echo "Δεν βρέθηκε το blender (sudo snap install blender --classic)"; exit 1; }
[ -f "$FCSTD" ] || { echo "Δεν υπάρχει το αρχείο: $FCSTD"; exit 1; }

mkdir -p "$BUILD"
rm -f "$BUILD/manifest.json" "$BUILD/export_error.txt"

echo "== 1/2 FreeCAD: εξαγωγή εξαρτημάτων"
SPOT_FCSTD="$FCSTD" SPOT_BUILD_DIR="$BUILD" freecad.cmd "$HERE/freecad_export.py" 2>&1 \
  | grep --line-buffered -E "^\[freecad_export\]|Error|Traceback|^  File" || true
if [ ! -f "$BUILD/manifest.json" ]; then
  echo "Η εξαγωγή από το FreeCAD απέτυχε."
  [ -f "$BUILD/export_error.txt" ] && cat "$BUILD/export_error.txt"
  exit 1
fi

SITE="$(cd "$HERE/.." && pwd)/public"
EXTRA=()
[ -d "$SITE" ] && EXTRA=(--cover "$SITE/projects/spot/render.png")

echo "== 2/2 Blender: καθάρισμα και εξαγωγή .glb"
blender -b --factory-startup -P "$HERE/blender_build_glb.py" -- \
  --build "$BUILD" --config "$HERE/spot_parts.json" --out "$OUT" "${EXTRA[@]}" "$@" 2>&1 \
  | grep --line-buffered -E "^\[blender_build\]|Error|Traceback|^  File"

if [ -d "$SITE" ]; then
  mkdir -p "$SITE/models"
  cp "$OUT" "$SITE/models/spot.glb"
  echo "== Το site χρησιμοποιεί πλέον το νέο μοντέλο: public/models/spot.glb"
fi
