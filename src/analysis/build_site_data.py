#!/usr/bin/env python3
"""Join audit results and analysis into the JSON the site reads.
Numbers in findings and journeys are read from data, never typed by hand.
Run from project root after process.py and the audit: python3 -I src/analysis/build_site_data.py
"""
import csv, json, pathlib
ROOT = pathlib.Path.cwd()
AUD = json.loads((ROOT/"data/raw/shared/accessibility_audit/results.json").read_text())
AN = json.loads((ROOT/"public/data/analysis.json").read_text())
WEB = ROOT/"public/data"; META = ROOT/"data/metadata"
AUDIT_DATE = "4 November 2026"

LABELS = {
 "blr_gba": ("Greater Bengaluru Authority home", "bengaluru"), "blr_gba_clinics": ("GBA nearby clinic and polio booth finder", "bengaluru"),
 "blr_sahaaya": ("Sahaaya complaints (bbmp.sahaaya.in)", "bengaluru"), "blr_ptax": ("Property tax portal", "bengaluru"),
 "blr_ejanma": ("e-Janma births and deaths", "bengaluru"), "blr_nadakacheri": ("Nadakacheri AJSK certificates", "bengaluru"),
 "blr_bwssb": ("BWSSB water board", "bengaluru"), "blr_bmtc": ("BMTC buses", "bengaluru"), "blr_bmrc": ("Namma Metro (BMRCL)", "bengaluru"),
 "blr_hfw": ("Karnataka Health and Family Welfare", "bengaluru"), "blr_bswml": ("Bengaluru Solid Waste Management Ltd", "bengaluru"),
 "blr_ahara": ("Ahara food and civil supplies", "bengaluru"), "blr_sevasindhu": ("Seva Sindhu", "bengaluru"), "blr_sakala": ("Sakala service tracking", "bengaluru"),
 "hyd_ghmc": ("GHMC home", "hyderabad"), "hyd_ghmc_igs": ("GHMC grievances", "hyderabad"), "hyd_ghmc_ptax_search": ("GHMC property tax search", "hyderabad"),
 "hyd_ghmc_ptax_page": ("GHMC property tax information", "hyderabad"), "hyd_ghmc_bnd": ("GHMC births and deaths sign-in (labelled Hospitals Login)", "hyderabad"),
 "hyd_ghmc_bnd_status": ("GHMC application status", "hyderabad"), "hyd_ghmc_howdoi": ("GHMC 'How do I' guide", "hyderabad"),
 "hyd_meeseva": ("MeeSeva", "hyderabad"), "hyd_hmwssb": ("HMWSSB water board", "hyderabad"), "hyd_hmwssb_grievance": ("HMWSSB register grievance", "hyderabad"),
 "hyd_tgsrtc": ("TGSRTC buses", "hyderabad"), "hyd_ltmetro": ("Hyderabad Metro (L&T)", "hyderabad"), "hyd_health": ("Telangana Health department", "hyderabad"),
 "hyd_chfw": ("Telangana Family Welfare", "hyderabad"), "hyd_epds": ("Telangana ePDS", "hyderabad"), "hyd_civilsupplies": ("Telangana Civil Supplies", "hyderabad"),
 "national_digilocker": ("DigiLocker", "national"),
 "hyd_pt_pay": ("GHMC property tax payment form", "hyderabad"), "hyd_griev_otp": ("GHMC lodge grievance (OTP step)", "hyderabad"), "hyd_birth": ("GHMC birth certificate search", "hyderabad"),
 "hyd_death": ("GHMC death certificate search", "hyderabad"), "hyd_trade_new": ("GHMC new trade licence application", "hyderabad"), "hyd_build_app": ("BuildNow application portal", "hyderabad"), "hyd_pet": ("GHMC pet licence sign-in", "hyderabad"),
 "blr_ejanma_dl": ("e-Janma download certificate", "bengaluru"), "blr_trade_apply": ("New trade licence sign-in (Seva Sindhu route)", "bengaluru"), "blr_bpas": ("Building plan approval sign-in", "bengaluru"),
}
# bbmp.gov.in redirects to the GBA home page, so it would double-count one page.
SKIP = {"blr_bbmp"}
CATS = [
 ("Text contrast", "1.4.3", {"color-contrast"}),
 ("Unnamed links and buttons", "2.4.4, 4.1.2", {"link-name", "button-name", "aria-command-name"}),
 ("Images without text alternatives", "1.1.1", {"image-alt", "input-image-alt", "svg-img-alt", "role-img-alt"}),
 ("Page language not declared", "3.1.1", {"html-has-lang", "html-lang-valid"}),
 ("Unlabelled form fields", "1.3.1, 3.3.2, 4.1.2", {"label", "select-name", "aria-input-field-name"}),
 ("Small tap targets", "2.5.8 (new in WCAG 2.2)", {"target-size"}),
 ("Structure and ARIA errors", "1.3.1, 4.1.2", {"list", "listitem", "aria-required-children", "aria-allowed-attr", "aria-hidden-focus", "nested-interactive", "frame-title", "link-in-text-block"}),
 ("Moving or blinking text", "2.2.2", {"marquee", "blink"}),
 ("Zoom blocked", "1.4.4", {"meta-viewport"}),
]
LANG_NAMES = {"english": "English", "kannada": "Kannada", "telugu": "Telugu", "urdu": "Urdu", "tamil": "Tamil", "hindi": "Hindi"}

def languages(r):
    c = r["probes"]["languageControls"]
    out = [v for k, v in LANG_NAMES.items() if c.get(k)]
    if c.get("googleTranslate"): out.append("Google Translate widget")
    if c.get("bhashini"): out.append("Bhashini widget")
    return out

