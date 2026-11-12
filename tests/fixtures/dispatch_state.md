# dispatch_state.md
Schema v6.2 · RULES.md v7.0 · 12 NOV 2026

Machine-readable state. `dispatch_calc.py` parses **this file** — THE FLEET,
MODEL LIMITS, REGION TABLE, AIRPORT CLASS REGISTER, THE LOGBOOK — not RULES.md.

**This file holds what a flight changes. RULES.md holds what governs a flight.
`dispatch_calc.py` holds every constant.** On a fact — where a tail is, what it
has flown, what class a field is — this file governs. Disagreements go to
ARCHIVE.md → OPEN DISCREPANCIES. History and reasoning behind the figures here
live in ARCHIVE.md → STATE HISTORY, not in this file, so it stays small.

Section headers and column names are parsed by name, and the script refuses a
file whose `Schema v` differs from its own. Do not rename a section or column
without making the matching change in the script and bumping the schema. A
malformed cell — a non-numeric weight, an unknown ops mode, an unparseable
logbook Route — stops the run with exit 3 naming the cell; nothing is skipped
silently.

-----

### THE FLEET

| Tail | Model | ICAO | Class | Ops | Status | Plan KTAS | Min rwy | Home | Current | Away |
|---|---|---|---|---|---|---|---|---|---|---|
| N612JD | Citation Sovereign+ | C680 | mid_jet | floating | stored | 425 | 4900 | KTEB | KTEB | 0 |
| N680MK | Citation Sovereign+ | C680 | mid_jet | floating | stored | 425 | 4900 | KBFI | KBFI | 0 |
| N13SY | Citation X | C750 | mid_jet | floating | active | 517 | 5000 | KDJT | KDJT | 0 |
| N610CD | Citation X | C750 | mid_jet | based | active | 517 | 5000 | KLGB | KSAF | 1 |
| N728QL | Citation X | C750 | mid_jet | regional | active | 517 | 5000 | KTEB | KTEB | 0 |
| N444BC | Citation X | C750 | mid_jet | floating | active | 517 | 5000 | KJAC | KBFI | 1 |
| N24SM | Hawker 800 | H25B | mid_jet | regional | active | 459 | 5000 | KLGB | KDAB | 1 |
| N707BM | Hawker 800 | H25B | mid_jet | based | active | 459 | 5000 | KJAC | KJAC | 0 |
| N988RS | Hawker 800 | H25B | mid_jet | floating | active | 459 | 5000 | KDJT | MMSD | 2 |
| N312FU | Hawker 800 | H25B | mid_jet | floating | active | 459 | 5000 | KTEB | KBHM | 1 |
| N388BB | Falcon 50 | FA50 | mid_jet | based | active | 478 | 4500 | KTEB | KTEB | 0 |
| N205JA | Falcon 50 | FA50 | mid_jet | regional | active | 478 | 4500 | KDJT | KDJT | 0 |
| N777ZL | Falcon 50 | FA50 | mid_jet | floating | active | 478 | 4500 | KJAC | KJAC | 0 |
| N539CA | Falcon 50 | FA50 | mid_jet | floating | active | 478 | 4500 | KLGB | KLGB | 0 |
| N737GG | 737-800 BBJ2 | B738 | large_jet | floating | active | 467 | 6500 | KOPF | KOPF | 0 |
| N839BA | 737-700 BBJ | B737 | large_jet | floating | active | 467 | 6000 | KPSP | KPSP | 0 |
| N417KG | TBM 850 | TBM8 | turboprop | regional | active | 320 | 3000 | KHPN | KHPN | 0 |
| N247LB | TBM 850 | TBM8 | turboprop | regional | active | 320 | 3000 | KJAC | KJAC | 0 |
| N514RS | Starship 2000A | STAR | turboprop | regional | active | 335 | 4000 | KSDL | KSDL | 0 |
| N80WE | Royal Turbine Duke | B60T | turboprop | based | active | 290 | 2500 | KFAR | KFAR | 0 |
| N75KY | Caravan (cargo pod) | C208 | turboprop | regional | active | 175 | 2500 | KNEW | KNEW | 0 |
| N828DC | Caravan (amphibious) | C208 | turboprop | based | active | 150 | 2500 | PALH | PALH | 0 |

