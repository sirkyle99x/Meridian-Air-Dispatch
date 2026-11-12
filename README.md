# Meridian Air Dispatch

`dispatch_calc.py` is the candidate math for the Meridian Air Dispatch Claude
project: block times, scoring, legality and card fields for a story-driven MSFS
charter board. The rules and state that drive it live in the Claude project
(`claude/RULES.md`, `dispatch_state.md`), not here.

Sessions fetch the script at a **version tag** (e.g. `v7.0`), never `main`, so
work in progress on `main` cannot reach a board. The script's `SCRIPT_VERSION`
must equal the RULES.md version; `--expect` enforces it at run time.

## Tests

`tests/run_golden.py` runs the golden cases against frozen inputs — a fixture
state file, an OurAirports snapshot pinned by commit and sha256, and pinned
packages — so a result moves only when the script does. The `golden tests`
GitHub Action runs them on every push.

```
pip install -r tests/requirements.txt
bash tests/fetch_data.sh
python3 tests/run_golden.py
```

Changing an expected value is a deliberate re-baseline, recorded in the
project's ARCHIVE.md → CHANGE CONTROL, never a quiet edit to make a test pass.
