#!/usr/bin/env python3
"""
dispatch_calc.py — Meridian Air Dispatch candidate math (RULES.md v7.3).

Reads dispatch_state.md for state: THE FLEET, MODEL LIMITS, REGION TABLE,
AIRPORT CLASS REGISTER, THE LOGBOOK. This file is the single source of truth
for every scoring CONSTANT — RULES.md references them rather than restating
them. `--rules` prints the active table. Airport geometry comes from the
OurAirports CSVs. Hosted at
https://raw.githubusercontent.com/sirkyle99x/Meridian-Air-Dispatch/main/dispatch_calc.py
and fetched rather than retyped.

Three modes:

  Candidates  Per destination: great-circle and route nm, block, session,
              fullness, every mechanical score component from RULES.md →
              VARIETY ENGINE, the LOAD PLANNING feasibility checks, and a
              SimBrief URL skeleton. `--json` for the full record, `--table`
              for the step-6 decision table with each departure airport's
              sun times, `--json-out FILE` to save the JSON while printing
              the table, so one run serves both.

  Finalize    `--finalize picks.json --hours X` takes the story picks — tail,
              dest, local departure time, pax, cargo — runs each through the
              same legality gate as the candidate loop, and returns
              everything a card needs: Zulu and local departure, Zulu date,
              the five-way day-part from real sun times, the RULE 1 icon,
              block, session, a payload check, and the finished SimBrief URL.

  Rules       `--rules` prints the constants.

Every run starts with a preflight: required CSV columns, a floor on airports
with a runway, and parsed state counts, reported as one `state:` manifest
line. A failed preflight is exit 3 with the cause named — never a silent
empty result. `--expect VERSION` halts with exit 5 when the RULES.md version
the session loaded differs from SCRIPT_VERSION.

Left to Dispatch: the story, job type, the chosen pax, cargo and departure
time, event verification, and board composition.

Usage
-----
  python3 dispatch_calc.py --expect 7.3 --hours 2.5 --tail N24SM --table --json-out cands.json
  python3 dispatch_calc.py --expect 7.3 --finalize picks.json --hours 2.5

picks.json is a list of objects:
  {"tail": "N24SM", "dest": "KAEX", "dep_local": "18:05",
   "pax": 4, "cargo": 40, "date": "21OCT26"}
`dep` defaults to the tail's Current; `date` is the LOCAL departure date at
the departure airport (DDMMMYY) and defaults to today there. `--hours` is
required. `"exempt": true` lifts the fullness floor for a positioning leg and
is honoured only when `--event` is also given and the destination lies inside
the event radius; home-base legs are exempt automatically. `"ferry": true`
lets the amphibious Caravan take a runway destination.

Exit codes: 0 ok, 2 no legal candidates, 3 parse/data error,
4 finalize found a pick that fails a check (details in its `problems`),
5 version mismatch (--expect).
"""

from __future__ import annotations

import argparse
import csv
import html
from decimal import Decimal, ROUND_HALF_UP
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SCRIPT_VERSION = "7.3"       # must equal the RULES.md version; see --expect
STATE_SCHEMA = "6.4"         # must equal dispatch_state.md's "Schema v" header
REF_SCHEMA = "1.0"           # must equal reference.md's "Reference v" header
REF_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "reference.md")
RUN_COUNTER = ".dispatch_runs"  # per-working-directory run count (C6)
HOME_TZ = "America/New_York" # Kyle's zone: the default --date is his local date


class DataError(Exception):
    """A state or airport-data problem. Always exit 3 with the cause named."""


# ---------------------------------------------------------------------------
# Scoring and timing constants. This file is their only home; RULES.md says
# where to find them rather than restating them. State lives in
# dispatch_state.md and is never hardcoded here.
# ---------------------------------------------------------------------------

ROUTE_FACTOR = 1.07          # FLIGHT TIME CALCULATION
TAXI_H = 0.25                # 8 min out + 7 min in
PREP_H = 0.35                # session time = block + prep
CEILING_MARGIN_H = 0.5       # block ceiling = availability - 30 min, every length
PAX_ALLOWANCE_LB = 230       # 175 body + 55 bag
BAG_PER_PAX_LB = 55

# Per-model overrides, keyed by MODEL LIMITS' ICAO column, for an airframe
# whose SimBrief profile has been confirmed to deviate from the global
# 230/55 standard above. Add an entry only when both numbers are screenshot-
# confirmed against that profile's Airframe Weights panel — see
# dispatch_state.md -> MODEL LIMITS for the confirming source and date.
PAX_ALLOWANCE_LB_OVERRIDE = {
    "H25B": 195,   # 170 body + 25 bag, confirmed 20 SEP 2026
    "FA50": 235,   # 200 body + 35 bag, confirmed 23 SEP 2026
}
BAG_PER_PAX_LB_OVERRIDE = {
    "H25B": 25,
    "FA50": 35,
}

# Overhead anchors: (gc_nm, hours). Linear interpolation between; flat outside.
OVERHEAD_ANCHORS = [(50.0, 0.26), (175.0, 0.26), (375.0, 0.26), (600.0, 0.26)]

SIMBRIEF_URL = (
    "https://dispatch.simbrief.com/options/custom"
    "?type={type}&orig={orig}&dest={dest}&reg={reg}"
    "&pax={{PAX}}&cargo={{CARGO_KLBS}}&date={date}&deph={deph}&depm={depm}"
)

# Airspace tiers a class may use without story justification.
#
# Class E is included for every class. Class is a proxy for "is this a real
# bizav environment"; for a towered field it answers that, for a non-towered
# field it answers nothing — Telluride (KTEX), Montrose (KMTJ), Rifle (KRIL)
# and Lake Tahoe (KTVL) are Class E and are serious jet destinations, while a
# grass strip is Class E for the opposite reason. No extra test is needed here
# because the filters that do the real work already ran: the min_rwy check and
# the jets-and-small-fields gate below both sit ahead of tier_ok in the
# candidate loop. Without E, verifying a good non-towered field into the
# AIRPORT CLASS REGISTER turned it into a permanent veto.
TIER_ALLOWED = {
    "turboprop": {"C", "D", "E"},
    "mid_jet": {"C", "D", "E"},
    "large_jet": {"C", "E"},     # D only when runway >= 7,000 ft; handled below
}
LARGE_JET_CLASS_D_MIN_RWY = 7000

# Field quality gate. Replaces the v4.2 type-plus-length test, which was wrong
# in both directions. OurAirports `type` is assigned inconsistently — Morristown,
# Manassas, Republic and Hanscom are medium_airport while John C Tune, McKinney
# National, Denton, Livermore, Hayward, Leesburg Executive and Witham Field are
# all small_airport, and they are the same class of field. The old test blocked
# ~980 real bizav airports on that label while admitting Petan Ranch (7,500 ft
# gravel), Melby Ranch (7,400 x 40 turf) and Bell Ranch (8,200 ft dirt) for
# being long.
#
# Surface and width separate them cleanly; length is left entirely to the tail's
# Min rwy. 75 ft rather than 100: 100 ft is the FAA design width for Airplane
# Design Group II, but design standards describe new construction, and Monmouth
# Executive (85 ft), Taos, McCall and Salida (75 ft) all take bizjets routinely.
# Applies to every class, turboprops included — Kyle's call, 12 SEP 2026. It
# costs turboprops most of Alaska's gravel, which is why N828DC's revenue
# missions run through the water branch and the fallback ferry below stays on
# Min rwy alone.
FIELD_MIN_WIDTH_FT = 75

# Ident re-keying. OurAirports keeps a field's original `ident` after it is
# renamed and records the new code in `icao_code` (KPBI -> KDJT, Palm Beach,
# 2026). Any row whose `icao_code` is a four-letter code differing from its
# ident, and not already some other row's ident, is re-keyed under the ICAO
# code: a tail homed at the new code resolves, SimBrief receives the code it
# expects, and the old ident stops appearing as a separate destination. This
# replaces the hand-kept alias table, which needed an edit for every rename.
ICAO_RE = re.compile(r"^[A-Z]{4}$")

PAVED_PREFIXES = ("ASP", "CON", "PEM", "BIT", "TAR", "COM", "PER", "PSP", "MAC")


def surface_class(raw: str) -> str:
    s = re.sub(r"[^A-Z]", "", (raw or "").upper())
    if s.startswith("WATE"):
        return "water"
    return "paved" if s.startswith(PAVED_PREFIXES) else "unpaved"


def field_quality_ok(ap: dict) -> bool:
    """Paved, and at least FIELD_MIN_WIDTH_FT wide. Length is Min rwy's job."""
    return ap["paved"] and ap["rwy_width"] >= FIELD_MIN_WIDTH_FT


# Event repositioning. Dispatch verifies the event and passes its market's
# airport(s) in with --event; the script does only the geometry.
#
# Radius is 50 nm, not 100: at 100 nm a Teterboro event swallows Philadelphia
# and Hartford, which are separate markets. For a genuinely multi-airport metro
# Dispatch passes each field (--event KPHX --event KSDL) rather than widening
# the ring.
#
# A destination inside the radius of an --event airport is `in_market`, and its
# `event_dist_nm` says how far from the event field it sits. That flag is the
# whole output: no event bonus is scored (it was +40 to v6.2, then 0, and was
# removed in v7.0). RULES.md reserves the event slot outright, fills it with a
# revenue leg by default, and gates an empty positioning leg on ops mode,
# outbound window and story — none of which a score can express.
#
# In-market records keep two neutralisations. A positioning leg is short and
# empty by nature, so it would fall below the fullness floor, and it flies
# toward exactly the region the variety engine is busy penalizing — the event is
# what concentrated traffic there in the first place. Scoring it as in-band and
# flooring its region term at zero removes penalties the leg does not deserve;
# it does not award anything.
EVENT_RADIUS_NM = 50

# Scoring constants. RULES.md documents what each component MEANS; the values
# live only here, so there is nothing to keep in sync. --rules prints them.
RECENCY_LAST3 = -50          # destination in the last 3 logged flights
RECENCY_LAST10 = -20         # destination in the last 10
RECENCY_NEVER = 10           # never a logged destination
REGION_BOTH_LAST2 = -30      # same region as both of the last 2 flights
REGION_LAST1 = -15           # same region as the last flight only
REGION_ABSENT_LAST5 = 20     # region absent from the last 5 flights
HOME_BASED_HOME = 35         # based tail, destination is its home field
HOME_BASED_TOWARD = 20       # based tail, destination is toward home
HOME_REGIONAL_HOME = 30      # regional tail outside its region, home field
HOME_REGIONAL_REGION = 25    # regional tail outside its region, home region
HOME_REGIONAL_TOWARD = 10    # regional tail outside its region, toward home
AFFINITY_BONUS = 10          # destination region not excluded for the class
# Model rotation was retired in v7.0: Kyle names the aircraft each session, so
# equipment rotation is no longer wanted. Region and destination recency stay.

# Candidates reported per tail when --top is not given. One default now that
# a board is built for the aircraft Kyle names rather than a fleet-wide spread.
TOP_DEFAULT = 12
TOP_MAX = 30

# Fullness band, in ABSOLUTE minutes against the ceiling — not a fraction of it.
# Kyle's tolerance is "15 minutes short is fine, 5 minutes over is fine" and that
# does not scale with session length: 15 min short of a 3h ceiling and 15 min
# short of a 90 min ceiling are the same concession to him, while 0.92 x ceiling
# is two different concessions. The v6.3 monotonic curve was proportional and
# collapsed a 20-minute tolerance into a ~2-minute slice: on a 3h ceiling every
# reported candidate landed between 177.7 and 179.9 minutes, so the engine chose
# among ~235 legal fields by a margin Kyle cannot perceive, and the 12 it
# surfaced were whichever ones sat nearest the ceiling radius by geographic
# accident.
#
# Inside the band every candidate scores the same, and DESTINATION QUALITY below
# does the discriminating, from runway length and scheduled service. It does not
# read airport `type` and does not favour relievers over hubs — a hub wins on
# both signals — so the reliever preference stays a board-time judgment.
BAND_UNDER_H = 0.25          # 15 min: full credit this far under the ceiling
BAND_OVER_H = 5.0 / 60.0     # 5 min: allowed to exceed the ceiling by this much
BAND_FULL_PTS = 20.0         # flat credit anywhere inside the band
BAND_SHORT_PTS = -60.0       # below the floor; normally filtered before scoring


def fullness_score(block_h: float, ceiling_h: float) -> float:
    if ceiling_h <= 0:
        return 0.0
    if block_h < ceiling_h - BAND_UNDER_H:
        return BAND_SHORT_PTS
    return BAND_FULL_PTS


