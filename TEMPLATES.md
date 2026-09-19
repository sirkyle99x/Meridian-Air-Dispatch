# TEMPLATES.md

Canonical render templates for RULE 2 (fleet table), RULE 3 (pre-flight brief),
and RULE 6 (release, manifest, invoice).

**Read this file only when one of those rules triggers.** The RULE 1 mission-card
template is not here — it stays in DISPATCH.md, because every board needs it.

**Why these are hardcoded.** Stated once, here, rather than repeated above every
template: hex and px values are locked so each document renders identically every
session, instead of being re-derived from the visualizer's live design-token
module each time. The templates fix the visual shell only. Every content rule in
DISPATCH.md — what to surface, what to discard, plain-English translation, which
blocks are omitted — still applies and is not restated here.

Companion files: DISPATCH.md (philosophy, rules, scoring) · dispatch_state.md
(fleet, logbook, register) · changelog.md (version history, on GitHub) ·
dispatch_calc.py (candidate math, on GitHub).

**Reconstructed 18 SEP 2026.** This file was deleted from the project and rebuilt
from the 11–12 JUL 2026 build session, where each template was originally
authored, with the v3.17, v3.27, v4.0 and v4.6 amendments applied. The RULE 6
markup and the RULE 3 required-variants text are verbatim from that session. The
RULE 2 table body was rebuilt from its prose spec plus the verbatim header,
badge, and legend markup; it matches the spec in every colour and size value but
may differ from the original in trivial arrangement. See OPEN DISCREPANCIES.

-----

## RULE 2 — Fleet table template

**Canonical table template (locked 11 JUL 2026):**

Same rationale as RULE 1's canonical card template — hardcoded hex/px values
so the table renders identically every session rather than being re-derived
from the visualizer's live design-token module each time. One `{ROW}` block
below is cloned per aircraft in the filtered set.

```html
<div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;font-family:sans-serif;overflow:hidden">
  <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 16px">
    <div style="font-size:16px;font-weight:500;color:#2C2C2A">Fleet status</div>
    <div style="font-size:12px;color:#888780">{COUNT} aircraft · {DATE}</div>
  </div>

  <table style="width:100%;border-collapse:collapse">
    <tr>
      <td style="font-size:11px;text-transform:uppercase;color:#888780;padding:6px 16px;border-bottom:0.5px solid #D3D1C7">Tail</td>
      <td style="font-size:11px;text-transform:uppercase;color:#888780;padding:6px 16px;border-bottom:0.5px solid #D3D1C7">Aircraft</td>
      <td style="font-size:11px;text-transform:uppercase;color:#888780;padding:6px 16px;border-bottom:0.5px solid #D3D1C7">Home base</td>
      <td style="font-size:11px;text-transform:uppercase;color:#888780;padding:6px 16px;border-bottom:0.5px solid #D3D1C7">Current location</td>
      <td style="font-size:11px;text-transform:uppercase;color:#888780;padding:6px 16px;border-bottom:0.5px solid #D3D1C7">Status</td>
    </tr>

    <!-- {ROW} — cloned once per aircraft; the last row omits border-bottom -->
    <tr>
      <td style="padding:10px 16px;border-bottom:0.5px solid #D3D1C7">
        <div style="display:flex;align-items:center;gap:6px">
          <i class="ti ti-plane" style="font-size:16px;color:{CLASS_COLOR}" aria-hidden="true"></i>
          <span style="font-family:monospace;font-weight:500;font-size:14px;color:#2C2C2A">{TAIL}</span>
          <span style="font-size:12px;color:#888780">· {ICAO_TYPE}</span>
        </div>
      </td>
      <td style="padding:10px 16px;border-bottom:0.5px solid #D3D1C7;font-size:13px;color:#5F5E5A">{AIRCRAFT_NAME}</td>
      <td style="padding:10px 16px;border-bottom:0.5px solid #D3D1C7;font-size:13px;color:#2C2C2A">{HOME_ICAO} · {HOME_CITY}</td>
      <td style="padding:10px 16px;border-bottom:0.5px solid #D3D1C7;font-size:13px;color:#2C2C2A">{CURRENT_ICAO} · {CURRENT_CITY}</td>
      <td style="padding:10px 16px;border-bottom:0.5px solid #D3D1C7">{STATUS_BADGE}</td>
    </tr>
  </table>

  <div style="padding:14px 16px;display:flex;gap:14px;font-size:11px;color:#888780">
    <div style="display:flex;align-items:center;gap:4px"><i class="ti ti-plane" style="font-size:14px;color:#534AB7" aria-hidden="true"></i>BBJ</div>
    <div style="display:flex;align-items:center;gap:4px"><i class="ti ti-plane" style="font-size:14px;color:#185FA5" aria-hidden="true"></i>Mid jet</div>
    <div style="display:flex;align-items:center;gap:4px"><i class="ti ti-plane" style="font-size:14px;color:#3B6D11" aria-hidden="true"></i>Turboprop</div>
  </div>
</div>
```

