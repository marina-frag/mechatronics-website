#!/usr/bin/env bash
# Αυτόματη συναρμολόγηση του Spot:
#   SPOT_assembly_solids.FCStd (της ομάδας, μόνο ανάγνωση) → SPOT_assembly_auto.FCStd (νέο αρχείο)
#
#   ./run.sh            # εξαγωγή γεωμετρίας, υπολογισμός θέσεων, εγγραφή .FCStd, έλεγχος συγκρούσεων
# Μετά: (cd ~/mechatronics_web && npm run glb)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
D="$HOME/Spot_NTUA/3D Design/full-assembly"
SRC="${SPOT_SRC:-$D/SPOT_assembly_solids.FCStd}"
DST="${SPOT_DST:-$D/SPOT_assembly_auto.FCStd}"
BUILD="$HERE/../../pipeline/build/probe"
VERIFY="$HERE/../../pipeline/build/verify"

export_geo() {  # $1 = .FCStd, $2 = φάκελος εξόδου
  mkdir -p "$2"
  SPOT_INCLUDE_HIDDEN=1 SPOT_FCSTD="$1" SPOT_BUILD_DIR="$(cd "$2" && pwd)" \
    freecad.cmd "$HERE/../../pipeline/freecad_export.py" 2>&1 | grep -E "^\[freecad_export\] (Εξαρτήματα|OK)" || true
}

echo "== 1/4 Εξαγωγή γεωμετρίας από $(basename "$SRC")"
export_geo "$SRC" "$BUILD"

echo "== 2/4 Υπολογισμός θέσεων"
(cd "$HERE" && rm -rf cache && python3 auto_assemble.py all | tail -4)

echo "== 3/4 Εγγραφή $(basename "$DST")"
SPOT_SRC="$SRC" SPOT_DST="$DST" SPOT_PLACEMENTS="$HERE/placements.json" SPOT_RENAMES="$HERE/renames.json" \
  SPOT_MIRRORS="$HERE/mirrors.json" \
  freecad.cmd "$HERE/freecad_apply.py" 2>&1 | grep -E "^\[freecad_apply\]|Error|Traceback"

echo "== 4/4 Έλεγχος συγκρούσεων στο $(basename "$DST") (βάθος > 1.5 mm)"
export_geo "$DST" "$VERIFY"
(cd "$HERE" && SPOT_GEO_BUILD="$(cd "$VERIFY" && pwd)" python3 check_all.py 1.5 --as-built)