`Model` is the join key into MODEL LIMITS. `Status` is `active` or `stored`; a
stored tail keeps full state but generates no candidates, and returning it to
service is a one-word edit. Ops modes are defined in RULES.md → VARIETY ENGINE.
`Hobbs` and `Flts` were dropped 20 OCT 2026; the script reads them with defaults
and its output is unchanged without them.

**Bases (23 SEP 2026).** Mid jets home on four hubs — KDJT, KTEB, KJAC, KLGB —
each carrying one Citation X, one Hawker 800 and one Falcon 50. Per type, one
tail is `based`, one `regional`, two `floating`; both BBJs are `floating`.
N444BC, N24SM and N312FU were rehomed without being ferried, so each shows
Away 1 at its old field until a leg moves it. Full reasoning: ARCHIVE.md →
STATE HISTORY.

**Tail notes** — story material for RULE 5. One per tail, kept with the row it
describes.

- **N612JD** — Sovereign+. NYC-area bizav; KTEB under the NY Class B shelf.
  Stored 17 SEP 2026.
- **N680MK** — Sovereign+. Pacific Northwest, KBFI as the KSEA reliever; Seattle
  tech and aerospace clientele. Stored 17 SEP 2026 without flying a leg, so the
  PNW slot was held rather than lost.
- **N13SY** — Citation X. Fastest business jet in the world at certification.
  South Florida: Caribbean, Bahamas, Southeast corporate. Floating, so the
  South Florida roots are flavor rather than a mechanical pull.
- **N610CD** — Citation X. West Coast; KLGB has 10,000 ft. The type's `based`
  tail.
- **N728QL** — Citation X. Northeast corner base at Teterboro. The C750's usable
  fuel is what makes a corner workable — transcon, Bermuda and the Caribbean all
  sit inside the envelope, where a Hawker would be locked east of Denver.
- **N444BC** — Citation X. Jackson Hole, joining the Hawker, TBM and Falcon 50
  working the resort circuit there. Floating, so its range still reaches both
  coasts. Still sitting at Boeing Field.
- **N24SM** — Hawker 800XP. Long Beach, alongside the based Citation X and a
  floating Falcon 50. Still sitting at Daytona from its last logged leg.
- **N707BM** — Hawker 800XP. Mountain West, sharing the KJAC ramp with N247LB.
  Jackson Hole sits at 6,451 ft inside Grand Teton National Park, the only Class
  D commercial-service field in a national park. Works the resort circuit —
  Telluride, Montrose, Rifle, Sun Valley, Gunnison, Aspen. The type's `based`
  tail, so the pull targets Jackson Hole exactly.
- **N988RS** — Hawker 800XP. KDJT, joining Citation X and Falcon 50 there.
  Floating; sitting at Los Cabos after its 26 SEP leg.
- **N312FU** — Hawker 800XP. Teterboro, joining Citation X and the based
  Falcon 50 there. Floating; still sitting at Birmingham.
- **N388BB** — Falcon 50. Northeast hub at Teterboro, shared with Citation X
  N728QL. The type's real reserve-compliant range (roughly 1,600 nm GC, see
  MODEL LIMITS) keeps it inside a coast-to-tech-stop pattern rather than the
  transcon/Caribbean reach of the Citation X sharing its ramp.
- **N205JA** — Falcon 50. KDJT, alongside Citation X N13SY and Hawker N988RS —
  the field's only regional tail among a floating majority.
- **N777ZL** — Falcon 50. Jackson Hole ramp with the based Hawker, the regional
  TBM and the floating Citation X; floating, so it ranges well past the Mountain
  West between home cycles.
- **N539CA** — Falcon 50. Long Beach, alongside the based Citation X N610CD
  and the regional Hawker N24SM; floating, West Coast flavor without a
  mechanical pull.