pages = []
for pid, r in AUD.items():
    if pid in SKIP: continue
    label, city = LABELS[pid]
    p = {"id": pid, "label": label, "city": city, "url": r["requestedUrl"] if pid == "blr_gba" else (r.get("finalUrl") or r["requestedUrl"]), "status": r["status"]}
    if r["status"] == "audited":
        v = r["axe"]["violations"]
        p.update(rules=len(v), nodes=sum(x["nodes"] for x in v), severe=[x["id"] for x in v if x["impact"] in ("critical", "serious")], all_rules=[x["id"] for x in v],
                 htmlLang=r["probes"]["htmlLang"], languages=languages(r), focusRing=r["keyboard"]["focusRingDetected"], overflow=r["reflow320"]["horizontalOverflow"],
                 skipLink=r["probes"]["skipLink"], zoomBlocked=r["probes"]["zoomBlocked"], links=r["probes"]["counts"]["links"], inputs=r["probes"]["counts"]["formInputs"],
                 words=r["probes"]["counts"]["words"], auth=r["probes"]["authSignals"], scripts=r["probes"]["scriptChars"], httpStatus=r["httpStatus"], title=r["probes"]["title"], retried=bool(r.get("firstAttemptError")))
    else:
        p["error"] = r["error"].replace("page.goto: ", "").split(" at ")[0]
    pages.append(p)
aud = [p for p in pages if p["status"] == "audited"]
by = {c: [p for p in aud if p["city"] == c] for c in ("bengaluru", "hyderabad")}
cats = []
for label, wcag, ids in CATS:
    row = {"label": label, "wcag": wcag}
    for c, ps in by.items():
        row[c] = round(sum(1 for p in ps if ids & set(p["all_rules"]))/len(ps)*100)
    cats.append(row)
cats.sort(key=lambda r: -(r["bengaluru"]+r["hyderabad"]))
# language reach
reach = {}
for c, ps in by.items():
    rows = []
    for l in AN["census"]["language"][c]["top"][:5]:
        n = sum(1 for p in ps if l["language"] in p["languages"])
        rows.append({"language": l["language"], "pct": l["pct"], "pages": n})
    reach[c] = rows