`{CLASS_COLOR}` per aircraft class: `#534AB7` (BBJ/large_jet), `#185FA5`
(mid_jet), `#3B6D11` (turboprop).

`{STATUS_BADGE}` is exactly one of the three below — never two, never any other
text in the cell:

```html
<!-- At home -->
<span style="background:#EAF3DE;color:#27500A;font-size:11px;padding:2px 8px;border-radius:8px;display:inline-flex;align-items:center;gap:5px"><span style="width:6px;height:6px;border-radius:50%;background:#27500A"></span>Home</span>

<!-- Away -->
<span style="background:#FAEEDA;color:#633806;font-size:11px;padding:2px 8px;border-radius:8px;display:inline-flex;align-items:center;gap:5px"><span style="width:6px;height:6px;border-radius:50%;background:#633806"></span>Away · {N} flight(s)</span>

<!-- Stored (THE FLEET Status = stored) — replaces the Home/Away badge entirely -->
<span style="background:#F1EFE8;color:#5F5E5A;font-size:11px;padding:2px 8px;border-radius:8px;display:inline-flex;align-items:center;gap:5px"><span style="width:6px;height:6px;border-radius:50%;background:#5F5E5A"></span>Stored</span>
```

-----

## RULE 3 — Pre-flight brief template

**Canonical brief template (locked 11 JUL 2026):** the hero is boxed in its own
white card because the route and tail/type text are hardcoded dark colours and
need a guaranteed-light background — rendered directly on the host canvas they
risk poor contrast in dark mode. The metrics grid is pinned to 3×2 and the
weather grid to 2×2 rather than auto-fit, so neither reflows session to session.