- **N737GG** — 737-800 BBJ2. South Florida: Caribbean, Latin America,
  transatlantic via the Azores viable. KOPF is a serious bizav environment.
- **N839BA** — 737-700 BBJ. Smaller cabin, exceptional range. Palm Springs:
  entertainment industry, Coachella Valley, desert circuit. An owner's aircraft
  rather than one on the charter market. Floating; Palm Springs remains its
  story anchor without a mechanical pull home.
- **N417KG** — TBM 850. NYC metro under the Class B shelf. Finance, media and
  legal clientele; Northeast corridor, New England, Canada.
- **N247LB** — TBM 850. Mountain West. Teton and Yellowstone gateway, strong ski
  and summer charter market.
- **N514RS** — Beechcraft Starship. Canard pusher, one of a kind, always draws a
  crowd. Desert VIP market: tech money, spring training, resorts.
- **N80WE** — Beechcraft B60 Duke, Royal Turbine conversion (PT6A-21, B60T).
  Northern Plains owner work, out-and-back by nature.
- **N75KY** — Caravan 208 with belly cargo pod. Passenger flights with generous
  freight capacity. Gulf Coast, Mississippi Delta, Louisiana bayou.
- **N828DC** — Caravan 208, amphibious. Land capable, but revenue missions
  deliver to water: seaplane bases, lakes, bays, coastal strips. Alaska bush, BC
  coast, Pacific NW islands, Florida Keys, Bahamas. Hooks always involve a water
  arrival; a ferry leg may use a runway.

**Retired tails** — out of the fleet, generating no missions. Their calibration
rows stay valid, since calibration reads class and model rather than tail.

| Tail | Model | Retired |
|---|---|---|
| N100PE | Citation Sovereign+ | 12 SEP 2026 |
| N471CB | Citation Sovereign+ | 12 SEP 2026 |
| N517CF | Citation X | 12 SEP 2026 |

### MODEL LIMITS

Weights in lbs. BOW is the SimBrief airframe Empty Weight field. One row per
model, not per tail. Confirmed 11 SEP 2026 against ten airframe screenshots;
BBJ1 baggage and Falcon 50 (full row) confirmed 23 SEP 2026; Hawker 800 BOW
and Baggage re-confirmed against the in-sim figures 25 SEP 2026.

| Model | ICAO | Seats | BOW | MZFW | MTOW | MLW | Max fuel | Baggage | Plan burn | Reserve |
|---|---|---|---|---|---|---|---|---|---|---|
| Citation Sovereign+ | C680 | 9 | 18781 | 21000 | 30775 | 27575 | 11390 | 1000 | 1350 | 1750 |
| Citation X | C750 | 9 | 22481 | 24400 | 36100 | 31800 | 12931 | 775 | 1900 | 2500 |
| 737-700 BBJ | B737 | 19 | 96625 | 126000 | 171500 | 134000 | 71662 | 29375 | 5000 | 6500 |
| 737-800 BBJ2 | B738 | 19 | 102187 | 138300 | 174700 | 146300 | 69980 | 17645 | 5300 | 6900 |
| Caravan (cargo pod) | C208 | 9 | 4237 | 8500 | 8750 | 8500 | 2224 | 1400 | 370 | 370 |
| Caravan (amphibious) | C208 | 8 | 5380 | 8800 | 9062 | 9062 | 2224 | 500 | 390 | 390 |
| TBM 850 | TBM8 | 5 | 4629 | 6032 | 7394 | 7024 | 1957 | 330 | 400 | 400 |
| Starship 2000A | STAR | 6 | 10085 | 12600 | 14900 | 13680 | 3752 | 400 | 750 | 750 |
| Royal Turbine Duke | B60T | 5 | 4553 | 7000 | 7000 | 7000 | 1595 | 400 | 430 | 430 |
| Hawker 800 | H25B | 8 | 16010 | 18450 | 28000 | 23350 | 9956 | 250 | 1500 | 1950 |
| Falcon 50 | FA50 | 9 | 22741 | 25570 | 40780 | 35715 | 15513 | 2829 | 2125 | 1508 |

