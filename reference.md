# reference.md
Reference v1.0 · dispatch_calc.py v7.2 · 12 NOV 2026

What rarely changes, fetched beside `dispatch_calc.py` from the same release
tag and parsed by it: MODEL LIMITS, REGION TABLE, AIRPORT CLASS REGISTER,
PREFERRED FIELDS and TAIL NOTES. It is never read into a Dispatch session —
the script prints what a board needs (tail notes included). What a flight
changes lives in the project's `dispatch_state.md`.

Editing this file is a release: commit to `main`, let the golden tests run,
tag the version, then point RULES.md at it (ARCHIVE.md → CHANGE CONTROL).
Section headers and column names are parsed by name, and the script refuses a
file whose `Reference v` differs from its own.

-----

### MODEL LIMITS

Weights in lbs. BOW is the SimBrief airframe Empty Weight field. One row per
model, not per tail. Confirmed 11 SEP 2026 against ten airframe screenshots;
BBJ1 baggage and Falcon 50 (full row) confirmed 23 SEP 2026; Hawker 800 BOW
and Baggage re-confirmed against the in-sim figures 25 SEP 2026.

| Model | ICAO | Seats | BOW | MZFW | MTOW | MLW | Max fuel | Baggage | Plan burn | Reserve | Max GC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Citation Sovereign+ | C680 | 9 | 18781 | 21000 | 30775 | 27575 | 11390 | 1000 | 1350 | 1750 | — |
| Citation X | C750 | 9 | 22481 | 24400 | 36100 | 31800 | 12931 | 775 | 1900 | 2500 | — |
| 737-700 BBJ | B737 | 19 | 96625 | 126000 | 171500 | 134000 | 71662 | 29375 | 5000 | 6500 | — |
| 737-800 BBJ2 | B738 | 19 | 102187 | 138300 | 174700 | 146300 | 69980 | 17645 | 5300 | 6900 | — |
| Caravan (cargo pod) | C208 | 9 | 4237 | 8500 | 8750 | 8500 | 2224 | 1400 | 370 | 370 | — |
| Caravan (amphibious) | C208 | 8 | 5380 | 8800 | 9062 | 9062 | 2224 | 500 | 390 | 390 | — |
| TBM 850 | TBM8 | 5 | 4629 | 6032 | 7394 | 7024 | 1957 | 330 | 400 | 400 | — |
| Starship 2000A | STAR | 6 | 10085 | 12600 | 14900 | 13680 | 3752 | 400 | 750 | 750 | — |
| Royal Turbine Duke | B60T | 5 | 4553 | 7000 | 7000 | 7000 | 1595 | 400 | 430 | 430 | — |
| Hawker 800 | H25B | 8 | 16010 | 18450 | 28000 | 23350 | 9956 | 250 | 1500 | 1950 | — |
| Falcon 50 | FA50 | 9 | 22741 | 25570 | 40780 | 35715 | 15513 | 2829 | 2125 | 1508 | 1550 |

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

**Max GC** caps a model's great-circle leg below what the fuel check allows;
`—` means no cap. The script drops longer candidates and `--finalize` flags a
longer pick. A fallback ferry is exempt, since a real ferry takes a tech stop.

**Falcon 50 real range is well under the published 3,057 nm.** KTEB–KSEA
(2,082 nm GC) and KLAX–KTEB (2,132 nm GC) both drew SimBrief's range warning
and came up short of reserves at max fuel; KELP–KTEB (1,644 nm GC) planned
clean with no margin — eastbound, with the usual tailwind. Max GC is set at
1,550 nm (12 NOV 2026) to keep a margin for a westbound headwind the board
cannot model. A clean westbound OFP beyond it would justify raising it.

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

Sorted by ICAO. Holds every US Class B airport — the 37 primaries, checked
against the FAA list 12 NOV 2026, plus Nellis (KLSV) and Love Field (KDAL),
which sit inside a primary's Class B surface area — and any other field whose
class has been verified. An unlisted field flies on its proxy class, and no
unlisted US field is Class B. Rules are in RULES.md → THE AIRPORT DATABASE.

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

### PREFERRED FIELDS

Kyle's preferred destinations. Each scores the destination-quality cap, so it
ranks level with the best airline airports, and a listed military field is
exempt from the military exclusion. The list ranks legal fields only: a field
that fails a tail's `Min rwy`, field quality, tier or Class B rule stays off
that tail's board regardless. Every ICAO must exist in the airport data
(checked every run). Scenery fields that are Class B (KDFW, KDAL, KIAH, KHOU,
KMSY) are left off because no jet may take them without `--allow-b`.

| ICAO | Note |
|---|---|
| KADS | reliever — Dallas |
| KAPA | reliever — Denver |
| KAPC | resort — Napa |
| KAPF | resort — Naples |
| KASE | resort — Aspen |
| KBCT | reliever — Boca Raton |
| KBED | reliever — Boston |
| KBUR | reliever — Los Angeles |
| KDTO | reliever — Dallas |
| KDWH | reliever — Houston |
| KEGE | resort — Vail |
| KFRG | reliever — New York |
| KFXE | reliever — Fort Lauderdale |
| KHDN | resort — Steamboat |
| KHEF | reliever — Washington |
| KHPN | reliever — New York |
| KJYO | reliever — Washington |
| KLUK | reliever — Cincinnati |
| KMKC | reliever — Kansas City |
| KMMU | reliever — New York |
| KMRY | resort — Monterey |
| KOPF | reliever — Miami |
| KPDK | reliever — Atlanta |
| KPWK | reliever — Chicago |
| KSDL | reliever — Phoenix |
| KSGR | reliever — Houston |
| KSUN | resort — Sun Valley |
| KSUS | reliever — St. Louis |
| KTEB | reliever — New York |
| KTEX | resort — Telluride |
| KTKI | reliever — Dallas |
| KTMB | reliever — Miami |
| KTRK | resort — Lake Tahoe |
| KVNY | reliever — Los Angeles |
| KABQ | scenery |
| KAMA | scenery |
| KAUS | scenery |
| KBHM | scenery |
| KELP | scenery |
| KOKC | scenery |
| KRVS | scenery |
| KSAT | scenery |
| KTUL | scenery |

### TAIL NOTES

Story material for RULE 5, one per tail; the script prints each under its tail
in the board table. A note is flavour, never a mechanic.

**Bases (23 SEP 2026).** Mid jets home on four hubs — KDJT, KTEB, KJAC, KLGB —
each carrying one Citation X, one Hawker 800 and one Falcon 50. Per type, one
tail is `based`, one `regional`, two `floating`; both BBJs are `floating`.
N444BC, N24SM and N312FU were rehomed without being ferried, so each shows
Away 1 at its old field until a leg moves it. Full reasoning: ARCHIVE.md →
STATE HISTORY.

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

### RETIRED TAILS

Out of the fleet, generating no missions. Their calibration rows stay valid,
since calibration reads class and model rather than tail.

| Tail | Model | Retired |
|---|---|---|
| N100PE | Citation Sovereign+ | 12 SEP 2026 |
| N471CB | Citation Sovereign+ | 12 SEP 2026 |
| N517CF | Citation X | 12 SEP 2026 |
