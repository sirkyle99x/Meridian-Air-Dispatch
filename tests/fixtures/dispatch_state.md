# dispatch_state.md
Schema v6.4 · RULES.md v7.2 · 12 NOV 2026

What a flight changes: THE FLEET and THE LOGBOOK, parsed by `dispatch_calc.py`
by section and column name. Everything that rarely changes — weights, regions,
the class register, preferred fields, tail notes — is in `reference.md` in the
repo; the calibration log is `claude/CALIBRATION.md`.

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

`Status` is `active` or `stored`. `Away` counts legs since the tail last left
home; a tail rehomed without a ferry (N444BC, N24SM, N312FU) shows Away 1 with
no matching row — expected, not drift.

## THE LOGBOOK

Last 10 flights, newest last; drop the oldest when an eleventh is added.
**Route is always `KAAA-KBBB`** — an unparseable Route stops the script.

| Date | Reg | Route | Block | Job type | Pax | Event | Hook |
|------|-----|-------|-------|----------|-----|-------|------|
| 19 SEP 2026 | N24SM | KPWK-KDAB | 2h 36m | Sports charter | 4 | — | Vantage Sports Hospitality to Daytona Speedway |
| 19 SEP 2026 | N988RS | KADS-KROW | 1h 26m | Sports charter | 7 | National Championship Air Races | Lone Star Aviation Partners to the closing day at Roswell |
| 20 SEP 2026 | N707BM | KJAC-KPUB | 1h 30m | Corporate charter | 3 | — | Defense-contractor engineers to a Pueblo meeting |
| 24 SEP 2026 | N707BM | KPUB-KJAC | 1h 27m | Owner trip | 2 | — | Owner and guest back to Jackson Hole after Pueblo business |
| 26 SEP 2026 | N988RS | KROW-MMSD | 2h 02m | VIP charter | 4 | — | Wedding party to the rehearsal dinner weekend in Los Cabos |
| 30 SEP 2026 | N610CD | KLGB-KSAF | 1h 37m | Corporate charter | 5 | Balloon Fiesta | Coastline Beverage Co. hospitality team (Dana Whitfield) to Santa Fe ahead of the Albuquerque Balloon Fiesta |
