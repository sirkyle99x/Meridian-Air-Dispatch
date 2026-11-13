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
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "dispatch_calc.py")
STATE = os.path.join(ROOT, "tests", "fixtures", "dispatch_state.md")
DATA = os.environ.get("DISPATCH_TEST_DATA", os.path.join(ROOT, "tests", "data"))
UPDATE_SNAPSHOT = "--update-snapshot" in sys.argv
_src = open(SCRIPT, encoding="utf-8").read()
SCRIPT_VERSION = re.search(r'SCRIPT_VERSION = "([\d.]+)"', _src).group(1)
STATE_SCHEMA = re.search(r'STATE_SCHEMA = "([\d.]+)"', _src).group(1)
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
check("G1", "--rules matches stored snapshot, current version, no retired components",
      rc == 0 and out == open(snap).read() and f"v{SCRIPT_VERSION}" in out
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
st = state_variant("schema.md", f"Schema v{STATE_SCHEMA}", "Schema v0.9")
rc2, _, err2 = run("--tail", "N13SY", "--hours", "2.5", doc=st)
check("B1", "--expect mismatch exit 5; old schema exit 3",
      rc == 5 and rc2 == 3 and "schema 0.9" in err2, f"{rc} {err} | {rc2} {err2}")

# A1 regression: an unparseable Route is a hard error
st = state_variant("route.md", "| KLGB-KSAF |", "| KLGB to KSAF |")
rc, _, err = run("--tail", "N13SY", "--hours", "2.5", doc=st)
check("A1", "unparseable logbook Route → exit 3 naming it",
      rc == 3 and "KLGB to KSAF" in err, err.strip()[:160])

# ---- v7.1 (Phase 3) -------------------------------------------------------

# G19 no military-only field in any class run at 1.5 / 2.5 / 4 h
mil = []
for hours in ("1.5", "2.5", "4"):
    for cls in ("turboprop", "mid_jet", "large_jet"):
        rc, out, _ = run("--class", cls, "--hours", hours, "--date", "12NOV26",
                         "--json")
        if rc != 0:
            continue
        for c in json.loads(out)["candidates"]:
            a = aps[c["dest"]]
            if dc.military_only(a) and c["dest"] not in doc.preferred:
                mil.append(f"{c['tail']}→{c['dest']} {hours}h")
gate_kept = all(not dc.military_only(aps[i])
                for i in ("KNYL", "KBLV", "KSPS", "KGRK", "KDOV", "KCEF", "KFHU"))
gate_out = all(dc.military_only(aps[i]) for i in ("KBAD", "KLRF", "KBIF", "KNFL"))
check("G19", "no military-only field on any board; joint-use civil fields kept",
      not mil and gate_kept and gate_out, "; ".join(mil[:5]))

# G20 Falcon 50 Max GC
rc, out, _ = run("--tail", "N388BB", "--hours", "4.5", "--date", "12NOV26", "--json")
cands = json.loads(out)["candidates"] if rc == 0 else []
far = [c["dest"] for c in cands if c["gc_nm"] > 1550]
rc6, _, err6 = run("--tail", "N388BB", "--hours", "6", "--date", "12NOV26", "--json")
rc2, j, _ = finalize([{"tail": "N388BB", "dest": "KSEA", "dep_local": "10:00",
                       "pax": 2, "cargo": 0, "date": "12NOV26"}], "--hours", "6.5",
                     "--allow-b")
probs = j["picks"][0]["problems"] if j else []
check("G20", "Falcon: 4.5 h board within 1,550 nm; 6 h sits out; KTEB→KSEA flagged",
      bool(cands) and not far and rc6 == 2 and "left off this board" in err6
      and any("Max GC of 1550" in p for p in probs),
      f"{len(cands)} cands, over {far} · 6h exit {rc6} · {probs}")

# G21 preferred fields score the cap, incl. a short reliever and a scenery field
tail_mj = next(f for f in doc.fleet if f["tail"] == "N13SY")
tail_tp = next(f for f in doc.fleet if f["tail"] == "N417KG")
qp = dc.quality_score(aps["KPWK"], "mid_jet", "KPWK" in doc.preferred)
qr = dc.quality_score(aps["KRVS"], "mid_jet", "KRVS" in doc.preferred)
qn = dc.quality_score(aps["KPWK"], "mid_jet", False)
check("G21", "KPWK and KRVS preferred → 14; KPWK unpreferred → 2.0",
      qp == 14 and qr == 14 and qn == 2.0 and len(doc.preferred) == 43,
      f"KPWK {qp} KRVS {qr} plain {qn} n={len(doc.preferred)}")

# G22 per-class runway curves
q = dc.quality_score
check("G22", "7,000 ft no-service field: mid jet 10, large jet 6.0; 5,000 ft: turboprop 10",
      q({"rwy": 7000, "sched": False}, "mid_jet") == 10
      and q({"rwy": 7000, "sched": False}, "large_jet") == 6.0
      and q({"rwy": 5000, "sched": False}, "turboprop") == 10
      and q({"rwy": 12000, "sched": True}, "mid_jet") == 14,
      "")

# G23 unregistered US hub proxies as C, never B
check("G23", "unregistered US large_airport (KAUS, KELP) proxies C; register B stays B",
      dc.proxy_class(aps["KAUS"]) == "C" and dc.proxy_class(aps["KELP"]) == "C"
      and doc.class_register.get("KATL") == "B")

# ---- v7.2 (Phase 4) -------------------------------------------------------

# G24 the staged state file stays small
size = os.path.getsize(STATE)
check("G24", "staged dispatch_state.md under 4 KB", size < 4096, f"{size} bytes")

# G25 reference handshake
REF = os.path.join(ROOT, "reference.md")
bad_ref = os.path.join(TMP, "ref.md")
with open(REF, encoding="utf-8") as fh, open(bad_ref, "w", encoding="utf-8") as out:
    out.write(fh.read().replace("Reference v", "Reference v0.", 1))
rc, _, err = run("--tail", "N13SY", "--hours", "2.5", "--ref", bad_ref)
check("G25", "reference.md from another version → exit 3 naming it",
      rc == 3 and "reference schema" in err, err.strip()[:160])

# G26 tail notes reach the table
rc, out, _ = run("--tail", "N707BM", "--hours", "2.5", "--date", "12NOV26", "--table")
check("G26", "22 tail notes parsed; N707BM's prints under its tail",
      len(doc.tail_notes) == 22 and rc == 0
      and "note: Hawker 800XP. Mountain West" in out, f"{len(doc.tail_notes)} notes")

# G27 run counter
cnt_dir = os.path.join(TMP, "cnt")
os.makedirs(cnt_dir)
outs = []
for _ in range(2):
    p_ = subprocess.run([sys.executable, SCRIPT, "--doc", STATE, "--data", DATA,
                         "--tail", "N13SY", "--hours", "2.5", "--date", "12NOV26",
                         "--table"], capture_output=True, text=True, cwd=cnt_dir)
    outs.append(p_.stdout.splitlines()[0] if p_.stdout else "")
check("G27", "run counter counts runs per working directory",
      outs[0].endswith("run 1") and outs[1].endswith("run 2"), " | ".join(outs))

# ---- v7.3 (Phase 6) -------------------------------------------------------

HOOK = ("Coastline Beverage's team flies home after the November tastings. "
        "Dana Whitfield wants them in Long Beach before Monday. "
        "The sun sets over the Mojave on the way.")

# G28 --widget: finished board, escaped, validated story fields
pk = [{"tail": "N610CD", "dest": "KLGB", "dep_local": "16:30", "pax": 5, "cargo": 40,
       "date": "12NOV26", "job": "Corporate charter", "event": "Fiesta <Week>",
       "hook": HOOK}]
path = os.path.join(TMP, "w.json")
json.dump(pk, open(path, "w"))
rc, out, _ = run("--finalize", path, "--hours", "2.5", "--widget", "--calls", "6")
wid = out.split("----- WIDGET (render verbatim) -----", 1)[1] if "WIDGET" in out else ""
ok1 = (rc == 0 and wid.count('class="mc"') == 1 and "Mission 1 of 1" in wid
       and "2330Z / 16:30 LCL" in wid and "ti-sunset" in wid
       and "Fiesta &lt;Week&gt;" in wid and "Board built in 6 tool calls" in wid
       and "pax=5&amp;cargo=0.04" in wid and "{" not in wid.split("</style>")[1])
bad = [dict(pk[0], job="Charter flight", hook="Too short."),
       dict(pk[0], job="Ferry flight")]
json.dump(bad, open(path, "w"))
rc2, out2, _ = run("--finalize", path, "--hours", "2.5", "--widget")
check("G28", "--widget renders an escaped board; bad job, short hook, loaded ferry rejected",
      ok1 and rc2 == 4 and "WIDGET" not in out2 and "not a RULE 1 job type" in out2
      and "hook has 1 sentence" in out2 and "Ferry flight carries 0 pax" in out2,
      f"ok1={ok1} rc2={rc2}")

# G29 --log-flight on a scratch copy: row, window, fleet, integrity, re-parse
st = os.path.join(TMP, "log.md")
shutil.copy(STATE, st)
fl = os.path.join(TMP, "f.json")
outs = []
for i, d in enumerate(["KLGB", "KSAF", "KLGB", "KSAF", "KLGB"], 1):
    json.dump({"tail": "N610CD", "dest": d, "date": f"1{i} NOV 2026", "block": "1h 46m",
               "job": "Corporate charter", "pax": 4, "event": "",
               "hook": "November test leg"}, open(fl, "w"))
    outs.append(run("--doc", st, "--log-flight", fl))
last = json.loads(outs[-1][1]) if outs[-1][0] == 0 else {}
d2 = dc.Doc(st)
t2 = next(f for f in d2.fleet if f["tail"] == "N610CD")
check("G29", "--log-flight: 5 legs → window of 10, oldest dropped, Away 0 at home, clean",
      all(o[0] == 0 for o in outs) and len(d2.logbook) == 10
      and d2.logbook[0]["reg"] == "N988RS" and last.get("dropped")
      and t2["current"] == "KLGB" and t2["away"] == 0 and last.get("integrity") == "clean"
      and "November test leg" in open(st).read() and "| 15 NOV 2026 |" in open(st).read(),
      f"{[o[0] for o in outs]} {len(d2.logbook)} {t2['current']}/{t2['away']}")

# G30 --invoice: lines, order, omission rules, half-up cents
rc, out, _ = run("--invoice", "--tail", "N610CD", "--dest", "KLGB", "--block", "1h 46m",
                 "--trip-fuel", "3350", "--fuel-price", "7.25", "--pax", "5",
                 "--handling", "350")
inv = json.loads(out) if rc == 0 else {}
descs = [i["desc"] for i in inv.get("items", [])]
rc2, out2, _ = run("--invoice", "--tail", "N737GG", "--dest", "MYNN", "--block", "2:10",
                   "--trip-fuel", "9000", "--fuel-price", "7", "--pax", "0")
inv2 = json.loads(out2) if rc2 == 0 else {}
d2s = [i["desc"] for i in inv2.get("items", [])]
check("G30", "--invoice: mid jet domestic $10,660.68; BBJ to Nassau gets crew day, no FET/catering",
      inv.get("total_fmt") == "$10,660.68"
      and descs == ["Aircraft charter — dry hourly rate", "Jet-A fuel", "In-flight catering",
                    "Ramp / handling", "Federal excise tax (FET)"]
      and d2s == ["Aircraft charter — dry hourly rate", "Jet-A fuel", "Crew day rate"]
      and inv2.get("domestic") is False, f"{inv.get('total_fmt')} {d2s}")

# G31 --calib reproduces logged rows and flags a real miss
rc, out, _ = run("--calib", "--tail", "N610CD", "--gc", "605", "--gnd", "626",
                 "--air", "580", "--air-min", "81", "--date", "30SEP26")
c1 = json.loads(out) if rc == 0 else {}
rc, out, _ = run("--calib", "--tail", "N388BB", "--gc", "2082", "--gnd", "2131",
                 "--air", "2307", "--air-min", "347", "--date", "23SEP26")
c2 = json.loads(out) if rc == 0 else {}
check("G31", "--calib: KLGB–KSAF row matches the log; Falcon KTEB–KSEA flagged as a miss",
      c1.get("row") == "| 30 SEP 2026 | N610CD | Citation X | mid_jet | 605 | 81 | 87.4 | 90.7 | −3.6% |"
      and not c1.get("warnings") and c2.get("warnings"),
      f"{c1.get('row')} | {c2.get('row')} {c2.get('warnings')}")

failed = [g for g, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed"
      + (f" · failed: {', '.join(failed)}" if failed else ""))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