# Destination quality. Every field that clears the gate is *legal*; almost none
# of them are places a business jet actually goes. Nothing in the engine could
# tell Denison, Iowa from Bangor, Maine — both unflown, both paved, both inside
# the band — so the whole judgment fell to Dispatch by hand, every board, and
# re-derived from scratch every session. These three signals are already loaded
# off OurAirports and cost nothing extra to read.
#
# Runway length carries the weight, and `type` is deliberately NOT used. This is
# the one place the rejected gate's evidence still applies: ARCHIVE.md records
# that OurAirports labels Morristown, Manassas, Republic and Hanscom
# `medium_airport` while John C Tune, McKinney National, Denton, Livermore,
# Hayward, Leesburg Executive and Witham Field are `small_airport` — the same
# class of field, different label. Scoring that label would re-commit the error
# that blocked ~980 real bizav airports, just softly instead of absolutely.
#
# Length is safe here in a way it was not as a gate. The gate's failure was
# admitting Petan Ranch (7,500 ft gravel), Melby Ranch (7,400 x 40 turf) and
# Bell Ranch (8,200 ft dirt) for being long. Those never reach this function:
# field_quality_ok has already required pavement and 75 ft of width, so scoring
# runs over an already-gated set where length cannot readmit a ranch strip. It
# is also the signal that still works for a pure bizav reliever with no airline
# service — Addison's 7,203 ft separates it from a 5,000 ft county strip, and
# from this function McKinney and Hanscom are indistinguishable, which is right.
#
# v7.1: the runway curve is per class and plateaus where more runway stops
# meaning a better field for that aircraft. Under one fleet-wide curve that
# topped out at 10,000 ft, a 7,000 ft bizav field scored like a compromise for
# a mid jet that needs 5,000 — Chicago Executive 0.0, Morristown 3.3 — while
# any airline airport with a long runway hit the cap. Every curve tops out at
# the same 10 points, so the classes stay comparable.
QUALITY_RWY_ANCHORS = {
    "turboprop": [(2500.0, 0.0), (4000.0, 6.0), (5000.0, 10.0)],
    "mid_jet":   [(4500.0, 0.0), (6000.0, 6.0), (7000.0, 10.0)],
    "large_jet": [(5000.0, 0.0), (6500.0, 5.0), (8000.0, 8.0), (10000.0, 10.0)],
}
QUALITY_SCHEDULED = 4.0      # someone runs airline service there: a real facility
# A field on dispatch_state.md → PREFERRED FIELDS scores the cap outright. That
# list is Kyle's: the bizav relievers AIRSPACE ROUTING RULES names, the resort
# fields he flies, and the scenery fields he owns. It ranks among legal fields
# only — it never readmits one the gate rejected.
QUALITY_MAX = 14.0


def quality_score(ap: dict, cls: str, preferred: bool = False) -> float:
    if preferred:
        return QUALITY_MAX
    anchors = QUALITY_RWY_ANCHORS[cls]
    rwy = float(ap.get("rwy") or 0)
    if rwy <= anchors[0][0]:
        pts = anchors[0][1]
    else:
        pts = anchors[-1][1]
        for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
            if rwy <= x1:
                pts = y0 + (y1 - y0) * (rwy - x0) / (x1 - x0)
                break
    if ap.get("sched"):
        pts += QUALITY_SCHEDULED
    return round(min(pts, QUALITY_MAX), 1)


# Military fields. A field named as a base, with no airline service and no civil
# designator in its name, is not a charter destination — Barksdale, Fort Bliss,
# NAS Fallon all reached boards on runway length alone. The test reads facts,
# not a hand-kept list: joint-use civil airports (Yuma International / MCAS
# Yuma, Scott AFB / MidAmerica, Westover Metropolitan) carry airline service or
# a civil name and stay legal. A field on PREFERRED FIELDS is always allowed.
MILITARY_NAME_RE = re.compile(
    r"\b(AFB|Air Force Base|Air Reserve Base|ARB|Air Reserve Station|"
    r"Naval Air Station|Naval Air Facility|NAS|NAF|JRB|Naval|Navy|"
    r"Army Air ?field|AAF|Army Heliport|Marine Corps|MCAS|MCAF|Joint Base|"
    r"Air National Guard|ANGB|Military|Air Base|Space Force)\b", re.I)
CIVIL_NAME_RE = re.compile(
    r"\b(Municipal|Regional|International|Metropolitan|Civil)\b", re.I)


def military_only(ap: dict) -> bool:
    return bool(MILITARY_NAME_RE.search(ap["name"]) and not ap.get("sched")
                and not CIVIL_NAME_RE.search(ap["name"]))


# Reporting aids. Fullness is flat inside the band, so ties at the top are now
# the normal case and quality is what separates them; TYPE_RANK survives only as
# a last-resort tie-break below quality, and the reported set is still spread
# across regions instead of clustering in whichever one sits at the band radius.
TYPE_RANK = {"large_airport": 3, "medium_airport": 2, "small_airport": 1,
             "seaplane_base": 1}
MAX_PER_REGION_REPORTED = 3

SUN_WINDOW_MIN = 45            # sunrise/sunset window, either side of the event
DAY_PART_ICON = {
    "sunrise": "ti-sunrise",
    "morning": "ti-sun",
    "afternoon": "ti-sun",
    "sunset": "ti-sunset",
    "night": "ti-moon-stars",
}


def sun_times(lat: float, lon: float, tzname: str, local_date):
    """(sunrise, sunset) as aware local datetimes, or None (no astral, polar)."""
    try:
        from astral import Observer
        from astral.sun import sunrise, sunset
    except ImportError:
        return None
    obs = Observer(latitude=lat, longitude=lon)
    tz = ZoneInfo(tzname)
    try:
        return (sunrise(obs, date=local_date, tzinfo=tz),
                sunset(obs, date=local_date, tzinfo=tz))
    except ValueError:            # sun never rises or never sets that day
        return None


def story_day_part(dep_local: datetime, sun) -> str:
    """Five-way day-part for a story-chosen local departure."""
    if sun is None:               # no sun data: clock-only fallback, no windows
        h = dep_local.hour
        return "morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 18 else "night"
    sr, ss = sun
    w = timedelta(minutes=SUN_WINDOW_MIN)
    if abs(dep_local - sr) <= w:
        return "sunrise"
    if abs(dep_local - ss) <= w:
        return "sunset"
    noon = dep_local.replace(hour=12, minute=0, second=0, microsecond=0)
    if sr + w < dep_local < noon:
        return "morning"
    if noon <= dep_local < ss - w:
        return "afternoon"
    return "night"


def cargo_klbs(lbs: int) -> str:
    """SimBrief's cargo parameter is thousands of lbs: 200 -> 0.2."""
    if lbs <= 0:
        return "0"
    return f"{lbs / 1000:.3f}".rstrip("0").rstrip(".")


def water_only(tail: dict) -> bool:
    """The amphibian's revenue missions deliver to water (THE FLEET tail note)."""
    return "amphibious" in tail["model"].lower()


def destination_gate(a: dict, tail: dict, doc, *, allow_small: bool,
                     land: bool, ferry: bool = False):
    """The legality gate, shared by the candidate loop and --finalize.

    Returns (problems, eff_class, class_b). Verified Class B is reported
    separately rather than as a problem: the candidate loop drops it unless
    --allow-b, while a finalize pick may carry it when the story demands the
    hub (AIRSPACE ROUTING RULES) and gets a note instead.
    """
    problems = []
    ident = a["ident"]
    is_home = ident == tail["home"]
    eff = doc.class_register.get(ident, proxy_class(a))
    amphib = water_only(tail)

    if amphib and not land and not ferry:
        if not a["water"]:
            problems.append(f"{ident} has no water landing area; the amphibian's "
                            f"revenue missions deliver to water")
        return problems, eff, False
    if amphib and ferry and a["water"]:
        return problems, eff, False       # a ferry may also end on water
    if a["type"] == "seaplane_base":
        problems.append(f"{ident} is a seaplane base")
    if a["rwy"] < tail["min_rwy"]:
        problems.append(f"{ident} longest land runway {a['rwy']} ft is below "
                        f"Min rwy {tail['min_rwy']} ft")
    if not allow_small and not is_home and not field_quality_ok(a):
        problems.append(f"{ident} fails the field quality gate (paved, "
                        f"{FIELD_MIN_WIDTH_FT} ft wide)")
    if not is_home and ident not in doc.preferred and military_only(a):
        problems.append(f"{ident} is a military field with no airline service "
                        f"({a['name']})")
    class_b = False
    if not is_home:
        if eff == "B":
            class_b = True
        elif not tier_ok(a, eff, tail["cls"], False):
            problems.append(f"{ident} class {eff} is outside the {tail['cls']} "
                            f"tiers")
    return problems, eff, class_b


def _int_field(p: dict, key: str, problems: list) -> int:
    v = p.get(key, 0)
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        problems.append(f"{key} must be a whole number, got {v!r}")
        return 0
    try:
        n = int(str(v).strip() or 0)
    except ValueError:
        problems.append(f"{key} must be a whole number, got {v!r}")
        return 0
    if n < 0:
        problems.append(f"{key} cannot be negative")
        return 0
    return n