```html
<div style="font-family:sans-serif">
  <div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem">
    <div style="font-size:11px;text-transform:uppercase;color:#888780;margin-bottom:8px">Pre-flight brief · {DATE}</div>
    <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:4px">
      <span style="font-size:28px;font-weight:500;color:#2C2C2A">{DEP_ICAO}</span>
      <i class="ti ti-arrow-right" style="font-size:20px;color:#888780" aria-hidden="true"></i>
      <span style="font-size:28px;font-weight:500;color:#2C2C2A">{DEST_ICAO}</span>
    </div>
    <div style="font-size:12px;color:#5F5E5A">{TAIL} · {AIRCRAFT_NAME} · {FILED_ROUTE} · {ALTITUDE}</div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:1.5rem">
    <div style="background:#F1EFE8;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Block time</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A">{BLOCK_TIME}</div>
    </div>
    <div style="background:#F1EFE8;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Out–in (Z)</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A">{OUT_Z}–{IN_Z}</div>
    </div>
    <div style="background:#F1EFE8;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Route dist</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A">{ROUTE_DIST} nm</div>
    </div>
    <div style="background:#EAF3DE;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#27500A">Wind comp</div>
      <div style="font-size:14px;font-weight:500;color:#27500A">{WIND_COMP}</div>
    </div>
    <div style="background:#F1EFE8;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Block fuel</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A">{BLOCK_FUEL} lbs</div>
    </div>
    <div style="background:#F1EFE8;border-radius:8px;padding:8px">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">TOW vs max</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A">{TOW} / {MAX_TOW}</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:1.5rem">
    <div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;padding:1rem">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Departure · {DEP_ICAO}</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A;margin:4px 0">{DEP_SUMMARY}</div>
      <div style="font-size:12px;color:#5F5E5A;line-height:1.7">{DEP_DETAIL}</div>
    </div>
    <div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;padding:1rem">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Destination · {DEST_ICAO}</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A;margin:4px 0">{DEST_SUMMARY}</div>
      <div style="font-size:12px;color:#5F5E5A;line-height:1.7">{DEST_DETAIL}</div>
    </div>
    <div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;padding:1rem">
      <div style="font-size:11px;text-transform:uppercase;color:#888780">Alternate · {ALTN_ICAO}</div>
      <div style="font-size:14px;font-weight:500;color:#2C2C2A;margin:4px 0">{ALTN_SUMMARY}</div>
      <div style="font-size:12px;color:#5F5E5A;line-height:1.7">{ALTN_DETAIL}</div>
    </div>
    <div style="background:#EAF3DE;border-radius:12px;padding:1rem">
      <div style="font-size:11px;text-transform:uppercase;color:#27500A">En route winds</div>
      <div style="font-size:14px;font-weight:500;color:#27500A;margin:4px 0">{ENROUTE_WIND}</div>
      <div style="font-size:12px;color:#27500A;line-height:1.7">{ENROUTE_DETAIL}</div>
    </div>
  </div>

  <div style="background:#FCEBEB;border:0.5px solid #E24B4A;border-radius:12px;padding:1rem;margin-bottom:1.5rem">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <i class="ti ti-alert-triangle" style="color:#791F1F;font-size:18px" aria-hidden="true"></i>
      <span style="font-size:14px;font-weight:500;color:#791F1F">Sigmet on route</span>
    </div>
    <div style="border-left:2px solid #E24B4A;padding-left:10px">
      <div style="font-size:13px;font-weight:500;color:#791F1F">{FIR_NAME} · {SIGMET_ID}</div>
      <div style="font-size:12px;color:#791F1F;line-height:1.7">{SIGMET_DETAIL}</div>
    </div>
  </div>

  <div style="background:#FFFFFF;border:0.5px solid #D3D1C7;border-radius:12px;padding:1rem;margin-bottom:1.5rem">
    <div style="font-size:14px;font-weight:500;color:#2C2C2A;margin-bottom:10px">Notams</div>
    <div style="font-size:11px;text-transform:uppercase;color:#888780;margin-bottom:6px">{NOTAM_GROUP_LABEL}</div>
    <div style="display:flex;gap:8px;margin-bottom:10px">
      <span style="width:8px;height:8px;border-radius:50%;background:{NOTAM_DOT};margin-top:5px;flex-shrink:0"></span>
      <div style="font-size:12px;color:#5F5E5A"><span style="font-weight:500;color:#2C2C2A">{NOTAM_SUBJECT}</span> {NOTAM_DETAIL}</div>
    </div>
  </div>

  <div style="background:#EAF3DE;border-radius:12px;padding:1rem">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <i class="ti ti-check" style="color:#27500A;font-size:18px" aria-hidden="true"></i>
      <span style="font-size:14px;font-weight:500;color:#27500A">Bottom line</span>
    </div>
    <div style="font-size:13px;color:#27500A;line-height:1.7">{BOTTOM_LINE}</div>
  </div>
</div>
```

`{NOTAM_DOT}` is `#E24B4A` for a runway or ILS item and `#378ADD` for taxiway
or nav information. The NOTAM group block is cloned per airport
(departure / destination / alternate).

**SIGMET all-clear variant.** When no SIGMET crosses the filed route, the red
card above is replaced by this green row — never omitted entirely:

```html
<div style="background:#EAF3DE;border-radius:12px;padding:12px 16px;margin-bottom:1.5rem;display:flex;align-items:center;gap:8px">
  <i class="ti ti-check" style="color:#27500A;font-size:18px" aria-hidden="true"></i>
  <span style="font-size:13px;color:#27500A">No SIGMETs affecting the filed route.</span>
</div>
```

### RULE 3 — Required variants

**No alternate filed.** When the OFP lists no alternate, the alternate cell reads
exactly `No alternate filed.` — not an empty cell, not a dash.

**No NOTAMs.** When nothing operationally relevant is found, the NOTAM card reads
exactly `No operationally relevant NOTAMs.` — the card is still rendered.