- **Royal Turbine Duke** — MZFW equals MTOW: SimBrief declares no separate
  zero-fuel limit, so fuel competes directly against MTOW and payload moves
  leg by leg.
- **Citation X** — keeps 9 seats but the payload check caps it at 8 at the full
  allowance; the ninth seat is weight-limited, as on the real aircraft. Every
  C750 SimBrief profile runs the fleet-standard 175/55 (reset 30 SEP 2026).
  Baggage 775 is SimBrief's Max Cargo Weight and is firm.
- **737-800 BBJ2** — Baggage 17,645 is SimBrief's Max Cargo Weight and is firm.
- **737-700 BBJ** — Max Cargo Weight is blank in SimBrief, so Baggage holds the
  zero-fuel envelope (MZFW − BOW = 29,375), shared by passengers, bags and
  freight. Runs 175/55; no weight override.
- **Hawker 800** — Baggage 250 is a firm hold cap matching the in-sim aircraft
  and the SimBrief profile, so freight room is `250 − (pax × 25)`: 50 lb at
  8 pax, 250 at zero. Passengers run 170 lb body / 25 lb bag via the script's
  "H25B" override. Usable load for passengers, bags and freight is MZFW − BOW
  = 2,440 lb (see ARCHIVE.md → PROVISIONAL VALUES on the crew reading).
- **Falcon 50** — Max Cargo Weight is blank, so Baggage holds the zero-fuel
  envelope (MZFW − BOW = 2,829). Passengers run 200 lb body / 35 lb bag via the
  script's "FA50" override. Plan burn and Reserve are averages of the four
  cleanest 23 SEP OFPs.
- **Caravans, TBM 850, Starship** — Baggage is published-spec or
  developer-statement derived, the softest figures here.

**Falcon 50 real range is well under the published 3,057 nm.** KTEB–KSEA
(2,082 nm GC) and KLAX–KTEB (2,132 nm GC) both drew SimBrief's range warning
and came up short of reserves at max fuel; KELP–KTEB (1,644 nm GC) planned
clean with no margin. Treat anything beyond roughly 1,600 nm GC as needing a
tech stop. A leg between 1,644 and 2,082 nm would narrow the ceiling.

### REGION TABLE

| Region | Scope | Members |
|---|---|---|
| Northeast | us_state | ME NH VT MA RI CT NY NJ PA |
| Mid-Atlantic | us_state | DE MD DC VA WV |
| Southeast | us_state | NC SC GA FL |
| Mid-South | us_state | TN KY AL MS AR |
| Gulf / South Central | us_state | LA TX OK |
| Great Lakes | us_state | OH MI IN IL WI |
| Upper Midwest / Plains | us_state | MN IA MO ND SD NE KS |
| Mountain West | us_state | MT ID WY CO UT NV |
| Southwest | us_state | AZ NM |
| Pacific | us_state | WA OR CA |
| Alaska | us_state | AK |
| Hawaii | us_state | HI |
| Canada | country | CA |
| Mexico | country | MX |
| Bahamas & Caribbean | country | BS TC KY JM PR VI CU AG BB DM DO GD HT KN LC VC MS TT VG AI AW CW SX BQ GP MQ BL MF |

**Affinity** — a destination scores the affinity bonus unless its region is
excluded for the tail's class below, or is `Other`. Parsed by the script;
region names must match the table above exactly. `—` excludes nothing.

| Class | Excluded regions |
|---|---|
| turboprop | Hawaii |
| mid_jet | Hawaii |
| large_jet | — |

`Scope` exists because US state codes and ISO country codes share a two-letter
namespace: without it Colombia resolves to Colorado's region and Canada to
California's. Anything outside every list is region `Other` — legal, but it
scores no affinity and always counts as a new region.

### AIRPORT CLASS REGISTER

Sorted by ICAO. An airport earns an entry when it first reaches a final board or
first appears in THE LOGBOOK by another route. Verification rules are in
RULES.md → THE AIRPORT DATABASE.