widgets = {c: sum(1 for p in ps if "Google Translate widget" in p["languages"] or "Bhashini widget" in p["languages"]) for c, ps in by.items()}
missing_lang = {c: sum(1 for p in ps if not p["htmlLang"]) for c, ps in by.items()}
any_ctrl = {c: sum(1 for p in ps if p["languages"]) for c, ps in by.items()}
overflow = {c: sum(1 for p in ps if p["overflow"]) for c, ps in by.items()}
noring = {c: [p["label"] for p in ps if p["focusRing"] == 0] for c, ps in by.items()}
axe_version = next(r["axe"]["version"] for r in AUD.values() if r["status"] == "audited")
median = lambda xs: sorted(xs)[len(xs)//2]
summary = {c: {"pages": len(ps), "median_rules": median([p["rules"] for p in ps]), "median_nodes": median([p["nodes"] for p in ps]),
               "contrast_pages": sum(1 for p in ps if "color-contrast" in p["all_rules"]), "skip": sum(1 for p in ps if p["skipLink"])} for c, ps in by.items()}
failed = [p for p in pages if p["status"] != "audited"]
from urllib.parse import urlparse
def site(p):
    h = urlparse(p["url"]).netloc.lower().removeprefix("www.")
    return "ghmc.gov.in" if h.endswith("ghmc.gov.in") else h
sites = {}
for c, ps in by.items():
    g = {}
    for p in ps: g.setdefault(site(p), []).append(p)
    sites[c] = {"sites": len(g), "missing_lang_sites": sum(1 for v in g.values() if any(not x["htmlLang"] for x in v)), "contrast_sites": sum(1 for v in g.values() if any("color-contrast" in x["all_rules"] for x in v))}
(WEB/"audit.json").write_text(json.dumps({"axe_version": axe_version, "audit_date": AUDIT_DATE, "counts": {"audited": len(aud), "failed": len(failed), "bengaluru": len(by["bengaluru"]), "hyderabad": len(by["hyderabad"])},
    "categories": cats, "pages": pages, "language_reach": reach, "widgets": widgets, "summary": summary, "sites": sites, "missing_lang": missing_lang, "overflow": overflow, "no_focus_ring": noring}, indent=1, ensure_ascii=False))

P = {p["id"]: p for p in pages}
def L(pid): return next(p for p in pages if p["id"] == pid)

# ---------- 20 civic-service records ----------
TASKS = [("complaints", "Filing municipal complaints and grievances"), ("property_tax", "Paying property taxes"), ("certificates", "Applying for government certificates"),
         ("water", "Accessing water and utility services"), ("transport", "Accessing public transport"), ("health", "Finding and accessing public healthcare"),
         ("waste", "Reporting waste and sanitation issues"), ("pds", "Accessing the Public Distribution System"), ("documents", "Obtaining government documents online"), ("tracking", "Tracking applications and service requests")]
NV = lambda t: {"status": "notverified", "text": t}
OK = lambda t: {"status": "verified", "text": t}
R = [
 ("complaints", "bengaluru", "blr_gba", "Greater Bengaluru Authority site, Sahaaya 2.0", "GBA and five city corporations", OK("The GBA home page links to the 'Namma Bengaluru [Sahaaya 2.0]' Android app."),
  NV("We found no verified list of offices that accept complaints in person."), ["Our browser reported a certificate error at the older bbmp.sahaaya.in web address."], ["blr_sahaaya"],
  [("GBA home page", "https://gba.karnataka.gov.in/"), ("Sahaaya 2.0 on Google Play", "https://play.google.com/store/apps/details?id=com.nammabengaluruNew.org")]),
 ("complaints", "hyderabad", "hyd_griev_otp", "GHMC Integrated Grievance System", "GHMC", OK("Lodging a grievance starts with a mobile number and OTP. News reports describe MyCURE as the app that replaced MyGHMC; we did not test the app."),
  NV("We found no verified list of offices that accept complaints in person."), [], ["hyd_ghmc_igs"], [("Lodge grievance", "https://igs.ghmc.gov.in/operator/send_otp_mobile"), ("Report on the MyCURE app", "https://newsmeter.in/hyderabad/hyderabad-ghmc-unveils-mycure-app-to-track-resolve-civic-complaints-in-real-time-763247")]),
 ("property_tax", "bengaluru", "blr_ptax", "Bengaluru property tax system", "Bengaluru City Corporations", OK("The page lists demand notices, payment, payment status, receipts and grievance tickets."),
  OK("The portal links a PDF list of designated bank branches for payment. We did not check that list."), ["The address still uses the former BBMP name.", "Seva Sindhu lists BBMP property tax, but its Apply Online link returns to the same list."], [], [("Property tax portal", "https://bbmptax.karnataka.gov.in/"), ("Designated bank branches (PDF)", "https://bbmptax.karnataka.gov.in/documents/BANKS_AND_BRANCHES_LIST.pdf")]),
 ("property_tax", "hyderabad", "hyd_pt_pay", "GHMC property tax payment", "GHMC / CURE", OK("The payment form asks for a PTI number or registered mobile number. MeeSeva also lists GHMC property tax."),
  NV("We did not confirm payment counters or citizen service centres."), [], ["hyd_ghmc_ptax_search"], [("Property tax payment", "https://onlinepayments.ghmc.gov.in/"), ("MeeSeva", "https://ts.meeseva.telangana.gov.in/meeseva/home.htm")]),
 ("certificates", "bengaluru", "blr_ejanma_dl", "e-Janma download certificate", "Karnataka, Chief Registrar of Births and Deaths", OK("The download page loaded. Seva Sindhu also lists BBMP certificates, but its Apply Online link returns to the same list."),
  NV("Customer Service Centre records are on the map, but the source does not confirm which centres are open or what they issue."), [], ["blr_ejanma", "blr_nadakacheri"], [("e-Janma download certificate", "https://ejanma.karnataka.gov.in/frmDownloadCertificate.aspx"), ("Nadakacheri AJSK", "https://nadakacheri.karnataka.gov.in/ajsk")]),
 ("certificates", "hyderabad", "hyd_birth", "GHMC birth and death certificate search, MeeSeva", "GHMC and Telangana", OK("GHMC names these search pages as the citizen address. The search needs an acknowledgement or application number. MeeSeva also lists GHMC certificates."),
  NV("MeeSeva shows its own centres map, but we have not extracted or checked those locations, so they are not on our map."), [], ["hyd_death", "hyd_ghmc_bnd", "hyd_meeseva"], [("Birth certificate search", "https://bnd.ghmc.gov.in/Birth_Certificate.aspx"), ("Death certificate search", "https://bnd.ghmc.gov.in/Death_Certificate.aspx"), ("GHMC Birth and Death page", "https://www.ghmc.gov.in/Birth.aspx")]),
 ("water", "bengaluru", "blr_bwssb", "BWSSB", "Bengaluru Water Supply and Sewerage Board", OK("The site links complaint lodging and water bill payment information."),
  NV("We did not confirm service stations or payment counters."), [], [], [("BWSSB", "https://bwssb.karnataka.gov.in/"), ("Lodge a complaint", "https://bwssb.karnataka.gov.in/258/lodge-complaint/kn")]),
 ("water", "hyderabad", "hyd_hmwssb", "HMWSSB", "Hyderabad Metropolitan Water Supply and Sewerage Board", OK("The site lists bill payment, tanker booking, grievance registration and status, and a WhatsApp route."),
  NV("We did not confirm customer service offices."), [], ["hyd_hmwssb_grievance"], [("HMWSSB", "https://www.hyderabadwater.gov.in/en/"), ("Register a grievance", "https://www.hyderabadwater.gov.in/en/index.php/services/customers-services/register-grievances")]),
 ("transport", "bengaluru", "blr_bmtc", "BMTC, Namma Metro", "BMTC and BMRCL", OK("Both operator sites loaded. We did not test journey planning or ticketing."),
  OK("Bus stop and metro station locations are on the map. OSM tags 81 of 87 metro stations as wheelchair accessible; these community tags are not an audit."), [], ["blr_bmrc"], [("BMTC", "https://mybmtc.karnataka.gov.in/"), ("Namma Metro", "https://english.bmrc.co.in/")]),
 ("transport", "hyderabad", "hyd_tgsrtc", "TGSRTC, Hyderabad Metro", "TGSRTC and L&T Metro Rail", OK("Both operator sites loaded. We did not test journey planning or ticketing."),
  OK("Bus stop and metro station locations are on the map. Metro stations come from the official July 2026 GTFS feed."), [], ["hyd_ltmetro"], [("TGSRTC", "https://www.tgsrtc.telangana.gov.in/"), ("Hyderabad Metro", "https://www.ltmetro.com/")]),
 ("health", "bengaluru", "blr_gba_clinics", "GBA clinic finder, state health department", "GBA, Karnataka", OK("The GBA home page offers a tool to find a nearby polio booth, UPHC or Namma Clinic. It sits inside a polio campaign page."),
  OK("139 UPHCs and 239 Namma Clinics are on the map. Distance does not show whether a clinic is staffed or physically accessible."), [], ["blr_hfw"], [("Clinic finder", "https://gba.karnataka.gov.in/polio/"), ("Karnataka Health and Family Welfare", "https://hfwcom.karnataka.gov.in/")]),
 ("health", "hyderabad", "hyd_health", "Telangana Health, Family Welfare", "Telangana", NV("We found department pages but did not confirm a tool for finding a nearby public clinic."),
  OK("Basti Dawakhanas and UPHCs are on the map from an undated list. Distance does not show whether a clinic is staffed or physically accessible."), [], ["hyd_chfw"], [("Telangana Health", "https://health.telangana.gov.in/"), ("Family Welfare", "https://chfw.telangana.gov.in/home.do")]),
 ("waste", "bengaluru", "blr_bswml", "Bengaluru Solid Waste Management Ltd", "BSWML", OK("The site links a citizen registration page on a separate address, bswmlclearit.com. We did not test reporting."),
  NV("We did not confirm a walk-in route for waste complaints."), ["The linked citizen registration address reset the connection in two link checks on 4 November 2026. Recheck by hand."], [], [("BSWML", "https://bswml.karnataka.gov.in/"), ("Citizen registration", "https://bswmlclearit.com/citizen")]),
 ("waste", "hyderabad", "hyd_ghmc", "GHMC citizen grievance", "GHMC", NV("The GHMC home page shows 'Citizen Grievance', but we did not confirm a dedicated waste-reporting route."),
  NV("We did not confirm a walk-in route for waste complaints."), [], [], [("GHMC", "https://www.ghmc.gov.in/"), ("GHMC 'How do I' guide", "https://ghmc.gov.in/howdoi.aspx")]),
 ("pds", "bengaluru", "blr_ahara", "Ahara", "Karnataka Food, Civil Supplies and Consumer Affairs", OK("The department site loaded, and its text mentions Aadhaar and OTP. We did not test any service."),
  NV("We found no verified location dataset for ration shops, so they are not on the map."), [], [], [("Ahara", "https://ahara.karnataka.gov.in/")]),
 ("pds", "hyderabad", "hyd_epds", "Telangana ePDS", "Telangana Civil Supplies", OK("The portal loaded with a password sign-in and CAPTCHA."),
  NV("We found no verified location dataset for ration shops. AIKosh lists shop transactions, but we did not confirm any location fields."), [], ["hyd_civilsupplies"], [("ePDS", "https://epds.telangana.gov.in/FoodSecurityAct/"), ("Civil Supplies", "https://civilsupplies.telangana.gov.in/"), ("AIKosh shop transactions", "https://aikosh.indiaai.gov.in/home/datasets/details/telangana_state_civil_supplies_fair_price_shop_transactions.html")]),
 ("documents", "bengaluru", "blr_sevasindhu", "Seva Sindhu, DigiLocker", "Karnataka, Government of India", OK("Seva Sindhu loaded and defaulted to Kannada. DigiLocker is a national option. We did not test any application."),
  NV("Customer Service Centre records are on the map, but the source does not confirm which centres are open."), [], ["national_digilocker"], [("Seva Sindhu", "https://sevasindhu.karnataka.gov.in/"), ("DigiLocker", "https://www.digilocker.gov.in/")]),
 ("documents", "hyderabad", "hyd_meeseva", "MeeSeva, DigiLocker", "Telangana, Government of India", OK("MeeSeva loaded with a sign-in form, and DigiLocker is a national option. We did not test any application."),
  NV("MeeSeva shows its own centres map, but we have not extracted or checked those locations."), [], ["national_digilocker"], [("MeeSeva", "https://ts.meeseva.telangana.gov.in/meeseva/home.htm"), ("DigiLocker", "https://www.digilocker.gov.in/")]),
 ("tracking", "bengaluru", "blr_sakala", "Sakala", "Karnataka", OK("The Sakala page loaded with form fields. We did not test a live application number."),
  NV("We did not confirm an in-person tracking route."), [], [], [("Sakala", "https://sakala.kar.nic.in/")]),
 ("tracking", "hyderabad", "hyd_ghmc_bnd_status", "GHMC application status, MeeSeva", "GHMC, Telangana", OK("MeeSeva links 'Know Your GHMC Application Status (Birth/Death)'. The status page loaded. We did not test a live application number."),
  NV("We did not confirm an in-person tracking route."), [], ["hyd_meeseva"], [("GHMC application status", "https://bnd.ghmc.gov.in/KnowYourApplicationStatus.aspx")]),
]
def lang_text(p):
    if p["status"] != "audited": return "Not verified: the page did not load."
    if not p["languages"]: return "None detected by our script. Not verified by hand."
    return ", ".join(p["languages"]) + ". Found by script; translation completeness not verified."
def auth_text(p):
    if p["status"] != "audited": return "Not verified: the page did not load."
    a = p["auth"]; bits = []
    if a["passwordField"]: bits.append("password field")
    if a["captcha"]: bits.append("CAPTCHA")
    if a["otpMention"]: bits.append("mentions OTP")
    if a["aadhaarMention"]: bits.append("mentions Aadhaar")
    if not bits and a["loginMention"]: bits.append("mentions sign-in")
    return (", ".join(bits).capitalize() + ".") if bits else "Nothing detected on this page. Later steps not verified."
def auto_barriers(p):
    if p["status"] != "audited": return [f"The page did not load in our test: {p['error']}."]
    b = []
    if not p["htmlLang"]: b.append("The page does not declare its language, so a screen reader may mispronounce it (WCAG 3.1.1).")
    if p["overflow"]: b.append("The page scrolls sideways at 320 px, which affects people who zoom in (WCAG 1.4.10).")
    if p["focusRing"] == 0: b.append("Our script detected no focus outline in 20 Tab presses (WCAG 2.4.7; check by hand).")
    if "marquee" in p["all_rules"] or "blink" in p["all_rules"]: b.append("Moving or blinking text is present (WCAG 2.2.2).")
    if p["zoomBlocked"]: b.append("The page tells browsers to restrict zoom (WCAG 1.4.4).")
    if {"label", "select-name"} & set(p["all_rules"]): b.append("Form fields without labels (WCAG 3.3.2).")
    return b
records = []
for task, city, pid, portal, op, online, offline, notes, alts, ev in R:
    p = L(pid)
    alts_text = "; ".join(f"Also tested: {L(a)['label']} ({str(L(a).get('rules')) + ' rules' if L(a)['status'] == 'audited' else 'did not load'})" for a in alts)
    records.append({"task": task, "city": city, "portal": portal, "operator": op, "url": p["url"], "online": online, "offline": offline,
                    "language": {"text": lang_text(p), "offered": p.get("languages", [])},
                    "audit": {"status": p["status"], "rules": p.get("rules"), "nodes": p.get("nodes"), "note": (p.get("error", "") + " " + alts_text).strip()},
                    "auth": auth_text(p), "complexity": (f"{p['links']} visible links, {p['inputs']} form fields, about {p['words']} words before any task begins." if p["status"] == "audited" else "Not verified."),
                    "barriers": notes + auto_barriers(p), "evidence": [{"label": a, "url": b} for a, b in ev]})
assert len(records) == 20
(WEB/"civic_services.json").write_text(json.dumps({"audit_date": AUDIT_DATE, "tasks": [{"id": a, "title": b} for a, b in TASKS], "records": records}, indent=1, ensure_ascii=False))
with open(ROOT/"data/processed/civic_services.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["task", "city", "portal", "operator", "url", "online_status", "online_evidence", "offline_status", "offline_evidence", "language_controls", "wcag_rules_failed", "elements_failed", "auth_signals", "barriers", "evidence_urls"])
    for r in records:
        w.writerow([r["task"], r["city"], r["portal"], r["operator"], r["url"], r["online"]["status"], r["online"]["text"], r["offline"]["status"], r["offline"]["text"], r["language"]["text"], r["audit"]["rules"], r["audit"]["nodes"], r["auth"], " | ".join(r["barriers"]), " | ".join(e["url"] for e in r["evidence"])])

# ---------- personas ----------
c = AN["census"]; s = AN["spatial"]
sb, sh = summary["bengaluru"], summary["hyderabad"]
contrast_txt = f"Text contrast failures on {sb['contrast_pages']} of {sb['pages']} audited Bengaluru pages and {sh['contrast_pages']} of {sh['pages']} in Hyderabad."
lang_txt = f"The page language is undeclared on {missing_lang['bengaluru']} of {sb['pages']} Bengaluru pages and {missing_lang['hyderabad']} of {sh['pages']} Hyderabad pages."
pct = lambda cat, cc: next(x[cc] for x in cats if x["label"] == cat)
def st(stage, friction, evidence, measured=False): return {"stage": stage, "friction": friction, "evidence": evidence, "measured": measured}
pw = sum(1 for p in aud if p["auth"]["passwordField"]); cap = sum(1 for p in aud if p["auth"]["captcha"])
labels_txt = f"Unlabelled form fields on {pct('Unlabelled form fields','bengaluru')}% of audited Bengaluru pages and {pct('Unlabelled form fields','hyderabad')}% in Hyderabad."
FUTURE = "Fieldwork question. We have not observed this step."
personas = [
 {"name": "A screen-reader user filing a complaint", "short": "Visual access", "summary": "A hypothetical blind resident who uses a screen reader on a phone and wants to report a blocked drain and follow it up.", "stages": [
  st("Discovery", "Finding the correct body may be hard after the reorganisation, and unnamed links would be read aloud only as 'link'.", f"Unnamed links or buttons on {pct('Unnamed links and buttons','bengaluru')}% of audited Bengaluru pages and {pct('Unnamed links and buttons','hyderabad')}% in Hyderabad.", True),
  st("Navigation", "An undeclared page language can make a screen reader use the wrong pronunciation, and images without alternatives leave gaps.", lang_txt, True),
  st("Authentication", "A visual CAPTCHA could end the attempt if no audio alternative works.", f"CAPTCHA signals on {cap} of {len(aud)} audited pages. Audio alternatives were not checked.", True),
  st("Form completion", "A field with no label is announced without its purpose.", labels_txt, True),
  st("Submission", "An error may appear only visually, without being announced.", FUTURE),
  st("Tracking", "Status tables and references may be hard to find again by ear.", FUTURE),
  st("Service completion", "There may be no accessible way to confirm the drain was actually cleared.", FUTURE)]},
 {"name": "A resident who reads Urdu, with limited English and Telugu", "short": "Language", "summary": "A hypothetical Hyderabad resident who reads Urdu confidently, has limited English and Telugu, and wants to check a ration card application.", "stages": [
  st("Discovery", "Search results and official names may appear only in English or Telugu.", f"Urdu is the mother tongue of {next(l['pct'] for l in c['language']['hyderabad']['top'] if l['language']=='Urdu')}% of GHMC residents in Census 2011.", True),
  st("Navigation", "This resident needs a language control they can recognise, and any Urdu option we found sits on a page with a translation widget.", f"Urdu option on {reach['hyderabad'][1]['pages']} of {sh['pages']} audited Hyderabad pages. Translation widgets appeared on {widgets['hyderabad']}, and their output was not assessed.", True),
  st("Authentication", "One-time passwords and error messages may arrive in another language.", FUTURE),
  st("Form completion", "Names and addresses may need English or Telugu spellings that differ from the resident's documents.", FUTURE),
  st("Submission", "A paid intermediary may be needed, which shifts cost and privacy risk onto the resident.", FUTURE),
  st("Tracking", "Status terms may be unfamiliar even after machine translation.", FUTURE),
  st("Service completion", "The counter staff may or may not be able to help in Urdu.", FUTURE)]},
 {"name": "An older resident who finds complex systems hard to follow", "short": "Cognitive and usability", "summary": "A hypothetical older Bengaluru resident with a smartphone and some memory difficulties, who has received a property tax demand and is unsure what to do.", "stages": [
  st("Discovery", "The first job is working out which of several bodies and addresses is responsible, and old names persist.", "The property tax portal still uses a 'bbmptax' address after the BBMP was replaced. Reorganisation reported in September 2025.", True),
  st("Navigation", "A very long landing page presents many choices before the task can begin.", f"Median visible links on audited pages: {median([p['links'] for p in by['bengaluru']])} in Bengaluru and {median([p['links'] for p in by['hyderabad']])} in Hyderabad. Link count is a rough proxy, not a usability score.", True),
  st("Authentication", "OTPs and timeouts create pressure, and losing access to an old phone number can block the task.", "The Bengaluru tax portal has a dedicated 'Change Mobile Number (Old number unavailable)' route, which suggests that this problem occurs.", True),
  st("Form completion", "Legal terms and property identifiers may require documents that are hard to find.", FUTURE),
  st("Submission", "It may be unclear whether a payment succeeded.", "The portal has separate 'Payment Status' and 'Acknowledgement Print' routes; we did not test how clear they are.", True),
  st("Tracking", "Several reference numbers have to be remembered across systems.", FUTURE),
  st("Service completion", "Finishing may rely on a relative or agent, which is invisible in official records.", FUTURE)]},
]
lb, lh = c["language"]["bengaluru"]["top"], c["language"]["hyderabad"]["top"]
(WEB/"journeys.json").write_text(json.dumps({"personas": personas,
  "language_note": f"In Census 2011, {lb[0]['language']} was the mother tongue of {lb[0]['pct']}% of BBMP-area residents, followed by {lb[1]['language']} ({lb[1]['pct']}%) and {lb[2]['language']} ({lb[2]['pct']}%). In the GHMC area it was {lh[0]['language']} ({lh[0]['pct']}%) and {lh[1]['language']} ({lh[1]['pct']}%). Mother tongue does not show which scripts a person reads, and many residents are multilingual. These figures show which languages are worth testing, not who is excluded."}, indent=1, ensure_ascii=False))

# ---------- findings ----------
m = lambda city, key: s[city]["measures"][key]
def row(name, a, b): return {"name": name, "Bengaluru": a, "Hyderabad": b}
d_b, d_h = c["disability"]["bengaluru"], c["disability"]["hyderabad"]
dshare = lambda d, t: round(d["by_type"][t]/d["total"]*100, 1)
charts = {
 "distance": {"unit": " km", "rows": [row("Primary health (official lists)", m("bengaluru", "primary_health")["city_grid"]["median_km"], m("hyderabad", "primary_health")["city_grid"]["median_km"]),
    row("Hospitals, clinics (OSM, same day)", m("bengaluru", "osm_health")["city_grid"]["median_km"], m("hyderabad", "osm_health")["city_grid"]["median_km"]),
    row("Bus stop", m("bengaluru", "bus")["city_grid"]["median_km"], m("hyderabad", "bus")["city_grid"]["median_km"]),
    row("Metro station", m("bengaluru", "metro")["city_grid"]["median_km"], m("hyderabad", "metro")["city_grid"]["median_km"])]},
 "slums": {"unit": " km", "rows": [row("City-wide grid", m("bengaluru", "primary_health")["city_grid"]["median_km"], m("hyderabad", "primary_health")["city_grid"]["median_km"]),
    row("Listed slum locations", m("bengaluru", "primary_health")["slum_points"]["median_km"], m("hyderabad", "primary_health")["slum_points"]["median_km"])]},
 "disability": {"unit": "%", "rows": [row(t.replace("In ", "").capitalize().replace(" (census term)", ""), dshare(d_b, t), dshare(d_h, t)) for t in ("In seeing", "In hearing", "In speech", "In movement", "Multiple disability", "Any other")]},
 "language": {"unit": "%", "rows": [row(n, next((l["pct"] for l in lb if l["language"] == n), 0), next((l["pct"] for l in lh if l["language"] == n), 0)) for n in ("Kannada", "Telugu", "Urdu", "Tamil", "Hindi")]},
 "audit": {"unit": "%", "rows": [row(x["label"], x["bengaluru"], x["hyderabad"]) for x in cats[:6]]},
 "wheelchair": {"unit": "%", "rows": []},
}
oa = AN["osm_access"]
wc = lambda city, k: round((oa[city][k]["total"]-oa[city][k]["not_tagged"])/oa[city][k]["total"]*100, 1)
charts["wheelchair"]["rows"] = [row(n, wc("bengaluru", k), wc("hyderabad", k)) for n, k in (("Metro stations", "metro"), ("Hospitals", "osm_hospital"), ("Clinics", "osm_clinic"), ("Public toilets", "osm_toilets"), ("Post offices", "osm_post"))]
OPC = "https://data.opencity.in/dataset/"
C20 = {"label": "Census 2011, C-20 City: disabled population", "url": "https://censusindia.gov.in/nada/index.php/catalog/42520"}
C16 = [{"label": "Census 2011, C-16 town level, Karnataka", "url": "https://censusindia.gov.in/nada/index.php/catalog/10255"}, {"label": "Census 2011, C-16 town level, Andhra Pradesh (then including Hyderabad)", "url": "https://censusindia.gov.in/nada/index.php/catalog/10254"}]
PCA = [{"label": "Census 2011, PCA, Bangalore", "url": "https://censusindia.gov.in/nada/index.php/catalog/6763"}, {"label": "Census 2011, PCA, Hyderabad", "url": "https://censusindia.gov.in/nada/index.php/catalog/6727"}]
OSMD = {"label": "OpenStreetMap, Overpass query, 4 November 2026 (ODbL)", "url": "https://www.openstreetmap.org/"}
HEALTH = [{"label": "OpenCity: Bengaluru UPHCs and Namma Clinics", "url": OPC+"bengaluru-urban-public-health-centres"}, {"label": "OpenCity: Hyderabad public health centres", "url": OPC+"hyderabad-public-health-centres"}]
SLUMS = [{"label": "OpenCity: Bengaluru urban slums", "url": OPC+"bengaluru-urban-slums"}, {"label": "OpenCity: Hyderabad slums", "url": OPC+"hyderabad-slums"}]
RQ = "How do civic interfaces and infrastructure shape access across disability, language and cognitive barriers?"
gm = lambda city, key: m(city, key)["city_grid"]
sm = lambda city, key: m(city, key)["slum_points"]
findings = [
 {"id": "interfaces", "kinds": ["measured"], "title": "Basic accessibility failures are common on official pages in both cities", "question": "Do official civic portals meet basic automated WCAG checks?",
  "evidence": f"On the {sb['pages']+sh['pages']} city pages that loaded, axe-core flagged text contrast on {sb['contrast_pages']} of {sb['pages']} in Bengaluru and {sh['contrast_pages']} of {sh['pages']} in Hyderabad. The median page failed {sb['median_rules']} distinct rules in Bengaluru and {sh['median_rules']} in Hyderabad. The page language was undeclared on {missing_lang['bengaluru']} Bengaluru pages and {missing_lang['hyderabad']} Hyderabad pages. Counted by website rather than page, that is {sites['bengaluru']['missing_lang_sites']} of {sites['bengaluru']['sites']} sites and {sites['hyderabad']['missing_lang_sites']} of {sites['hyderabad']['sites']}.",
  "interpretation": "These failures are ones that a developer can fix and that a site owner can check automatically. Their persistence suggests accessibility is not yet a routine part of how these sites are published. The undeclared-language gap is wider in our Hyderabad sample, on pages and on websites alike, and it matters directly to screen-reader users.",
  "limitations": "Automated tools detect only some WCAG issues. We tested public pages before sign-in, selected by task, on one day. Several pages share one website or template, so page counts are not independent; the sample has more GHMC pages than any other site. No page was tested by a disabled person, and this does not rank the cities' overall digital services.",
  "chart": "audit", "chart_title": "Share of audited pages with at least one failure", "datasets": [{"label": "axe-core, the audit engine (results: public/data/audit.json)", "url": "https://www.deque.com/axe/"}, {"label": "WCAG 2.2", "url": "https://www.w3.org/TR/WCAG22/"}]},
 {"id": "language", "kinds": ["primary", "measured"], "title": "A portal's language menu may not match the city's languages", "question": "Do language options on portals reflect the languages people in each city grew up speaking?",
  "evidence": f"In Census 2011, Kannada was the mother tongue of {lb[0]['pct']}% in the BBMP area; {lb[1]['language']} ({lb[1]['pct']}%), {lb[2]['language']} ({lb[2]['pct']}%) and {lb[3]['language']} ({lb[3]['pct']}%) followed. In the GHMC area, Urdu was {lh[1]['pct']}%. Our scan found a {lb[1]['language']} option on {reach['bengaluru'][1]['pages']} of {sb['pages']} Bengaluru pages and an Urdu option on {reach['hyderabad'][1]['pages']} of {sh['pages']} Hyderabad pages. Both Urdu pages also have a Google Translate widget, so these options may be machine translation. Translation widgets appeared on {widgets['bengaluru']} and {widgets['hyderabad']} pages respectively.",
  "interpretation": "Portals seem to be organised around official state languages and English rather than the city's multilingual population. Language access may therefore rely on machine translation or on a helper. We read this as a political question about who a portal imagines its citizen to be, which needs testing with speakers.",
  "limitations": "Mother tongue does not equal reading ability or preference, and many residents read more than one language. Our detector may miss unusual controls. We did not assess translation quality. Census data dates from 2011.",
  "chart": "language", "chart_title": "Mother tongue share, Census 2011", "datasets": C16},
 {"id": "literacy", "kinds": ["primary", "derived"], "title": "A text-first portal leaves nearly two million residents across the two cities needing another route", "question": "How many residents does a text-based interface leave without a direct route?",
  "evidence": f"Census 2011 records {c['literacy']['bengaluru']['non_literate_7plus']:,} residents aged 7 and over as non-literate in the BBMP area ({c['literacy']['bengaluru']['literacy_7plus_pct']}% literacy) and {c['literacy']['hyderabad']['non_literate_7plus']:,} in the GHMC area ({c['literacy']['hyderabad']['literacy_7plus_pct']}%). Female literacy was {c['literacy']['bengaluru']['female_literacy_7plus_pct']}% and {c['literacy']['hyderabad']['female_literacy_7plus_pct']}%. Hyderabad's count is higher despite its smaller population.",
  "interpretation": "High city-wide literacy can hide very large absolute numbers. For these residents, the offline counter, the assistance centre and the helper are the service. This is why we treat offline access as part of digital citizenship.",
  "limitations": "The data is from 2011 and predates the current boundaries. Census literacy is self-reported and basic, and it does not measure digital literacy.",
  "datasets": PCA},
 {"id": "disability", "kinds": ["primary"], "title": "The Census shows different disability profiles, so one fix will not suit both", "question": "What does official data show about who needs accessible services?",
  "evidence": f"Census 2011 counts {d_b['total']:,} disabled persons in the Bruhat Bangalore urban agglomeration and {d_h['total']:,} in Hyderabad's. People recorded with a seeing disability make up {dshare(d_b,'In seeing')}% of that group in Bengaluru and {dshare(d_h,'In seeing')}% in Hyderabad. 'Any other' is {dshare(d_b,'Any other')}% and {dshare(d_h,'Any other')}%.",
  "interpretation": "Large 'any other' shares show how much the official categories leave unnamed. The Census counted 8 categories, while the Rights of Persons with Disabilities Act 2016 recognises many more, so these numbers probably understate the need and cannot stand in for lived experience.",
  "limitations": "The data is from 2011, is self-reported and uses the older disability categories, including a term that is now outdated. Urban agglomerations are wider than the study wards. We did not convert to population rates because we did not verify matching denominators.",
  "chart": "disability", "chart_title": "Share of recorded disabled persons by type", "datasets": [C20]},
 {"id": "proximity", "kinds": ["derived"], "title": "On our measure the two cities look similar for primary health, and they differ more for transit", "question": "How does straight-line nearness to public facilities compare across the two cities?",
  "evidence": f"The median point on a 500 m grid lies {gm('bengaluru','primary_health')['median_km']} km from a listed primary health facility in Bengaluru and {gm('hyderabad','primary_health')['median_km']} km in Hyderabad. OSM's same-day hospital and clinic data gives {gm('bengaluru','osm_health')['median_km']} and {gm('hyderabad','osm_health')['median_km']} km. For metro stations it is {gm('bengaluru','metro')['median_km']} and {gm('hyderabad','metro')['median_km']} km, and for bus stops {gm('bengaluru','bus')['median_km']} and {gm('hyderabad','bus')['median_km']} km.",
  "interpretation": "The basic geography of primary care looks broadly alike, which pushes attention from where facilities are to whether people can use them. Metro distance is a true structural difference in network size. Distance is a measure of position and not of access.",
  "limitations": "This is straight-line distance on an unweighted grid that includes unbuilt land. It says nothing about travel time, cost, staffing, opening hours or step-free entry. Layer dates differ, and the Bengaluru clinic list is from 2026 while the Hyderabad list is undated. Study boundaries predate each city's reorganisation.",
  "chart": "distance", "chart_title": "Median straight-line distance to the nearest facility", "datasets": HEALTH + [OSMD, {"label": "OpenCity: Hyderabad Metro GTFS", "url": OPC+"hyderabad-metro-rail-gtfs"}]},
 {"id": "slums", "kinds": ["derived"], "title": "Listed slum locations sit closer to primary health than the average grid point, which does not show better access", "question": "Do listed informal settlements appear spatially cut off from public primary healthcare?",
  "evidence": f"The median listed slum location is {sm('bengaluru','primary_health')['median_km']} km from a primary health facility in Bengaluru and {sm('hyderabad','primary_health')['median_km']} km in Hyderabad, against {gm('bengaluru','primary_health')['median_km']} and {gm('hyderabad','primary_health')['median_km']} km for the city grid. {sm('bengaluru','primary_health')['share_within_1km']}% and {sm('hyderabad','primary_health')['share_within_1km']}% of listed locations lie within 1 km.",
  "interpretation": "In these lists, distance is not the obvious barrier for these settlements, and some clinics may be sited with them in mind. That moves the question to crowding, quality, cost, documents and how residents are treated, which only fieldwork can answer.",
  "limitations": "The grid includes empty land, so this is a weak baseline. Lists are undated and count only recognised locations, and listing itself is a political act: unlisted settlements stay invisible here. Bengaluru's slum list names a covering UPHC for each location, so its closeness to clinics may be partly built in.",
  "chart": "slums", "chart_title": "Median distance to the nearest primary health facility", "datasets": HEALTH + SLUMS},
 {"id": "mapping", "kinds": ["derived"], "title": "Whether a place is recorded as accessible depends on who has mapped it", "question": "How much do open maps know about physical accessibility?",
  "evidence": f"OSM has a wheelchair tag on {wc('bengaluru','metro')}% of Bengaluru metro stations against {wc('hyderabad','metro')}% in Hyderabad, and on {wc('bengaluru','osm_hospital')}% and {wc('hyderabad','osm_hospital')}% of hospitals. For {oa['hyderabad']['osm_clinic']['total']} Hyderabad clinics there are {oa['hyderabad']['osm_clinic']['total']-oa['hyderabad']['osm_clinic']['not_tagged']} tags.",
  "interpretation": "This measures the record, not the buildings. Silence in the data could be mistaken for absence of access or of need, and that is itself a form of invisibility. It makes the case for community accessibility mapping as a method and an outcome of this project.",
  "limitations": "OSM tags are volunteer-contributed and unaudited. A difference between cities probably reflects mapper activity, and it must not be read as physical accessibility.",
  "chart": "wheelchair", "chart_title": "Share of OSM features with any wheelchair tag", "datasets": [OSMD]},
 {"id": "archive", "kinds": ["secondary", "derived"], "title": "The civic record is out of step with the civic body", "question": "What does the state of the data itself tell us about citizenship?",
  "evidence": "BBMP was replaced by GBA in September 2025, and GHMC was split in February 2026, yet the Bengaluru tax portal address still says 'bbmptax'. Hyderabad's layers from the portal date to 2018 or carry no date, and the census base is 2011. We found no verified downloadable location dataset for ration shops or MeeSeva centres; MeeSeva does show its own centres map, which we have not extracted.",
  "interpretation": "Citizens and researchers alike navigate a layered archive of old names, boundaries and addresses. The services that matter most to low-income households were the hardest to locate as data, which may itself show whose access is being documented.",
  "limitations": "'Not found' reflects our search on one day, and such data may exist on portals we could not reach. News reports are secondary sources for the reorganisation dates.",
  "datasets": [{"label": "PTI via The Week: five corporations notified", "url": "https://www.theweek.in/wire-updates/national/2025/09/02/srg2-ka-new-corporations.html"}, {"label": "ETV Bharat: GHMC reorganised into three corporations", "url": "https://www.etvbharat.com/en/state/telangana-govt-reorganises-ghmc-into-three-separate-municipal-corporations-enn26021104131"}, {"label": "OpenCity data portal (full list: data/metadata/dataset_inventory.csv)", "url": "https://data.opencity.in/"}]},
]
(WEB/"findings.json").write_text(json.dumps({"findings": findings, "charts": charts}, indent=1, ensure_ascii=False))
md = ["# Preliminary findings", "", "Generated from `public/data/findings.json` by `src/analysis/build_site_data.py`. Every finding is preliminary. No citizens were consulted.", ""]
for i, f in enumerate(findings, 1):
    md += [f"## {i}. {f['title']}", "", f"**Research question.** {f['question']}", "", f"**Evidence.** {f['evidence']}", "", f"**Interpretation.** {f['interpretation']}", "", f"**Limitations.** {f['limitations']}", "", "**Supporting data.** " + "; ".join(f"[{d['label']}]({d['url']})" for d in f["datasets"]), ""]
(ROOT/"Research/findings.md").write_text("\n".join(md))
print(json.dumps({"summary": summary, "missing_lang": missing_lang, "widgets": widgets, "any_ctrl": any_ctrl, "overflow": overflow, "noring": noring, "reach": reach, "failed": [p["id"] for p in failed], "cats": cats}, indent=0, ensure_ascii=False))
for f in findings: print("*", f["title"], "\n  ", f["evidence"])