def finalize(args, doc, airports, tf, manifest: str) -> int:
    try:
        with open(args.finalize, encoding="utf-8") as fh:
            picks = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error reading {args.finalize}: {exc}", file=sys.stderr)
        return 3
    if isinstance(picks, dict):
        picks = picks.get("picks", [picks])
    if not isinstance(picks, list):
        picks = [picks]
    if tf is None:
        print("timezonefinder is required for --finalize", file=sys.stderr)
        return 3

    event_pts = [airports[e.upper()] for e in args.event if e.upper() in airports]
    fleet = {f["tail"].upper(): f for f in doc.fleet}
    out, notes, failed = [], [], False
    ceil_f = args.hours - CEILING_MARGIN_H

    def reject(n, msg, tail_id=None):
        rec = {"pick": n, "problems": [msg]}
        if tail_id:
            rec["tail"] = tail_id
        out.append(rec)

    for n, p in enumerate(picks, 1):
        if not isinstance(p, dict):
            reject(n, f"pick must be an object, got {p!r}")
            failed = True
            continue
        problems = []
        tail = fleet.get(str(p.get("tail", "")).upper())
        if tail is None:
            reject(n, f"unknown tail {p.get('tail')!r}")
            failed = True
            continue
        dep = str(p.get("dep") or tail["current"]).upper()
        dest = str(p.get("dest", "")).upper()
        cur, a = airports.get(dep), airports.get(dest)
        if cur is None or a is None:
            reject(n, f"{dep if cur is None else dest or '(blank dest)'} not in "
                      f"the airport database", tail["tail"])
            failed = True
            continue
        if dest == dep:
            reject(n, "destination is the departure airport", tail["tail"])
            failed = True
            continue
        lim = doc.limits_for(tail["model"])
        pax_allow = PAX_ALLOWANCE_LB_OVERRIDE.get(lim["icao"], PAX_ALLOWANCE_LB)
        bag_pp = BAG_PER_PAX_LB_OVERRIDE.get(lim["icao"], BAG_PER_PAX_LB)

        # The same gate the candidate loop applies. A pick that could never
        # have appeared as a candidate does not become legal by being typed.
        gate, eff, class_b = destination_gate(
            a, tail, doc, allow_small=args.allow_small_fields, land=args.land,
            ferry=bool(p.get("ferry")))
        problems.extend(gate)
        if class_b:
            if args.allow_b:
                notes.append(f"pick {n}: {dest} is Class B in the register — "
                             f"only if the story demands it (AIRSPACE ROUTING "
                             f"RULES)")
            else:
                problems.append(f"{dest} is Class B in the register; rerun "
                                f"with --allow-b only if the story demands it")
        if a["country"] == "CU" or cur["country"] == "CU":
            notes.append(f"pick {n}: Cuban leg — the hook must name an OFAC "
                         f"authorized category; tourist travel is prohibited")

        gc = gc_nm(cur["lat"], cur["lon"], a["lat"], a["lon"])
        if lim["max_gc"] and gc > lim["max_gc"]:
            problems.append(f"{round(gc)} nm great-circle exceeds the "
                            f"{tail['model']} Max GC of {lim['max_gc']:.0f} nm")
        route = gc * ROUTE_FACTOR
        block = route / tail["ktas"] + overhead_h(gc) + TAXI_H
        pax = _int_field(p, "pax", problems)
        cargo = _int_field(p, "cargo", problems)
        if args.widget:
            problems.extend(story_problems(p, pax, cargo))

        in_market = None
        for ea in event_pts:
            d = 0.0 if ea["ident"] == dest else gc_nm(a["lat"], a["lon"],
                                                       ea["lat"], ea["lon"])
            if d <= args.event_radius and (in_market is None or d < in_market):
                in_market = d
        exempt = dest == tail["home"]
        if p.get("exempt"):
            if in_market is None:
                problems.append("\"exempt\" needs --event with the destination "
                                "inside the event radius")
            else:
                exempt = True
        if block > ceil_f + BAND_OVER_H:
            problems.append(f"block {fmt_hm(block)} is over the "
                            f"{fmt_hm(ceil_f)} ceiling")
        elif block < ceil_f - BAND_UNDER_H and not exempt:
            problems.append(f"block {fmt_hm(block)} is below the fullness "
                            f"band for a {fmt_hm(ceil_f)} ceiling")
        feas = feasibility(lim, block)
        room = None
        if feas is None:
            problems.append("fuel or payload infeasible at this block time")
        else:
            if pax > feas["max_pax"]:
                problems.append(f"{pax} pax exceeds max {feas['max_pax']}")
            room = round(min(feas["payload_avail"] - pax * pax_allow,
                             lim["baggage"] - pax * bag_pp))
            if cargo > room:
                problems.append(f"{cargo} lbs cargo exceeds the {room} lbs "
                                f"room at {pax} pax")

        tzname = tf.timezone_at(lat=cur["lat"], lng=cur["lon"])
        if not tzname:
            reject(n, f"no time zone for {dep}", tail["tail"])
            failed = True
            continue
        tz = ZoneInfo(tzname)
        if p.get("date"):
            try:
                ld = datetime.strptime(str(p["date"]).strip(), "%d%b%y").date()
            except ValueError:
                reject(n, f"date must be DDMMMYY, got {p['date']!r}", tail["tail"])
                failed = True
                continue
        else:
            ld = datetime.now(tz).date()
        hhmm = str(p.get("dep_local", "")).replace(":", "").strip()
        if (len(hhmm) != 4 or not hhmm.isdigit() or int(hhmm[:2]) > 23
                or int(hhmm[2:]) > 59):
            reject(n, "dep_local must be HH:MM", tail["tail"])
            failed = True
            continue
        mins = int(hhmm[:2]) * 60 + int(hhmm[2:])
        rounded = int(round(mins / 5.0)) * 5
        if rounded != mins:
            notes.append(f"pick {n}: {hhmm[:2]}:{hhmm[2:]} rounded to the "
                         f"nearest 5 minutes")
        if rounded >= 24 * 60:            # 23:58 rounds into the next day
            rounded -= 24 * 60
            ld = ld + timedelta(days=1)
        dep_l = datetime(ld.year, ld.month, ld.day, rounded // 60, rounded % 60,
                         tzinfo=tz)
        dep_z = dep_l.astimezone(timezone.utc)
        sun = sun_times(cur["lat"], cur["lon"], tzname, ld)
        part = story_day_part(dep_l, sun)
        zdate = dep_z.strftime("%d%b%y").upper()
        url = (SIMBRIEF_URL.format(type=tail["icao"], orig=dep, dest=dest,
                                   reg=tail["tail"], date=zdate,
                                   deph=f"{dep_z.hour:02d}",
                                   depm=f"{dep_z.minute:02d}")
               .replace("{PAX}", str(pax))
               .replace("{CARGO_KLBS}", cargo_klbs(cargo)))
        failed = failed or bool(problems)
        out.append({
            "pick": n, "tail": tail["tail"], "model": tail["model"],
            "icao_type": tail["icao"], "dep": dep, "dep_city": cur["muni"],
            "dest": dest, "dest_city": a["muni"], "dest_name": a["name"],
            "dest_class": eff, "in_market": in_market is not None,
            "event_dist_nm": None if in_market is None else round(in_market),
            "gc_nm": round(gc), "route_nm": round(route),
            "block": fmt_hm(block), "session": fmt_hm(block + PREP_H),
            "pax": pax, "cargo": cargo, "cargo_room_at_pax": room,
            "departure": f"{dep_z:%H%M}Z / {dep_l:%H:%M} LCL",
            "dep_zulu": f"{dep_z:%H%M}Z", "dep_local": f"{dep_l:%H:%M}",
            "local_date": ld.strftime("%d%b%y").upper(), "zulu_date": zdate,
            "tz": tzname,
            "sunrise": f"{sun[0]:%H:%M}" if sun else None,
            "sunset": f"{sun[1]:%H:%M}" if sun else None,
            "day_part": part, "sun_edge": part in ("sunrise", "sunset"),
            "icon": DAY_PART_ICON[part],
            "simbrief": url, "problems": problems,
            "job": str(p.get("job", "")).strip(),
            "event": str(p.get("event") or "").strip(),
            "hook": " ".join(str(p.get("hook", "")).split()),
        })

    good = [r for r in out if "day_part" in r]
    if good:
        counts: dict[str, int] = {}
        for r in good:
            counts[r["day_part"]] = counts.get(r["day_part"], 0) + 1
        for part, c in counts.items():
            if c > 2:
                notes.append(f"{c} cards in the {part} day-part; the cap is 2")
        if len(good) > 1 and not any(r["sun_edge"] for r in good):
            notes.append("no sun-edge card on this board")
    if args.widget:
        # The board is rendered by the session verbatim. Card fields are
        # repeated in the widget, so the JSON stays compact here.
        slim = [{k: r.get(k) for k in ("pick", "tail", "dest", "departure",
                                       "zulu_date", "day_part", "block",
                                       "session", "problems")} for r in out]
        print(json.dumps({"version": SCRIPT_VERSION, "manifest": manifest,
                          "notes": notes, "picks": slim}, indent=1,
                         ensure_ascii=False))
        if not failed:
            print(WIDGET_MARK)
            print(board_html(out, args.calls))
        return 4 if failed else 0
    print(json.dumps({"version": SCRIPT_VERSION, "manifest": manifest,
                      "notes": notes, "picks": out}, indent=2))
    return 4 if failed else 0


def print_table(results, notes, ceiling, date_ddmmmyy, airports, tf, flight_date,
                manifest):
    """Step-6 decision table: one block per tail, plus departure sun times."""
    print(f"dispatch_calc v{SCRIPT_VERSION} · {manifest}")
    print(f"Block ceiling {fmt_hm(ceiling)} · date {date_ddmmmyy} · "
          f"{len(results)} candidates")
    for n in notes:
        print(f"note: {n}")
    by_tail: dict[str, list] = {}
    for c in results:
        by_tail.setdefault(c["tail"], []).append(c)
    sun_cache: dict[str, str] = {}
    for tail_id, cands in by_tail.items():
        t = cands[0]
        dep = t["dep"]
        if dep not in sun_cache:
            line = "sun n/a"
            ap = airports.get(dep)
            tzname = tf.timezone_at(lat=ap["lat"], lng=ap["lon"]) if (tf and ap) else None
            if tzname:
                ld = flight_date.astimezone(ZoneInfo(tzname)).date()
                sun = sun_times(ap["lat"], ap["lon"], tzname, ld)
                if sun:
                    w = timedelta(minutes=SUN_WINDOW_MIN)
                    sr, ss = sun
                    line = (f"sunrise {sr:%H:%M} ({sr - w:%H:%M}–{sr + w:%H:%M}) · "
                            f"sunset {ss:%H:%M} ({ss - w:%H:%M}–{ss + w:%H:%M}) "
                            f"{sr:%Z}")
            sun_cache[dep] = line
        print(f"\n{tail_id} {t['icao_type']} · {t['ops']} · at {dep} {t['dep_city']}"
              + (" · home pull" if t["home_pull_active"] else "")
              + f" · {sun_cache[dep]}")
        if t.get("tail_note"):
            print(f"  note: {t['tail_note']}")
        print(f"  {'DEST':<5} {'CITY':<18} {'REGION':<20} {'CL':<3} {'RWY':>6} "
              f"{'TYPE':<6} {'Q':>4} {'FULL':>5} {'BLOCK':>7} {'SESS':>7} "
              f"{'PAX':>3} {'CGO':>5} {'SCORE':>6} FLAGS")
        for c in cands:
            flags = []
            if c.get("fallback"):
                flags.append("FALLBACK")
            if c["event_dist_nm"] is not None:
                flags.append(f"EV{c['event_dist_nm']}")
            if c["event_tie_available"]:
                flags.append("EV-OUT")
            if c["toward_home"]:
                flags.append("home-ward")
            if c["dest"] == c["home"]:
                flags.append("HOME")
            if c.get("preferred"):
                flags.append("PREF")
            q = c["score_parts"].get("quality", 0)
            cl = c["dest_class"] + ("" if c["class_verified"] else "?")
            print(f"  {c['dest']:<5} {c['dest_city'][:18]:<18} "
                  f"{c['dest_region'][:20]:<20} {cl:<3} {c['dest_rwy_ft']:>6} "
                  f"{c['dest_type'].replace('_airport', '')[:6]:<6} {q:>4g} "
                  f"{str(c['fullness_pct']) + '%':>5} {c['block']:>7} "
                  f"{c['session']:>7} {c['max_pax']:>3} "
                  f"{c['cargo_room_at_max_pax']:>5} {c['score']:>6g} "
                  + " ".join(flags))
    print("\nCL '?' = proxy class, unverified. CGO = freight room at max pax. "
          "EV<nm> = in the event market. Card times come only from --finalize.")


# ---------------------------------------------------------------------------
# Markdown table parsing
# ---------------------------------------------------------------------------

def _split_row(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def parse_table(text: str, header: str, first_col: str | None = None,
                required: tuple = ()) -> list[dict]:
    """Return a markdown table under section `header` as a list of dicts.

    Takes the first table in the section, or the first whose header row starts
    with `first_col`. A blank line inside a table does not end it — a stray
    blank line used to truncate THE FLEET silently — but any other non-table
    line does, so the prose and the second table that follow a table are never
    merged into it. Every column in `required` must be present.
    """
    pat = re.compile(r"^#{1,4}\s+" + re.escape(header) + r"\s*$", re.M)
    m = pat.search(text)
    if not m:
        raise DataError(f"section not found: {header}")
    rest = text[m.end():]
    stop = re.search(r"^#{1,4}\s+\S", rest, re.M)
    if stop:
        rest = rest[: stop.start()]

    tables, rows, cols = [], [], None
    for line in rest.splitlines():
        s = line.strip()
        if not s:
            continue
        if not s.startswith("|"):
            if cols is not None:
                tables.append((cols, rows))
                rows, cols = [], None
            continue
        cells = _split_row(s)
        if cols is None:
            cols = cells
            continue
        if all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells):
            continue           # separator row
        if len(cells) < len(cols):
            cells += [""] * (len(cols) - len(cells))
        rows.append(dict(zip(cols, cells[: len(cols)])))
    if cols is not None:
        tables.append((cols, rows))

    for cols, rows in tables:
        if first_col is None or (cols and cols[0] == first_col):
            missing = [c for c in required if c not in cols]
            if missing:
                raise DataError(f"{header}: missing column(s) {', '.join(missing)}")
            return rows
    want = f" starting with column {first_col!r}" if first_col else ""
    raise DataError(f"no table{want} under section: {header}")


def _num(v: str, cast=float, default=None):
    v = (v or "").strip().replace(",", "")
    if not v:
        return default
    try:
        return cast(v)
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Document model
# ---------------------------------------------------------------------------

CLASSES = ("turboprop", "mid_jet", "large_jet")
OPS_MODES = ("based", "regional", "floating")
STATUSES = ("active", "stored")
ROUTE_RE = re.compile(r"^\s*([A-Z0-9]{3,4})\s*(?:→|->|[-–—])\s*([A-Z0-9]{3,4})\s*$")


def _req_num(table: str, key: str, field: str, v: str, cast=float):
    """A required numeric cell: a bad value is exit 3 with the cell named."""
    n = _num(v, cast)
    if n is None:
        raise DataError(f"{table}: {key} has a non-numeric {field} ({v!r})")
    return n


