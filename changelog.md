CHANGELOG.md

Version history for the Dispatch system, v1.0 onward.

Read this file only during a full review pass. It is a record of what changed, not an alternate rule set. Where this file and DISPATCH.md body text disagree, the body text governs and the disagreement is logged to OPEN DISCREPANCIES. Any behavior change is written into the body in the same edit that adds the entry here.

Companion files: DISPATCH.md (philosophy, rules, scoring, fleet, logbook) · TEMPLATES.md (RULE 2/3/6 templates) · dispatch_calc.py (candidate math).

VERSION HISTORY

v1.0 — 16 JUN 2026 — Founded. Split from FlightDesk after Sprint 3.

v1.1 — 16 JUN 2026 — Hangar populated (since wiped). 15 aircraft added across 6 type classes. Performance data sourced from published add-on specs.

v1.2 — 16 JUN 2026 — Airspace routing rules added. Aircraft assigned to airspace tiers by class.

v1.3 — 16 JUN 2026 — Money layer removed entirely. Dispatch is now purely about the mission, the route, and the flight.

v1.4 — 16 JUN 2026 — Hangar wiped and restarted. Interface conventions established.

v1.5 — 18 JUN 2026 — Airspace routing rules refined. Home base and current location tracked as separate fields. Soft-pull repositioning model adopted. Hobbs and total flight count tracked per aircraft, no mechanical consequence.

v1.6 — 19 JUN 2026 — Interface conventions replaced with fully prescriptive hard-coded visual spec (Rules 1-5). Dual time on mission cards. Language standards locked. Story hook standards codified.

v1.7 — 19 JUN 2026 — Full document review and cleanup. Removed redundant sections and stale language. Block time calculation updated to use 1.07 routing factor with SimBrief as authoritative source. Block time adj field added to hangar template. Logbook enriched with job type and pax count columns. Session flow updated to reflect project-based doc management.

v1.8 — 19 JUN 2026 — Fleet expanded to 14 aircraft (3 pending). Phenom 300E removed from fleet and airspace rules. BBJs added: N737GG (BBJ2 738) at KOPF, N839BA (BBJ 737-700) at KPSP. Citation X fleet expanded: N517CF at KPWK, N610CD at KLGB. TBM 850s added: N417KG at KHPN, N247LB at KJAC. Turboprops added: N828DC amphib Caravan at W55, N75KY cargo pod Caravan at KNEW, N514RS Starship at KSDL. HondaJets added: N542MP at KRIC, N121HJ at KGSP. Aircraft type rotation rule added to variety engine. International ops fully open by range and session time only. Session length flags converted from distance-based to block-time-based with jet short-leg floor of 150nm.

v1.9 — 19 JUN 2026 — BBJ airspace routing reclassified: Class C now primary; Class B only when no suitable Class C serves the metro or story demands it; Class D capable if runway >= 7,000 ft. Class C example airports seeded (KHPN, KBFI, KMDW, KBUR, KBDL, KBHM, KSAT, KCOS, KFAT). Mission card badge slot 2 rewritten: now a real-world event badge with concise event name label; omitted entirely when no event applies.

v2.0 — 19 JUN 2026 — Fleet completed at 21 aircraft. Seven new tails added: N825GB (A36TC) at KGEG, N6060E (B36TC) at KSAT, N18VK (BE6G Grand Duke) at KBNA, N80WE (Royal Turbine Duke) at KFAR, N95BH (Baron 58P) at KABE, N572J (Aerostar 601P) at KAUS, N8298P (PA-24-250 Comanche) at KCHD. Piston twins and piston singles added as new hangar sections. Duplicate LIGHT JETS and TURBOPROP sections removed. Regional coverage now spans Pacific Northwest, Texas (×2), Mid-South, Northern Great Plains, Mid-Atlantic PA, and Phoenix metro piston tier.

v2.1 — 20 JUN 2026 — Rules review and corrections. Session length flags updated: all aircraft classes now explicitly eligible within block time ceiling regardless of session length. Short-leg floors revised: jets 50nm minimum, turboprops and pistons no minimum. Rule 2 trigger tightened: fleet table only on explicit fleet request or specific tail lookup; aircraft/class stated as mission preference goes directly to filtered mission cards. Hobbs and Flights columns removed from fleet table spec. N18VK corrected to BE6G Grand Duke.

v2.2 — 20 JUN 2026 — Block time formula: taxi out (20 min) and taxi in (8 min) added directly into block time calculation. Prep (12 min) added as session time on top of block time. Card count locked at 4.

v2.3 — 20 JUN 2026 — All 21 airframes evaluated every session; math runs silently, board renders directly. No jet minimum leg floor — Kyle decides if a leg is too short, including repositioning hops. Routed nm added as Air dist (Cell 6) on mission cards. Stats grid expanded to 6-cell 2x3 layout.

v2.4 — 04 JUL 2026 — Full drift-reconciliation and event-story pass.