| ICAO | Class | Verified |
|---|---|---|
| CYVR | C | 12 SEP 2026 |
| CYWG | C | 18 SEP 2026 |
| KADW | B | 12 SEP 2026 |
| KASE | D | 19 SEP 2026 |
| KATL | B | 12 SEP 2026 |
| KBEC | D | 18 SEP 2026 |
| KBFI | D | 11 SEP 2026 |
| KBOS | B | 12 SEP 2026 |
| KBWI | B | 12 SEP 2026 |
| KCLE | B | 12 SEP 2026 |
| KCLT | B | 12 SEP 2026 |
| KCVG | B | 12 SEP 2026 |
| KDAL | B | 12 SEP 2026 |
| KDCA | B | 12 SEP 2026 |
| KDEN | B | 12 SEP 2026 |
| KDFW | B | 12 SEP 2026 |
| KDTW | B | 12 SEP 2026 |
| KEDC | D | 12 SEP 2026 |
| KEWR | B | 12 SEP 2026 |
| KGRR | C | 25 SEP 2026 |
| KHOU | B | 12 SEP 2026 |
| KHPN | D | 11 SEP 2026 |
| KIAD | B | 12 SEP 2026 |
| KIAH | B | 12 SEP 2026 |
| KILE | E | 19 SEP 2026 |
| KJFK | B | 12 SEP 2026 |
| KLAS | B | 12 SEP 2026 |
| KLAX | B | 12 SEP 2026 |
| KLGA | B | 12 SEP 2026 |
| KLGB | D | 11 SEP 2026 |
| KLSV | B | 12 SEP 2026 |
| KMCI | B | 12 SEP 2026 |
| KMCO | B | 12 SEP 2026 |
| KMEM | B | 12 SEP 2026 |
| KMIA | B | 12 SEP 2026 |
| KMSP | B | 12 SEP 2026 |
| KMSY | B | 12 SEP 2026 |
| KNKX | B | 12 SEP 2026 |
| KNYL | D | 19 SEP 2026 |
| KOPF | D | 11 SEP 2026 |
| KORD | B | 12 SEP 2026 |
| KPHL | B | 12 SEP 2026 |
| KPHX | B | 12 SEP 2026 |
| KPIT | B | 12 SEP 2026 |
| KPWK | D | 11 SEP 2026 |
| KSAN | B | 12 SEP 2026 |
| KSEA | B | 12 SEP 2026 |
| KSFO | B | 12 SEP 2026 |
| KSLC | B | 12 SEP 2026 |
| KSTL | B | 12 SEP 2026 |
| KTEB | D | 11 SEP 2026 |
| KTEX | E | 18 SEP 2026 |
| KTPA | B | 12 SEP 2026 |
| KVKS | E | 19 SEP 2026 |
| MYGF | C | 18 SEP 2026 |
| PHNL | B | 12 SEP 2026 |

## THE LOGBOOK

**A rolling window of the last 10 flights, newest last.** When an eleventh row
is added the oldest is dropped. Nothing in the scoring model reads past ten —
recency looks at 10, region rotation at 5, the event-badge cap at 2, recurring
characters at 3 — so this table never grows. Kyle keeps permanent flight
history, Hobbs and OFPs in a separate program; this table exists only to steer
variety.

**Route is always `KAAA-KBBB`** — departure ICAO, hyphen, destination ICAO, no
spaces or other text. The script reads Route to score recency and region
rotation, and an unparseable Route stops the run (exit 3).

