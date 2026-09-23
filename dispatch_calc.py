#!/usr/bin/env python3
"""
dispatch_calc.py — Meridian Air Dispatch v6.0 candidate math.

Replaces mental great-circle math and live distance iteration with one tool call.
Reads dispatch_state.md as the single source of truth for state: THE FLEET, MODEL
LIMITS, REGION TABLE, AIRPORT CLASS REGISTER, THE LOGBOOK. This file is the
single source of truth for every scoring CONSTANT — RULES.md references them
rather than restating them, so they exist in exactly one place. `--rules`
prints the active table. Reads airport geometry
from the OurAirports CSVs.

v5.0 split the inputs. State (which changes every flight) lives in
dispatch_state.md; rules (which change rarely) live in DISPATCH.md, which this
script no longer reads. The script parsed about 9% of DISPATCH.md and ignored the
rest, so pointing it at a small state file costs nothing and makes the file cheap
to put on disk at session start. This file is hosted at
https://raw.githubusercontent.com/sirkyle99x/Meridian-Air-Dispatch/main/dispatch_calc.py
and fetched rather than retyped.

Computes, per candidate destination: great-circle nm, route nm, block, session,
fullness, every mechanical score component from DISPATCH.md's VARIETY ENGINE, the
Section 6a feasibility checks, the departure day-part, and a SimBrief URL.

Left to Dispatch: the event bonus, the story, job type, pax and cargo within the
computed envelope, and board composition.

Usage
-----
  python3 dispatch_calc.py --hours 3.5
  python3 dispatch_calc.py --hours 4 --tail N100PE
  python3 dispatch_calc.py --hours 6 --model "Citation X" --depz 1330
  python3 dispatch_calc.py --hours 2 --class turboprop --json

Exit codes: 0 ok, 2 no legal candidates, 3 parse/data error.
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

# ---------------------------------------------------------------------------
# Constants that mirror DISPATCH.md body text (rules, not state). Any change here
# must be made in that document in the same edit — see CORE PHILOSOPHY, body text
# governs. State lives in dispatch_state.md and is never hardcoded here.
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
# The bonus is 0 as of v6.2. It was +40, set when a positioning ferry was the
# only route by which an event reached a board. At that value an in-market leg
# scored ~100 against a non-event cluster near 60 — an automatic win for the one
# card type whose payoff lands in a later session that may never happen, bought
# silently on every board where any event verified. RULES.md now reserves the
# event slot outright and fills it with a revenue leg by default, so the event
# card no longer has to win on points, and the positioning leg is gated on ops
# mode, outbound window and story rather than priced. The constant survives at 0
# so --rules still names the component and so restoring a value stays one edit.
#
# The floors below are NOT part of the bonus and stay. A positioning leg is short
# and empty by nature, so it earns little or no fullness credit, and it flies
# toward exactly the region the variety engine is busy penalizing — the event is
# what concentrated traffic there in the first place. Flooring those two at zero
# removes a penalty the leg does not deserve; it does not award anything.
EVENT_RADIUS_NM = 50
EVENT_POSITIONING_BONUS = 0

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
AFFINITY_BONUS = 10          # destination region in the class's affinity list
MODEL_ROTATION_PENALTY = -15 # same model as the last logged flight
EVENT_VERIFIED_BONUS = 25    # applied by Dispatch, not by this script

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
# does the discriminating. That is the v4.2 failure mode inverted rather than
# repeated: v4.2's step bands tied at the top and fell through to TYPE_RANK,
# which pulled toward hubs; here the tie-break is an explicit quality term that
# ranks medium_airport ABOVE large_airport, so it pulls toward relievers.
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

DAY_PARTS = [
    ("early morning", 5, 8),
    ("daylight", 8, 17),
    ("evening", 17, 20),
    ("night", 20, 5),
]


# ---------------------------------------------------------------------------
# Markdown table parsing
# ---------------------------------------------------------------------------

def _split_row(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def parse_table(text: str, header: str) -> list[dict]:
    """Return the first markdown table appearing under `header` as list of dicts."""
    pat = re.compile(r"^#{1,4}\s+" + re.escape(header) + r"\s*$", re.M)
    m = pat.search(text)
    if not m:
        raise KeyError(f"section not found in document: {header}")
    rest = text[m.end():]
    stop = re.search(r"^#{1,4}\s+\S", rest, re.M)
    if stop:
        rest = rest[: stop.start()]

    rows, cols = [], None
    for line in rest.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if cols is not None:
                break          # table ended
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
    if cols is None:
        raise KeyError(f"no table under section: {header}")
    return rows


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

class Doc:
    def __init__(self, path: str):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.path = path

        self.fleet = []
        for r in parse_table(text, "THE FLEET"):
            if not r.get("Tail"):
                continue
            self.fleet.append({
                "tail": r["Tail"],
                "model": r["Model"],
                "icao": r["ICAO"],
                "cls": r["Class"],
                "ops": (r.get("Ops") or "floating").strip().lower(),
                "status": (r.get("Status") or "active").strip().lower(),
                "ktas": _num(r["Plan KTAS"]),
                "min_rwy": _num(r["Min rwy"], int, 0),
                "home": r["Home"],
                "current": r["Current"],
                "away": _num(r["Away"], int, 0),
                # v6.0: no longer tracked. Read if present so an older state
                # file still parses, but never required.
                "hobbs": _num(r.get("Hobbs", ""), float, 0.0),
                "flts": _num(r.get("Flts", ""), int, 0),
            })

        self.limits = {}
        for r in parse_table(text, "MODEL LIMITS"):
            if not r.get("Model"):
                continue
            self.limits[r["Model"]] = {
                "icao": r["ICAO"],
                "seats": _num(r["Seats"], int, 0),
                "bow": _num(r["BOW"]),
                "mzfw": _num(r["MZFW"]),
                "mtow": _num(r["MTOW"]),
                "mlw": _num(r["MLW"]),
                "max_fuel": _num(r["Max fuel"]),
                "baggage": _num(r["Baggage"]),
                "burn": _num(r["Plan burn"]),
                "reserve": _num(r["Reserve"]),
            }

        # Region table. The Scope column keeps US state codes and ISO country
        # codes in separate namespaces — they collide otherwise (CO, CA, MS...).
        self.region_by_state, self.region_by_country = {}, {}
        for r in parse_table(text, "REGION TABLE"):
            region = r.get("Region", "").strip()
            scope = r.get("Scope", "").strip().lower()
            if not region or not r.get("Members"):
                continue
            target = (self.region_by_state if scope == "us_state"
                      else self.region_by_country)
            for tok in r["Members"].split():
                tok = tok.strip().strip(",").upper()
                if len(tok) == 2:
                    target.setdefault(tok, region)

        self.affinity = {}
        m = re.search(r"\|\s*Class\s*\|\s*Regions\s*\|(.+?)(?=\n\s*\n|\n#{1,4}\s)",
                      text, re.S)
        if m:
            for line in m.group(1).splitlines():
                if not line.strip().startswith("|"):
                    continue
                cells = _split_row(line)
                if len(cells) >= 2 and cells[0] in ("turboprop", "mid_jet", "large_jet"):
                    self.affinity[cells[0]] = cells[1]

        self.class_register = {}
        try:
            for r in parse_table(text, "AIRPORT CLASS REGISTER"):
                if r.get("ICAO") and r.get("Class"):
                    self.class_register[r["ICAO"].strip()] = r["Class"].strip().upper()
        except KeyError:
            pass

        self.logbook = []
        for r in parse_table(text, "THE LOGBOOK"):
            route = r.get("Route", "")
            mm = re.search(r"([A-Z0-9]{3,4})\s*(?:→|->)\s*([A-Z0-9]{3,4})", route)
            if not mm:
                continue
            self.logbook.append({
                "date": r.get("Date", ""),
                "reg": r.get("Reg", ""),
                "dep": mm.group(1),
                "dest": mm.group(2),
                "job": r.get("Job type", ""),
                "event": r.get("Event", ""),
                "hook": r.get("Hook", ""),
            })
        # Newest last in the document; work newest-first internally.
        self.logbook_recent = list(reversed(self.logbook))

        self.model_by_tail = {f["tail"]: f["model"] for f in self.fleet}

    def limits_for(self, model: str) -> dict:
        if model not in self.limits:
            raise KeyError(f"no MODEL LIMITS row for model: {model}")
        return self.limits[model]


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------

USABLE_TYPES = {"large_airport", "medium_airport", "small_airport", "seaplane_base"}


def load_airports(data_dir: str) -> dict:
    runways: dict[str, int] = {}
    widths: dict[str, int] = {}
    paved: dict[str, bool] = {}
    water: set[str] = set()
    with open(os.path.join(data_dir, "runways.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
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
    with open(os.path.join(data_dir, "airports.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
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
            }
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


def day_part(local_hour: int) -> str:
    for name, lo, hi in DAY_PARTS:
        if lo < hi:
            if lo <= local_hour < hi:
                return name
        else:
            if local_hour >= lo or local_hour < hi:
                return name
    return "daylight"


# ---------------------------------------------------------------------------
# Feasibility (DISPATCH.md LOAD PLANNING STANDARDS, Section 6a)
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
# Scoring (DISPATCH.md VARIETY ENGINE)
# ---------------------------------------------------------------------------

def build_history(doc: Doc, airports: dict) -> dict:
    recent = doc.logbook_recent
    dests = [f["dest"] for f in recent]
    regions = []
    for f in recent:
        ap = airports.get(f["dest"])
        regions.append(region_of(ap, doc) if ap else "Other")
    last_model = doc.model_by_tail.get(recent[0]["reg"]) if recent else None
    return {
        "dest_last3": set(dests[:3]),
        "dest_last10": set(dests[:10]),
        "dest_all": set(dests),
        "region_last1": regions[0] if regions else None,
        "region_last2": regions[:2],
        "region_last5": set(regions[:5]),
        "last_model": last_model,
    }


def score_candidate(ap, tail, lim, doc, hist, block_h, ceiling_h,
                    dest_region, home_ap, cur_ap, named_filter,
                    event_dist_nm=None) -> dict:
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

    # Aircraft-region affinity.
    aff = doc.affinity.get(tail["cls"], "")
    in_affinity = True
    if tail["cls"] == "mid_jet" and dest_region == "Hawaii":
        in_affinity = False
    if tail["cls"] == "turboprop" and dest_region in ("Hawaii", "Other"):
        in_affinity = False
    parts["affinity"] = (AFFINITY_BONUS
                         if in_affinity and dest_region != "Other" else 0)

    # Model rotation — ignored when Kyle named a tail, model, or class.
    parts["model_rotation"] = (
        0 if named_filter or hist["last_model"] != tail["model"]
        else MODEL_ROTATION_PENALTY
    )

    # Event repositioning. A positioning leg into an event market is usually a
    # short empty hop, so the fullness penalty would otherwise guarantee it
    # never reaches a board — which is exactly backwards. The penalty is
    # floored at zero for these. The bonus itself is 0: Dispatch selects the
    # event card into a reserved slot, so `positioning` and `event_dist_nm`
    # are the load-bearing output here, not the score.
    positioning = event_dist_nm is not None
    parts["event_positioning"] = EVENT_POSITIONING_BONUS if positioning else 0

    # Destination quality — the discriminator inside a flat fullness band.
    parts["quality"] = quality_score(ap)

    # Fullness.
    fullness = block_h / ceiling_h if ceiling_h > 0 else 0
    parts["fullness"] = fullness_score(block_h, ceiling_h)
    if positioning:
        # Under the v6.3 curve, flooring at zero was enough to neutralise the
        # short-hop penalty. Under the band it is not: an in-band leg scores
        # BAND_FULL_PTS, so a floored positioning leg would sit a full band's
        # worth behind and never reach the reported set — the exact failure the
        # floor exists to prevent. Positioning legs are scored as in-band, which
        # removes the penalty without awarding anything on top.
        parts["fullness"] = BAND_FULL_PTS
        parts["region"] = max(0, parts["region"])

    return {
        "parts": parts,
        "total": round(sum(parts.values()), 1),
        "fullness_pct": round(fullness * 100),
        "toward_home": toward_home,
        "positioning": positioning,
        "event_dist_nm": None if event_dist_nm is None else round(event_dist_nm),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def print_rules() -> None:
    """Print every scoring constant. RULES.md points here instead of restating
    them, so there is exactly one place a number can be wrong."""
    w = 30
    print("Meridian Air Dispatch — active scoring constants\n")
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
        ("model rotation", MODEL_ROTATION_PENALTY),
        ("event positioning", EVENT_POSITIONING_BONUS),
        ("verified event (by Dispatch)", EVENT_VERIFIED_BONUS),
    ):
        print(f"  {label:<{w}} {val:+d}")
    print("\nFullness band (absolute, not a fraction of the ceiling)")
    print(f"  {'full credit from':<{w}} ceiling -{BAND_UNDER_H * 60:.0f} min")
    print(f"  {'through':<{w}} ceiling +{BAND_OVER_H * 60:.0f} min")
    print(f"  {'credit inside the band':<{w}} {BAND_FULL_PTS:+.0f}")
    print(f"  {'below the floor':<{w}} not offered "
          f"(positioning legs and home base exempt)")
    print("\nDestination quality (airport `type` is deliberately not scored)")
    print("  runway anchors (ft -> pts)   "
          + ", ".join(f"{int(x)}:{y:+.0f}" for x, y in QUALITY_RWY_ANCHORS))
    print(f"  {'scheduled service':<{w}} {QUALITY_SCHEDULED:+.0f}")
    print(f"\nEvent market radius            {EVENT_RADIUS_NM} nm")


def main() -> int:
    if "--rules" in sys.argv[1:]:
        print_rules()
        return 0

    ap_arg = argparse.ArgumentParser(
        description="Meridian Air Dispatch v6.0 candidate math")
    ap_arg.add_argument("--rules", action="store_true",
                        help="print the active scoring constants and exit")
    ap_arg.add_argument("--hours", type=float, required=True,
                        help="stated availability in hours")
    ap_arg.add_argument("--include-stored", action="store_true",
                        help="include tails marked stored in THE FLEET")
    ap_arg.add_argument("--tail", help="restrict to one tail, e.g. N100PE")
    ap_arg.add_argument("--model", help='restrict to one model, e.g. "Citation X"')
    ap_arg.add_argument("--class", dest="cls",
                        choices=["turboprop", "mid_jet", "large_jet"])
    ap_arg.add_argument("--date", help="flight date DDMMMYY (default: today UTC)")
    ap_arg.add_argument("--depz", default="1500",
                        help="assumed Zulu departure HHMM for day-part and URL")
    ap_arg.add_argument("--doc", default="dispatch_state.md",
                        help="state file holding THE FLEET, MODEL LIMITS, "
                             "REGION TABLE, AIRPORT CLASS REGISTER and THE "
                             "LOGBOOK (default: dispatch_state.md)")
    ap_arg.add_argument("--data", default="data", help="OurAirports CSV directory")
    ap_arg.add_argument("--top", type=int, default=None,
                        help="candidates reported per tail (default: 12 when a "
                             "tail, model, or class is named; 6 for a "
                             "full-fleet run)")
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
                             "Candidates at or near it score an event "
                             "positioning bonus and are exempt from the "
                             "fullness penalty (empty ferry legs are short)")
    ap_arg.add_argument("--event-radius", type=float, default=EVENT_RADIUS_NM,
                        help=f"nm around each --event airport (default "
                             f"{EVENT_RADIUS_NM})")
    ap_arg.add_argument("--event-phase", choices=["inbound", "outbound"],
                        default="inbound",
                        help="inbound: bonus for flying INTO the event market "
                             "(empty positioning). outbound: the tail is "
                             "already in the market and departures may carry "
                             "the event tie — no geographic bonus applies, "
                             "because every departure is equally event-tied")
    ap_arg.add_argument("--json", action="store_true")
    args = ap_arg.parse_args()

    try:
        doc = Doc(args.doc)
    except (OSError, KeyError) as exc:
        print(f"error reading {args.doc}: {exc}", file=sys.stderr)
        return 3
    try:
        airports = load_airports(args.data)
    except OSError as exc:
        print(f"error reading airport data: {exc}", file=sys.stderr)
        return 3

    ceiling = args.hours - CEILING_MARGIN_H
    if ceiling <= 0:
        print("availability leaves no block time after fixed overhead",
              file=sys.stderr)
        return 2

    pool = doc.fleet
    if not args.include_stored:
        pool = [f for f in pool if f["status"] != "stored"]
    named = False
    top_default_named, top_default_fleet = 12, 6
    if args.tail:
        pool = [f for f in pool if f["tail"].upper() == args.tail.upper()]
        named = True
    elif args.model:
        pool = [f for f in pool if f["model"].lower() == args.model.lower()]
        named = True
    elif args.cls:
        pool = [f for f in pool if f["cls"] == args.cls]
        named = True
    if not pool:
        print("no tails match that filter", file=sys.stderr)
        return 2
    if args.top is None:
        args.top = top_default_named if named else top_default_fleet

    flight_date = (datetime.strptime(args.date, "%d%b%y")
                   if args.date else datetime.now(timezone.utc))
    date_ddmmmyy = flight_date.strftime("%d%b%y").upper()
    deph, depm = args.depz[:2], args.depz[2:4]
    dep_dt_utc = datetime(flight_date.year, flight_date.month, flight_date.day,
                          int(deph), int(depm), tzinfo=timezone.utc)

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
        except KeyError as exc:
            notes.append(str(exc))
            continue

        local_hour, local_str = int(deph), f"{deph}:{depm}Z"
        if tf:
            tzname = tf.timezone_at(lat=cur["lat"], lng=cur["lon"])
            if tzname:
                loc = dep_dt_utc.astimezone(ZoneInfo(tzname))
                local_hour = loc.hour
                local_str = loc.strftime("%H:%M")
        part = day_part(local_hour)

        amphib_water_only = tail["tail"] == "N828DC" and not args.land
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

            if amphib_water_only:
                if not a["water"]:
                    continue
            else:
                if a["type"] == "seaplane_base":
                    continue
                if a["rwy"] < tail["min_rwy"]:
                    continue
                if (not args.allow_small_fields
                        and not field_quality_ok(a)
                        and ident != tail["home"]):
                    continue

            is_home = ident == tail["home"]
            eff = doc.class_register.get(ident, proxy_class(a))
            if not is_home and not amphib_water_only:
                # A tail's home base is always a legal destination regardless of tier.
                if eff == "B" and not args.allow_b:
                    continue
                if not tier_ok(a, eff, tail["cls"], args.allow_b):
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
                                 dest_region, home, cur, named, ev_dist)

            cands.append({
                "tail": tail["tail"],
                "model": tail["model"],
                "icao_type": tail["icao"],
                "class": tail["cls"],
                "dep": tail["current"],
                "dep_city": cur["muni"],
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
                "positioning": sc["positioning"],
                "event_tie_available": event_tie_available,
                "event_dist_nm": sc["event_dist_nm"],
                "ops": tail["ops"],
                "home_pull_active": (tail["ops"] != "floating"
                                     and tail["current"] != tail["home"]),
                "day_part": part,
                "dep_local": local_str,
                "dep_zulu": f"{deph}{depm}Z",
                "score": sc["total"],
                "score_parts": sc["parts"],
                **feas,
                "simbrief": SIMBRIEF_URL.format(
                    type=tail["icao"], orig=tail["current"], dest=ident,
                    reg=tail["tail"], date=date_ddmmmyy, deph=deph, depm=depm),
            })

        if not cands and home is not None:
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
                    "toward_home": True, "positioning": False,
                    "event_tie_available": False, "event_dist_nm": None,
                    "home_pull_active": True,
                    "day_part": part, "dep_local": local_str,
                    "dep_zulu": f"{deph}{depm}Z",
                    "score": 0, "score_parts": {"fallback_ferry": 0}, **feas,
                    "simbrief": SIMBRIEF_URL.format(
                        type=tail["icao"], orig=tail["current"], dest=ident,
                        reg=tail["tail"], date=date_ddmmmyy,
                        deph=deph, depm=depm),
                })
                notes.append(
                    f"{tail['tail']}: no scoring candidates from "
                    f"{tail['current']} — offering a ferry leg toward "
                    f"{tail['home']} instead")

        # Tie-break: score, then better-equipped field, then positioning legs
        # ahead of ordinary ones, then nearest-to-event for positioning and
        # longest-leg for everything else.
        def _key(c):
            return (-c["score"],
                    -TYPE_RANK.get(c["dest_type"], 0),
                    0 if c["positioning"] else 1,
                    c["event_dist_nm"] if c["positioning"] else -c["gc_nm"])

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
        results.extend(picked)

    if not results:
        print("no legal candidates within the block ceiling", file=sys.stderr)
        for n in notes:
            print(f"  note: {n}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ceiling_h": ceiling, "date": date_ddmmmyy,
                          "notes": notes, "candidates": results}, indent=2))
        return 0

    print(f"Block ceiling {fmt_hm(ceiling)} "
          f"(availability {fmt_hm(args.hours)} − 30 min) · "
          f"date {date_ddmmmyy} · assumed departure {deph}{depm}Z")
    for n in notes:
        print(f"note: {n}")

    by_tail: dict[str, list] = {}
    for c in results:
        by_tail.setdefault(c["tail"], []).append(c)

    for tail_id, cands in by_tail.items():
        t = cands[0]
        print(f"\n{tail_id} · {t['model']} ({t['icao_type']}) · from {t['dep']} "
              f"{t['dep_city']} · {t['dep_local']} local, {t['day_part']} · "
              f"ops {t['ops']}"
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
            if c["positioning"]:
                extra += (" POSITIONING-ferry"
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
