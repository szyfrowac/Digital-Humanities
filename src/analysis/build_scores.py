#!/usr/bin/env python3
"""Merge Lighthouse (and WAVE, once run) into one spreadsheet and the site's JSON.
Run from project root: python3 -I src/analysis/build_scores.py
Output: data/processed/audit_scores.csv, public/data/scores.json
"""
import csv, json, pathlib, statistics, urllib.parse

ROOT = pathlib.Path.cwd()
LH = json.loads((ROOT/"data/raw/shared/lighthouse/summary.json").read_text())
wave_file = ROOT/"data/raw/shared/wave/results.json"
WAVE = json.loads(wave_file.read_text()) if wave_file.exists() else {}
AUDIT = {p["id"]: p for p in json.loads((ROOT/"public/data/audit.json").read_text())["pages"]}
CIVIC = json.loads((ROOT/"public/data/civic_services.json").read_text())

# bbmp.gov.in redirects to the GBA home page: it stays in the raw files, but is not counted twice.
SKIP = {"blr_bbmp"}
# Service-specific pages from data/metadata/audit_url_list.csv. None = no web page found.
BRIEF = {
    "Property tax": {"bengaluru": "blr_ptax", "hyderabad": "hyd_pt_pay"},
    "Citizen grievance": {"bengaluru": "blr_sahaaya", "hyderabad": "hyd_griev_otp"},
    "Birth certificate": {"bengaluru": "blr_ejanma_dl", "hyderabad": "hyd_birth"},
    "Death certificate": {"bengaluru": "blr_ejanma_dl", "hyderabad": "hyd_death"},
    "Trade licence": {"bengaluru": "blr_trade_apply", "hyderabad": "hyd_trade_new"},
    "Building plan": {"bengaluru": "blr_bpas", "hyderabad": "hyd_build_app"},
    "Pet dog licence": {"bengaluru": None, "hyderabad": "hyd_pet"},
    "E-waste pickup": {"bengaluru": None, "hyderabad": None},
}
SERVICE_IDS = {c: sorted({v[c] for v in BRIEF.values() if v[c]}) for c in ("bengaluru", "hyderabad")}
def band(s):
    if s is None: return "No score"
    return "Red (under 50)" if s < 50 else "Yellow (50 to 79)" if s < 80 else "Green (80 and over)"
def site(u):
    h = urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")
    return "ghmc.gov.in" if h.endswith("ghmc.gov.in") else h

rows = []
for pid, r in LH.items():
    if pid in SKIP: continue
    a, w = AUDIT.get(pid, {}), WAVE.get(pid, {})
    if w.get("status") != "audited":  # failed or invalid WAVE records contribute no numbers
        w = {"status": w.get("status", "not run")}
    f = r.get("focus") or {}
    n = lambda k: (f.get(k) or {}).get("items", "") if r.get("status") == "audited" else ""
    rows.append({"id": pid, "page": a.get("label", pid), "city": a.get("city", ""), "url": r.get("finalUrl") or r["requestedUrl"], "site": site(r.get("finalUrl") or r["requestedUrl"]),
                 "lighthouse_status": r["status"], "lighthouse_score": r.get("score"), "band": band(r.get("score")), "lighthouse_error": r.get("error") or r.get("runtimeError") or "",
                 "lh_contrast_items": n("color-contrast"), "lh_image_alt_items": n("image-alt"), "lh_button_name_items": n("button-name"), "lh_link_name_items": n("link-name"), "lh_label_items": n("label"),
                 "lh_heading_order_items": n("heading-order"), "lh_failed_audits": len(r.get("failed") or []), "lighthouse_version": r.get("lighthouseVersion", ""), "audited_at": r["auditedAt"],
                 "wave_status": w.get("status", "not run"), "wave_errors": w.get("errors", ""), "wave_contrast_errors": w.get("contrastErrors", ""), "wave_missing_alt": w.get("missingAlt", ""),
                 "wave_missing_form_labels": w.get("missingFormLabels", ""), "wave_empty_buttons": w.get("emptyButtons", ""), "wave_h1": w.get("h1", ""), "wave_h2": w.get("h2", ""), "wave_h3": w.get("h3", "")})
with open(ROOT/"data/processed/audit_scores.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def stat(ps):
    s = sorted(p["lighthouse_score"] for p in ps if p["lighthouse_score"] is not None)
    bysite = {}
    for p in ps:
        if p["lighthouse_score"] is not None: bysite.setdefault(p["site"], []).append(p["lighthouse_score"])
    means = sorted(statistics.mean(v) for v in bysite.values())
    return {"pages": len(s), "not_scored": len(ps)-len(s), "median": round(statistics.median(s), 1), "min": s[0], "max": s[-1], "red": sum(x < 50 for x in s), "yellow": sum(50 <= x < 80 for x in s), "green": sum(x >= 80 for x in s),
            "sites": len(means), "median_of_site_means": round(statistics.median(means), 1)}
out = {"cities": {c: stat([r for r in rows if r["id"] in SERVICE_IDS[c]]) for c in ("bengaluru", "hyderabad")},
       "all_pages": {c: stat([r for r in rows if r["city"] == c]) for c in ("bengaluru", "hyderabad")},
       "pages": [{k: r[k] for k in ("id", "page", "city", "url", "lighthouse_status", "lighthouse_score", "band", "lighthouse_error", "lh_contrast_items", "lh_image_alt_items", "lh_button_name_items", "lh_label_items")} for r in rows],
       "brief": [{"type": t, "bengaluru": next((r for r in rows if r["id"] == v["bengaluru"]), None) and next(r for r in rows if r["id"] == v["bengaluru"])["lighthouse_score"],
                  "hyderabad": next((r for r in rows if r["id"] == v["hyderabad"]), None) and next(r for r in rows if r["id"] == v["hyderabad"])["lighthouse_score"], "bengaluru_id": v["bengaluru"], "hyderabad_id": v["hyderabad"]} for t, v in BRIEF.items()],
       "version": next((r["lighthouse_version"] for r in rows if r["lighthouse_version"]), ""), "wave_run": any(r.get("status") == "audited" for r in WAVE.values())}
(ROOT/"public/data/scores.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({k: out[k] for k in ("cities", "brief", "version")}, indent=0))
for r in sorted(rows, key=lambda x: (x["city"], -(x["lighthouse_score"] or -1))):
    print(r["city"][:3], r["lighthouse_score"], r["page"], "|", r["lh_contrast_items"], r["lh_image_alt_items"], r["lh_button_name_items"], r["lh_label_items"], r["lighthouse_error"][:70] if r["lighthouse_error"] else "")