class Doc:
    """State plus reference.

    v7.2 split the old state file in two. `dispatch_state.md` (the project
    doc, staged every session) holds only what a flight changes: THE FLEET and
    THE LOGBOOK. `reference.md` (in the repo, fetched beside this script at the
    same tag) holds what rarely changes: MODEL LIMITS, REGION TABLE, AIRPORT
    CLASS REGISTER, PREFERRED FIELDS and TAIL NOTES. Each carries its own
    schema header and is checked against this script.
    """

    def __init__(self, path: str, ref_path: str | None = None):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        ref_path = ref_path or REF_DEFAULT
        with open(ref_path, encoding="utf-8") as fh:
            ref = fh.read()
        self.path, self.ref_path = path, ref_path
        m = re.search(r"Reference v([\d.]+)", ref)
        self.ref_schema = m.group(1) if m else None
        if self.ref_schema != REF_SCHEMA:
            raise DataError(f"reference schema {self.ref_schema or '(none)'} != "
                            f"{REF_SCHEMA} expected by script v{SCRIPT_VERSION} — "
                            f"fetch reference.md from the same tag as the script")

        # Schema handshake. The script parses this file by section name and
        # column name; a state file from another schema fails here, by name,
        # rather than parsing into something subtly wrong.
        m = re.search(r"Schema v([\d.]+)", text)
        self.schema = m.group(1) if m else None
        if self.schema != STATE_SCHEMA:
            raise DataError(f"state schema {self.schema or '(none)'} != "
                            f"{STATE_SCHEMA} expected by script v{SCRIPT_VERSION}")

        self.fleet = []
        for r in parse_table(text, "THE FLEET", "Tail", required=(
                "Tail", "Model", "ICAO", "Class", "Ops", "Status", "Plan KTAS",
                "Min rwy", "Home", "Current", "Away")):
            if not r.get("Tail"):
                continue
            t = r["Tail"].strip()
            rec = {
                "tail": t,
                "model": r["Model"].strip(),
                "icao": r["ICAO"].strip(),
                "cls": r["Class"].strip(),
                "ops": r["Ops"].strip().lower(),
                "status": r["Status"].strip().lower(),
                "ktas": _req_num("THE FLEET", t, "Plan KTAS", r["Plan KTAS"]),
                "min_rwy": _req_num("THE FLEET", t, "Min rwy", r["Min rwy"], int),
                "home": r["Home"].strip().upper(),
                "current": r["Current"].strip().upper(),
                "away": _req_num("THE FLEET", t, "Away", r["Away"], int),
            }
            for field, ok in (("cls", CLASSES), ("ops", OPS_MODES),
                              ("status", STATUSES)):
                if rec[field] not in ok:
                    raise DataError(f"THE FLEET: {t} has {field} {rec[field]!r}; "
                                    f"expected one of {', '.join(ok)}")
            if rec["ktas"] <= 0:
                raise DataError(f"THE FLEET: {t} Plan KTAS must be positive")
            self.fleet.append(rec)
        if not self.fleet:
            raise DataError("THE FLEET: no tails parsed")

        self.limits = {}
        num_cols = ("Seats", "BOW", "MZFW", "MTOW", "MLW", "Max fuel", "Baggage",
                    "Plan burn", "Reserve")
        for r in parse_table(ref, "MODEL LIMITS", "Model",
                             required=("Model", "ICAO", "Max GC") + num_cols):
            if not r.get("Model"):
                continue
            mdl = r["Model"].strip()
            v = {c: _req_num("MODEL LIMITS", mdl, c, r[c],
                             int if c == "Seats" else float) for c in num_cols}
            self.limits[mdl] = {
                "icao": r["ICAO"].strip(), "seats": v["Seats"], "bow": v["BOW"],
                "mzfw": v["MZFW"], "mtow": v["MTOW"], "mlw": v["MLW"],
                "max_fuel": v["Max fuel"], "baggage": v["Baggage"],
                "burn": v["Plan burn"], "reserve": v["Reserve"],
                "max_gc": (None if not r["Max GC"].strip() or r["Max GC"].strip()
                           in ("—", "-") else _req_num("MODEL LIMITS", mdl,
                                                        "Max GC", r["Max GC"])),
            }
        for f in self.fleet:
            if f["model"] not in self.limits:
                raise DataError(f"THE FLEET: {f['tail']} model {f['model']!r} has "
                                f"no MODEL LIMITS row")

        # Region table. The Scope column keeps US state codes and ISO country
        # codes in separate namespaces — they collide otherwise (CO, CA, MS...).
        self.region_by_state, self.region_by_country = {}, {}
        self.regions = set()
        for r in parse_table(ref, "REGION TABLE", "Region",
                             required=("Region", "Scope", "Members")):
            region = r.get("Region", "").strip()
            scope = r.get("Scope", "").strip().lower()
            if not region or not r.get("Members"):
                continue
            if scope not in ("us_state", "country"):
                raise DataError(f"REGION TABLE: {region} scope {scope!r}; expected "
                                f"us_state or country")
            self.regions.add(region)
            target = (self.region_by_state if scope == "us_state"
                      else self.region_by_country)
            for tok in r["Members"].split():
                tok = tok.strip().strip(",").upper()
                if len(tok) == 2:
                    target.setdefault(tok, region)

        # Affinity: the regions each class does NOT score the affinity bonus
        # for. Region `Other` never scores it. Parsed, so the table governs.
        self.affinity_excluded = {}
        for r in parse_table(ref, "REGION TABLE", "Class",
                             required=("Class", "Excluded regions")):
            cls = r.get("Class", "").strip()
            if cls not in CLASSES:
                raise DataError(f"REGION TABLE affinity: unknown class {cls!r}")
            raw = r.get("Excluded regions", "").strip()
            names = ([] if raw in ("", "—", "-", "none")
                     else [x.strip() for x in raw.split(",") if x.strip()])
            bad = [x for x in names if x not in self.regions]
            if bad:
                raise DataError(f"REGION TABLE affinity: {cls} excludes unknown "
                                f"region(s) {', '.join(bad)}")
            self.affinity_excluded[cls] = set(names)
        missing = [c for c in CLASSES if c not in self.affinity_excluded]
        if missing:
            raise DataError(f"REGION TABLE affinity: no row for {', '.join(missing)}")

        self.class_register = {}
        for r in parse_table(ref, "AIRPORT CLASS REGISTER", "ICAO",
                             required=("ICAO", "Class")):
            if r.get("ICAO") and r.get("Class"):
                self.class_register[r["ICAO"].strip().upper()] = \
                    r["Class"].strip().upper()

        # Kyle's preferred destinations: score the quality cap, and override
        # the military exclusion. Unknown idents are checked in preflight.
        self.preferred = {}
        for r in parse_table(ref, "PREFERRED FIELDS", "ICAO",
                             required=("ICAO", "Note")):
            icao = r.get("ICAO", "").strip().upper()
            if icao:
                if icao in self.preferred:
                    raise DataError(f"PREFERRED FIELDS: {icao} listed twice")
                self.preferred[icao] = r.get("Note", "").strip()

        # A Route that does not parse is a hard error. It used to be skipped
        # silently: rows written `KPWK-KDAB` never matched an arrow-only
        # pattern, so recency and region rotation read an empty logbook from
        # about 19 SEP to 12 NOV 2026 and scored every candidate the same.
        self.logbook = []
        self.logbook_rows = 0
        for r in parse_table(text, "THE LOGBOOK", "Date",
                             required=("Date", "Reg", "Route", "Job type")):
            if not any(v.strip() for v in r.values()):
                continue
            self.logbook_rows += 1
            route = r.get("Route", "")
            mm = ROUTE_RE.match(route)
            if not mm:
                raise DataError(f"THE LOGBOOK: unparseable Route {route!r} — "
                                f"write it as KAAA-KBBB")
            self.logbook.append({
                "date": r.get("Date", ""),
                "reg": r.get("Reg", "").strip(),
                "dep": mm.group(1),
                "dest": mm.group(2),
                "job": r.get("Job type", ""),
                "event": r.get("Event", ""),
                "hook": r.get("Hook", ""),
            })
        # Newest last in the document; work newest-first internally.
        self.logbook_recent = list(reversed(self.logbook))

        # Tail notes: story material for RULE 5, printed under each tail in
        # the board table so a session never opens another document for them.
        self.tail_notes = {}
        sec = re.search(r"^###\s+TAIL NOTES\s*$(.*?)(?=^#{1,3}\s|\Z)", ref,
                        re.M | re.S)
        if not sec:
            raise DataError("reference: section not found: TAIL NOTES")
        for m in re.finditer(r"^- \*\*(\w+)\*\* — (.*?)(?=^- \*\*|\Z)",
                             sec.group(1), re.M | re.S):
            self.tail_notes[m.group(1)] = " ".join(m.group(2).split())

    def manifest(self, airports: dict | None = None) -> str:
        active = sum(1 for f in self.fleet if f["status"] == "active")
        s = (f"state: {len(self.fleet)} tails ({active} active) · "
             f"{len(self.limits)} models · {len(self.class_register)} register · "
             f"{len(self.logbook)}/{self.logbook_rows} logbook rows · "
             f"{len(self.preferred)} preferred")
        if airports is not None:
            s += f" · {len(airports):,} airports"
        return s

    def limits_for(self, model: str) -> dict:
        if model not in self.limits:
            raise DataError(f"no MODEL LIMITS row for model: {model}")
        return self.limits[model]


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------

USABLE_TYPES = {"large_airport", "medium_airport", "small_airport", "seaplane_base"}
AIRPORT_COLS = ("ident", "type", "name", "latitude_deg", "longitude_deg",
                "elevation_ft", "iso_country", "iso_region", "municipality",
                "scheduled_service", "icao_code")
RUNWAY_COLS = ("airport_ident", "length_ft", "width_ft", "surface", "closed")
# Floor on usable airports with a land runway. The full OurAirports set holds
# about 49,000 usable airports; a truncated download, an HTML error page saved
# as CSV, or a renamed column lands far below it. A trimmed test snapshot
# passes --data-floor 0.
DATA_FLOOR_DEFAULT = 20000


def _check_cols(fh, path: str, need: tuple) -> csv.DictReader:
    rd = csv.DictReader(fh)
    have = set(rd.fieldnames or [])
    missing = [c for c in need if c not in have]
    if missing:
        raise DataError(f"{path}: missing column(s) {', '.join(missing)} — "
                        f"OurAirports schema changed or the download failed")
    return rd


def load_airports(data_dir: str, floor: int = DATA_FLOOR_DEFAULT) -> dict:
    runways: dict[str, int] = {}
    widths: dict[str, int] = {}
    paved: dict[str, bool] = {}
    water: set[str] = set()
    rpath = os.path.join(data_dir, "runways.csv")
    with open(rpath, encoding="utf-8") as fh:
        for row in _check_cols(fh, rpath, RUNWAY_COLS):
            if row.get("closed") == "1":
                continue
            ident = row.get("airport_ident") or ""
            try:
                length = int(row.get("length_ft") or 0)
            except ValueError:
                length = 0
            try:
                width = int(row.get("width_ft") or 0)
            except ValueError:
                width = 0
            surf = surface_class(row.get("surface"))
            if surf == "water":
                water.add(ident)
                continue
            # Water lanes are excluded from the land maximum. Taking the max
            # across every runway let a seaplane lane stand in for pavement:
            # 43 US fields were inflated and 24 of them cleared the C750's
            # 5,000 ft floor on water alone — Sky Harbor Duluth reported
            # 10,000 ft against a 2,602 ft land strip, St Augustine 12,000
            # against 8,001. The amphibian reads `water` separately, so
            # nothing it needs is lost here.
            if length > runways.get(ident, 0):
                runways[ident] = length
                widths[ident] = width
                paved[ident] = surf == "paved"

    airports: dict[str, dict] = {}
    apath = os.path.join(data_dir, "airports.csv")
    with open(apath, encoding="utf-8") as fh:
        for row in _check_cols(fh, apath, AIRPORT_COLS):
            if row.get("type") not in USABLE_TYPES:
                continue
            ident = row.get("ident") or ""
            if not ident:
                continue
            try:
                lat = float(row["latitude_deg"])
                lon = float(row["longitude_deg"])
            except (TypeError, ValueError, KeyError):
                continue
            airports[ident] = {
                "ident": ident,
                "name": row.get("name", ""),
                "muni": row.get("municipality", "") or "",
                "lat": lat,
                "lon": lon,
                "country": row.get("iso_country", ""),
                "region_code": (row.get("iso_region", "") or "").split("-")[-1],
                "iso_region": row.get("iso_region", "") or "",
                "type": row.get("type", ""),
                "sched": (row.get("scheduled_service", "") or "") == "yes",
                "rwy": runways.get(ident, 0),
                "rwy_width": widths.get(ident, 0),
                "paved": paved.get(ident, False),
                "water": ident in water or row.get("type") == "seaplane_base",
                "elev": _num(row.get("elevation_ft", ""), float, 0.0),
                "icao_code": (row.get("icao_code") or "").strip().upper(),
            }
    for old in [k for k, a in airports.items()
                if ICAO_RE.match(a["icao_code"]) and a["icao_code"] != k]:
        new = airports[old]["icao_code"]
        if new not in airports:
            airports[new] = dict(airports.pop(old), ident=new)
    with_rwy = sum(1 for a in airports.values() if a["rwy"] > 0)
    if with_rwy < floor:
        raise DataError(f"only {with_rwy:,} airports with a land runway (floor "
                        f"{floor:,}) — airport data truncated or malformed")
    return airports


def proxy_class(ap: dict) -> str:
    """Coarse airspace-tier proxy from the OurAirports `type` field.

    Returns a string of candidate classes. A verified class always comes from
    AIRPORT CLASS REGISTER instead; this is only the fallback for the fields
    the register does not list, none of which is Class B.
    """
    t = ap["type"]
    if t == "seaplane_base":
        return "W"
    if ap["country"] == "US":
        # v7.1: the register holds every US Class B airport (37 primaries,
        # checked against the FAA list 12 NOV 2026, plus Nellis and Love Field
        # inside a primary's surface area), so an unregistered US hub is not B.
        return {"large_airport": "C", "medium_airport": "CD",
                "small_airport": "DE"}.get(t, "E")
    if t == "large_airport":
        return "C"
    if t == "medium_airport":
        return "C" if ap["sched"] else "D"
    return "E"


def tier_ok(ap: dict, eff_class: str, cls: str, allow_b: bool) -> bool:
    if eff_class == "W":
        return False                      # water handled separately
    allowed = set(TIER_ALLOWED[cls])
    if cls == "large_jet" and ap["rwy"] >= LARGE_JET_CLASS_D_MIN_RWY:
        allowed.add("D")
    if allow_b:
        allowed.add("B")
    return bool(set(eff_class) & allowed)


def region_of(ap: dict, doc: Doc) -> str:
    if ap["country"] == "US":
        return doc.region_by_state.get(ap["region_code"], "Other")
    return doc.region_by_country.get(ap["country"], "Other")


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------

