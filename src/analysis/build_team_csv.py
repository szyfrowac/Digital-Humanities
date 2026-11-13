#!/usr/bin/env python3
"""Lighthouse results in the team's spreadsheet layout. WAVE columns stay blank for the team to fill.
Run from project root: python3 -I src/analysis/build_team_csv.py
Output: data/processed/team_audit_sheet.csv
"""
import csv, json, pathlib
ROOT = pathlib.Path.cwd(); LH = ROOT/"data/raw/shared/lighthouse"
S = json.loads((LH/"summary.json").read_text())
SERVICES = [("Property Tax Payment", "blr_ptax", "hyd_pt_pay"), ("Civic Grievance Redressal", "blr_sahaaya", "hyd_griev_otp"),
            ("Birth Certificate", "blr_ejanma_dl", "hyd_birth"), ("Death Certificate", "blr_ejanma_dl", "hyd_death"), ("Trade Licence Portal", "blr_trade_apply", "hyd_trade_new"),
            ("Building Plan", "blr_bpas", "hyd_build_app"), ("Pet Dog Licences", None, "hyd_pet"), ("E-Waste Doorstep Pickup", None, None)]
HEAD = ["Civic Body", "Serial Number", "Civic Service", "Accessibility Score", "Missing [alt] Attributes", "Contrast Errors",
        "Accessibility Score (WAVE)", "WCAG Errors", "Contrast Errors (WAVE)", "Missing [alt] Attributes (WAVE)", "Missing Form Label", "Empty Button",
        "Lang Attribute", "Document Main Landmark", "Page Audited (Lighthouse)", "Lighthouse Status"]
GROUP = ["", "", "", "LIGHTHOUSE", "LIGHTHOUSE", "LIGHTHOUSE", "WAVE", "WAVE", "WAVE", "WAVE", "WAVE", "WAVE", "LIGHTHOUSE", "LIGHTHOUSE", "", ""]
def yn(a):
    if a is None or a.get("score") is None: return "Not applicable"
    return "Yes" if a["score"] == 1 else "No"
def row(body, n, name, pid):
    wave = [""]*6
    if pid is None:
        return [body, n, name, "", "", ""] + wave + ["", "", "", "No web page found"]
    r = S[pid]
    if r["status"] != "audited":
        return [body, n, name, "", "", ""] + wave + ["", "", r["requestedUrl"], "Not scored: " + (r.get("error") or "no score")[:80]]
    a = json.loads((LH/f"{pid}.report.json").read_text())["audits"]
    return [body, n, name, r["score"], r["focus"]["image-alt"]["items"], r["focus"]["color-contrast"]["items"]] + wave + [yn(a.get("html-has-lang")), yn(a.get("landmark-one-main")), r["finalUrl"], "Audited"]
with open(ROOT/"data/processed/team_audit_sheet.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(GROUP); w.writerow(HEAD)
    for body, i in (("GHMC", 2), ("BBMP / GBA", 1)):
        for n, s in enumerate(SERVICES, 1):
            w.writerow(row(body, n, s[0], s[i]))
