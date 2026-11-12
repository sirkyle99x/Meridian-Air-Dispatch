#!/usr/bin/env bash
# Fetch the frozen OurAirports snapshot the golden tests are baselined against.
# Commit 97afc8b is byte-identical to the live data of 12 NOV 2026, the day the
# expected values were observed. The sha256 check fails loudly if the files are
# ever not what the baseline assumes.
set -euo pipefail
SHA=97afc8b3ee4711d70199fda73bdd66df9fd58cb8
DEST="${1:-tests/data}"
mkdir -p "$DEST"
for f in airports runways; do
  curl -fsS -o "$DEST/$f.csv" \
    "https://raw.githubusercontent.com/davidmegginson/ourairports-data/$SHA/$f.csv"
done
cd "$DEST"
sha256sum -c - <<'SUMS'
11e7a1edf9e5bef91aa4492e3ab42bb5b38b5f2df81358a235ed5a393a571e54  airports.csv
a20681ecd8375543db4830618f71a56fcb04cb63b6608514c1b17f1963b3fca8  runways.csv
SUMS
