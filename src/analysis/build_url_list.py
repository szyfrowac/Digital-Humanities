#!/usr/bin/env python3
"""Master list of audit URLs per service. Load-tests each in Chrome, then writes data/metadata/audit_url_list.csv.
Run from project root: python3 -I src/analysis/build_url_list.py"""
import csv, json, pathlib, subprocess
G = "Linked from GHMC home page"; B = "Linked from Bengaluru property tax portal"; S = "Found by search"; A = "Audited earlier"; SV = "Listed on Seva Sindhu"
# service, city, role, page, url, how found, note.
# Main = task-specific page to audit. Alternate = another official route. Reference = not a task page.
ME = "Listed on MeeSeva"
MH = "https://ts.meeseva.telangana.gov.in/meeseva/home.htm"
MN = "No direct address: open MeeSeva, choose Services, then GHMC. Its service list refused a direct load."
U = [
 ("Property tax payment", "Hyderabad", "Main", "Property tax payment form", "https://onlinepayments.ghmc.gov.in/", G, "Form asks for PTI or registered mobile number."),
 ("Property tax payment", "Hyderabad", "Alternate", "MeeSeva: GHMC PROPERTY TAX", MH, ME, MN),
 ("Property tax payment", "Bengaluru", "Main", "Property tax lookup and filing form", "https://bbmptax.karnataka.gov.in/", A, "The portal's first page is the task form: application or PID number, then owner name."),
 ("Property tax payment", "Bengaluru", "Alternate", "Demand notice payment", "https://bbmptax.karnataka.gov.in/Notices/NoticesPayment_Trans.aspx", B, "Only for people who received a notice. Uses CAPTCHA."),
 ("Citizen grievance", "Hyderabad", "Main", "Lodge grievance: mobile OTP step", "https://igs.ghmc.gov.in/operator/send_otp_mobile", G, "First step of filing a complaint."),
 ("Citizen grievance", "Hyderabad", "Alternate", "Grievance sign-in page", "https://igs.ghmc.gov.in/", A, "Has password and CAPTCHA fields. The sign-in may be for staff; not confirmed."),
 ("Citizen grievance", "Bengaluru", "Main", "Sahaaya complaints", "https://bbmp.sahaaya.in/", A, "Certificate error. GBA now links Sahaaya 2.0 as an Android app."),
 ("Citizen grievance", "Bengaluru", "Alternate", "iPGRS, Karnataka grievance portal", "https://ipgrs.karnataka.gov.in/home/index", SV, "Statewide, not city-specific."),
 ("Birth certificate", "Hyderabad", "Main", "Birth certificate search", "https://bnd.ghmc.gov.in/Birth_Certificate.aspx", "Named as the citizen address on GHMC's Birth and Death page", "Needs an acknowledgement or application number."),
 ("Birth certificate", "Hyderabad", "Alternate", "MeeSeva: BIRTH AND DEATH CERTIFICATE GHMC", MH, ME, MN),
 ("Death certificate", "Hyderabad", "Main", "Death certificate search", "https://bnd.ghmc.gov.in/Death_Certificate.aspx", "Named as the citizen address on GHMC's Birth and Death page", ""),
 ("Birth/death certificate", "Bengaluru", "Main", "e-Janma: download certificate", "https://ejanma.karnataka.gov.in/frmDownloadCertificate.aspx", "Linked from e-Janma home", "One page covers both birth and death."),
 ("Birth/death certificate", "Bengaluru", "Alternate", "e-Janma: birth and death verification", "https://ejanma.karnataka.gov.in/frmBirthDeathSearch.aspx", "Linked from e-Janma home", ""),
 ("Trade licence", "Hyderabad", "Main", "New trade licence application", "https://sa.ghmc.gov.in/TradeNewApplicationEntry.aspx", G, "Starts with mobile number."),
 ("Trade licence", "Hyderabad", "Alternate", "Trade licence payment", "https://onlinepayments.ghmc.gov.in/TLTax/TLPayment", G, ""),
 ("Trade licence", "Hyderabad", "Alternate", "MeeSeva: GHMC TRADE LICENCE FRESH APPLICATIONS", MH, ME, MN),
 ("Trade licence", "Bengaluru", "Main", "New trade licence application, sign-in step", "https://sevaone.karnataka.gov.in/services/directApply.do?serviceId=1649", "Apply Online link from Seva Sindhu's BBMP list", "Redirects to a Service Plus sign-in page with CAPTCHA."),
 ("Trade licence", "Bengaluru", "Alternate", "GBA trade licence service", "https://trade.bbmpgov.in/", "Address tried by us; official source not confirmed", "Page title says Unavailable."),
 ("Building plan", "Hyderabad", "Main", "BuildNow application portal", "https://app.buildnow.telangana.gov.in/", "Linked from BuildNow home", ""),
 ("Building plan", "Hyderabad", "Alternate", "BuildNow citizen search", "https://app.buildnow.telangana.gov.in/citizen-search", "Linked from BuildNow home", ""),
 ("Building plan", "Bengaluru", "Main", "Building plan approval sign-in", "https://bpas.bbmpgov.in/BPAMSClient4/Default.aspx", "Apply Online link from Seva Sindhu's BBMP list", "Redirects to NewDefault1.aspx; has CAPTCHA."),
 ("Pet dog licence", "Hyderabad", "Main", "Pet licence: citizen mobile sign-in", "https://petanimal.ghmc.gov.in/Login/Login", G, "OTP step."),
 ("Pet dog licence", "Bengaluru", "Main", "No web page found", "", "Not in Seva Sindhu's BBMP list; search found only proposed GBA rules", "Confirm with GBA."),
 ("E-waste doorstep pickup", "Hyderabad", "Main", "No web page found", "", "Reports describe the MyGHMC app and QR codes", "Not in MeeSeva's GHMC keyword matches."),
 ("E-waste doorstep pickup", "Bengaluru", "Main", "No web page found", "", "Not in Seva Sindhu's BBMP list; search found drop-off points run by others", "BSWML's DClutter app is for bulky waste."),
 ("Waste complaint (related)", "Bengaluru", "Alternate", "BSWML: register complaint", "https://bswml.karnataka.gov.in/174/register-complaint/en", "Linked from BSWML home", "General waste, not e-waste."),
 ("Offline centres", "Hyderabad", "Reference", "MeeSeva Centres map", MH, ME, "Open MeeSeva, then Map View. Its address refuses a direct load."),
 ("Offline centres", "Bengaluru", "Reference", "Seva Sindhu service centres", "https://sevasindhu.karnataka.gov.in/Sevasindhu/Servicecenters", SV, ""),
 ("Service list", "Hyderabad", "Reference", "MeeSeva home", MH, A, "General portal page."),
 ("Service list", "Bengaluru", "Reference", "Seva Sindhu: department services", "https://sevasindhu.karnataka.gov.in/Sevasindhu/DepartmentServices", SV, "General portal page. Property tax and birth or death Apply Online links return to this list."),
 ("Home page", "Hyderabad", "Reference", "GHMC home", "https://www.ghmc.gov.in/", A, "General main page; listed in the course brief."),
 ("Home page", "Bengaluru", "Reference", "Greater Bengaluru Authority home", "https://gba.karnataka.gov.in/", A, "General main page; listed in the course brief."),
]
JS = r"""
import { chromium } from 'playwright';
const urls = JSON.parse(process.argv[2]); const out = {};
const b = await chromium.launch({ channel: 'chrome', headless: true });
for (const u of urls) { const p = await (await b.newContext()).newPage();
  try { const r = await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(1500);
    out[u] = { status: r.status(), title: (await p.title()).trim().slice(0, 70), final: p.url() }; }
  catch (e) { out[u] = { error: String(e.message).split('\n')[0].replace('page.goto: ', '').split(' at ')[0] }; }
  await p.close(); console.error(u, JSON.stringify(out[u]).slice(0, 110)); }
await b.close(); console.log(JSON.stringify(out));
"""
pathlib.Path("audit/.probe.mjs").write_text(JS)
urls = sorted({u[4] for u in U if u[4]})
res = subprocess.run(["node", ".probe.mjs", json.dumps(urls)], cwd="audit", capture_output=True, text=True, timeout=500)
pathlib.Path("audit/.probe.mjs").unlink()
P = json.loads(res.stdout)
LH = json.loads(pathlib.Path("data/raw/shared/lighthouse/summary.json").read_text())
scored = {v.get("requestedUrl"): v.get("score") for v in LH.values()} | {v.get("finalUrl"): v.get("score") for v in LH.values() if v.get("finalUrl")}
def state(u):
    if not u: return "No URL"
    p = P[u]
    if "error" in p: return "Failed: " + p["error"].replace("net::", "")
    if p["status"] >= 400: return f"HTTP {p['status']}"
    if any(w in p["title"].lower() for w in ("unavailable", "error", "not found")): return "Loads, but page title says: " + p["title"]
    return "Loads"
with open("data/metadata/audit_url_list.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["Service", "City", "Role", "Page", "URL", "How found", "Load test (Chrome, 4 Nov 2026)", "Page title", "Lighthouse score so far", "Tested with WAVE", "Note"])
    for s, c, r, pg, u, how, note in U:
        w.writerow([s, c, r, pg, u, how, state(u), P.get(u, {}).get("title", ""), scored.get(u, ""), "", note])
for s, c, r, pg, u, how, note in U:
    print(f"{r[:1]} {c[:3]} {s[:22]:22} {pg[:34]:34} {state(u)[:52]:52} LH={scored.get(u,'')}")
