#!/usr/bin/env python3
"""Golden tests for dispatch_calc.py (IMPLEMENTATION_PLAN.md §5, G1–G17).

Frozen inputs, so a result changes only when the script changes:
  - state:   tests/fixtures/dispatch_state.md (the 12 NOV 2026 state file)
  - airports: OurAirports commit 97afc8b, fetched by tests/fetch_data.sh and
             checked by sha256 (byte-identical to the 12 NOV live data)
  - packages: tests/requirements.txt
  - date:    --date 12NOV26 wherever the date matters

Run from the repo root:
    pip install -r tests/requirements.txt
    bash tests/fetch_data.sh
    python3 tests/run_golden.py                 # all cases
    python3 tests/run_golden.py --update-snapshot   # re-baseline G1 on purpose

A changed expectation is a deliberate re-baseline, never a quiet edit: see
ARCHIVE.md → CHANGE CONTROL. Exits non-zero on any failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "dispatch_calc.py")
STATE = os.path.join(ROOT, "tests", "fixtures", "dispatch_state.md")
DATA = os.environ.get("DISPATCH_TEST_DATA", os.path.join(ROOT, "tests", "data"))
UPDATE_SNAPSHOT = "--update-snapshot" in sys.argv
if not os.path.exists(os.path.join(DATA, "airports.csv")):
    sys.exit(f"no airport data in {DATA} — run: bash tests/fetch_data.sh")
TMP = tempfile.mkdtemp(prefix="dispatch_g_")
results = []


def run(*args, doc=STATE, data=DATA):
    cmd = [sys.executable, SCRIPT, "--doc", doc, "--data", data, *args]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def finalize(picks, *extra, doc=STATE):
    path = os.path.join(TMP, "picks.json")
    with open(path, "w") as fh:
        json.dump(picks, fh)
    rc, out, err = run("--finalize", path, *extra, doc=doc)
    try:
        return rc, json.loads(out), err
    except ValueError:
        return rc, None, err + out


def check(gid, desc, cond, detail=""):
    results.append((gid, cond))
    print(f"{'PASS' if cond else 'FAIL'}  {gid:<4} {desc}"
          + (f"\n        {detail}" if detail and not cond else ""))


def state_variant(name, old, new):
    text = open(STATE, encoding="utf-8").read()
    assert old in text, f"fixture edit not found: {old[:40]}"
    path = os.path.join(TMP, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new, 1))
    return path


# G1 --rules
rc, out, _ = run("--rules")
snap = os.path.join(ROOT, "tests", "rules.snapshot")
if UPDATE_SNAPSHOT:
    with open(snap, "w") as fh:
        fh.write(out)
    print(f"snapshot rewritten: {snap}")
check("G1", "--rules matches stored snapshot, v7.0, no retired components",
      rc == 0 and out == open(snap).read() and "v7.0" in out
      and "model rotation" not in out and "verified event" not in out
      and "Sun window" in out and "override H25B" in out)

# G2 manifest
rc, out, _ = run("--tail", "N13SY", "--hours", "2.5", "--date", "12NOV26", "--table")
want = "state: 22 tails (20 active) · 11 models · 56 register · 6/6 logbook rows"
check("G2", "manifest line", rc == 0 and want in out, out.splitlines()[0] if out else "")

# G3 recency and region now live (scored directly; KJAC/KPUB/KSAF sit far
# outside a 2.5 h ring from KDJT, so the components are read off the scorer)
sys.path.insert(0, ROOT)
import dispatch_calc as dc  # noqa: E402
doc = dc.Doc(STATE)
aps = dc.load_airports(DATA)
hist = dc.build_history(doc, aps)
tail = next(f for f in doc.fleet if f["tail"] == "N13SY")
lim = doc.limits_for(tail["model"])


def parts(ident):
    a = aps[ident]
    return dc.score_candidate(a, tail, lim, doc, hist, 2.0, 2.0,
                              dc.region_of(a, doc), aps[tail["home"]],
                              aps[tail["current"]])["parts"]


p_saf, p_jac, p_pub = parts("KSAF"), parts("KJAC"), parts("KPUB")
check("G3", "Southwest region −15, KJAC recency −50, KPUB recency −20",
      p_saf["region"] == -15 and p_jac["recency"] == -50
      and p_pub["recency"] == -20,
      f"KSAF {p_saf} KJAC {p_jac} KPUB {p_pub}")

# G4 band at 1.5 / 2.5 / 4 h, named runs across every class
bad = []
for hours in ("1.5", "2.5", "4"):
    for cls in ("turboprop", "mid_jet", "large_jet"):
        rc, out, _ = run("--class", cls, "--hours", hours, "--date", "12NOV26",
                         "--json")
        if rc not in (0, 2):
            bad.append(f"{cls} {hours}h exit {rc}")
            continue
        if rc == 2:
            continue
        payload = json.loads(out)
        ceil = payload["ceiling_h"]
        for c in payload["candidates"]:
            if c.get("fallback") or c["in_market"] or c["dest"] == c["home"]:
                continue
            m = (c["block_h"] - ceil) * 60
            if not -15.01 <= m <= 5.01:
                bad.append(f"{c['tail']}→{c['dest']} {m:+.1f} min at {hours}h")
check("G4", "every non-exempt block within ceiling −15/+5 min", not bad,
      "; ".join(bad[:5]))

# G5 home leg reported, in-band
rc, out, _ = run("--tail", "N610CD", "--hours", "3.5", "--date", "12NOV26", "--json")
cands = json.loads(out)["candidates"] if rc == 0 else []
home = [c for c in cands if c["dest"] == "KLGB"]
check("G5", "N610CD 3.5 h: KLGB reported with fullness +20",
      bool(home) and home[0]["score_parts"]["fullness"] == 20,
      f"exit {rc}, home rows {home[:1]}")

# G6 Duke at home, window too long
rc, out, err = run("--tail", "N80WE", "--hours", "4", "--date", "12NOV26", "--table")
check("G6", "N80WE 4 h: left off this board, exit 2",
      rc == 2 and "left off this board" in err, f"exit {rc} {err.strip()[:120]}")

# G7 amphibian parked inland: fallback ferry
st = state_variant("g7.md", "| PALH | PALH | 0 |", "| PALH | KELP | 1 |")
rc, out, _ = run("--tail", "N828DC", "--hours", "2.5", "--date", "12NOV26",
                 "--json", doc=st)
payload = json.loads(out) if rc == 0 else {"candidates": [], "notes": []}
fb = [c for c in payload["candidates"] if c.get("fallback")]
ok = (len(payload["candidates"]) == 1 and len(fb) == 1 and fb[0]["dest"] == "KGNT"
      and fb[0]["gc_nm"] == 216 and fb[0]["block"] == "2h 03m"
      and any("ferry leg toward PALH" in n for n in payload["notes"]))
check("G7", "N828DC at KELP: one fallback to KGNT, 216 nm, 2h 03m, with note", ok,
      json.dumps(fb)[:200])

# G8 night departure crossing UTC midnight
rc, j, _ = finalize([{"tail": "N610CD", "dest": "KLGB", "dep_local": "18:30",
                      "pax": 2, "cargo": 0, "date": "12NOV26"}], "--hours", "2.5")
r = j["picks"][0] if j else {}
check("G8", "KSAF 18:30 → 0130Z / 18:30 LCL, Zulu 13NOV26, night",
      r.get("departure") == "0130Z / 18:30 LCL" and r.get("zulu_date") == "13NOV26"
      and r.get("day_part") == "night", json.dumps(r)[:200])

# G9 rounding, sunset, URL
rc, j, _ = finalize([{"tail": "N610CD", "dest": "KLGB", "dep_local": "16:32",
                      "pax": 5, "cargo": 40, "date": "12NOV26"}], "--hours", "2.5")
r = j["picks"][0] if j else {}
check("G9", "16:32 → 16:30; 2330Z; sunset; 1h 46m; URL tail",
      rc == 0 and r.get("departure") == "2330Z / 16:30 LCL"
      and r.get("day_part") == "sunset" and r.get("block") == "1h 46m"
      and r.get("simbrief", "").endswith(
          "pax=5&cargo=0.04&date=12NOV26&deph=23&depm=30")
      and any("rounded" in n for n in j["notes"]), json.dumps(r)[:300])

# G10 summer date, Zulu rollover
rc, j, _ = finalize([{"tail": "N539CA", "dest": "KSAF", "dep_local": "19:50",
                      "pax": 2, "cargo": 0, "date": "21JUN27"}], "--hours", "2.5")
r = j["picks"][0] if j else {}
check("G10", "KLGB 19:50 21JUN27 → 0250Z / 19:50 LCL, 22JUN27, sunset",
      r.get("departure") == "0250Z / 19:50 LCL" and r.get("zulu_date") == "22JUN27"
      and r.get("day_part") == "sunset", json.dumps(r)[:200])

# G11 Hawker hold
rc, out, _ = run("--tail", "N24SM", "--hours", "2.5", "--date", "12NOV26", "--json")
dest = json.loads(out)["candidates"][0]["dest"]
rc, j, _ = finalize([{"tail": "N24SM", "dest": dest, "dep_local": "10:00",
                      "pax": 8, "cargo": 300, "date": "12NOV26"}], "--hours", "2.5")
probs = j["picks"][0]["problems"] if j else []
check("G11", "N24SM 8 pax 300 lb rejected on hold room, exit 4",
      rc == 4 and "300 lbs cargo exceeds the 50 lbs room at 8 pax" in probs, probs)

# G12 BBJ into a short field with an unearned exemption
rc, j, _ = finalize([{"tail": "N737GG", "dest": "KFXE", "dep_local": "10:00",
                      "pax": 4, "cargo": 0, "date": "12NOV26", "exempt": True}],
                    "--hours", "2.5")
probs = j["picks"][0]["problems"] if j else []
check("G12", "N737GG→KFXE exempt: fails on runway and on the unearned exemption",
      rc == 4 and any("below Min rwy 6500" in p for p in probs)
      and any("exempt" in p for p in probs), probs)

# G13 Class B hub and an impossible cabin
rc, j, _ = finalize([{"tail": "N13SY", "dest": "KATL", "dep_local": "10:00",
                      "pax": 12, "cargo": 0, "date": "12NOV26"}],
                    "--hours", "2.5", "--allow-b")
probs = j["picks"][0]["problems"] if j else []
check("G13", "N13SY→KATL: Class B note (with --allow-b); 12 pax exceeds max 8",
      rc == 4 and any("Class B" in n for n in j["notes"])
      and "12 pax exceeds max 8" in probs, f"{probs} {j and j['notes']}")
rc, j, _ = finalize([{"tail": "N13SY", "dest": "KATL", "dep_local": "10:00",
                      "pax": 2, "cargo": 0, "date": "12NOV26"}], "--hours", "2.5")
check("G13b", "without --allow-b a Class B pick is a problem",
      rc == 4 and any("Class B" in p for p in j["picks"][0]["problems"]))

# G14 polar night
rc, j, err = finalize([{"tail": "N75KY", "dep": "PABR", "dest": "PAFA",
                        "dep_local": "12:00", "pax": 0, "cargo": 0,
                        "date": "12DEC26"}], "--hours", "3")
r = j["picks"][0] if j else {}
check("G14", "PABR 12DEC26: null sun times, no crash, not sun-edge",
      j is not None and r.get("sunrise") is None and r.get("sun_edge") is False,
      f"exit {rc} {err[:200]} {json.dumps(r)[:200]}")

# G15 malformed picks
rc, j, err = finalize([{"tail": "N13SY", "dest": "KBNA", "dep_local": "10:00",
                        "pax": 2, "date": "31FEB26"},
                       {"tail": "N13SY", "dest": "KBNA", "dep_local": "10:00",
                        "pax": "two"},
                       "N13SY KBNA"], "--hours", "2.5")
picks = j["picks"] if j else []
check("G15", "bad date, string pax, bare string → exit 4 with problems",
      rc == 4 and len(picks) == 3 and all(p.get("problems") for p in picks),
      f"exit {rc} {err[:200]} {json.dumps(picks)[:300]}")

# G16 renamed CSV column; blank line inside THE FLEET
bad_data = os.path.join(TMP, "baddata")
os.makedirs(bad_data)
shutil.copy(os.path.join(DATA, "runways.csv"), bad_data)
with open(os.path.join(DATA, "airports.csv"), encoding="utf-8") as src, \
        open(os.path.join(bad_data, "airports.csv"), "w", encoding="utf-8") as dst:
    dst.write(src.readline().replace('"latitude_deg"', '"lat_deg"'))
    shutil.copyfileobj(src, dst)
rc, out, err = run("--tail", "N13SY", "--hours", "2.5", data=bad_data)
c1 = rc == 3 and "latitude_deg" in err
st = state_variant("g16.md", "| N388BB |", "\n| N388BB |")
rc2, out2, err2 = run("--tail", "N13SY", "--hours", "2.5", "--date", "12NOV26",
                      "--table", doc=st)
check("G16", "renamed column → exit 3 naming it; blank line → 22 tails",
      c1 and rc2 == 0 and "22 tails (20 active)" in out2,
      f"csv: exit {rc} {err.strip()[:120]} | state: exit {rc2} {err2.strip()[:120]}")

# G17 event market
rc, out, _ = run("--class", "mid_jet", "--event", "KAUS", "--hours", "2.5",
                 "--date", "12NOV26", "--json")
cands = json.loads(out)["candidates"] if rc == 0 else []
hit = [c for c in cands if c["tail"] == "N312FU" and c["dest"] == "KAUS"]
check("G17", "N312FU→KAUS in-market at 0 nm, block 1h 53m, no `positioning` key",
      bool(hit) and hit[0]["in_market"] and hit[0]["event_dist_nm"] == 0
      and hit[0]["block"] == "1h 53m" and "positioning" not in hit[0],
      json.dumps(hit[:1])[:200])

# Handshakes (B1)
rc, _, err = run("--expect", "6.9", "--rules")
rc_rules = rc
rc, _, err = run("--expect", "6.9", "--tail", "N13SY", "--hours", "2.5")
st = state_variant("schema.md", "Schema v6.2", "Schema v6.1")
rc2, _, err2 = run("--tail", "N13SY", "--hours", "2.5", doc=st)
check("B1", "--expect mismatch exit 5; old schema exit 3",
      rc == 5 and rc2 == 3 and "schema 6.1" in err2, f"{rc} {err} | {rc2} {err2}")

# A1 regression: an unparseable Route is a hard error
st = state_variant("route.md", "| KLGB-KSAF |", "| KLGB to KSAF |")
rc, _, err = run("--tail", "N13SY", "--hours", "2.5", doc=st)
check("A1", "unparseable logbook Route → exit 3 naming it",
      rc == 3 and "KLGB to KSAF" in err, err.strip()[:160])

failed = [g for g, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed"
      + (f" · failed: {', '.join(failed)}" if failed else ""))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