Jet short-leg floor corrected back to true "no minimum" (the v2.1 changelog's 50nm figure was never reflected in body text and is superseded — body text is now the sole source of truth per the new standing rule below).
RULE 1 mission label changed from a hardcoded "Mission N of 3" to "Mission N of [total]" to prevent future drift when card count changes.
FLIGHT TIME CALCULATION corrected: only taxi time and prep time (already real, from v2.2) are implemented. The v2.2 changelog's additional claims of a tiered routing factor, class-based climb/descent modeling, and seasonal wind adjustment were never actually specified or built — these are now explicitly marked NOT YET IMPLEMENTED rather than silently assumed active.
New standing rule: body text is always authoritative over version history; a changelog entry describing a change not reflected in the body above it is a bug. New OPEN DISCREPANCIES section added as a running log for anything caught between full reconciliation passes.
Calibration rule added: Block time adj only updates after 3+ logged flights on a specific tail show a consistent 10%+ deviation from estimate, and only as a proposal to Kyle requiring explicit confirmation — never applied silently or fleet-wide.
Variety engine: "time-fit is highest priority" removed as a scored factor (it was double-counting against the existing block-time ceiling gate, which already enforces it). Added board composition rules: anti-clustering (max 2 of 4 cards share aircraft type or region), explicit tie-break order, and a live-event scoring bonus (+25) with a reserved event slot (1-2 of 4 cards) for verified live events — never forced if no genuine event fits.
New REAL-WORLD EVENT VERIFICATION section: fixed-date recurring events (Sun 'n Fun, Oshkosh, ski season, etc.) may be checked directly against the calendar; all other named/variable events require a live web search in the current session before use. Memory of an event from a past conversation or training data is never sufficient on its own. Applies to both the mission-card event badge and the new scoring bonus/reserved slot.
Hangar updated to reflect current fleet positions: N100PE now at KCHS (1 flight from home base, KPBI→KCHS corporate charter), N612JD now at KMEM (2 flights from home base, KSTL→KMEM freight leg, soft-pull toward KTEB now active). N612JD flagged as not yet calibration-eligible pending 3+ logged flights, despite the noticed 15-20% under-estimate pattern.

v2.5 — 05 JUL 2026 — Fleet expanded to 22 aircraft. Added N680MK (Skyward Simulations Cessna Citation Sovereign+) at KLGB, sharing the ramp with N610CD (Citation X). Third Sovereign+ in the fleet alongside N100PE (KPBI) and N612JD (KTEB). Mission generation rule updated to reference all 22 airframes.

v2.6 — 05 JUL 2026 — Fleet expanded to 23 aircraft. Added N471CB (Skyward Simulations Cessna Citation Sovereign+) at KBFI — fourth Sovereign+ in the fleet, first Pacific Northwest mid-jet presence. Chosen over KADS, KAPA, KDTS, KISP, and EGLC to open new regional territory without overlapping an existing base; KBFI is already named as a preferred Class C reliever in the airspace routing rules. EGLC (international home base) considered and set aside for now as a bigger structural question — international ops remain story/range-gated per existing rules rather than a standing base, but the door is intentionally left open for a future international tail if it comes up again. Mission generation rule updated to reference all 23 airframes.

v2.7 — 08 JUL 2026 — Session logging pass. N471CB's KBFI→KBOI flight (07 JUL 2026, 1h22m actual vs 1h37m OFP, ~15% under-estimate) logged to the logbook; hangar entry updated to reflect current location KBOI, 1 flight from home base, soft-pull toward KBFI primed, and the under-estimate pattern flagged for monitoring alongside N612JD. New OPEN DISCREPANCIES item logged: N612JD's hangar Notes claims soft-pull is active at 2 flights from home, which conflicts with the VARIETY ENGINE scoring table (no adjustment until 3+ flights away) — body text governs, hangar language not yet corrected. New standing rule added to SESSION FLOW: at the conclusion of each session, Dispatch outputs a complete updated DISPATCH.md file (incremented version, dated changelog) for Kyle to review and re-attach to the project, rather than only updating silently in-chat.

v2.8 — 08 JUL 2026 — Corrected N612JD hangar Notes language: previously stated soft-pull toward KTEB was "active" at 2 flights from home base, which conflicted with the VARIETY ENGINE scoring table (no adjustment until 3+ flights away). Notes now correctly state no scoring adjustment applies yet and that one more leg away without a return will trigger it. OPEN DISCREPANCIES entry logged in v2.7 for this conflict is now resolved and cleared.

v2.9 — 08 JUL 2026 — REAL-WORLD EVENT VERIFICATION widened. Search scope is no longer destination-only: it now covers the full reachable-metro set for the session (origins and destinations for every candidate tail, bounded by the block-time ceiling) and runs as a candidate-generating seed before scoring, not only as a check on destinations already picked by geography. New timing-tense rule: destination-side events that are upcoming or in-progress support a forward-looking arrival story; origin-side events concluded within the last 2 days support a past-tense departure/wrap-up story with the badge still applying; anything older than 2 days is dropped from badge/bonus eligibility even if verified. Event dates must be checked explicitly against the session date to assign the correct tense — never assumed. RULE 5 (story hook standards) gained an explicit in-world-voice requirement: hooks must never reference the search process, what was checked, or what was ruled out and why — that reasoning stays internal to mission generation, never in the rendered card.

v3.0 — 11 JUL 2026 — Session logging pass on a Sovereign+-only board.

RULE 5 gained a new hook-standard: hook text must never characterize the aircraft's fit for the mission (e.g. "stays in its comfort zone," "earns its keep") — story stays on passengers, stakes, and place, never on the airframe's suitability. Flagged by Kyle after two mission-card hooks drifted into narrating the plane instead of the story.
Noted in-session (not written into rules): board composition rule 1 (anti-clustering) is scoped to the automatic scoring path and does not apply when Kyle explicitly requests a specific type or tail, since all 4 cards are then drawn from that requested pool by design. Added as a clarifying sentence directly in the rule rather than a changelog-only note, per the standing body-text-governs rule.
N612JD's KMEM→KBNA leg flown and logged: 51m actual vs 1h10m OFP estimate, ~27% under — second logged flight with a SimBrief-actual time for this tail, continuing the same under-estimate direction and rough magnitude already flagged. Still short of the 3-flight calibration threshold; one more qualifying flight likely triggers a proposal.
Hangar updated: N612JD now at KBNA, 3 flights from home base (KTEB) — crosses the soft-pull threshold, so destinations toward KTEB now carry the +10 scoring bonus and this tail's cards will show the blue soft-pull border on future boards.
Logbook: added 11 JUL 2026 KMEM→KBNA entry for N612JD.

v3.1 — 11 JUL 2026 — Card rendering lock-in.

RULE 1 gained a new "Canonical card template" subsection: the literal HTML/CSS for a single mission card, with hardcoded hex colors and px values instead of theme variables. Kyle noticed rendered cards had drifted slightly session to session; root cause was that RULE 1 only specified content and structure in prose, leaving the visual shell to be re-derived from the visualizer's live design-token module each time.
Going forward, every board is built by cloning this template per card and substituting mission data into the marked fields — never regenerated from the prose spec alone. Prose spec still governs content rules (hook length, badge wording, etc.); the template governs the visual shell only.
Documented soft-pull border and event-badge variants directly beneath the template (border color swap; second badge span) so both known variants are captured, not just the base card.
SESSION FLOW note added: rules/format changes agreed mid-session can trigger an immediate incremented file output at Kyle's request, rather than always waiting for the session's flight to close out — this file is an example of that.

v3.2 — 11 JUL 2026 — SimBrief handoff improved.

Removed the SimBrief Pilot ID from THE PILOT — it served no function in this document; nothing here ever queried the SimBrief API using it.
SIMBRIEF INTEGRATION rewritten: after Kyle selects a mission, Dispatch now generates a SimBrief Dispatch Redirect URL (dispatch.simbrief.com/options/custom) prefilled with aircraft type, origin, destination, tail, pax, cargo, and departure time, so Kyle lands on a filled-in Dispatch Options form instead of a blank one. Confirmed this link requires no Pilot ID — it only needs Kyle to already be logged into simbrief.com in his browser.
SESSION FLOW steps 6-7 updated to reflect the new link being offered at mission selection, ahead of Kyle filing and pasting back the OFP.

v3.3 — 11 JUL 2026 — SimBrief link on every card, auto-fetch ruled out.

Confirmed the SimBrief OFP auto-fetch endpoint (xml.fetcher.php) is blocked by SimBrief's robots.txt — Claude's fetch tooling will not circumvent a site's stated bot policy, so this is a permanent limitation, not something worth re-testing in future sessions. Kyle continues to paste OFPs into chat for the pre-flight brief.
RULE 1 canonical card template gained a second button: "Open in SimBrief ↗", a real clickable link (not sendPrompt) sitting directly below the existing "Fly this mission ↗" button. It's a working SimBrief Dispatch Redirect link, prefilled per-card at render time — Kyle does not need to select a mission first to get a usable link for any of the 4 cards. This decouples "tell Dispatch I'm flying this" from "open SimBrief to file it," so either can happen first.
SESSION FLOW step 6 updated: the SimBrief link is now live on the board itself rather than generated only after mission selection.

v3.4 — 11 JUL 2026 — Visual and story enhancements.

RULE 1 gained a new terrain banner section: a 320x90 flat SVG banner (mountain, coastal, city skyline, desert, or plains/farmland) now sits atop every mission card, chosen by the destination's actual geography. Skyline is the fallback for dense metro destinations. Illustrative only — not a claim about what the destination literally looks like. Replaced an earlier idea of using real destination photos via image search, which rendered out of order with the board and produced generic, non-specific stock imagery.
RULE 1 Cell 1 (Departure) gained two small icons: a time-of-day icon (sunrise/sun/sunset/moon-stars, derived from departure local hour) and a weather icon (sun/cloud/cloud-rain/bolt/snowflake, from a live current-conditions check at the destination, one fetch per card). This is current weather, not a forecast for the actual flight date — no caption needed on the card, but treated as flavor internally, not a guarantee.
Canonical card template updated with all five terrain banner SVG variants and the icon markup in Cell 1.
RULE 2 fleet table gained a color-coded plane icon per aircraft class (purple BBJ, blue mid jet, teal light jet, green turboprop, coral piston) and now shows ICAO aircraft type next to the tail number (e.g. "N612JD · C680"), with a small legend below the table.
RULE 5 gained recurring-character guidance: named clients, businesses, and booking agents from prior logged hooks may reasonably reappear in later hooks, pulled straight from existing logbook text rather than a new tracking system. Also codified a boundary on real public figures in hooks — never assert a specific real person is aboard a specific fictional flight as fact; keep real-figure references generic enough to read as fiction.
Considered and explicitly tabled for now: a persistent storage-backed fleet dashboard (replacing hangar-block re-parsing each session) and a one-off career-stats chart pulled from the logbook. Neither was built this session — noted here so they don't need to be re-pitched from scratch if revisited later.
Considered and paused: lightweight Part 135 release and invoice documents. Concept liked, but the first visual pass didn't meet the bar — revisit with a stronger design before building into rules.

v3.5 — 11 JUL 2026 — Variety engine gaps closed.

Kyle flagged that departure times had quietly drifted toward a flat early-afternoon default across sessions, with no early mornings or evening/night departures showing up even on legs that would clearly support them. Root cause: RULE 5 governed story-coherence for departure time but nothing governed its distribution — no rotation logic like the ones already protecting region, aircraft type, and destination variety.
New Departure day-part rotation rule added to VARIETY ENGINE: four buckets (early morning, daylight, evening, night) based on departure local hour, actively varied across candidates absent a specific story reason pinning the time, and capped at 2 of 4 cards per board same as the existing anti-clustering dimensions.
Board composition anti-clustering rule (rule 1) expanded to also cover job type badge and departure day-part, alongside the existing aircraft type and region caps — a board of four "Corporate charter" cards, or four same-day-part departures, is now a rule violation rather than an unflagged coincidence.
New reuse caps added to prevent the fixes from going stale themselves: a multi-day verified event is soft-deprioritized from re-badging in back-to-back sessions (unless it's the event's last eligible day), and a recurring character (RULE 5, added v3.4) shouldn't reappear more than once every 3 sessions. Both are soft caps, not hard blocks.

v3.6 — 11 JUL 2026 — Full drift-and-vagueness review pass, requested by Kyle to catch anything else likely to cause inconsistent session-to- session behavior before it becomes a pattern.

Fixed a real inconsistency: RULE 1's terrain banner prose said "blue for mountain/coastal/skyline," but the coastal SVG in the canonical template actually uses teal/green. Prose corrected to match the template.
RULE 1 gained an explicit terrain banner selection rubric (ordered coastal → mountain → desert → plains → skyline-fallback, with example airports per category) — previously "chosen by the destination's actual geography" had no actual mapping anywhere, the same category of gap that caused the departure-time drift Kyle caught last pass.
Session length buckets clarified: boundary values (exactly 2h, 4h, 6h) now explicitly fall into the lower/tighter bucket rather than being ambiguous.
RULE 5's "when a plausible hook exists" — circular wording that could be misread as forcing a real-world reference into every hook — reworded to "when a genuine verified tie-in exists," matching how REAL-WORLD EVENT VERIFICATION actually gates it.
Cross-references added: RULE 5's recurring-character bullet now points to VARIETY ENGINE's reuse cap; RULE 1's event badge spec now points to the event-badge reuse cap. Previously both caps lived only in VARIETY ENGINE with no pointer from the rules that actually use them.
RULE 2 gained a canonical hardcoded table template, matching RULE 1's card treatment — previously RULE 2 still referenced a theme variable (var(--color-background-secondary)) for row hover, the same drift risk the RULE 1 canonical template was built to eliminate.
SESSION FLOW step 3 reworded: restating an aircraft's last position is now explicitly a fallback for when the hangar wasn't updated, not a routine step — the hangar's current-location field is normally authoritative on its own.
Found and fixed real data drift: N612JD's Hobbs field was still an unresolved placeholder despite 2 logged flights with real block times on record — filled in as 2.9 hrs (2h04m + 0h51m), computed directly from the logbook.
Found and flagged (not silently resolved) a second data gap: N100PE's hangar Notes describe a KPBI→KCHS flight that was never added to THE LOGBOOK, leaving its Hobbs/Total flights permanently unresolved. Logged to OPEN DISCREPANCIES rather than guessed at, since the actual block time isn't known and Dispatch never fabricates flight data.

v3.7 — 11 JUL 2026 — N100PE discrepancy resolved.

Kyle confirmed the missing KPBI→KCHS leg: 02 JUL 2026, 1h24m block, corporate charter, 3 pax. Added as a real logbook row.
N100PE hangar updated: Hobbs 1.4, Total flights 1 logged. OPEN DISCREPANCIES entry from v3.6 cleared per the doc's own policy — resolved items are removed, not left to accumulate.

v3.8 — 11 JUL 2026 — Second logbook gap found and closed.

While reviewing N612JD's flight history on the map, found the same category of gap as N100PE: version history (v2.4) referenced a KSTL→KMEM "freight leg" that moved N612JD 2 flights from home base, but no corresponding logbook row existed for it.
Kyle confirmed the leg: 04 JUL 2026, 1h02m block, freight run, 0 pax. Added as a real logbook row between the existing 19 JUN and 11 JUL entries.
N612JD hangar updated: Hobbs 3.95 (sum of all 3 logged actual block times), Total flights 3. This technically clears the flight-count threshold for calibration (3+), but the calibration rule also requires knowing each flight's deviation from its original Dispatch estimate — that estimate was never recorded for the 19 JUN or 04 JUL legs, so only 1 of the 3 flights (11 JUL, ~27% under) has a confirmed deviation. No calibration proposal made; guessing at the missing two would violate the doc's no-fabrication standard. Flagged in the hangar Notes rather than silently treated as calibration-ready.
Places-map tool confirmed to have no great-circle/geodesic routing mode — only driving/walking/transit/bicycling. Route lines are omitted going forward for flight-history maps rather than showing a misleading road-style connector between airports.

v3.9 — 11 JUL 2026 — Calibration rule fixed, data integrity check added.

Found the 19 JUN N612JD KDEN→KSTL leg's original OFP in an earlier session: it ran exactly on estimate (2h04m planned and actual, 0% deviation). Combined with the 04 JUL (~11% under) and 11 JUL (~27% under) legs, this meant 2 of 3 logged flights showed a consistent under-estimate exceeding 10%, but the calibration rule as written required all logged flights to show deviation in the same direction — a single on-estimate flight would have permanently blocked calibration for this tail even with a real pattern on the other two.
Calibration rule reworded: now a majority test (more than half of logged flights) rather than a unanimous one. A flight landing on or near its estimate no longer invalidates a pattern shown by the majority, as long as it doesn't itself deviate in the opposite direction.
N612JD now meets the corrected rule. Hangar updated with a specific proposed correction (~15-20% under Dispatch's estimate) — not applied, per the calibration rule's requirement that Kyle explicitly confirm before any hangar field is edited.
Checked the rest of the fleet against session history for the same category of gap that hit N100PE and N612JD: no other tails have missing logbook rows. N839BA, N737GG, and the rest remain genuinely at 0 Hobbs/0 flights.
New Data integrity check added to THE HANGAR: every time a flight is logged, and during any full document review, Dispatch now cross-checks each hangar entry's "N flight(s) from home base" narrative, Hobbs, Total flights, and current-location field against the actual logbook rows for that tail. Mismatches get logged to OPEN DISCREPANCIES immediately instead of being discovered by accident later, which is how both this session's gaps actually surfaced. SESSION FLOW step 10 updated to reference this check explicitly.

v3.10 — 11 JUL 2026 — Calibration system rebuilt around class × distance, not per-tail.

Kyle's read on the data was right: deviation tracks leg distance and plausibly aircraft class, not the individual tail. Confirmed by pulling actual OFP distances for 4 of 5 logged flights from earlier sessions — the pattern lines up almost exactly on a ~500nm threshold: the one long leg (608nm) matched its estimate exactly, while every leg under ~450nm ran meaningfully under, regardless of which Sovereign+ tail flew it.
Retired the per-tail Block time adj calibration model entirely. Replaced with tracking by [aircraft class] × [distance band] — a correction now applies to every tail of that class on that distance band, not just the specific aircraft that generated the data.
New BLOCK TIME CALIBRATION LOG section added (separate from THE LOGBOOK), logging distance, class, band, planned, actual, and deviation per flight. Populated with all 5 known data points, including one flagged as unconfirmed since its OFP was never pasted.
New rule: only flights with a confirmed distance (from an actual pasted OFP) count toward the 3-flight review trigger for a given class/band cell. Flights logged without an OFP still get recorded for story/Hobbs purposes but don't feed calibration — prevents proposing a correction off a guessed distance.
Overhead Calibration Matrix added, replacing the old flat "Overhead by leg length" table. All cells start at the original default values; each is only adjusted once its own class/band data clears the review trigger. Currently mid jet × 250–500nm is closest (2 of 3 needed flights, both showing 15-18% under) — no cell has triggered yet.
N612JD, N100PE, and N471CB hangar entries updated to point to the shared system instead of carrying tail-specific proposals; the earlier N612JD-specific 15-20% correction proposed in v3.9 is superseded by this system and was never applied.
Fixed an unrelated ordering bug from the v3.8/v3.9 edits: THE LOGBOOK's rows had drifted out of chronological order and one row had been stranded below the new calibration section. Both corrected.

v3.11 — 11 JUL 2026 — Taxi/prep constants corrected; flight record fixed.

Kyle provided real OFF/ON breakdowns (via Volanta) for the 19 JUN KDEN→KSTL and 04 JUL KSTL→KMEM flights. Checking the climb/cruise/ descent formula against actual air time in isolation from taxi showed it's already close (1 and 9 minutes off respectively, no consistent bias) — the real gap was taxi. Dispatch assumed 28 min (20 out + 8 in); actual taxi on these flights was 10 and 16 min. Kyle also confirmed real prep (spawn to taxi) runs ~15 min, not 12.
Taxi time corrected: 20/8 split (28 min total) → 8/7 split (15 min total). Prep corrected: 12 → 15 min.
Found and fixed a real data error while reviewing the OFP: the 19 JUN KDEN→KSTL logbook/calibration entry had been logging the OFP's estimated block time (2h04m) as if it were the reported actual — no real actual had ever been captured for that flight before now. Real actual per Volanta: 1h54m. Corrected in THE LOGBOOK, the BLOCK TIME CALIBRATION LOG, and N612JD's Hobbs total (3.95 → 3.78).
KSTL→KMEM's distance is now confirmed at 305nm (from the OFP Kyle provided) — moved from "unconfirmed, estimated ~239nm" to a fully confirmed medium-long-band data point.
Per Kyle's explicit direction: the block-time/distance formula itself is not being adjusted, and no Overhead Calibration Matrix correction is being applied even though mid jet × 250–500nm technically cleared its review trigger with these updates (3 of 3 flights now confirmed, 15-23% under). That deviation looks substantially explained by the taxi overestimate rather than a genuine distance-band effect, so the cell is being left at default pending fresh data logged against the corrected taxi/prep constants.

v3.12 — 11 JUL 2026 — Air-time data completed for all 5 logged flights.

Kyle provided actual air time for the 3 remaining flights (KMEM→KBNA, KBFI→KBOI, KPBI→KCHS) that previously only had block time. Combined with the two Volanta breakdowns from v3.11, every logged flight now has a real taxi/air-time split.
BLOCK TIME CALIBRATION LOG restructured: replaced the Planned/Actual/ Deviation columns (which conflated taxi error with air-time error) with Block/Air time/Taxi and a dedicated air-time-vs-formula deviation column, isolating the two error sources cleanly.
Result: taxi actuals across all 5 flights range 8-16 min (avg ~11.4), consistent with the v3.11 fix. Air-time deviation from the formula is +10%, -3%, +2%, +14%, -15% — no consistent direction across distance bands or legs. This confirms the working theory from v3.11: the block-time formula has no systematic bias, and nearly all of the deviation chased across v3.9-v3.11 was a taxi-assumption artifact. No formula or matrix changes made — this entry is confirmation, not correction.
Mid jet × Medium (100–250nm) still stands out slightly (-15% air-time deviation on its one data point) — flagged as worth watching with 2 more confirmed flights, not treated as a pattern yet.

v3.13 — 11 JUL 2026 — RULE 3 canonical template lock-in.

RULE 3 (pre-flight brief) gained a canonical hardcoded HTML template, matching the treatment RULE 1's card and RULE 2's fleet table already got. Same rationale: an earlier brief generated this session had used theme variables (var(--surface-2), var(--bg-danger), etc.) instead of the fixed hex palette RULE 1/2 already use — same drift risk that prompted those earlier fixes, caught before it became a repeated pattern rather than after.
Hero section is now boxed in its own white card (
#FFFFFF bg, 0.5px border) rather than sitting directly on the host canvas. The route and tail/type text use hardcoded dark colors, which need a guaranteed-light background to stay readable — sitting unboxed risked poor contrast if the host renders in dark mode.
Metrics grid and weather grid are now pinned to fixed column counts (3×2 and 2×2 respectively) instead of auto-fit, so layout can't reflow session to session.
Documented the SIGMET all-clear variant directly in the template (as a commented alternate block) alongside the main SIGMET-present version, matching how RULE 1 documents its soft-pull and event-badge variants.
All hex values tied to the same 9-color palette already governing RULE 1 and RULE 2, so the brief now reads as part of the same visual system instead of a separately-styled surface.

v3.14 — 11 JUL 2026 — Session-length ceiling made formula-based.

The block-time ceiling table (1h30m / 3h00m / 5h00m hardcoded buckets) was never actually tied to the prep/taxi overhead constants it was supposed to reflect — confirmed by checking it against the corrected v3.11 constants (15 min prep + 15 min taxi = 30 min fixed overhead). The 2h bucket happened to still match by coincidence (2h − 30min = 1h30m), but the 4h and 6h buckets were each 30 minutes more conservative than the real formula, silently cutting legitimate flying time from every longer session.
Replaced the fixed buckets with a direct calculation: block ceiling = stated availability − 30 min, for any session ≤6h. Above 6h the ceiling is still removed entirely (unchanged) — at that scale the fixed overhead is negligible and a hard ceiling adds no value.
This also eliminates the boundary-ambiguity rule added in v3.6 (which stated exactly-2h/4h/6h falls into the lower bucket) — a continuous formula has no discrete boundaries to be ambiguous about, so that clarification is now moot and was removed.

v3.15 — 11 JUL 2026 — New RULE 6: flight release and manifest.

Revisited the Part 135 release concept from earlier in the session (previously paused — the first visual pass didn't meet the bar). Rebuilt as a paper-form-style document (monospace, black hairline grid, no rounded corners) rather than the rounded card aesthetic used elsewhere, deliberately styled to read as real operational paperwork.
Fixed operator identity established: Meridian Air Charter, FAA Certificate No. M3RDNA412J. Dispatcher name is always "Brown, Jacqueline" — this overrides whatever dispatcher name actually appears in the pasted OFP, by design.
Triggers automatically immediately after RULE 3's pre-flight brief, every session, no separate request needed. Weather/NOTAM/SIGMET findings and fuel/W&B figures are pulled directly from what RULE 3 already computed — never re-derived independently, so the two documents can't disagree with each other.
New passenger manifest: randomized name/age/weight/bag per passenger, summing reasonably close to the standing 230 lbs/pax allowance from LOAD PLANNING STANDARDS. For freight runs (0 pax) a cargo manifest variant replaces the passenger table with item/weight rows instead — the release document itself still renders in full either way.
Booking contact can be either a listed passenger or a separate ground-side contact, whichever fits the hook already established by RULE 5 — no invented contact that contradicts the story.
Canonical hardcoded template locked immediately (same session), same drift-proofing rationale as RULE 1/2/3 — this was built and finalized together rather than shipped first and locked down later.

v3.16 — 11 JUL 2026 — Invoice added; FBO and passenger-request detail.

RULE 6 retitled to cover a third document: the invoice, rendering immediately after the release and manifest, same trigger, same session, every time.
New live-lookup requirement: FBO at departure and destination, and current Jet-A price at the departure FBO, both via a live search each session — same standard as REAL-WORLD EVENT VERIFICATION. Never invented, never carried over from a prior session's search.
Invoice line items: dry hourly charter rate by class (fixed table, not tracked or accumulated across sessions), fuel priced by the live-sourced gallon rate, catering (jet classes with pax > 0 only — never piston, turboprop, or freight runs), ramp/handling, crew day rate (block time ≥2h only), and FET at 7.5% scoped correctly to just the charter and fuel lines per 26 USC 4261.
Release gained an optional "Passenger requests / special needs" section — general phrasing only ("Passengers requested...", never "Pax 2 requested..."), omitted on freight runs and whenever nothing fits naturally. Prefer tying it to RULE 5's existing hook/story over an unrelated random detail. Not every flight needs one.
Canonical template updated with FBO fields on the release and the full invoice document, same hardcoded-hex treatment as the rest of RULE 6.

v3.17 — 12 JUL 2026 — Session logging pass (N612JD KBNA→KROA) plus three RULE 6 corrections flagged by Kyle after reviewing the release/manifest.

Flight logged: N612JD, KBNA→KROA, 12 JUL 2026, block 1h13m, air time 1h04m, taxi 9min, distance confirmed 325nm (medium-long band). Added to THE LOGBOOK and the BLOCK TIME CALIBRATION LOG.
Calibration note: air time ran +40% over the formula estimate — the largest single-flight gap logged to date, and notable because the leg flew with a 24kt tailwind, which should have pushed air time under the model, not over it. Most likely explained by SIGMET-avoidance track miles (a convective SIGMET was confirmed crossing the filed route that night) rather than a real distance-band effect. Logged as such rather than silently folded into the trend. Mid jet × 250–500nm now has 4 confirmed flights, 2 of which exceed the 10% deviation threshold (both over-model) — exactly half, not yet a majority, so no calibration proposal.
N612JD hangar updated: Hobbs 3.78 → 5.00, total flights 3 → 4, current location KBNA → KROA, still in the 3-4 flight soft-pull tier (+10) with one more leg away from KTEB needed to cross into the 5+ tier. Data integrity check run and passed — no mismatch found.
RULE 6 correction 1: the flight release's departure/destination cells now include an FBO contact phone number alongside the FBO name — this was missing from the release even though the same live search that finds the FBO name typically surfaces a number too.
RULE 6 correction 2: booking contact moved from the manifest to the release. A dispatcher would reference the release for "who to call," not the manifest, whose job is the passenger/cargo weight record. The manifest's footer is now the weight declaration only, with no duplication between the two documents.
RULE 6 correction 3: added a live-search-with-fallback standard for ramp/handling and landing fees, matching how fuel pricing is already sourced. Unlike Jet-A pricing, these are rarely published in a citable way — most FBOs quote them directly per aircraft rather than posting a schedule — so a miss is expected and not a failure. Search each session; use a real figure if one turns up; otherwise fall back to a clearly-labeled cosmetic estimate rather than presenting a guess as sourced fact, same standard the fuel line already used.
Canonical RULE 6 template updated to reflect all three: {DEP_FBO_TEL} / {DEST_FBO_TEL} fields added to the release, a new booking-contact block added to the release between the fuel/weight grid and passenger requests, and the old booking-contact footer line removed from the manifest template entirely.

v3.18 — 17 JUL 2026 — New operator: Halcyon Air Charter (European/international ops).

Established a second, fully separate operator alongside Meridian — Halcyon Air Charter — to open up European and international flying without mixing fleets, regions, or scoring history with the US company. New HALCYON AIR CHARTER section added, mirroring Meridian's identity/ rules structure rather than bolting international routes onto Meridian.
Fixed identity established: Halcyon Air Charter, UK CAA AOC holder (cosmetic certificate H4LCY0N41C, same stylized-encoding convention as Meridian's), same dispatcher (Brown, Jacqueline) and PIC (Brown, Kyle) as Meridian. Pricing in GBP. Dry hourly rates mirror Meridian's numbers directly (£3,200/hr mid jet, £6,200/hr BBJ class).
New tax line: UK Air Passenger Duty (APD) replaces Meridian's FET on Halcyon invoices. Real current 2026/27 rates confirmed via live search: standard/higher rate x distance band from London (domestic/A/B/C) x pax count, applied only on UK-departing legs. Only VP-CZW (BBJ, >=20 tonnes MTOW) clears the higher-rate threshold today; EC-MLV and M-ARCH use standard rate until the higher-rate threshold drops to 5.7 tonnes on 1 April 2027 - flagged in-doc so that date doesn't sneak up unnoticed. EIKY departures (Ireland) carry no UK APD at all - never guessed at a substitute Irish tax.
New three-tail Halcyon fleet, each tail's home base checked against real runway/approach suitability before being locked in - London City (EGLC) was considered and rejected after research showed its 4,948 ft runway and mandatory 5.5 degree steep approach exclude all three requested airframes (Sovereign+, Citation X, and especially a 737-based BBJ) from real-world certification there. Split across three separate UK/Ireland bizav fields instead, mirroring how Meridian avoids stacking tails on one ramp:
EC-MLV (Sovereign+, Spanish-registered) - EIKY, Kerry, Ireland
M-ARCH (Citation X, Isle of Man-registered) - EGGW, Luton, England
VP-CZW (BBJ, Cayman-registered) - EGSS, Stansted, England
New Halcyon-specific region taxonomy (UK & Ireland, Western Europe, Mediterranean/Iberia, Nordics & Iceland, North Africa, Middle East) - kept fully separate from Meridian's US-shaped region buckets rather than forcing European geography into categories built for Southeast/ Mountain West/etc. Recency penalty, region rotation, and soft-pull scoring are scoped per company: a Halcyon flight never counts against Meridian's history or vice versa.
New airspace tier mapping built for Halcyon's operating theater, same jet-prefers-reliever logic as Meridian's existing table (e.g. LFPB over LFPG, LIRA over LIRF, OMAD over OMAA) - worked out fresh per metro rather than assumed from the US table.
SESSION FLOW step 2 updated: Kyle selects Halcyon by naming the company or one of its tails when stating availability; absent that, Dispatch defaults to Meridian. The two fleets never appear on the same board.
THE LOGBOOK gained a Company column (all prior rows backfilled as Meridian, since they predate Halcyon's existence).
RULE 6 header updated to note it governs both operators - structure, sections, and template shell are identical; only the identity block, currency, and tax line swap per company.
Story character intentionally left open per Kyle's direction: hooks develop naturally, informed by European context and behavior (transatlantic/ continental commuting patterns, European race and ski calendars, art and auction circuits, Gulf business travel) rather than a fixed imposed theme.
No missions were flown this session - the four Meridian mission-board options generated earlier (BBJ/Sovereign, 7hr availability) were not flown. No logbook or hangar changes from that board.

v3.19 — 18 JUL 2026 — Block-time fullness bias added; weather/terrain removed from mission cards; strict-adherence statement added; N612JD KROA→KTEB session logged.

New scoring factor: block-time fullness bias. Agreed with Kyle in a 15 JUL 2026 session ("Planning a 2.5 hour sovereign flight") but never actually written into the body text at the time — confirmed via conversation search this session rather than assumed from memory, per this document's own event-verification standard. The prior Time-fit section claimed no partial credit for using more of the ceiling, which directly contradicted what had been agreed; that language is now replaced. Candidates using more of the stated session window score higher within the block-time gate, applies to all classes, stacks with existing scoring factors, remains a nudge rather than a hard rule.
Mission cards no longer fetch or display live weather. The weather icon is removed from RULE 1's departure cell and the canonical card template. The only weather check Dispatch performs now is at OFP generation (RULE 3) — job-board generation is weather-free.
Terrain banner graphics removed entirely from mission cards — Kyle reported they weren't rendering correctly. The five-variant SVG selection rubric, the canonical SVG markup, and the {TERRAIN_BANNER_SVG} template slot are all removed from RULE 1. Mission card section lettering renumbered A-D accordingly (card header, route band, stats grid, hook section).
New CORE PHILOSOPHY line: strict adherence to every rule in this document, every session, with no drift from inactivity — added at Kyle's request since he works across many chats and the document is the only thing that reliably persists between them.
Flight logged: N612JD, KROA→KTEB, 18 JUL 2026, block 1h19m, air 1h10m, confirmed distance 365nm (mid-jet, medium-long band). Added to THE LOGBOOK and the BLOCK TIME CALIBRATION LOG. Air time ran 13% under the formula estimate despite a similar tailwind to the 12 JUL flight that ran 40% over — the mid-jet × 250-500nm cell now has 5 confirmed flights, 3 of which exceed the 10% deviation threshold but split 2-over/1-under, so still no majority and no calibration proposal.
N612JD hangar updated: Hobbs 5.00 → 6.32, total flights 4 → 5, current location KROA → KTEB (home base, status flips to Home), soft-pull tier reset to 0. Data integrity check run and passed — Hobbs sum, flight count, and current location all reconcile against the logbook.

v3.20 — 19 JUL 2026 — N100PE KCHS→KMSY session logged; two in-session corrections (RULE 5 hook drift, RULE 6 sequencing drift); calibration matrix summary discrepancy found and resolved.

Flight logged: N100PE, KCHS→KMSY, 19 JUL 2026, block 1h46m, air 1h29m, taxi 17min, confirmed distance 551nm (mid-jet, long band). Added to THE LOGBOOK and the BLOCK TIME CALIBRATION LOG. Air time ran 3% over the formula estimate — near exact. Mid jet × Long (>500nm) now has 2 confirmed flights (+10%, +3%), still short of the 3-flight review trigger.
N100PE hangar updated: Hobbs 1.4 → 3.17, total flights 1 → 2, current location KCHS → KMSY, 2 flights from home base (KPBI).
Mid-session correction: a mission-board hook (N471CB, KBOI→KAPA) had narrated the soft-pull mechanic directly in-world ("continues this tail's drift east, still just one flight from its Seattle home ramp"), violating RULE 5's in-world-voice standard. Rewritten to stay on the passenger and place; mechanic-narration is never supposed to surface inside hook text regardless of which mechanic is involved.
Mid-session correction: RULE 6's flight release/manifest/invoice were deferred until after landing instead of rendering immediately after the pre-flight brief in the same turn, as the rule specifies. Corrected mid-session; documents rendered retroactively before the flight closed out.
Open Discrepancies: found and resolved a stale Overhead Calibration Matrix summary that undercounted the mid jet × 250–500nm cell (4 vs. the table's actual 5 confirmed flights, missing the 18 JUL entry). Summary corrected to match the table; conclusion (no majority deviation, no correction proposed) unchanged. See OPEN DISCREPANCIES.

v3.21 — 19 JUL 2026 — Anti-drift mechanisms added at Kyle's request, in direct response to the RULE 5/RULE 6 misses logged in v3.20 and a pattern Kyle flagged across recent sessions.

New RECENT EXECUTION MISSES section added after CORE PHILOSOPHY: a short, dated, self-maintaining log of actual rule violations (not hypothetical ones) to check against before generating cards, briefs, or paperwork. Seeded with the two v3.20 misses. Entries age out at Kyle's discretion once a pattern stops recurring, not automatically.
CORE PHILOSOPHY gained two new principles: "Checklists over intentions" (a statement of intent doesn't prevent drift — where a rule has an attached pre-output checklist, it gets run explicitly, not aspired to) and "Flag uncertainty instead of proceeding silently" (mid-response uncertainty about a step or rule gets surfaced in the moment rather than silently skipped and caught later).
RULE 5 gained an explicit 4-item pre-output checklist, run before rendering any hook — directly targets the mechanic-narration miss (item 1) plus the existing aircraft-personification and event- verification standards.
RULE 6 gained an explicit 4-item pre-output checklist at the trigger itself — item 1 directly targets the same-turn sequencing miss from this session (ending a turn after only the brief renders).
Explicitly not claimed: these checklists make drift less likely and more self-catching, not impossible. No mechanism in this document can guarantee zero drift session to session — that limitation was stated to Kyle directly rather than oversold.

v3.22 — 06 SEP 2026 — N100PE KMSY→KRDU session logged, clean run against the v3.21 anti-drift checklists; a stale running-tally count found and resolved.

Flight logged: N100PE, KMSY→KRDU, 06 SEP 2026, block 2h04m, air time 1h53m, taxi 11min, confirmed distance 717nm (mid-jet, long band). Added to THE LOGBOOK and the BLOCK TIME CALIBRATION LOG. Air time ran 12% over the formula estimate. Mid jet × Long (>500nm) now has 3 confirmed flights (+10%, +3%, +12%) — just crossed the 3-flight review-trigger count; only the newest flight clearly exceeds the 10% threshold, not a majority, so no correction proposed.
N100PE hangar updated: Hobbs 3.17 → 5.23, total flights 2 → 3, current location KMSY → KRDU, now 3 flights from home base (KPBI) — crosses into the 3-4 flight soft-pull tier.
RULE 5 and RULE 6 pre-output checklists both run clean this session: hook stayed on the passengers/place with no mechanic-narration, and the flight release/manifest/invoice rendered immediately after the pre-flight brief in the same turn. No new entries added to RECENT EXECUTION MISSES.
Open Discrepancies: found and resolved a stale BLOCK TIME CALIBRATION LOG running-tally count that undercounted the mid jet × Long (>500nm) cell (1 vs. the table's actual 2 confirmed flights prior to tonight, now 3 with tonight's leg added). Summary corrected to match the table; conclusion (no majority deviation, no correction proposed) unchanged. See OPEN DISCREPANCIES.

v3.23 — 10 SEP 2026 — Performance review pass, requested by Kyle after noticing mission generation taking noticeably longer. No flight logged this session — document-only changes.

Event-search budget added (REAL-WORLD EVENT VERIFICATION, Search scope): the reachable-metro sweep was previously unbounded — for sessions >6h, removing the block-time ceiling had also implicitly removed any limit on how many metros/searches the event pass could cover, up to a worldwide sweep across all 23 tails' reachable range. Capped at ~10 search calls per board generation regardless of session length; within that budget, metros already favored by other scoring factors (new-region, soft-pull direction, aircraft-region affinity) are prioritized over a blind sweep, and combined per-metro queries are preferred over one query per airport. This is the most likely single cause of the slowdown Kyle noticed.
Candidate pool narrows before math runs (VARIETY ENGINE, Mission generation process): previously read "run block time and session time math silently for ALL 23 airframes before rendering" with no exception — meaning naming a specific tail or type (RULE 2) narrowed the rendered board but not the actual computation behind it. Now explicitly narrows the evaluated pool to the named tail/type the moment Kyle states one, before any math runs.
RULE 6 live-lookup retry cap added: FBO/fuel/ramp-handling searches previously had no stated retry limit. Capped at one attempt plus at most one reformulated retry per lookup, then an immediate fallback to the labeled estimate — bounding worst case at ~10 searches instead of open-ended retrying.
Stale calibration summary paragraphs corrected (BLOCK TIME CALIBRATION LOG): the taxi-actuals and air-time-deviation summary paragraphs had drifted stale again (stopped at 7 of 9 logged flights, missing 19 JUL and 06 SEP) — same category of drift as v3.20 and v3.22, caught during this review rather than by accident. See OPEN DISCREPANCIES.
No rule content, scoring logic, or fleet data changed beyond the above — this pass was scoped to performance and the one discrepancy found along the way, not a rules review.

v3.24 — 10 SEP 2026 — Halcyon Air Charter removed at Kyle's request; no international expansion planned for now. No flight logged this session — document-only change.

HALCYON AIR CHARTER section (identity, GBP pricing, UK APD tax logic, region taxonomy, airspace tier mapping) removed in full.
THE HALCYON FLEET section removed in full. All three tails (EC-MLV, M-ARCH, VP-CZW) were still at 0.0 Hobbs / 0 flights with no logged history, so removal is clean — nothing to reconcile in THE LOGBOOK or BLOCK TIME CALIBRATION LOG.
THE LOGBOOK's Company column removed — every existing row was already Meridian, so the column was tracking a distinction that never had a second value. Table and header text reverted to single-operator form.
RULE 6 header's dual-operator/GBP/APD substitution language removed; RULE 6 now documents only Meridian's fixed identity and USD pricing, as it did before v3.18.
VARIETY ENGINE candidate-pool language (added v3.23) simplified back to a flat 23-tail fleet, dropping the Meridian/Halcyon split.
SESSION FLOW step 2's fleet-selection language removed — Dispatch now has only one fleet, so there's nothing to select between.
v3.18 (Halcyon's original addition) and all subsequent Halcyon-related changelog entries are left as historical record per this document's own source-of-truth rule — version history is what happened, not a live rule set. If Halcyon or a similar international operator is revisited later, v3.18-v3.23's entries are the reference for how it was built the first time.

v3.25 — 10 SEP 2026 — v3.23's changelog trimmed at Kyle's request, since Halcyon's full history now lives in its own standalone document (HALCYON.md, forked from this document's v3.24). No flight logged this session — document-only change.

The "candidate pool narrows before math runs" bullet in v3.23 dropped its closing clause about removing the hardcoded "23" for "a Halcyon session (3 tails)." That clause was also stale independent of the Halcyon question — it claimed the pool was "now stated as fleet-dependent," but v3.24 already reverted VARIETY ENGINE's body text to a flat 23-tail description. The bullet now just describes the actual fix (narrowing before math runs), without a claim the current body text no longer matches.
v3.18 and v3.24 left fully intact, at Kyle's explicit direction — those remain the complete record of Halcyon's addition and removal in this document, even though the fuller build detail now also lives in HALCYON.md.

v3.26 — 10 SEP 2026 — Sovereign+-only board generated for a 3h30m session; performance and fullness-bias misses caught by Kyle; no flight logged this session — document-only change.

New RECENT EXECUTION MISSES entry: two non-event-tied cards on this session's board (N471CB→KAPA, N100PE→MYNN) landed well short of the 3h block ceiling with no story/event exception, violating VARIETY ENGINE's fullness-bias default. Caught by Kyle, not self-caught; corrected in-session by swapping to KICT (Wichita, ~2h34m) and MBPV (Providenciales, ~2h32m) respectively.
Kyle separately flagged board-generation time (~10 minutes) as too slow. Root cause was execution overhead this session — reading DISPATCH.md in many small chunks instead of a few larger sweeps, and iterating live on candidate distances (Jackson Hole, then Denver, before landing on Wichita) rather than converging once — not a defect in the v3.23 search-budget/candidate-pool fixes. No rule change proposed; noted here as a process note for future sessions rather than a body-text change, since it's a matter of how Dispatch reads and plans within a session, not what the rules say.
N100PE→MBPV was selected, flown through OFP/pre-flight-brief/ release/manifest/invoice generation (SIGMET 07E noted on the filed route; ramp/handling came back unsourced and was shown as a labeled estimate), but the flight was ultimately cancelled before being flown in MSFS. No hangar, logbook, or calibration log changes — SESSION FLOW step 10 only fires on a reported landing, and none occurred this session.

v3.27 — 11 SEP 2026 — Fleet reduced to turboprops and jets at Kyle's request; review discrepancies logged. No flight logged this session — document-only change.

Removed all piston aircraft and both HondaJets from THE HANGAR: N18VK (Grand Duke), N95BH (Baron 58P), N572J (Aerostar 601P), N825GB (A36TC), N6060E (B36TC), N8298P (Comanche), N542MP and N121HJ (HondaJet Elite). All eight were at 0.0 Hobbs / 0 flights with no logbook or calibration history, so removal is clean.
N80WE (Royal Turbine Duke) retained and reclassified piston_twin → turboprop: it has PT6A turbine engines, and AIRSPACE ROUTING RULES already listed the turbine Duke under TURBOPROPS. Moved to the TURBOPROPS hangar section; ICAO B60T noted.
Fleet is now 15 aircraft: 7 mid jets, 2 BBJs, 6 turboprops.
Citation X hangar entries (N13SY, N517CF, N610CD) now name the add-on developer, FlightFX, per Kyle.
Body text updated to match: piston and light-jet tiers removed from AIRSPACE ROUTING RULES ("LIGHT & MID JETS" → "MID JETS"); calibration classes and Overhead Calibration Matrix reduced to turboprop / mid jet / large jet; piston affinity lines and short-leg floor removed from VARIETY ENGINE; candidate pool 23 → 15 tails; RULE 2 class colors and legend reduced to BBJ / mid jet / turboprop; RULE 6 dry rates and catering scope reduced to turboprop / mid jet / large jet; hangar Type enum reduced to turboprop | mid_jet | large_jet.
OPEN DISCREPANCIES populated with the unresolved findings from the 11 SEP document review (moot piston-twin items dropped). These are logged, not fixed — resolution is scheduled for the v4.0 rebuild.

v4.0 — 11 SEP 2026 — Structural rebuild. The version jumps a major number because the file structure changes: DISPATCH.md splits into four project files (DISPATCH.md, TEMPLATES.md, CHANGELOG.md, dispatch_calc.py). Executed against the approved DISPATCH_v4.0_recommendations sheet, with the deviations noted below, all of which arose from testing rather than from redesign.

File structure

Version history (v1.0–v3.27) moved here. DISPATCH.md no longer carries it.
RULE 2, RULE 3, and RULE 6 canonical templates moved to TEMPLATES.md, read only when that rule triggers. The RULE 1 card template stays in DISPATCH.md because every board needs it.
Historical narrative moved out of the body: the 11 JUL calibration finding, the old ceiling-bucket explanation, the 12 JUL integrity run note, N100PE's cancelled-mission note, and the "this is what fixed the drift" paragraph.

MODEL LIMITS (new section)

Built from ten SimBrief airframe weight screenshots: BOW, MZFW, MTOW, MLW, and max fuel for all nine fleet models, plus a pending Hawker 800.
Citation X baggage 775 lb and BBJ2 cargo 17,645 lb read directly from the SimBrief Max Cargo Weight field; the remaining baggage figures are published-spec or developer-statement derived and are the softest column.
Starship seats corrected 7 → 6. This was the one case where the SimBrief airframe was more restrictive than the recommendations sheet, confirmed independently against 2000A type data.
Citation X retains 9 seats; the payload check caps it at 8 at the full 230 lb allowance, which is how the real aircraft behaves. Verified in testing across every candidate leg.
Royal Turbine Duke has MZFW = MTOW, SimBrief's way of declaring no separate zero-fuel limit. Fuel competes directly against MTOW, so its payload moves leg by leg rather than sitting at a fixed structural maximum.
Reserve derives from one convention rather than nine guesses: jets = plan burn × 1.3h, turboprops × 1.0h, anchored to the sheet's approved Citation X figure of 2,500 lb.

dispatch_calc.py (new)

Reads DISPATCH.md directly for fleet, limits, regions, class register, and logbook; reads OurAirports for geometry. Full 15-tail sweep across ~45,000 airports runs in about 1.3 seconds.
Validated against KMSY→KRDU: 677 nm great circle × 1.07 = 724 nm against the logged OFP's 717, block 2h 06m against an actual 2h 04m.
REGION TABLE gains a Scope column. US state codes and ISO country codes share a two-letter namespace, so without it Colombia resolved to Colorado's region and Canada would have resolved to California's. Cuba was missing from the table entirely and is now in Bahamas & Caribbean.
Scoring ties are common — a never-flown, new-region, in-affinity candidate near the ceiling always reaches the same total — so ties now resolve toward the better-equipped field and the reported set spreads across regions. Without this the board degenerated into "farthest legal airstrip."

AIRSPACE ROUTING RULES

Jets are excluded from fields that are both OurAirports small_airport and under 7,000 ft. Type alone is not a usable proxy: Scottsdale (8,249 ft, N514RS's own home base) and Addison (7,203 ft) are both typed small_airport, while Chicago Executive is medium_airport at 5,001 ft. Type plus runway length separates a bizav field from a farm strip; neither does alone. Nassau and Kissimmee both pass. A tail's home base is always exempt.

Operating model replaces soft pull

The v3.x soft pull applied one weak nudge to all fifteen tails, had no reason in the fiction, and at +10/+25 against a ~60-point baseline could never actually move a board. Removed.
New Ops column on the fleet table: based (out-and-back; strong pull to home or home-bound destinations), regional (no pull inside the home region, pull toward the region once outside it), floating (no pull ever; base is the maintenance facility, crew domicile, and certificate address).
Assignment follows character: Duke and amphibious Caravan based; TBMs, Starship, and cargo Caravan regional; Sovereigns, Citation Xs, and both BBJs floating.
Guaranteed fallback: a tail with no scoring candidates is always offered a ferry leg toward base. Range never strands an aircraft — real ferries use tech stops — but mission availability can. The fallback ignores the amphibian's water-only rule, since the aircraft is amphibious and a ferry leg may use a runway.
The Away counter is retained for hangar tracking only. It no longer drives any scoring.
Maintenance remains narrative only. No inspection mechanic, no grounding, no cost, nothing tracked. A based tail returning home may be framed as going back for scheduled work, and Kyle may declare a squawk mid-flight and direct a return to base at any time.

Event repositioning (new)

Events now pull aircraft. A positioning leg into a verified event market carries the Ferry flight badge, 0 pax, 0 cargo, and the event badge.
Region and fullness penalties are floored at zero for positioning legs. Both rules were firing against the behavior: an event concentrates traffic in one region, which is exactly the region rotation penalizes, and a positioning leg is short and empty so it earns no fullness credit. At +20 an Atlanta positioning leg scored 35 against 60 for an unrelated Iowa run.
Bonus set at +40, market radius at 50 nm. At 100 nm a Teterboro event swallowed Philadelphia and Hartford, which are separate markets; a genuine multi-airport metro is handled by passing each field instead.
Outbound legs carry the event tie with no geographic bonus at all. When the aircraft is sitting in the market, every departure is equally event-tied, so a bonus would discriminate between none of them. The mechanic is temporal, not geographic: the tail is in the market, a window follows the event, and normal scoring picks where the passengers actually live.
Board composition caps positioning legs at one of four cards.

RULE 5 additions

Cuban destinations require the hook to name one of the twelve OFAC authorized categories. Tourism and vacation framings are not permitted — tourist travel is prohibited by statute, while professional research, educational, religious, journalistic, public-performance, and support-for- the-Cuban-people travel are authorized. The return is a deadhead unless the hook establishes an authorized return party.
No internal state ever appears in hook text or on a card: not the away count, ops mode, home-pull status, scores or score components, fullness, airport class, or whether a leg is a positioning ferry or a fallback. The narrative reason for going home is always in-fiction.
The 18 JUL 2026 N612JD hook was rewritten to remove "after four legs away," the only instance of internal state reaching a mission card. The mission itself is unchanged.

Class B register seed (added 12 SEP 2026, post-rebuild)

All 37 US Class B airspace areas seeded into the AIRPORT CLASS REGISTER from FAA Order JO 7400.11, including Andrews, Nellis, Miramar, Dallas Love, and Houston Hobby, which sit inside a primary airport's Class B surface area. Kyle raised that KORD and KATL were appearing in candidate lists.
Root cause: the Class B restriction in AIRSPACE ROUTING RULES had never been enforceable. An unverified US large_airport carries the proxy class BC and passes the filter on its C branch, so hubs ranked alongside genuine Class C fields. The reliever preference ("KPWK over KORD, KPDK over KATL") existed only as prose examples that nothing implemented.
Seeding the register makes the existing exclusion logic work as written and turns the reliever preference into default behaviour. No new rule or scoring change was needed — the rule was already there, it just lacked the data.
Reclassification consequence: KMSY, KMEM, KSTL, and KDEN are Class B, not Class C as the pre-v4.0 document assumed. Five of the nine logged flights touched a Class B field. History is left as flown and the finding is logged to OPEN DISCREPANCIES.

Close-out before shakedown (12 SEP 2026)

OPEN DISCREPANCIES cleared to none, and split from a new PROVISIONAL VALUES section. The two had been conflated: drift means two parts of the system contradicting each other and must be fixed; a derived-but-unmeasured number is neither wrong nor fixable by editing, and resolves through calibration. Mixing them meant the drift list could never reach zero, which defeats its purpose as a pre-session check.
RULE 1's blue "soft-pull active" card border removed. The mechanic no longer existed after the Ops rewrite, and the border was internal state on a card — RULE 5 forbids that in visual form as much as in text. Found by sweeping for stale references rather than by it failing.
RULE 1 template's soft-pull border variant and the event-search priority list updated for the same reason.
Away corrected from "vestigial" to its actual three uses: the data integrity check, the RULE 2 fleet-table badge, and the board-composition tie-break. RULE 4 wording tightened to permit it in the fleet table (an operations view Kyle asks for) while forbidding it on mission cards.
RULE 6 invoice: planned-block billing with no post-flight true-up is now stated as deliberate convention rather than left as an open question.
Final verification pass found the Cell 6 rename half-applied: the prose reference had been changed to "Route dist" but the RULE 1 card cell, the RULE 3 six-cell list, and the RULE 3 template in TEMPLATES.md still rendered "Air dist" with an {AIR_DIST} placeholder. All four renamed to Route dist / {ROUTE_DIST}, and the definition pinned in RULE 3 so the label cannot drift back: route distance is the OFP ground distance, never SimBrief's wind-adjusted "air distance" field — the same value the calibration log records.

v4.1 — 12 SEP 2026 — Two discrepancies logged from the v4.0 shakedown board (3h, Citation X, no flight flown). No behaviour changed.

Board size: RULE 1's flat "4 cards per board" and board composition's one-card-per-tail cap disagree whenever Kyle names a model or class with fewer than four tails. The Citation X fleet is three tails, so the board rendered three. Board composition's short-board escape covers a shortage of legal candidates, not a shortage of tails.
Class E veto: a non-towered field passes the tier gate on its unverified CD proxy, then fails permanently once AIRPORT CLASS REGISTER verification records E. Telluride and Montrose are the live cases; the Blues & Brews tie-in was dropped for it. Logged rather than fixed in the moment — the fix changes AIRSPACE ROUTING RULES and tier_ok together and needs Kyle's threshold.

v4.2 — 12 SEP 2026 — Class E opened to every class; field performance ruled permanently out of scope.

AIRSPACE ROUTING RULES gains a Class E clause. Class is a proxy for "real bizav environment"; a towered field's class answers that, a non-towered field's does not. Telluride, Montrose, Rifle and Lake Tahoe are Class E jet destinations; a grass strip is Class E for the opposite reason. The gate is the jets-and-small-fields test plus the tail's Min rwy.
TIER_ALLOWED in dispatch_calc.py gains "E" for turboprop, mid_jet and large_jet. No extra test was needed in tier_ok: the min_rwy check and the jets-and-small-fields gate both already run ahead of it in the candidate loop, so the filtering was in place and only the tier set was wrong. The --allow-small-fields override and the home-base exemption keep working unchanged.
Field performance is now stated as permanently out of scope. Elevation, temperature, gradient and density altitude change what an aircraft can lift out of a field, not whether the field is legal. A density-altitude surcharge on Min rwy was proposed in-session and rejected: Min rwy is already an MTOW-sea-level figure, so surcharging it double-counts one assumption while ignoring the lever real operators actually use, which is weight. SimBrief and the sim own this. Kyle owns field-specific procedure; no per-airport procedures table will be added.
AIRPORT CLASS REGISTER: CYVR verified C, KEDC verified D, both from the 12 SEP board.
The board-size discrepancy from v4.1 stays open.

v4.3 — 12 SEP 2026 — Field quality gate replaces the type-plus-length test; water-lane bug fixed; board size resolved.

AIRSPACE ROUTING RULES: a destination must be paved with a land runway at least 75 ft wide. Length is Min rwy's job alone. Researched against the full OurAirports set: the old test blocked ~980 real bizav airports — John C Tune, McKinney National, Denton, Livermore, Hayward, Leesburg Executive, Witham Field, Jack Edwards, Houma Terrebonne, Gaylord — because OurAirports types them small_airport, while admitting Petan Ranch (7,500 ft gravel), Melby Ranch (7,400 x 40 turf) and Bell Ranch (8,200 ft dirt) for being long. 100 ft was tested first as the FAA Design Group II width and rejected: Monmouth Executive, Taos, McCall and Salida are narrower and all take bizjets. Citation X pool from KPWK went 680 -> 1487.
The gate applies to turboprops too — Kyle's call. It costs them ~57% of fields worldwide at a 2,500 ft floor and two thirds of Alaska. N828DC's revenue missions are unaffected (water branch), and the fallback ferry stays on Min rwy alone so no tail can be stranded. Caravan pool from KNEW went 827 -> 360, accepted knowingly.
load_airports now excludes water surfaces from the land runway maximum. 43 US fields were inflated by a seaplane lane and 24 cleared the C750 floor on water alone: Sky Harbor Duluth reported 10,000 ft against 2,602, St Augustine 12,000 against 8,001, Shawano 12,000 against 3,901. The runway lighted column was evaluated as a third signal and rejected as unreliable — KABQ, PHNL and one KCLT runway all report unlit.
RULE 1 no longer states a card count; board composition owns it and fills short boards from the tails with the best unused candidates, requiring a second card to differ in region and job type.
OPEN DISCREPANCIES is empty again.

v4.4 — 12 SEP 2026 — Fullness scoring interpolated instead of banded.

VARIETY ENGINE's fullness component moves from four step bands to linear interpolation between anchors at 50%/-25, 60%/-10, 78%/+10, 100%/+20, flat below 50%. Same construction as the Overhead Calibration Matrix. The band values are preserved as anchors; the steps between them are gone, and scores now carry one decimal.
Reason: the v4.3 field-quality gate roughly doubled the mid-jet candidate pool, and under step bands everything at or above 85% fullness scored an identical +20. Measured on N517CF from KPWK: the top 40 candidates held 1 distinct score before and 22 after, across 514 distinct scores in a 1,487-candidate pool. The event search prioritises metros already favoured by scoring, which it could not do when several hundred candidates tied.
TYPE_RANK still breaks genuine ties but now fires rarely, so the reported set no longer drifts toward large_airport. Telluride surfaces in the default N517CF report for the first time; it was previously pushed out by the per-region cap while tied.
Consequence accepted: the reported pool leans toward whatever sits nearest the ceiling radius, so small paved western fields (Dubois, Moriarty, Rangely) now appear alongside Grand Junction and Santa Fe. MAX_PER_REGION_REPORTED keeps the spread honest.

v4.5 — 12 SEP 2026 — Fleet restructure. 15 tails to 14; jet bases redistributed from a coastal cluster to national coverage.

Retired N100PE (Sovereign+, KPBI), N471CB (Sovereign+, KBFI) and N517CF (Citation X, KPWK). A Retired tails table under THE FLEET records their last known state. Their LOGBOOK and BLOCK TIME CALIBRATION LOG rows stay: history is never edited, recency and region rotation read the logbook by route rather than by tail, and the calibration rows remain valid mid_jet data. The data integrity check is now scoped to active tails so a logbook tail with no fleet row is not read as drift.
Added the Hawker 800 as N24SM (KPWK, floating) and N707BM (KJAC, regional). MODEL LIMITS already carried the confirmed row. Plan speed 415 KTAS is derived, not measured — 447 book high cruise x the fleet's ~93% ratio — and sits in PROVISIONAL VALUES pending 3 confirmed flights. Min rwy 5,000 tracks the published 5,032 ft sea-level takeoff figure.
N680MK moved KLGB -> KBFI. Three of six remaining jets sat within 110 nm of each other in Southern California while the Pacific Northwest had none; the move fixes both at no cost, and KBFI was already verified Class D.
N839BA at KPSP switched floating -> based. A BBJ at Palm Springs is an owner's aircraft, not one on the charter market.
Jet bases are now KBFI, KPWK, KJAC, KTEB, KPBI, KOPF, KLGB, KPSP. Ops mix across the jets is six floating, one regional, one based.
Correction recorded: the v4.4 session claimed KPWK's 5,001 ft runway was "right at the type minimum" and treated that as a reason to avoid basing a Hawker there. Min rwy is a flat pass/fail with no opinion about margin, the 5,032 ft figure is a full-fuel MTOW number, and KPWK is one of the busiest business aviation fields in the country. Same error as the density-altitude surcharge: importing real-world performance into a model that AIRSPACE ROUTING RULES says does not model performance. The N517CF tail note carrying that claim is gone with the tail.

v4.6 — 17 SEP 2026 — Aircraft storage, and two mid jets added.

THE FLEET gains a Status column, active or stored. Kyle has gone cold on the Sovereign+ add-on but did not want the tails gone, and there was no mechanism for that: every fleet row generated candidates, and board composition's one-card-per-tail rule meant a tail he was not flying would actively displace one he was. Retired was the only exit and it is framed as permanent. Stored keeps the tail fully tracked — ops mode, home base, tail note, Current, Hobbs, Flts, and the data integrity check all still apply — while removing it from the candidate pool. Returning it to service is a one-word edit. dispatch_calc.py filters stored tails out of the pool by default and --include-stored puts them back; RULE 2 renders them with a gray "Stored" badge rather than hiding them, since Kyle still owns them.
The data integrity check previously read "each active tail," which meant non-retired. With active now a column value that wording was ambiguous, so it is restated explicitly: the check covers active and stored alike, because a stored tail keeps live state. Retired tails remain out of scope.
N612JD and N680MK set to stored. N612JD keeps its five logged flights and the recurring clients in its hooks, which RULE 5 can still call back since it reads hook text rather than tail assignment. N680MK never flew a leg from KBFI, so the Pacific Northwest slot is held open rather than lost.
Added N728QL (Citation X, KTEB, floating). Restores the Northeast corridor, which was down to N417KG, a TBM at KHPN, in the densest bizav market in the country. The airframe choice follows from fuel: usable fuel less reserve gives the C750 roughly 2,330 nm of leg against the Hawker's 1,915 nm, so a corner base is workable for the X and confining for the Hawker. Completes a three-corner C750 spread with KPBI and KLGB.
Added N988RS (Hawker 800, KADS Addison, floating). Gulf / South Central was one Caravan and Mid-South had no tail at all — the largest uncovered area in the fleet. Center-of-country is where the Hawker's shorter legs stop being a constraint, and KADS is already the named DFW reliever in AIRSPACE ROUTING RULES. KBFI stays dark as the next open slot; Pacific remains two SoCal tails, accepted deliberately in exchange for opening Texas.
Fleet is now 16 tails: 14 active, 2 stored, 3 retired. Mid jets are three C750 and three H25B, all active.
Calibration consequence, recorded not corrected: all nine BLOCK TIME CALIBRATION LOG rows are Sovereign+ at 425 KTAS, and both Sovereign+ tails are now stored. Every active mid jet plans on a derived speed, and the Hawker's 415 KTAS is derived from a 0.93 ratio that was itself measured on the Sovereign+. The rows stay valid mid_jet data for the overhead matrix. Three confirmed flights each on the C750 and the H25B clear both PROVISIONAL VALUES entries; worth flying deliberately rather than waiting.
KADS is not in the AIRPORT CLASS REGISTER. Home base is exempt from tier filtering so nothing is blocked; it gets verified the first time it appears as a destination.

v4.7 — 18 SEP 2026 — First Hawker flight logged; calibration pool contradiction surfaced.

Logged N24SM KBEC -> KPWK, 18 SEP 2026, 1h 34m block / 87 min air, Ferry flight, 0 pax. A factory delivery: the aircraft was collected at Beech Factory, Wichita, where the 800XP line was built, and flown to its Wheeling home base to enter service. Fleet row updated to Hobbs 1.57, Flts 1; Current stays KPWK and Away stays 0, since the leg terminated at home. Data integrity check passes.
Calibration row: 529 nm OFP ground distance, model_air_min 86.4, actual 87, deviation +0.7%. Tally regenerated from the table: 10 mid_jet flights, mean bias +0.7%, mean absolute error 6.0% (down from 6.6%), 1 flight beyond +/-10%. No review trigger met. The 600 nm band now holds four flights, all positive, mean +2.1% — inside the +/-8% trigger (b) would need.
First calibration row on an airframe other than the Sovereign+. The Hawker's derived 415 KTAS produced a +0.7% deviation on its first measured leg, with an avg wind component of P006 — a 6 kt tailwind over 522 nm, small enough that the number is not wind-flattered.
OPEN DISCREPANCIES gains its first open item since v4.3: the review trigger evaluates per class x band, while PROVISIONAL VALUES resolves plan speeds on "3 confirmed C750 flights" and "3 confirmed Hawker flights" — per model. The two disagreed silently while every logged flight was a Sovereign+ and class and model were the same population. With three mid_jet models planning at 425, 490 and 415 KTAS, they no longer are. Logged rather than fixed, per CORE PHILOSOPHY; the proposed fix (a Model column and a per-model plan-speed trigger, overhead left on class) is recorded with it and awaits Kyle.
AIRPORT CLASS REGISTER gains KBEC (Class D, verified 18 SEP 2026 against the FAA final rule establishing Class D and E airspace at Wichita, effective 2019). The register's entry rule is widened in the same edit: an airport earns an entry when it first makes a final board OR when it first appears in THE LOGBOOK by another route. The "only when it makes a board" clause exists to stop speculative lookups on candidates that never fly, not to discard a verification already earned on a field Kyle has actually flown. Stated here rather than applied silently.
Not done, raised instead: RULE 3 and RULE 6 did not fire on this OFP. Their trigger is "any time Kyle pastes an OFP," but the flight was already flown and the actuals arrived in the same message, and both documents are pre-flight artifacts — the invoice explicitly bills planned block with no post-flight true-up. Rendering a pre-flight brief for a completed leg would be mechanical compliance against obvious intent. A trigger clarification is proposed, not applied.

v4.8 — 18 SEP 2026 — Fourth Hawker and fourth Citation X; every region now has a tail.

Added N312FU (Hawker 800, KBHM Birmingham, floating). Fills Mid-South, which was the last region in the REGION TABLE with no tail of any kind. AIRSPACE ROUTING RULES already names KBHM among its Class C regional hubs, so no new register lookup was needed; the field's 12,007 ft runway puts no constraint on the type. Center-of-country placement keeps both coasts inside the Hawker's envelope — KTEB 747 nm, KLGB 1,563 nm.
Added N444BC (Citation X, KBFI Boeing Field, floating). Takes the Pacific Northwest slot that has been held open since N680MK went to storage at v4.6. The airframe choice is the corner/center rule applied in mirror: KBFI to KTEB is 2,080 nm, inside the C750's envelope and past the Hawker's ~1,915 nm, so the northwest corner takes the longer-legged type. Florida remains beyond one leg even for the C750 (KPBI 2,336 nm) — a real limit of the base, recorded rather than worked around. KBFI already sits in the AIRPORT CLASS REGISTER as Class D.
Both tails set to floating, matching every other mid jet except N707BM. Kyle did not specify an ops mode; floating is the fleet default for this class and neither base has a reason to pull.
KBFI now carries two tails — active N444BC and stored N680MK. Precedent exists at KJAC (N707BM and N247LB) and KTEB (N728QL and the stored N612JD), and a stored tail generates no candidates, so the shared ramp has no mechanical effect.
Fleet is now 18 tails: 16 active, 2 stored, 3 retired. Mid jets are four Citation X and four Hawker 800. The intent behind the pair is board shape — board composition places one card per tail before any tail gets a second, so a model-filtered board now fills all four slots with four distinct tails instead of doubling one up.
Consequence noted, not acted on: mid jets are now eight of sixteen active tails. Board composition caps 2 of 4 cards per model, not per class, so a full-fleet board can still render two Hawkers and two Citation Xs and shut out both BBJs and all six turboprops. This was already possible at six mid jets; eight makes it likelier. A per-class cap alongside the per-model one would close it, and is not applied.

v5.0 — 18 SEP 2026 — Structural split: state leaves DISPATCH.md, the script leaves the project. Board generation had reached ~12 minutes, and ~80% of that was Dispatch retyping files that already existed.

Root cause

SESSION FLOW step 11 read "copy /mnt/project files to /home/claude." That mount does not exist in the current environment — verified 18 SEP 2026 by listing /mnt. Project docs now reach Dispatch only through the project tool, into context rather than onto disk. Because dispatch_calc.py takes a file path, the only bridge from context to disk was Dispatch retyping the file by hand, every session.
Measured on the 18 SEP Hawker board: 135,508 bytes retyped per session (DISPATCH.md 92,102 + dispatch_calc.py 43,406), about 36,600 generated tokens, roughly 80% of everything produced that session. The candidate math, the event search and the OurAirports download together were under two minutes. The bottleneck was never the math — v4.0 solved that — it was the I/O the fix introduced.
Second finding: the script parsed 7,870 bytes of DISPATCH.md — THE FLEET, MODEL LIMITS, REGION TABLE, AIRPORT CLASS REGISTER, THE LOGBOOK — and ignored the other 91%. Even a perfect transfer mechanism would have been moving twelve times more data than the math needed.

The split

New dispatch_state.md (11,594 bytes) holds everything a flight changes: THE FLEET, retired tails, MODEL LIMITS, REGION TABLE, the affinity lists, AIRPORT CLASS REGISTER, THE LOGBOOK, and the BLOCK TIME CALIBRATION LOG with its running tally. dispatch_calc.py reads it by default; --doc points elsewhere. Stored in the project at claude/dispatch_state.md, written to disk under its bare name.
DISPATCH.md keeps the rules and the prose explaining them, including the tail notes, which are story material for RULE 5 rather than state. It is no longer a script input and never goes to disk. 92,102 -> 86,331 bytes.
New CORE PHILOSOPHY principle, "Rules here, state there": on a rule, DISPATCH.md governs; on a fact — where a tail is, what it has flown, what class a field is — dispatch_state.md governs, and any disagreement is logged to OPEN DISCREPANCIES.
dispatch_calc.py is hosted at github.com/sirkyle99x/Meridian-Air-Dispatch and fetched by curl at session start rather than retyped. Verified reachable: raw.githubusercontent.com returns 200 from the session container. gist.githubusercontent.com is blocked by the proxy allowlist, so a repository is required rather than a gist. api.github.com is reachable but write access is not attached, so pushes are unavailable — which is why state stayed in the project, where the project tool can write it, and only the read-only script moved out.
CHANGELOG.md moved to the same repository for the same reason: it is append-only history read on review passes, and the project tool has no append, only full rewrite, so keeping it there cost a full retype per entry.

Per-session cost

Transcription drops from 135,508 bytes to 11,594 — roughly 36,600 generated tokens to 3,100, a 91% reduction. The script and both CSVs now arrive in one setup call in about two seconds.

Other fixes in the same pass

AIRPORT CLASS REGISTER sorted by ICAO. It had been grouped by class with no stated rule, so inserting a row was a judgement call; two rows went into the wrong group on the 18 SEP board and had to be reverted and redone.
SESSION FLOW step 5 now specifies one --json run, read from the JSON. The 18 SEP board ran the script three times, each re-parsing ~134,000 CSV rows for output already in hand.
SESSION FLOW step 6 now specifies a single search round: pick the three or four most story-viable metros off the candidate table, issue the searches and any follow-up fetches together, and drop a thread the moment its first result fails to confirm. The 18 SEP board ran three sequential rounds, including one dead end that produced nothing usable.
SESSION FLOW step 12 now pushes from disk with the project tool's local_path option, which uploads without the file passing through context, and states that CHANGELOG.md earns an entry for a rule or structure change, not for a routine flight — a flight is already recorded in THE LOGBOOK and the calibration log.

Verification

The split was run against the 18 SEP Hawker board before anything was published: 48 candidates, identical set, zero differences in great-circle distance, route distance, block time, session time, fullness, max pax, fuel plan, available payload, or score. KTEX, CYWG and MYGF now carry verified register classes (E, C, C) instead of proxies. Full run 4.5 seconds.
No flight was flown this session. No LOGBOOK, fleet, or calibration changes beyond the three register verifications earned by the 18 SEP board.