| Date | Reg | Route | Block | Job type | Pax | Event | Hook |
|------|-----|-------|-------|----------|-----|-------|------|
| 19 SEP 2026 | N24SM | KPWK-KDAB | 2h 36m | Sports charter | 4 | — | Vantage Sports Hospitality to Daytona Speedway |
| 19 SEP 2026 | N988RS | KADS-KROW | 1h 26m | Sports charter | 7 | National Championship Air Races | Lone Star Aviation Partners to the closing day at Roswell |
| 20 SEP 2026 | N707BM | KJAC-KPUB | 1h 30m | Corporate charter | 3 | — | Defense-contractor engineers to a Pueblo meeting |
| 24 SEP 2026 | N707BM | KPUB-KJAC | 1h 27m | Owner trip | 2 | — | Owner and guest back to Jackson Hole after Pueblo business |
| 26 SEP 2026 | N988RS | KROW-MMSD | 2h 02m | VIP charter | 4 | — | Wedding party to the rehearsal dinner weekend in Los Cabos |
| 30 SEP 2026 | N610CD | KLGB-KSAF | 1h 37m | Corporate charter | 5 | Balloon Fiesta | Coastline Beverage Co. hospitality team (Dana Whitfield) to Santa Fe ahead of the Albuquerque Balloon Fiesta |

## OFP CALIBRATION LOG

Measures the model against **SimBrief's own predicted air time** (OFF to ON on
the filed OFP), never against what was flown. The reference is deterministic,
so points can be generated without flying and a single anomalous flight can
never move a constant. Method, refit procedure and the reason wind is removed
are in RULES.md → FLIGHT TIME.

```
still_air_min = ofp_air_min × (ofp_gnd_dist / ofp_air_dist)
```

`GC` is the OFP great-circle distance — the figure the script has at board
time, before the 1.07 route factor. `Model` is
`gc × 1.07 / plan_ktas × 60 + overhead_min` under the constants live at the time
of the row. `Dev` compares Model against the still-air column. A row may be
logged as soon as the OFP is pasted; it does not depend on the leg being flown.

| Date | Tail | Airframe | Class | GC | OFP air | Still-air | Model | Dev |
|---|---|---|---|---|---|---|---|---|
| 19 SEP 2026 | N988RS | Hawker 800 | mid_jet | 39 | 20 | 20.3 | 21.1 | −3.5% |
| 19 SEP 2026 | N988RS | Hawker 800 | mid_jet | 146 | 37 | 38.3 | 36.0 | +6.4% |
| 19 SEP 2026 | N988RS | Hawker 800 | mid_jet | 363 | 68 | 69.2 | 66.4 | +4.2% |
| 19 SEP 2026 | N988RS | Hawker 800 | mid_jet | 624 | 101 | 100.6 | 102.9 | −2.3% |
| 19 SEP 2026 | N24SM | Hawker 800 | mid_jet | 845 | 134 | 133.9 | 133.8 | +0.0% |
| 19 SEP 2026 | N728QL | Citation X | mid_jet | 47 | 20 | 18.6 | 21.4 | −13.2% |
| 19 SEP 2026 | N728QL | Citation X | mid_jet | 164 | 37 | 33.7 | 36.0 | −6.3% |
| 19 SEP 2026 | N728QL | Citation X | mid_jet | 282 | 53 | 48.8 | 50.6 | −3.6% |
| 19 SEP 2026 | N728QL | Citation X | mid_jet | 470 | 76 | 73.3 | 74.0 | −0.9% |
| 19 SEP 2026 | N728QL | Citation X | mid_jet | 826 | 121 | 119.9 | 118.2 | +1.5% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 48 | 21 | 21.3 | 22.2 | −4.1% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 161 | 37 | 37.9 | 37.7 | +0.4% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 377 | 66 | 69.3 | 67.4 | +2.7% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 560 | 92 | 93.7 | 92.6 | +1.2% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 949 | 144 | 149.2 | 146.1 | +2.1% |
| 19 SEP 2026 | N737GG | 737-800 BBJ2 | large_jet | 2030 | 307 | 292.9 | 294.7 | −0.6% |
| 19 SEP 2026 | N839BA | 737-700 BBJ | large_jet | 365 | 72 | 64.0 | 65.8 | −2.8% |
| 19 SEP 2026 | N839BA | 737-700 BBJ | large_jet | 976 | 145 | 155.6 | 149.8 | +3.9% |
| 19 SEP 2026 | N988RS | Hawker 800 | mid_jet | 387 | 70 | 66.1 | 69.7 | −5.1% |
| 20 SEP 2026 | N707BM | Hawker 800 | mid_jet | 426 | 66 | 69.5 | 75.2 | −7.6% |
| 24 SEP 2026 | N707BM | Hawker 800 | mid_jet | 426 | 71 | 73.0 | 75.2 | −2.9% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 29 | 27 | 27.8 | 19.5 | −29.9% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 164 | 33 | 36.0 | 37.6 | +4.5% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 470 | 85 | 78.6 | 78.7 | +0.2% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 956 | 159 | 144.5 | 144.0 | −0.3% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 1395 | 214 | 194.7 | 203.0 | +4.2% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 1644 | 221 | 236.8 | 236.4 | −0.2% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 2082 | 347 | 320.7 | 295.2 | −7.9% |
| 23 SEP 2026 | N388BB | Falcon 50 | mid_jet | 2132 | 282 | 296.3 | 302.0 | +1.9% |
| 26 SEP 2026 | N988RS | Hawker 800 | mid_jet | 668 | 106 | 104.1 | 109.0 | −4.6% |
| 27 SEP 2026 | N707BM | Hawker 800 | mid_jet | 614 | 107 | 102.5 | 101.5 | +1.0% |
| 30 SEP 2026 | N610CD | Citation X | mid_jet | 605 | 81 | 87.4 | 90.7 | −3.6% |
| 21 OCT 2026 | N839BA | 737-700 BBJ | large_jet | 2580 | 355 | 372.2 | 370.3 | +0.5% |