R_NM = 3440.065


def gc_nm(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_NM * math.asin(min(1.0, math.sqrt(a)))


def overhead_h(gc: float) -> float:
    pts = OVERHEAD_ANCHORS
    if gc <= pts[0][0]:
        return pts[0][1]
    if gc >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= gc <= x1:
            return y0 + (y1 - y0) * (gc - x0) / (x1 - x0)
    return pts[-1][1]


def fmt_hm(hours: float) -> str:
    total = int(round(hours * 60))
    return f"{total // 60}h {total % 60:02d}m"


# ---------------------------------------------------------------------------
# Feasibility (RULES.md → LOAD PLANNING)
# ---------------------------------------------------------------------------

def feasibility(lim: dict, block_h: float) -> dict | None:
    pax_allowance = PAX_ALLOWANCE_LB_OVERRIDE.get(lim["icao"], PAX_ALLOWANCE_LB)
    bag_per_pax = BAG_PER_PAX_LB_OVERRIDE.get(lim["icao"], BAG_PER_PAX_LB)

    fuel_plan = lim["burn"] * block_h + lim["reserve"]
    if fuel_plan > lim["max_fuel"]:
        return None                       # infeasible regardless of range

    if lim["mzfw"] and lim["mzfw"] < lim["mtow"]:
        payload_avail = min(lim["mzfw"] - lim["bow"],
                            lim["mtow"] - lim["bow"] - fuel_plan)
    else:
        payload_avail = lim["mtow"] - lim["bow"] - fuel_plan
    if payload_avail <= 0:
        return None

    max_pax = min(lim["seats"],
                  int(payload_avail // pax_allowance),
                  int(lim["baggage"] // bag_per_pax))
    while max_pax > 0:
        ldg = lim["bow"] + max_pax * pax_allowance + lim["reserve"]
        if ldg <= lim["mlw"]:
            break
        max_pax -= 1

    cargo_only = min(payload_avail, lim["baggage"])
    return {
        "fuel_plan": round(fuel_plan),
        "payload_avail": round(payload_avail),
        "max_pax": max_pax,
        "cargo_cap_freight": round(cargo_only),
        "cargo_room_at_max_pax": round(
            min(payload_avail - max_pax * pax_allowance,
                lim["baggage"] - max_pax * bag_per_pax)),
    }


# ---------------------------------------------------------------------------
# Scoring (RULES.md → VARIETY ENGINE)
# ---------------------------------------------------------------------------

def build_history(doc: Doc, airports: dict) -> dict:
    recent = doc.logbook_recent
    dests = [f["dest"] for f in recent]
    regions = []
    for f in recent:
        ap = airports.get(f["dest"])
        regions.append(region_of(ap, doc) if ap else "Other")
    return {
        "dest_last3": set(dests[:3]),
        "dest_last10": set(dests[:10]),
        "dest_all": set(dests),
        "region_last1": regions[0] if regions else None,
        "region_last2": regions[:2],
        "region_last5": set(regions[:5]),
    }


def score_candidate(ap, tail, lim, doc, hist, block_h, ceiling_h,
                    dest_region, home_ap, cur_ap, event_dist_nm=None) -> dict:
    parts = {}

    # Recency — fleet-wide, larger penalty only.
    if ap["ident"] in hist["dest_last3"]:
        parts["recency"] = RECENCY_LAST3
    elif ap["ident"] in hist["dest_last10"]:
        parts["recency"] = RECENCY_LAST10
    elif ap["ident"] not in hist["dest_all"]:
        parts["recency"] = RECENCY_NEVER
    else:
        parts["recency"] = 0

    # Region rotation.
    l2 = hist["region_last2"]
    if len(l2) == 2 and l2[0] == dest_region and l2[1] == dest_region:
        parts["region"] = REGION_BOTH_LAST2
    elif hist["region_last1"] == dest_region:
        parts["region"] = REGION_LAST1
    elif dest_region not in hist["region_last5"]:
        parts["region"] = REGION_ABSENT_LAST5
    else:
        parts["region"] = 0

    # Home pull, by operating model. Replaces v3.x soft pull, which applied one
    # weak nudge to every tail and had no reason in the fiction. Magnitudes are
    # sized against the ~60-point baseline a strong ordinary candidate reaches;
    # at the old +10/+25 the pull could never actually move a board.
    parts["home_pull"] = 0
    toward_home = False
    away = tail["current"] != tail["home"]
    if home_ap and cur_ap and away and tail["ops"] != "floating":
        d_cur = gc_nm(cur_ap["lat"], cur_ap["lon"], home_ap["lat"], home_ap["lon"])
        d_dest = gc_nm(ap["lat"], ap["lon"], home_ap["lat"], home_ap["lon"])
        is_home = ap["ident"] == tail["home"]
        toward_home = is_home or (d_cur > 0 and d_dest <= 0.75 * d_cur)

        if tail["ops"] == "based":
            # Out-and-back: the aircraft is wanted back at its field.
            if is_home:
                parts["home_pull"] = HOME_BASED_HOME
            elif toward_home:
                parts["home_pull"] = HOME_BASED_TOWARD
        elif tail["ops"] == "regional":
            # Works a territory. No pull at all while still inside it; the pull
            # points at the home region, not the exact field.
            home_region = region_of(home_ap, doc)
            cur_region = region_of(cur_ap, doc)
            if cur_region != home_region:
                if is_home:
                    parts["home_pull"] = HOME_REGIONAL_HOME
                elif dest_region == home_region:
                    parts["home_pull"] = HOME_REGIONAL_REGION
                elif toward_home:
                    parts["home_pull"] = HOME_REGIONAL_TOWARD

    # Aircraft-region affinity, from the REGION TABLE affinity rows.
    parts["affinity"] = (AFFINITY_BONUS
                         if dest_region != "Other"
                         and dest_region not in doc.affinity_excluded[tail["cls"]]
                         else 0)

    # Event market. The flag is the output; nothing is scored for it.
    in_market = event_dist_nm is not None

    # Destination quality — the discriminator inside a flat fullness band.
    parts["quality"] = quality_score(ap, tail["cls"],
                                     ap["ident"] in doc.preferred)

    # Fullness.
    fullness = block_h / ceiling_h if ceiling_h > 0 else 0
    parts["fullness"] = fullness_score(block_h, ceiling_h)
    # Two legs are short by nature and exempt from the band floor: an in-market
    # leg and the tail's own home base. Both are scored as in-band. Before v7.0
    # the home leg kept BAND_SHORT_PTS, so a based tail asked for 3.5 h ranked
    # its own home field last of 222 — the one leg the home pull exists for.
    if in_market or ap["ident"] == tail["home"]:
        parts["fullness"] = BAND_FULL_PTS
    if in_market:
        parts["region"] = max(0, parts["region"])

    return {
        "parts": parts,
        "total": round(sum(parts.values()), 1),
        "fullness_pct": round(fullness * 100),
        "toward_home": toward_home,
        "in_market": in_market,
        "event_dist_nm": None if event_dist_nm is None else round(event_dist_nm),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def print_rules() -> None:
    """Print every scoring constant. RULES.md points here instead of restating
    them, so there is exactly one place a number can be wrong."""
    w = 30
    print(f"Meridian Air Dispatch — active scoring constants · script "
          f"v{SCRIPT_VERSION} · state schema {STATE_SCHEMA}\n")
    print("Timing")
    print(f"  {'route factor':<{w}} x{ROUTE_FACTOR}")
    print(f"  {'taxi':<{w}} {TAXI_H:.2f} h")
    print(f"  {'prep (session time only)':<{w}} {PREP_H:.2f} h")
    print(f"  {'ceiling margin':<{w}} {CEILING_MARGIN_H:.2f} h")
    print("  overhead anchors (nm -> h)   "
          + ", ".join(f"{int(x)}:{y:.2f}" for x, y in OVERHEAD_ANCHORS))
    print("\nLoad")
    print(f"  {'pax allowance':<{w}} {PAX_ALLOWANCE_LB} lb")
    print(f"  {'of which baggage':<{w}} {BAG_PER_PAX_LB} lb")
    for icao in sorted(PAX_ALLOWANCE_LB_OVERRIDE):
        print(f"  {'override ' + icao:<{w}} {PAX_ALLOWANCE_LB_OVERRIDE[icao]} lb "
              f"({BAG_PER_PAX_LB_OVERRIDE[icao]} lb bag)")
    print("\nField quality")
    print(f"  {'minimum width':<{w}} {FIELD_MIN_WIDTH_FT} ft")
    print(f"  {'large jet on Class D needs':<{w}} {LARGE_JET_CLASS_D_MIN_RWY} ft")
    print("\nScoring")
    for label, val in (
        ("recency: in last 3", RECENCY_LAST3),
        ("recency: in last 10", RECENCY_LAST10),
        ("recency: never flown", RECENCY_NEVER),
        ("region: both of last 2", REGION_BOTH_LAST2),
        ("region: last 1 only", REGION_LAST1),
        ("region: absent from last 5", REGION_ABSENT_LAST5),
        ("home pull: based, home", HOME_BASED_HOME),
        ("home pull: based, toward", HOME_BASED_TOWARD),
        ("home pull: regional, home", HOME_REGIONAL_HOME),
        ("home pull: regional, region", HOME_REGIONAL_REGION),
        ("home pull: regional, toward", HOME_REGIONAL_TOWARD),
        ("aircraft-region affinity", AFFINITY_BONUS),
    ):
        print(f"  {label:<{w}} {val:+d}")
    print("\nFullness band (absolute, not a fraction of the ceiling)")
    print(f"  {'full credit from':<{w}} ceiling -{BAND_UNDER_H * 60:.0f} min")
    print(f"  {'through':<{w}} ceiling +{BAND_OVER_H * 60:.0f} min")
    print(f"  {'credit inside the band':<{w}} {BAND_FULL_PTS:+.0f}")
    print(f"  {'below the floor':<{w}} not offered "
          f"(in-market legs and home base exempt, scored in-band)")
    print("\nDestination quality (airport `type` is deliberately not scored)")
    for cls, anchors in QUALITY_RWY_ANCHORS.items():
        print(f"  {'runway ' + cls + ' (ft:pts)':<{w}} "
              + ", ".join(f"{int(x)}:{y:+.0f}" for x, y in anchors))
    print(f"  {'scheduled service':<{w}} {QUALITY_SCHEDULED:+.0f}")
    print(f"  {'PREFERRED FIELDS':<{w}} {QUALITY_MAX:.0f} (the cap)")
    print(f"  {'military, no service':<{w}} not offered unless preferred")
    print(f"\nEvent market radius            {EVENT_RADIUS_NM} nm (flag only, "
          f"no score)")
    print(f"Sun window                     ±{SUN_WINDOW_MIN} min of sunrise/sunset")
    print("\nInvoice (--invoice)")
    for cls in ("turboprop", "mid_jet", "large_jet"):
        print(f"  {cls + ' dry rate / crew day':<{w}} ${INVOICE_DRY_RATE[cls]:,}/hr · "
              f"${INVOICE_CREW_DAY[cls]:,} at {INVOICE_CREW_DAY_MIN_BLOCK_H:g}h+ block")
    print(f"  {'catering (jets, pax > 0)':<{w}} ${INVOICE_CATERING_PER_PAX}/pax")
    print(f"  {'federal excise tax':<{w}} {INVOICE_FET_RATE * 100:.1f}% of charter + "
          f"fuel, domestic only")
    print(f"  {'Jet-A':<{w}} {JET_A_LB_PER_GAL} lb/gal")
    print(f"Calibration warning (--calib)  miss > {CALIB_WARN_MIN:g} min on a leg "
          f"> {CALIB_WARN_GC:g} nm GC")
    print(f"Candidates per tail (--top)    {TOP_DEFAULT} default, {TOP_MAX} max")
    print(f"Default --date                 today in {HOME_TZ}")


# ---------------------------------------------------------------------------
# v7.3 — the board widget (E4)
# ---------------------------------------------------------------------------
#
# The RULE 1 card template lives here, not in RULES.md. Finalize fills it from
# the same values it computes, plus the story fields Dispatch writes into each
# pick (job, event, hook), and prints one finished widget. The session copies
# it into the visualize tool verbatim. A template kept in one place cannot
# drift between sessions; a template cloned by hand four times a board can.

JOB_TYPES = ("Sports charter", "Corporate charter", "Entertainment charter",
             "Freight run", "Ferry flight", "Medical charter", "VIP charter",
             "Owner trip")
WIDGET_MARK = "----- WIDGET (render verbatim) -----"
HOOK_MIN_SENTENCES = 3

CARD_CSS = """<style>
.mb{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.mc{max-width:320px;background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;overflow:hidden;font-family:sans-serif}
.mc-hd{padding:16px 20px 8px}
.mc-n{font-size:11px;text-transform:uppercase;letter-spacing:0.02em;color:#888780;font-weight:400}
.mc-tail{font-size:22px;font-weight:500;color:#2C2C2A;margin-top:2px}
.mc-type{font-size:12px;color:#5F5E5A;margin-top:1px}
.mc-rt{background:#F1EFE8;padding:12px 20px;display:flex;align-items:center;justify-content:space-between}
.mc-rt-r{text-align:right}
.mc-icao{font-size:18px;font-weight:500;color:#2C2C2A}
.mc-city{font-size:11px;color:#888780}
.mc-arw{color:#888780;font-size:18px}
.mc-st{padding:16px 20px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.mc-c{background:#F1EFE8;border-radius:8px;padding:8px}
.mc-c-dep{display:flex;align-items:center;justify-content:space-between}
.mc-c-ses{background:#E6F1FB}
.mc-k{font-size:11px;text-transform:uppercase;color:#888780}
.mc-v{font-size:14px;font-weight:500;color:#2C2C2A}
.mc-c-ses .mc-k{color:#185FA5}
.mc-c-ses .mc-v{color:#185FA5}
.mc-tod{font-size:16px;color:#854F0B}
.mc-ft{padding:0 20px 20px}
.mc-bd{display:flex;gap:6px;margin-bottom:10px}
.mc-b{background:#F1EFE8;color:#5F5E5A;font-size:12px;padding:4px 10px;border-radius:8px}
.mc-b-ev{background:#E6F1FB;color:#185FA5}
.mc-hk{font-size:12px;line-height:1.7;color:#5F5E5A;margin:0 0 14px}
.mc .mc-fly{width:100%;background:transparent;border:0.5px solid #B4B2A9;border-radius:8px;padding:10px;font-size:13px;font-weight:500;color:#2C2C2A;cursor:pointer;margin-bottom:8px}
.mc .mc-sb{display:block;width:100%;box-sizing:border-box;text-align:center;background:transparent;border:0.5px solid #B4B2A9;border-radius:8px;padding:10px;font-size:13px;font-weight:500;color:#2C2C2A;text-decoration:none}
.mb-foot{font-size:11px;color:#888780;margin-top:8px;font-family:sans-serif}
</style>"""


def story_problems(p: dict, pax: int, cargo: int) -> list:
    """The parts of RULE 5 a script can check; the rest stays judgment."""
    probs = []
    job = str(p.get("job", "")).strip()
    if job not in JOB_TYPES:
        probs.append(f"job {job!r} is not a RULE 1 job type "
                     f"({', '.join(JOB_TYPES)})")
    if job == "Ferry flight" and (pax or cargo):
        probs.append("a Ferry flight carries 0 pax and 0 cargo")
    hook = " ".join(str(p.get("hook", "")).split())
    n = len(re.findall(r"[.!?](?=\s|$)", hook))
    if n < HOOK_MIN_SENTENCES:
        probs.append(f"hook has {n} sentence(s); RULE 5 needs at least "
                     f"{HOOK_MIN_SENTENCES}")
    ev = str(p.get("event") or "").strip()
    if len(ev) > 40:
        probs.append("event badge over 40 characters; keep it concise")
    return probs


def _card(n: int, total: int, r: dict) -> str:
    e = html.escape
    badges = f'<span class="mc-b">{e(r["job"])}</span>'
    if r["event"]:
        badges += f'<span class="mc-b mc-b-ev">{e(r["event"])}</span>'
    z, lcl = r["departure"].split(" / ")
    prompt = f"I want to fly Mission {n} — {r['tail']} {r['dep']} to {r['dest']}"
    return (
        f'<div class="mc"><div class="mc-hd"><div class="mc-n">Mission {n} of '
        f'{total}</div><div class="mc-tail">{e(r["tail"])}</div><div '
        f'class="mc-type">{e(r["model"])}</div></div>'
        f'<div class="mc-rt"><div><div class="mc-icao">{e(r["dep"])}</div><div '
        f'class="mc-city">{e(r["dep_city"])}</div></div><i class="ti '
        f'ti-arrow-right mc-arw" aria-hidden="true"></i><div class="mc-rt-r">'
        f'<div class="mc-icao">{e(r["dest"])}</div><div class="mc-city">'
        f'{e(r["dest_city"])}</div></div></div>'
        f'<div class="mc-st"><div class="mc-c mc-c-dep"><div><div class="mc-k">'
        f'Departure</div><div class="mc-v">{e(z)} / {e(lcl)}</div></div><i '
        f'class="ti {r["icon"]} mc-tod" aria-hidden="true"></i></div>'
        f'<div class="mc-c"><div class="mc-k">Block time</div><div class="mc-v">'
        f'{r["block"]}</div></div><div class="mc-c mc-c-ses"><div class="mc-k">'
        f'Session time</div><div class="mc-v">{r["session"]}</div></div>'
        f'<div class="mc-c"><div class="mc-k">Passengers</div><div class="mc-v">'
        f'{r["pax"]} pax</div></div><div class="mc-c"><div class="mc-k">Cargo'
        f'</div><div class="mc-v">{r["cargo"]} lbs</div></div><div class="mc-c">'
        f'<div class="mc-k">Route dist</div><div class="mc-v">{r["route_nm"]} nm'
        f'</div></div></div>'
        f'<div class="mc-ft"><div class="mc-bd">{badges}</div><p class="mc-hk">'
        f'{e(r["hook"])}</p><button class="mc-fly" onclick="sendPrompt('
        f'{e(json.dumps(prompt))})">Fly this mission ↗</button><a class="mc-sb" '
        f'href="{e(r["simbrief"])}" target="_blank">Open in SimBrief ↗</a>'
        f'</div></div>')


def board_html(rows: list, calls: int | None) -> str:
    total = len(rows)
    cards = "\n".join(_card(i, total, r) for i, r in enumerate(rows, 1))
    foot = (f'\n<div class="mb-foot">Board built in {calls} tool calls</div>'
            if calls else "")
    return f'{CARD_CSS}\n<div class="mb">\n{cards}\n</div>{foot}'


# ---------------------------------------------------------------------------
# v7.3 — invoice, calibration and flight logging (E6)
# ---------------------------------------------------------------------------
#
# These rates used to live in RULES.md and TEMPLATES.md, the one set of numbers
# outside this file. TEMPLATES.md now says which lines appear and in what
# order; the amounts come from --invoice.
JET_A_LB_PER_GAL = 6.7
INVOICE_DRY_RATE = {"turboprop": 1500, "mid_jet": 3200, "large_jet": 6200}
INVOICE_CREW_DAY = {"turboprop": 600, "mid_jet": 1200, "large_jet": 2500}
INVOICE_CATERING_PER_PAX = 65
INVOICE_CREW_DAY_MIN_BLOCK_H = 2.0
INVOICE_FET_RATE = 0.075     # 26 USC 4261: charter and fuel, domestic legs only

# --calib flags a miss worth questioning: more than this many minutes on a leg
# longer than this many great-circle nm. Percentage is not the test at short
# range (RULES.md → FLIGHT TIME).
CALIB_WARN_MIN = 5.0
CALIB_WARN_GC = 300.0
LOGBOOK_WINDOW = 10


def parse_block(v) -> float:
    """'1h 46m', '1:46' or '106' (minutes) -> hours."""
    t = str(v).strip().lower()
    m = re.fullmatch(r"(\d+)\s*h\s*(\d+)\s*m?", t) or re.fullmatch(r"(\d+):(\d{2})", t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60
    if re.fullmatch(r"\d+", t):
        return int(t) / 60
    raise ValueError(f"block {v!r}: use '1h 46m', '1:46' or minutes")


def _money(x: float) -> str:
    return f"{x:,.2f}"


def _cents(x: float) -> float:
    """Round money half-up to the cent (float rounding can drop half a cent)."""
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def invoice(args, doc, airports) -> int:
    tail = next((f for f in doc.fleet if f["tail"].upper() == (args.tail or "").upper()), None)
    errs = []
    if tail is None:
        errs.append(f"unknown tail {args.tail!r}")
    dep = (args.dep or (tail["current"] if tail else "")).upper()
    dest = (args.dest or "").upper()
    for ident in (dep, dest):
        if ident not in airports:
            errs.append(f"{ident or '(blank)'} not in the airport database")
    try:
        block = parse_block(args.block)
    except ValueError as exc:
        errs.append(str(exc))
        block = 0
    for name in ("trip_fuel", "fuel_price"):
        if getattr(args, name) is None:
            errs.append(f"--{name.replace('_', '-')} is required")
    if errs:
        print(json.dumps({"problems": errs}, indent=1))
        return 4
    cls = tail["cls"]
    pax = args.pax or 0
    domestic = airports[dep]["country"] == "US" and airports[dest]["country"] == "US"
    hrs = round(block, 2)
    items = []
    charter = hrs * INVOICE_DRY_RATE[cls]
    items.append({"desc": "Aircraft charter — dry hourly rate", "qty": f"{hrs:.2f} HR",
                  "rate": f"${_money(INVOICE_DRY_RATE[cls])}/HR",
                  "amount": _cents(charter)})
    gal = args.trip_fuel / JET_A_LB_PER_GAL
    fuel = round(gal) * args.fuel_price
    items.append({"desc": "Jet-A fuel" + (" (price estimated)" if args.fuel_est else ""),
                  "qty": f"{round(gal):,} GAL", "rate": f"${args.fuel_price:.2f}/GAL",
                  "amount": _cents(fuel)})
    if cls in ("mid_jet", "large_jet") and pax > 0:
        items.append({"desc": "In-flight catering", "qty": f"{pax} PAX",
                      "rate": f"${INVOICE_CATERING_PER_PAX:.2f}/PAX",
                      "amount": float(pax * INVOICE_CATERING_PER_PAX)})
    if args.handling is not None:
        items.append({"desc": "Ramp / handling" + (" (estimated)" if args.handling_est else ""),
                      "qty": "—", "rate": "—", "amount": _cents(args.handling)})
    if block >= INVOICE_CREW_DAY_MIN_BLOCK_H:
        items.append({"desc": "Crew day rate", "qty": "1", "rate": "—",
                      "amount": float(INVOICE_CREW_DAY[cls])})
    if domestic:
        fet = (_cents(charter) + _cents(fuel)) * INVOICE_FET_RATE
        items.append({"desc": "Federal excise tax (FET)", "qty": "—",
                      "rate": f"{INVOICE_FET_RATE * 100:.1f}%", "amount": _cents(fet)})
    total = _cents(sum(i["amount"] for i in items))
    for i in items:
        i["amount_fmt"] = f"${_money(i['amount'])}"
    print(json.dumps({"tail": tail["tail"], "class": cls, "route": f"{dep}-{dest}",
                      "domestic": domestic, "block_hrs": f"{hrs:.2f}",
                      "fuel_gal": round(gal), "items": items, "total": total,
                      "total_fmt": f"${_money(total)}"}, indent=1, ensure_ascii=False))
    return 0


def calib(args, doc) -> int:
    tail = next((f for f in doc.fleet if f["tail"].upper() == (args.tail or "").upper()), None)
    need = {"gc": args.gc, "gnd": args.gnd, "air": args.air, "air-min": args.air_min}
    errs = [f"--{k} is required" for k, v in need.items() if v is None]
    if tail is None:
        errs.append(f"unknown tail {args.tail!r}")
    if errs:
        print(json.dumps({"problems": errs}, indent=1))
        return 4
    lim = doc.limits_for(tail["model"])
    still = args.air_min * args.gnd / args.air
    model = args.gc * ROUTE_FACTOR / tail["ktas"] * 60 + overhead_h(args.gc) * 60
    dev = (still - model) / model
    date = (datetime.strptime(args.date, "%d%b%y") if args.date
            else datetime.now(ZoneInfo(HOME_TZ))).strftime("%d %b %Y").upper()
    sign = lambda x: f"{x * 100:+.1f}%".replace("-", "−")
    row = (f"| {date} | {tail['tail']} | {tail['model']} | {tail['cls']} | "
           f"{args.gc:g} | {args.air_min:g} | {still:.1f} | {model:.1f} | {sign(dev)} |")
    warnings = []
    if abs(still - model) > CALIB_WARN_MIN and args.gc > CALIB_WARN_GC:
        warnings.append(f"still-air {still:.1f} min vs model {model:.1f} min: a "
                        f"{abs(still - model):.1f}-minute miss on a {args.gc:g} nm "
                        f"leg — question the {tail['model']} plan speed "
                        f"(ARCHIVE.md → REFIT METHOD)")
    if args.empty_weight is not None and abs(args.empty_weight - lim["bow"]) > 1:
        warnings.append(f"OFP empty weight {args.empty_weight:g} ≠ MODEL LIMITS BOW "
                        f"{lim['bow']:g} — check the SimBrief airframe")
    if args.pax_weight is not None:
        allow = PAX_ALLOWANCE_LB_OVERRIDE.get(lim["icao"], PAX_ALLOWANCE_LB)
        if abs(args.pax_weight - allow) > 0.5:
            warnings.append(f"OFP weight per passenger {args.pax_weight:g} ≠ the "
                            f"script's {allow} lb for {lim['icao']}")
    print(json.dumps({"row": row, "still_air_min": round(still, 1),
                      "model_min": round(model, 1), "deviation": round(dev, 4),
                      "miss_min": round(still - model, 1), "warnings": warnings},
                     indent=1, ensure_ascii=False))
    return 0


def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def log_flight(args, doc, airports) -> int:
    """Append a landed flight to THE LOGBOOK and move the tail, in place."""
    try:
        with open(args.log_flight, encoding="utf-8") as fh:
            f = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error reading {args.log_flight}: {exc}", file=sys.stderr)
        return 3
    errs = []
    tail = next((t for t in doc.fleet if t["tail"].upper() == str(f.get("tail", "")).upper()), None)
    if tail is None:
        errs.append(f"unknown tail {f.get('tail')!r}")
    dest = str(f.get("dest", "")).upper()
    if dest not in airports:
        errs.append(f"{dest or '(blank)'} not in the airport database")
    if tail and dest == tail["current"]:
        errs.append(f"{tail['tail']} is already at {dest}")
    try:
        date = datetime.strptime(str(f.get("date", "")).strip().title(), "%d %b %Y")
    except ValueError:
        errs.append("date must be 'DD MMM YYYY', e.g. 12 NOV 2026")
        date = None
    try:
        block = fmt_hm(parse_block(f.get("block", "")))
    except ValueError as exc:
        errs.append(str(exc))
        block = None
    job = str(f.get("job", "")).strip()
    if job not in JOB_TYPES:
        errs.append(f"job {job!r} is not a RULE 1 job type")
    pax = f.get("pax", 0)
    if not isinstance(pax, int) or pax < 0:
        errs.append("pax must be a whole number")
    hook = " ".join(str(f.get("hook", "")).replace("|", "/").split())
    if not hook:
        errs.append("hook is required (a one-line summary)")
    event = " ".join(str(f.get("event") or "—").replace("|", "/").split())
    if errs:
        print(json.dumps({"problems": errs}, indent=1))
        return 4

    with open(args.doc, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    dep = tail["current"]
    new_away = 0 if dest == tail["home"] else tail["away"] + 1

    # THE FLEET row for the tail: Current and Away, by column name.
    hdr = next(i for i, l in enumerate(lines) if l.startswith("| Tail |"))
    cols = _cells(lines[hdr])
    ci, ai = cols.index("Current"), cols.index("Away")
    ri = next(i for i, l in enumerate(lines)
              if l.startswith("|") and _cells(l)[0] == tail["tail"])
    cells = _cells(lines[ri])
    cells[ci], cells[ai] = dest, str(new_away)
    lines[ri] = "| " + " | ".join(cells) + " |"

    # THE LOGBOOK: append, then drop the oldest beyond the window.
    lh = next(i for i, l in enumerate(lines)
              if l.startswith("| Date |") and "Route" in l)
    end = lh + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    dstr = date.strftime("%d %b %Y").upper()
    row = (f"| {dstr} | {tail['tail']} | {dep}-{dest} | {block} | {job} | "
           f"{pax} | {event} | {hook} |")
    lines.insert(end, row)
    data = list(range(lh + 2, end + 1))
    dropped = None
    if len(data) > LOGBOOK_WINDOW:
        dropped = lines.pop(data[0])
    with open(args.doc, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    # Re-parse what was written and run DATA INTEGRITY's Current check.
    try:
        doc2 = Doc(args.doc, args.ref)
    except DataError as exc:
        print(f"error: the edited state no longer parses: {exc}", file=sys.stderr)
        return 3
    integrity = []
    for t in doc2.fleet:
        rows = [r for r in doc2.logbook if r["reg"] == t["tail"]]
        if rows and rows[-1]["dest"] != t["current"]:
            integrity.append(f"{t['tail']}: Current {t['current']} but last logged "
                             f"leg ends at {rows[-1]['dest']}")
        if t["current"] == t["home"] and t["away"] != 0:
            integrity.append(f"{t['tail']}: at home but Away {t['away']}")
    print(json.dumps({"logged": row, "dropped": dropped,
                      "fleet": f"{tail['tail']} Current {dep}→{dest}, Away "
                               f"{tail['away']}→{new_away}",
                      "manifest": doc2.manifest(airports),
                      "integrity": integrity or "clean"}, indent=1, ensure_ascii=False))
    return 0


def main() -> int:
    if "--rules" in sys.argv[1:]:
        print_rules()
        return 0

    ap_arg = argparse.ArgumentParser(
        description=f"Meridian Air Dispatch candidate math (script "
                    f"v{SCRIPT_VERSION}, RULES.md v{SCRIPT_VERSION})")
    ap_arg.add_argument("--rules", action="store_true",
                        help="print the active scoring constants and exit")
    ap_arg.add_argument("--hours", type=float,
                        help="stated availability in hours (always required)")
    ap_arg.add_argument("--include-stored", action="store_true",
                        help="include tails marked stored in THE FLEET")
    ap_arg.add_argument("--tail", help="restrict to one tail, e.g. N100PE")
    ap_arg.add_argument("--model", help='restrict to one model, e.g. "Citation X"')
    ap_arg.add_argument("--class", dest="cls",
                        choices=["turboprop", "mid_jet", "large_jet"])
    ap_arg.add_argument("--date", help=f"flight date DDMMMYY (default: today in "
                                         f"{HOME_TZ})")
    ap_arg.add_argument("--expect", metavar="VERSION",
                        help="RULES.md version this session loaded; exit 5 if "
                             "it differs from the script's")
    ap_arg.add_argument("--data-floor", type=int, default=DATA_FLOOR_DEFAULT,
                        help="minimum airports with a land runway before the "
                             "data is treated as truncated (tests use 0)")
    ap_arg.add_argument("--doc", default="dispatch_state.md",
                        help="state file: THE FLEET and THE LOGBOOK "
                             "(default: dispatch_state.md)")
    ap_arg.add_argument("--ref", default=None,
                        help="reference file: MODEL LIMITS, REGION TABLE, "
                             "AIRPORT CLASS REGISTER, PREFERRED FIELDS, TAIL "
                             "NOTES (default: reference.md beside the script)")
    ap_arg.add_argument("--data", default="data", help="OurAirports CSV directory")
    ap_arg.add_argument("--top", type=int, default=None,
                        help=f"candidates reported per tail (default "
                             f"{TOP_DEFAULT}, max {TOP_MAX})")
    ap_arg.add_argument("--allow-b", action="store_true",
                        help="permit destinations VERIFIED as Class B in the "
                             "register. Note this does not gate unverified "
                             "large_airport fields, which carry the proxy "
                             "class BC and pass on the C branch — the register "
                             "verification at board time is that gate")
    ap_arg.add_argument("--land", action="store_true",
                        help="allow land destinations for the amphibious Caravan")
    ap_arg.add_argument("--allow-small-fields", action="store_true",
                        help="lift the field quality gate, allowing unpaved "
                             "or sub-75 ft fields. Off by default: AIRSPACE "
                             "ROUTING RULES makes the gate governing, so this "
                             "is the escape hatch for a story that wants an "
                             "aircraft on a rough strip")
    ap_arg.add_argument("--event", action="append", default=[], metavar="ICAO",
                        help="airport of a verified event market; repeatable. "
                             "Destinations within --event-radius are flagged "
                             "in_market (EV<nm> in the table) and exempt from "
                             "the fullness floor. Nothing is added to the score")
    ap_arg.add_argument("--event-radius", type=float, default=EVENT_RADIUS_NM,
                        help=f"nm around each --event airport (default "
                             f"{EVENT_RADIUS_NM})")
    ap_arg.add_argument("--event-phase", choices=["inbound", "outbound"],
                        default="inbound",
                        help="inbound: flag destinations inside the event "
                             "market. outbound: the tail is already in the "
                             "market, so every departure may carry the event "
                             "tie (event_tie_available) and no destination is "
                             "flagged")
    ap_arg.add_argument("--json", action="store_true")
    ap_arg.add_argument("--table", action="store_true",
                        help="print the step-6 decision table with each "
                             "departure airport's sun times")
    ap_arg.add_argument("--json-out", metavar="FILE",
                        help="also write the --json payload to FILE")
    ap_arg.add_argument("--widget", action="store_true",
                        help="with --finalize: picks carry job, event and hook; "
                             "print the finished RULE 1 board after the JSON")
    ap_arg.add_argument("--calls", type=int, default=None,
                        help="with --widget: tool calls the board took, for its "
                             "footer line")
    ap_arg.add_argument("--log-flight", metavar="FLIGHT",
                        help="append the landed flight in FLIGHT (JSON) to THE "
                             "LOGBOOK and move the tail, editing --doc in place")
    ap_arg.add_argument("--invoice", action="store_true",
                        help="compute RULE 6 invoice lines: --tail --dest "
                             "--block --trip-fuel --fuel-price [--pax "
                             "--handling --dep --fuel-est --handling-est]")
    ap_arg.add_argument("--calib", action="store_true",
                        help="compute a CALIBRATION.md row: --tail --gc --gnd "
                             "--air --air-min [--date --empty-weight "
                             "--pax-weight]")
    ap_arg.add_argument("--dep", help="--invoice: departure (default: Current)")
    ap_arg.add_argument("--dest", help="--invoice: destination")
    ap_arg.add_argument("--block", help="--invoice: OFP planned block (1h 46m)")
    ap_arg.add_argument("--trip-fuel", type=float, help="--invoice: OFP trip fuel, lb")
    ap_arg.add_argument("--fuel-price", type=float, help="--invoice: $/gal at departure FBO")
    ap_arg.add_argument("--fuel-est", action="store_true", help="--invoice: price is an estimate")
    ap_arg.add_argument("--pax", type=int, help="--invoice: passengers")
    ap_arg.add_argument("--handling", type=float, help="--invoice: ramp/handling $")
    ap_arg.add_argument("--handling-est", action="store_true", help="--invoice: handling is an estimate")
    ap_arg.add_argument("--gc", type=float, help="--calib: OFP great-circle nm")
    ap_arg.add_argument("--gnd", type=float, help="--calib: OFP ground (route) nm")
    ap_arg.add_argument("--air", type=float, help="--calib: OFP air nm")
    ap_arg.add_argument("--air-min", type=float, help="--calib: OFP OFF–ON minutes")
    ap_arg.add_argument("--empty-weight", type=float, help="--calib: OFP empty weight, lb")
    ap_arg.add_argument("--pax-weight", type=float, help="--calib: OFP weight per passenger, lb")
    ap_arg.add_argument("--finalize", metavar="PICKS",
                        help="compute card fields and finished SimBrief URLs "
                             "for the story picks in PICKS (a JSON file)")
    args = ap_arg.parse_args()
    if args.expect and args.expect.lstrip("v") != SCRIPT_VERSION:
        print(f"version mismatch: RULES {args.expect}, script {SCRIPT_VERSION} — "
              f"fetch the matching script or reload RULES.md", file=sys.stderr)
        return 5
    utility = args.log_flight or args.invoice or args.calib
    if args.hours is None and not utility:
        ap_arg.error("--hours is required")
    if args.top is not None and not 1 <= args.top <= TOP_MAX:
        ap_arg.error(f"--top must be between 1 and {TOP_MAX}")

    try:
        doc = Doc(args.doc, args.ref)
    except (OSError, DataError) as exc:
        print(f"error reading state/reference: {exc}", file=sys.stderr)
        return 3
    try:
        airports = load_airports(args.data, args.data_floor)
    except (OSError, DataError) as exc:
        print(f"error reading airport data: {exc}", file=sys.stderr)
        return 3
    for f in doc.fleet:
        for col in ("home", "current"):
            if f[col] not in airports and f["status"] == "active":
                print(f"error: THE FLEET {f['tail']} {col} {f[col]} is not in the "
                      f"airport database", file=sys.stderr)
                return 3
    unknown = sorted(i for i in doc.preferred if i not in airports)
    if unknown:
        print(f"error: PREFERRED FIELDS lists {', '.join(unknown)}, not in the "
              f"airport database", file=sys.stderr)
        return 3
    manifest = doc.manifest(airports)
    # Run counter (C6). Counts script runs in this working directory, so a
    # session can see at a glance whether it is inside the two-run board budget
    # (one candidate run, one --event re-run) plus one finalize.
    try:
        with open(RUN_COUNTER, encoding="utf-8") as fh:
            run_no = int(fh.read().strip() or 0) + 1
    except (OSError, ValueError):
        run_no = 1
    try:
        with open(RUN_COUNTER, "w", encoding="utf-8") as fh:
            fh.write(str(run_no))
    except OSError:
        pass
    manifest += f" · run {run_no}"

    if args.log_flight:
        return log_flight(args, doc, airports)
    if args.invoice:
        return invoice(args, doc, airports)
    if args.calib:
        return calib(args, doc)
    if args.finalize:
        try:
            from timezonefinder import TimezoneFinder
            tf_f = TimezoneFinder()
        except ImportError:
            tf_f = None
        return finalize(args, doc, airports, tf_f, manifest)

    ceiling = args.hours - CEILING_MARGIN_H
    if ceiling <= 0:
        print("availability leaves no block time after fixed overhead",
              file=sys.stderr)
        return 2

    pool = doc.fleet
    if not args.include_stored:
        pool = [f for f in pool if f["status"] != "stored"]
    if args.tail:
        pool = [f for f in pool if f["tail"].upper() == args.tail.upper()]
    elif args.model:
        pool = [f for f in pool if f["model"].lower() == args.model.lower()]
    elif args.cls:
        pool = [f for f in pool if f["cls"] == args.cls]
    if not pool:
        print("no tails match that filter", file=sys.stderr)
        return 2
    if args.top is None:
        args.top = TOP_DEFAULT

    try:
        flight_date = (datetime.strptime(args.date, "%d%b%y")
                       if args.date else datetime.now(ZoneInfo(HOME_TZ)))
    except ValueError:
        ap_arg.error(f"--date must be DDMMMYY, got {args.date!r}")
    date_ddmmmyy = flight_date.strftime("%d%b%y").upper()
    # Noon UTC on the flight date: only used to pick the local date for the
    # table's sun times. Card times come from --finalize.
    sun_ref = datetime(flight_date.year, flight_date.month, flight_date.day, 12,
                       tzinfo=timezone.utc)

    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
    except ImportError:
        tf = None

    hist = build_history(doc, airports)
    results, notes = [], []

    event_pts = []
    for e in args.event:
        ea = airports.get(e.upper())
        if ea is None:
            notes.append(f"--event {e}: not in the airport database — ignored")
        else:
            event_pts.append(ea)

    for tail in pool:
        cur = airports.get(tail["current"])
        home = airports.get(tail["home"])
        if cur is None:
            notes.append(f"{tail['tail']}: current location {tail['current']} "
                         f"not in the airport database — skipped")
            continue
        try:
            lim = doc.limits_for(tail["model"])
        except DataError as exc:
            notes.append(str(exc))
            continue

        cands = []

        # Outbound phase: the bonus is temporal, not geographic. If the tail is
        # sitting in the event market, EVERY departure is equally event-tied, so
        # a geographic bonus would discriminate between none of them. The script
        # only reports that the tie is available; normal scoring picks where the
        # passengers are actually going.
        in_event_market = None
        for ea in event_pts:
            d = (0.0 if ea["ident"] == tail["current"]
                 else gc_nm(cur["lat"], cur["lon"], ea["lat"], ea["lon"]))
            if d <= args.event_radius and (in_event_market is None
                                           or d < in_event_market):
                in_event_market = d
        event_tie_available = (args.event_phase == "outbound"
                               and in_event_market is not None)

        for ident, a in airports.items():
            if ident == tail["current"]:
                continue

            # The shared legality gate (also run by --finalize). A tail's home
            # base is legal regardless of tier and field quality.
            gate, eff, class_b = destination_gate(
                a, tail, doc, allow_small=args.allow_small_fields, land=args.land)
            if gate or (class_b and not args.allow_b):
                continue

            gc = gc_nm(cur["lat"], cur["lon"], a["lat"], a["lon"])
            if gc < 1:
                continue
            # A model's MODEL LIMITS `Max GC` caps a leg below what the fuel
            # check alone allows (the Falcon 50 falls short of reserves well
            # inside its published range). A fallback ferry is exempt: real
            # ferries use tech stops, and nothing may strand an aircraft.
            if lim["max_gc"] and gc > lim["max_gc"]:
                continue
            route = gc * ROUTE_FACTOR
            block = route / tail["ktas"] + overhead_h(gc) + TAXI_H
            if block > ceiling + BAND_OVER_H:
                continue

            ev_dist = None
            if args.event_phase == "inbound":
                for ea in event_pts:
                    d = (0.0 if ea["ident"] == ident
                         else gc_nm(a["lat"], a["lon"], ea["lat"], ea["lon"]))
                    if d <= args.event_radius and (ev_dist is None or d < ev_dist):
                        ev_dist = d

            # Band floor. A leg this far short of the ceiling is not what Kyle
            # asked for when he stated his availability, so it is not offered at
            # all rather than offered at a penalty — that is the difference
            # between a preference and a guarantee. Two exemptions, both legs
            # that are SUPPOSED to be short: a positioning leg into a verified
            # event market, and the tail's own home base, which AIRSPACE ROUTING
            # RULES already holds legal regardless of the other gates.
            if (block < ceiling - BAND_UNDER_H
                    and ev_dist is None and ident != tail["home"]):
                continue

            feas = feasibility(lim, block)
            if feas is None or feas["max_pax"] < 0:
                continue

            dest_region = region_of(a, doc)
            sc = score_candidate(a, tail, lim, doc, hist, block, ceiling,
                                 dest_region, home, cur, ev_dist)

            cands.append({
                "tail": tail["tail"],
                "model": tail["model"],
                "icao_type": tail["icao"],
                "class": tail["cls"],
                "dep": tail["current"],
                "dep_city": cur["muni"],
                "home": tail["home"],
                "dest": ident,
                "dest_name": a["name"],
                "dest_city": a["muni"],
                "dest_region": dest_region,
                "dest_class": eff,
                "class_verified": ident in doc.class_register,
                "preferred": ident in doc.preferred,
                "dest_rwy_ft": a["rwy"],
                "dest_type": a["type"],
                "water": a["water"],
                "gc_nm": round(gc),
                "route_nm": round(route),
                "block_h": round(block, 3),
                "block": fmt_hm(block),
                "session": fmt_hm(block + PREP_H),
                "fullness_pct": sc["fullness_pct"],
                "toward_home": sc["toward_home"],
                "in_market": sc["in_market"],
                "event_tie_available": event_tie_available,
                "event_dist_nm": sc["event_dist_nm"],
                "ops": tail["ops"],
                "tail_note": doc.tail_notes.get(tail["tail"], ""),
                "home_pull_active": (tail["ops"] != "floating"
                                     and tail["current"] != tail["home"]),
                "score": sc["total"],
                "score_parts": sc["parts"],
                **feas,
            })

        if not cands and tail["current"] == tail["home"]:
            # Already home: a "ferry toward base" would be a pointless hop to
            # the nearest field. Nothing strands an aircraft at its own base,
            # so the tail simply sits this board out.
            notes.append(
                f"{tail['tail']}: no mission fits this window from its home "
                f"base {tail['home']} — left off this board")
        elif not cands and home is not None:
            # Guaranteed fallback. Range never strands an aircraft — real ferry
            # flights use tech stops — but mission availability can: the amphib
            # parked where there is no water in reach, or a BBJ at a field where
            # every candidate is a short hop. A repositioning leg toward base is
            # always on offer regardless of score.
            best = None
            for ident, a in airports.items():
                if ident == tail["current"]:
                    continue
                # The amphibian is amphibious: a ferry leg may use a runway even
                # though revenue missions are written as water arrivals.
                if a["type"] == "seaplane_base":
                    if not a["water"]:
                        continue
                elif a["rwy"] < tail["min_rwy"]:
                    continue
                gc = gc_nm(cur["lat"], cur["lon"], a["lat"], a["lon"])
                if gc < 1:
                    continue
                block = gc * ROUTE_FACTOR / tail["ktas"] + overhead_h(gc) + TAXI_H
                if (block > ceiling + BAND_OVER_H
                        or feasibility(lim, block) is None):
                    continue
                d_home = gc_nm(a["lat"], a["lon"], home["lat"], home["lon"])
                if best is None or d_home < best[0]:
                    best = (d_home, ident, a, gc, block)
            if best:
                _, ident, a, gc, block = best
                feas = feasibility(lim, block)
                cands.append({
                    "tail": tail["tail"], "model": tail["model"],
                    "icao_type": tail["icao"], "class": tail["cls"],
                    "ops": tail["ops"], "fallback": True,
                    "tail_note": doc.tail_notes.get(tail["tail"], ""),
                    "dep": tail["current"], "dep_city": cur["muni"],
                    "home": tail["home"],
                    "dest": ident, "dest_name": a["name"],
                    "dest_city": a["muni"], "dest_region": region_of(a, doc),
                    "dest_class": doc.class_register.get(ident, proxy_class(a)),
                    "class_verified": ident in doc.class_register,
                    "dest_rwy_ft": a["rwy"], "dest_type": a["type"],
                    "water": a["water"], "gc_nm": round(gc),
                    "route_nm": round(gc * ROUTE_FACTOR),
                    "block_h": round(block, 3), "block": fmt_hm(block),
                    "session": fmt_hm(block + PREP_H),
                    "fullness_pct": round(block / ceiling * 100),
                    "toward_home": True, "in_market": False,
                    "event_tie_available": False, "event_dist_nm": None,
                    "home_pull_active": True,
                    "score": 0, "score_parts": {"fallback_ferry": 0}, **feas,
                })
                notes.append(
                    f"{tail['tail']}: no scoring candidates from "
                    f"{tail['current']} — offering a ferry leg toward "
                    f"{tail['home']} instead")

        # Tie-break: score, then better-equipped field, then in-market legs
        # ahead of ordinary ones, then nearest-to-event for in-market and
        # longest-leg for everything else.
        def _key(c):
            return (-c["score"],
                    -TYPE_RANK.get(c["dest_type"], 0),
                    0 if c["in_market"] else 1,
                    c["event_dist_nm"] if c["in_market"] else -c["gc_nm"])

        cands.sort(key=_key)
        # Spread the reported set across regions rather than returning twelve
        # variations on the same ring of airports at the ceiling radius.
        picked, per_region = [], {}
        for c in cands:
            r = c["dest_region"]
            if per_region.get(r, 0) >= MAX_PER_REGION_REPORTED:
                continue
            per_region[r] = per_region.get(r, 0) + 1
            picked.append(c)
            if len(picked) >= args.top:
                break
        if len(picked) < args.top:                      # backfill if thin
            for c in cands:
                if c not in picked:
                    picked.append(c)
                if len(picked) >= args.top:
                    break
            picked.sort(key=_key)
        # A tail away from home always sees its home leg, whatever it scores,
        # so the board can send it home without a second run.
        if tail["current"] != tail["home"]:
            home_c = next((c for c in cands if c["dest"] == tail["home"]), None)
            if home_c is not None and home_c not in picked:
                if len(picked) >= args.top:
                    picked.pop()
                picked.append(home_c)
                picked.sort(key=_key)
        results.extend(picked)

    if not results:
        print("no legal candidates within the block ceiling", file=sys.stderr)
        for n in notes:
            print(f"  note: {n}", file=sys.stderr)
        return 2

    payload = {"version": SCRIPT_VERSION, "manifest": manifest,
               "ceiling_h": ceiling, "date": date_ddmmmyy,
               "notes": notes, "candidates": results}
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    if args.table:
        print_table(results, notes, ceiling, date_ddmmmyy, airports, tf,
                    sun_ref, manifest)
        return 0
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Block ceiling {fmt_hm(ceiling)} "
          f"(availability {fmt_hm(args.hours)} − 30 min) · "
          f"date {date_ddmmmyy}")
    print(manifest)
    for n in notes:
        print(f"note: {n}")

    by_tail: dict[str, list] = {}
    for c in results:
        by_tail.setdefault(c["tail"], []).append(c)

    for tail_id, cands in by_tail.items():
        t = cands[0]
        print(f"\n{tail_id} · {t['model']} ({t['icao_type']}) · from {t['dep']} "
              f"{t['dep_city']} · ops {t['ops']}"
              + ("  [home pull active]" if t["home_pull_active"] else "")
              + ("  [FALLBACK FERRY — no scoring candidates]"
                 if t.get("fallback") else ""))
        print(f"{'DEST':<6}{'CITY':<22}{'REGION':<24}{'CL':<4}{'GC':>6}"
              f"{'RTE':>6}{'BLOCK':>8}{'FULL':>6}{'PAX':>5}{'CARGO':>7}{'SCORE':>7}")
        for c in cands:
            flag = "" if c["class_verified"] else "?"
            print(f"{c['dest']:<6}{c['dest_city'][:21]:<22}{c['dest_region'][:23]:<24}"
                  f"{c['dest_class'] + flag:<4}{c['gc_nm']:>6}{c['route_nm']:>6}"
                  f"{c['block']:>8}{str(c['fullness_pct']) + '%':>6}"
                  f"{c['max_pax']:>5}{c['cargo_room_at_max_pax']:>7}"
                  f"{c['score']:>7g}")
            bits = " ".join(f"{k}{v:+g}" for k, v in c["score_parts"].items() if v)
            extra = " toward-home" if c["toward_home"] else ""
            if c["in_market"]:
                extra += (" IN-MARKET"
                          + (f" ({c['event_dist_nm']} nm from event market)"
                             if c["event_dist_nm"] else " (in event market)"))
            print(f"      {bits}{extra} · fuel {c['fuel_plan']} lb · "
                  f"payload {c['payload_avail']} lb")
    print("\nClass column: '?' = proxy from OurAirports type, not yet verified in "
          "the AIRPORT CLASS REGISTER. Verify before a card makes the final board.")
    print("CARGO is freight room remaining at max pax; freight-only capacity is in "
          "--json as cargo_cap_freight.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
