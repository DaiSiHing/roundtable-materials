"""D-7 stakes table builder v1 — band -> ground-level dependencies, MEASURED from the
verified 15-Jul-2026 catalog pull (32,010 objects; parse convention matches the D2
referee-verified reader: 3LE, altitude from line-2 mean motion, a - Re).
Deterministic (no draws). Name-pattern category counts are DERIVED (method stated,
conservative patterns); band placement MEASURED (TLE); census-side rows SOURCED (GCAT
epoch 8 Jul). This table is the WHITELIST for every ground-level claim on the surface."""
import json, math, re

RE_KM, MU = 6378.137, 398600.4418
# v1.1 (2026-07-19): 495-570 label corrected — the band is the migration's ORIGIN
# (the old ~550 km shells; paper F13 "550-km era", skeleton §2 "from 550 to 480 km"),
# not its destination. Editor-ratified; see ledger DV2 note. Numbers unchanged.
BANDS = [(150,380,"below the stations"),(380,430,"the crewed band — where people live"),
         (430,465,"between crews and the corridor"),(465,495,"the internet corridor (trigger band)"),
         (495,570,"the emptying band (the migration’s origin)"),(570,700,"upper transition"),
         (700,1000,"the ratchet band — where Earth-watching lives"),(1000,2000,"high LEO")]
CATS = {  # conservative, recognizable-name patterns (uppercase match)
 "stations_and_crew_vehicles": r"\b(ZARYA|NAUKA|ISS \(|TIANHE|WENTIAN|MENGTIAN|CSS \(|CREW DRAGON|SOYUZ-MS|PROGRESS-MS|TIANZHOU|SHENZHOU)\b",
 "starlink": r"^STARLINK",
 "oneweb": r"^ONEWEB",
 "qianfan_g60": r"^(QIANFAN|G60)",
 "weather_climate_ops": r"^(NOAA \d|METOP|DMSP|FENGYUN|FY-3|SUOMI|JPSS|METEOR-M)",
 "earth_science_observation": r"^(LANDSAT|SENTINEL-|TERRA\b|AQUA\b|AURA\b|ICESAT|GRACE-FO|SWOT|FLOCK|SKYSAT|SPOT |WORLDVIEW|PLEIADES|EOS-)",
}
objs, name = [], None
for ln in open("../sources/Space-track.txt", encoding="utf-8", errors="replace"):  # repo-relative (was a chat-era upload path); run from engines_and_data/
    ln = ln.rstrip("\r\n")
    if ln.startswith("0 "): name = ln[2:].strip()
    elif ln.startswith("2 ") and name is not None:
        try: n = float(ln[52:63])
        except ValueError: continue
        a = MU**(1/3) / ((2*math.pi*n/86400.0)**(2/3))
        objs.append((name, a - RE_KM))
total = len(objs)
rows = []
for lo, hi, label in BANDS:
    inband = [nm for nm, alt in objs if lo <= alt < hi]
    row = {"band_km": f"{lo}-{hi}", "label": label, "tracked_objects": len(inband),
           "debris_and_rb": sum(1 for nm in inband if " DEB" in nm or " R/B" in nm),
           "categories": {}}
    for cat, pat in CATS.items():
        c = sum(1 for nm in inband if re.search(pat, nm))
        if c: row["categories"][cat] = c
    rows.append(row)
out = {
 "artifact": "kessler_stakes_table_v1", "built": "2026-07-16",
 "source": "Space-track.txt full pull 15 Jul 2026 (referee-parse-verified file); altitude = a-Re from line-2 mean motion (near-circular convention, method stated)",
 "total_objects_parsed": total, "expected_total": 32010,
 "rows": rows,
 "census_sourced_rows_NOT_rederivable_here": {
   "active_non_maneuverable": {"count": 2113, "tag": "SOURCED (GCAT census, epoch 8 Jul 2026)",
     "meaning": "active satellites that cannot dodge — the burden-shift population"},
   "active_payloads_total": 16234, "active_starlink": 10736},
 "usage_rule": "This table is the WHITELIST: no ground-level dependency ships on the surface unless it maps to a row here or a census-sourced entry above. Out-of-band services (e.g., GPS/GNSS — MEO) are NEVER invoked.",
 "tags": "band placement MEASURED (TLE); category counts DERIVED (stated name patterns, conservative — undercounts by design); census rows SOURCED",
 # v1.1: category_caveat folded into the builder — it existed in the blessed v1 OUTPUT
 # but not in this script (post-hoc addition); the builder now reproduces its artifact.
 "category_caveat": "name-pattern counts are STATUS-BLIND: they include retired generations still on orbit (e.g., decades of NOAA/METEOR/DMSP in the ratchet band). Surface phrasing must say 'working and retired' or cite the census for active-only claims. Undercounting by conservative patterns is accepted; overclaiming operational status is not.",
}
json.dump(out, open("kessler_stakes_table_v1.json","w", newline="\n"), indent=1)  # LF, matching the blessed artifact
print("total parsed:", total, "(expected 32,010)")
for r in rows:
    print(f"{r['band_km']:>10} {r['tracked_objects']:>6} objs | " + ", ".join(f"{k}={v}" for k,v in r["categories"].items())[:110])
