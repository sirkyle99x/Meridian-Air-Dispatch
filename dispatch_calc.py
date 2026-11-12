#!/usr/bin/env python3
"""
dispatch_calc.py — Meridian Air Dispatch candidate math (RULES.md v7.0).

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
  python3 dispatch_calc.py --expect 7.0 --hours 2.5 --tail N24SM --table --json-out cands.json
  python3 dispatch_calc.py --expect 7.0 --finalize picks.json --hours 2.5

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
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SCRIPT_VERSION = "7.0"       # must equal the RULES.md version; see --expect
STATE_SCHEMA = "6.2"         # must equal dispatch_state.md's "Schema v" header
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
QUALITY_RWY_ANCHORS = [(5000.0, 0.0), (6500.0, 5.0), (8000.0, 8.0),
                       (10000.0, 10.0)]
QUALITY_SCHEDULED = 4.0      # someone runs airline service there: a real facility


def quality_score(ap: dict) -> float:
    rwy = float(ap.get("rwy") or 0)
    if rwy <= QUALITY_RWY_ANCHORS[0][0]:
        pts = QUALITY_RWY_ANCHORS[0][1]
    else:
        pts = QUALITY_RWY_ANCHORS[-1][1]
        for (x0, y0), (x1, y1) in zip(QUALITY_RWY_ANCHORS,
                                      QUALITY_RWY_ANCHORS[1:]):
            if rwy <= x1:
                pts = y0 + (y1 - y0) * (rwy - x0) / (x1 - x0)
                break
    if ap.get("sched"):
        pts += QUALITY_SCHEDULED
    return round(pts, 1)


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
        route = gc * ROUTE_FACTOR
        block = route / tail["ktas"] + overhead_h(gc) + TAXI_H
        pax = _int_field(p, "pax", problems)
        cargo = _int_field(p, "cargo", problems)

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
        raise DataError(f"section not found in state file: {header}")
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
    def __init__(self, path: str):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.path = path

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
        for r in parse_table(text, "MODEL LIMITS", "Model",
                             required=("Model", "ICAO") + num_cols):
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
            }
        for f in self.fleet:
            if f["model"] not in self.limits:
                raise DataError(f"THE FLEET: {f['tail']} model {f['model']!r} has "
                                f"no MODEL LIMITS row")

        # Region table. The Scope column keeps US state codes and ISO country
        # codes in separate namespaces — they collide otherwise (CO, CA, MS...).
        self.region_by_state, self.region_by_country = {}, {}
        self.regions = set()
        for r in parse_table(text, "REGION TABLE", "Region",
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
        for r in parse_table(text, "REGION TABLE", "Class",
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
        for r in parse_table(text, "AIRPORT CLASS REGISTER", "ICAO",
                             required=("ICAO", "Class")):
            if r.get("ICAO") and r.get("Class"):
                self.class_register[r["ICAO"].strip().upper()] = \
                    r["Class"].strip().upper()

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

    def manifest(self, airports: dict | None = None) -> str:
        active = sum(1 for f in self.fleet if f["status"] == "active")
        s = (f"state: {len(self.fleet)} tails ({active} active) · "
             f"{len(self.limits)} models · {len(self.class_register)} register · "
             f"{len(self.logbook)}/{self.logbook_rows} logbook rows")
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

    Returns a string of candidate classes. 'BC' means the register has not
    verified it yet and it could be either — Dispatch verifies before it makes
    a final board, per AIRPORT CLASS REGISTER.
    """
    t = ap["type"]
    if t == "seaplane_base":
        return "W"
    if ap["country"] == "US":
        return {"large_airport": "BC", "medium_airport": "CD",
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
    parts["quality"] = quality_score(ap)

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
    print("  runway anchors (ft -> pts)   "
          + ", ".join(f"{int(x)}:{y:+.0f}" for x, y in QUALITY_RWY_ANCHORS))
    print(f"  {'scheduled service':<{w}} {QUALITY_SCHEDULED:+.0f}")
    print(f"\nEvent market radius            {EVENT_RADIUS_NM} nm (flag only, "
          f"no score)")
    print(f"Sun window                     ±{SUN_WINDOW_MIN} min of sunrise/sunset")
    print(f"Candidates per tail (--top)    {TOP_DEFAULT} default, {TOP_MAX} max")
    print(f"Default --date                 today in {HOME_TZ}")


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
                        help="state file holding THE FLEET, MODEL LIMITS, "
                             "REGION TABLE, AIRPORT CLASS REGISTER and THE "
                             "LOGBOOK (default: dispatch_state.md)")
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
    ap_arg.add_argument("--finalize", metavar="PICKS",
                        help="compute card fields and finished SimBrief URLs "
                             "for the story picks in PICKS (a JSON file)")
    args = ap_arg.parse_args()
    if args.expect and args.expect.lstrip("v") != SCRIPT_VERSION:
        print(f"version mismatch: RULES {args.expect}, script {SCRIPT_VERSION} — "
              f"fetch the matching script or reload RULES.md", file=sys.stderr)
        return 5
    if args.hours is None:
        ap_arg.error("--hours is required")
    if args.top is not None and not 1 <= args.top <= TOP_MAX:
        ap_arg.error(f"--top must be between 1 and {TOP_MAX}")

    try:
        doc = Doc(args.doc)
    except (OSError, DataError) as exc:
        print(f"error reading {args.doc}: {exc}", file=sys.stderr)
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
    manifest = doc.manifest(airports)

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