**Amber bottom line.** The bottom-line card switches from the green all-clear
palette (#EAF3DE bg / #27500A text) to amber (#FAEEDA bg / #854F0B text) whenever
a SIGMET crosses the route or a runway/ILS item is listed in NOTAMs.

**Wind component cell.** Green (#EAF3DE bg / #27500A text) for a tailwind, amber
(#FAEEDA bg / #854F0B text) for a headwind.

**Limits exceedance.** If the OFP shows takeoff weight over max or fuel below
minimum, say so in the single post-render note, and the release must not print
`WITHIN LIMITS`.

-----

## RULE 6 — Release, manifest, and invoice templates

**Canonical template (locked 11 JUL 2026):** Same rationale as the other
canonical templates in this document — hardcoded hex/px values so all
three documents render identically every session. Deliberately styled as
paper forms rather than app cards: monospace font, black hairline grid
borders, no rounded corners on the outer frame, no color beyond the
existing neutral palette. Only `{PLACEHOLDER}` fields vary; the structure,
labels, fonts, and colors below never do.

```html
<div style="background:#FFFFFF;border:1px solid #2C2C2A;font-family:'Courier New',monospace;color:#2C2C2A;font-size:12px;max-width:680px;margin-bottom:16px">
  <div style="border-bottom:2px solid #2C2C2A;padding:12px 16px;display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div style="font-size:15px;font-weight:700;letter-spacing:0.5px">MERIDIAN AIR CHARTER</div>
      <div style="font-size:10px;color:#5F5E5A">14 CFR PART 135 ON-DEMAND CHARTER OPERATOR</div>
      <div style="font-size:10px;color:#5F5E5A">FAA CERTIFICATE NO. M3RDNA412J</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:14px;font-weight:700">FLIGHT RELEASE</div>
      <div style="font-size:10px;color:#5F5E5A">RELEASE NO. {RELEASE_NO}</div>
      <div style="font-size:10px;color:#5F5E5A">ISSUED {DATE} {ISSUED_TIME}Z</div>
    </div>
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:11px">
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:16%"><span style="color:#5F5E5A">TAIL NO</span><br><b>{TAIL}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:20%"><span style="color:#5F5E5A">AIRCRAFT TYPE</span><br><b>{ICAO_TYPE} / {AIRCRAFT_NAME}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:16%"><span style="color:#5F5E5A">TRIP NO</span><br><b>{TRIP_NO}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:16%"><span style="color:#5F5E5A">PAX</span><br><b>{PAX}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:32%"><span style="color:#5F5E5A">PIC</span><br><b>BROWN, KYLE</b></td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px" colspan="2"><span style="color:#5F5E5A">DEPARTURE</span><br><b>{DEP_ICAO} · {DEP_NAME}</b><br><span style="color:#5F5E5A">FBO</span> {DEP_FBO} · {DEP_FBO_TEL}</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px" colspan="2"><span style="color:#5F5E5A">DESTINATION</span><br><b>{DEST_ICAO} · {DEST_NAME}</b><br><span style="color:#5F5E5A">FBO</span> {DEST_FBO} · {DEST_FBO_TEL}</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">ALTERNATE</span><br><b>{ALTN_ICAO} · {ALTN_NAME}</b></td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">ETD (Z)</span><br><b>{ETD_Z}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">ETA (Z)</span><br><b>{ETA_Z}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">BLOCK TIME</span><br><b>{BLOCK_TIME}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">ROUTE ALT</span><br><b>{ALTITUDE}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px"><span style="color:#5F5E5A">DISPATCHER</span><br><b>BROWN, JACQUELINE</b></td>
    </tr>
  </table>

  <div style="padding:8px 16px;font-size:10px;line-height:1.6;color:#5F5E5A">FILED ROUTE: {FILED_ROUTE}</div>

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px">
    <div style="font-weight:700;font-size:11px;margin-bottom:6px">WEATHER AND NOTAM BRIEFING</div>
    <div style="font-size:11px;line-height:1.9">
      <span style="border:1px solid #2C2C2A;padding:0 4px;margin-right:6px">X</span>PIC has reviewed current weather for departure, en route, destination, and alternate<br>
      <span style="border:1px solid #2C2C2A;padding:0 4px;margin-right:6px">X</span>PIC has reviewed NOTAMs applicable to this route of flight<br>
      <!-- only include this third line if RULE 3 found a SIGMET on route -->
      <span style="border:1px solid #2C2C2A;padding:0 4px;margin-right:6px">X</span>{SIGMET_LINE}
    </div>
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:8px">
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:25%"><span style="color:#5F5E5A">MIN FUEL REQ</span><br><b>{MIN_FUEL} LBS</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:25%"><span style="color:#5F5E5A">FUEL ON BOARD</span><br><b>{FUEL_ONBOARD} LBS</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:25%"><span style="color:#5F5E5A">TOW / MAX</span><br><b>{TOW} / {MAX_TOW}</b></td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:25%"><span style="color:#5F5E5A">W&B / CG</span><br><b>WITHIN LIMITS</b></td>
    </tr>
  </table>

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px">
    <div style="font-weight:700;font-size:11px;margin-bottom:4px">BOOKING CONTACT</div>
    <div style="font-size:11px;color:#5F5E5A">{CONTACT_NAME} · {CONTACT_COMPANY} · {CONTACT_PHONE}</div>
  </div>

  <!-- Passenger requests section: OPTIONAL, omit entirely on freight runs or when nothing fits -->
  <div style="border-top:1px solid #2C2C2A;padding:10px 16px">
    <div style="font-weight:700;font-size:11px;margin-bottom:4px">PASSENGER REQUESTS / SPECIAL NEEDS</div>
    <div style="font-size:11px;color:#5F5E5A">{PASSENGER_REQUESTS_TEXT}</div>
  </div>

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px">
    <div style="font-weight:700;font-size:11px;margin-bottom:4px">MEL / REMARKS</div>
    <div style="font-size:11px;color:#5F5E5A">{MEL_REMARKS}</div>
  </div>

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px;font-size:10px;line-height:1.6;color:#5F5E5A">
    This flight is released for operation under 14 CFR Part 135 operating rules. The dispatcher certifies that this release meets applicable weather minimums, fuel requirements, and weight and balance limitations for the aircraft and route specified above. The pilot in command retains final authority for the safety of this flight and may decline this release at their discretion.
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:4px">
    <tr>
      <td style="border-top:1px solid #2C2C2A;padding:16px 8px 6px;width:50%">
        <div style="border-bottom:1px solid #2C2C2A;height:24px"></div>
        <div style="color:#5F5E5A;font-size:10px;margin-top:2px">DISPATCHER SIGNATURE — BROWN, JACQUELINE — {DATE} {ISSUED_TIME}Z</div>
      </td>
      <td style="border-top:1px solid #2C2C2A;padding:16px 8px 6px;width:50%">
        <div style="border-bottom:1px solid #2C2C2A;height:24px"></div>
        <div style="color:#5F5E5A;font-size:10px;margin-top:2px">PIC SIGNATURE — BROWN, KYLE — ACCEPTED</div>
      </td>
    </tr>
  </table>
</div>

<div style="background:#FFFFFF;border:1px solid #2C2C2A;font-family:'Courier New',monospace;color:#2C2C2A;font-size:12px;max-width:680px;margin-bottom:16px">
  <div style="border-bottom:2px solid #2C2C2A;padding:10px 16px;display:flex;justify-content:space-between;align-items:baseline">
    <div style="font-size:13px;font-weight:700">{MANIFEST_TITLE}</div>
    <div style="font-size:10px;color:#5F5E5A">TRIP {TRIP_NO} · {TAIL} · {DEP_ICAO}-{DEST_ICAO}</div>
  </div>

  <!-- Passenger manifest variant (pax > 0) -->
  <table style="width:100%;border-collapse:collapse;font-size:11px">
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">#</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">NAME</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">AGE</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">WT (LBS)</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">BAG (LBS)</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">TOTAL</td>
    </tr>
    <!-- repeat one row per passenger -->
    <tr>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{N}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{SURNAME}, {FIRST_NAME}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{AGE}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{BODY_WT}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{BAG_WT}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{TOTAL_WT}</td>
    </tr>
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700" colspan="5">TOTAL PAX WEIGHT</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">{TOTAL_PAX_WT}</td>
    </tr>
  </table>

  <!-- Cargo manifest variant (pax = 0 / freight run) — use instead of the table above.
       On a passenger flight carrying cargo above 0, add this table BENEATH the
       passenger table rather than replacing it.
  <table style="width:100%;border-collapse:collapse;font-size:11px">
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">#</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">DESCRIPTION</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">WT (LBS)</td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{N}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{CARGO_DESCRIPTION}</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px">{CARGO_WT}</td>
    </tr>
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700" colspan="2">TOTAL CARGO WEIGHT</td>
      <td style="border:1px solid #B4B2A9;padding:5px 8px;font-weight:700">{TOTAL_CARGO_WT}</td>
    </tr>
  </table>
  -->

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px;font-size:10px;line-height:1.7;color:#5F5E5A">
    {WEIGHT_DECLARATION_NOTE}
  </div>
</div>

<div style="background:#FFFFFF;border:1px solid #2C2C2A;font-family:'Courier New',monospace;color:#2C2C2A;font-size:12px;max-width:680px">
  <div style="border-bottom:2px solid #2C2C2A;padding:12px 16px;display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div style="font-size:15px;font-weight:700;letter-spacing:0.5px">MERIDIAN AIR CHARTER</div>
      <div style="font-size:10px;color:#5F5E5A">14 CFR PART 135 ON-DEMAND CHARTER OPERATOR</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:14px;font-weight:700">INVOICE</div>
      <div style="font-size:10px;color:#5F5E5A">INVOICE NO. {RELEASE_NO}</div>
      <div style="font-size:10px;color:#5F5E5A">DATE {DATE}</div>
    </div>
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:11px">
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:50%"><span style="color:#5F5E5A">BILL TO</span><br><b>{CONTACT_COMPANY}</b><br>ATTN: {CONTACT_NAME}<br>{CONTACT_PHONE}</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;width:50%;vertical-align:top">
        <span style="color:#5F5E5A">TRIP</span><br><b>{TRIP_NO} · {TAIL} · {ICAO_TYPE}</b><br>
        <span style="color:#5F5E5A">DATE</span> {DATE} &nbsp; <span style="color:#5F5E5A">ROUTE</span> {DEP_ICAO}-{DEST_ICAO}<br>
        <span style="color:#5F5E5A">BLOCK TIME</span> {BLOCK_TIME} &nbsp; <span style="color:#5F5E5A">PAX</span> {PAX}
      </td>
    </tr>
  </table>

  <table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:8px">
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700">DESCRIPTION</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700;text-align:right;width:18%">QTY</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700;text-align:right;width:18%">RATE</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700;text-align:right;width:18%">AMOUNT</td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">Aircraft charter — dry hourly rate</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">{BLOCK_HRS} HR</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${DRY_RATE}/HR</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${CHARTER_AMOUNT}</td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">Jet-A fuel — {DEP_FBO}, {DEP_ICAO}</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">{FUEL_GAL} GAL</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${FUEL_PRICE}/GAL</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${FUEL_AMOUNT}</td>
    </tr>
    <!-- catering row: only for mid jet and large jet/BBJ classes with pax > 0, omit entirely otherwise -->
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">In-flight catering</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">{PAX} PAX</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">$65.00/PAX</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${CATERING_AMOUNT}</td>
    </tr>
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">Ramp / handling — {DEP_ICAO}, {DEST_ICAO}</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">—</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">—</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${HANDLING_AMOUNT}</td>
    </tr>
    <!-- crew day rate row: only when block time >= 2h, omit otherwise -->
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">Crew day rate</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">1</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">—</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${CREW_DAY_RATE}</td>
    </tr>
    <!-- FET row: domestic legs only, omit entirely on legs to or from outside the US -->
    <tr>
      <td style="border:1px solid #B4B2A9;padding:6px 8px">Federal excise tax (FET)</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">—</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">7.5%</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;text-align:right">${FET_AMOUNT}</td>
    </tr>
    <tr style="background:#F1EFE8">
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700" colspan="3">TOTAL DUE</td>
      <td style="border:1px solid #B4B2A9;padding:6px 8px;font-weight:700;text-align:right">${TOTAL_DUE}</td>
    </tr>
  </table>

  <div style="border-top:1px solid #2C2C2A;padding:10px 16px;font-size:10px;line-height:1.7;color:#5F5E5A">
    PAYMENT TERMS: DUE UPON RECEIPT · FUEL PRICED AT DEPARTURE FBO, DAY OF FLIGHT
  </div>
</div>
```

`{MANIFEST_TITLE}` is "PASSENGER MANIFEST" or "CARGO MANIFEST" depending on
pax count. `{WEIGHT_DECLARATION_NOTE}` is "Weights per passenger
declaration." or "Weights per shipper declaration." — no other footer
text is ever added, and the booking contact does not appear on the manifest;
it lives on the release. `{SIGMET_LINE}` is omitted (drop that whole checkbox
row) when RULE 3 found no SIGMET on the route; otherwise it names the
SIGMET ID and validity exactly as RULE 3 already computed it. The
passenger-requests block in the release is omitted entirely (not left
empty) when there's nothing worth including. The catering and crew-day-
rate rows in the invoice are omitted entirely, not shown as $0, when the
conditions for them (mid or large jet + pax>0; block ≥2h) aren't met.