**Running tally.** Each model was fitted against its own rows, so a tight fit is
expected rather than evidence; the rows are a baseline for detecting drift.

| Pool | n | Mean | Mean abs | Fitted |
|---|---|---|---|---|
| Hawker 800 | 10 | −1.4% | 4.1% | 459 KTAS |
| Citation X | 6 | −4.4% | 4.9% | 517 KTAS |
| BBJ2 · BBJ | 9 | +0.4% | 2.0% | 467 KTAS, shared |
| Falcon 50 (fit rows only) | 3 | −0.1% | 0.2% | 478 KTAS |

**Out-of-sample status.** Rows planned after a fit closed are the only ones
that can falsify a constant. Hawker 800: five points (−5.1%, −7.6%, −2.9%,
−4.6%, +1.0%), all inside the fitted scatter; the 27 SEP KJAC–CYVR point broke
the short-side streak, so 459 KTAS stands with nothing to watch. Citation X:
one point (KLGB–KSAF, −3.6%), consistent with the shared overhead running a
touch high on this airframe. BBJ: one point (KPSP–TXKF, +0.5%, planned
21 OCT, not flown). Per-point narratives are in ARCHIVE.md → STATE
HISTORY.

**Rows excluded from fitting.**
- **Falcon 50 fit** used KTEB–KCLT, KTEB–KMIA and KELP–KTEB (3 kt spread across
  470–1,644 nm). KTEB–KDEN (+4.2%) and KTEB–KBOS (+4.5%) are retained as checks.
- **KDJT–KFXE (Falcon, −29.9%)** — excluded: a 3.6× ground/GC dogleg on a 29 nm
  hop. Not evidence the model is broken at short range.
- **KTEB–KSEA and KLAX–KTEB (Falcon)** — excluded from speed: fuel-limited
  plans. Retained because they bound the range ceiling (MODEL LIMITS).

**Standing notes.**
- Overhead is one global constant (0.26h, in the script), not per-model; each
  plan speed was fitted with it held fixed. Citation X residuals trend positive
  with distance, so 0.26h is a touch high there — worth a per-class column only
  if that 2–3 minute error ever matters.
- The two BBJs share one constant; the -700's two points fall inside the -800's
  spread with opposite signs.
- Percentage misleads at short range: −13.2% is a 2.8-minute miss on a
  nineteen-minute flight. Read absolute minutes at the short end.
- No turboprop points exist. Both TBMs, the Starship, the Duke and both Caravans
  carry derived plan speeds against a jet-fitted overhead — the least
  trustworthy estimates in the fleet.
