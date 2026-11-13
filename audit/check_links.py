#!/usr/bin/env python3
"""Check every source URL cited on the site. TLS verified. Run from project root with python3 -I."""
import json, pathlib, ssl, urllib.request, re, concurrent.futures as cf
urls = set()
for f in ("civic_services.json", "findings.json", "layers.json"):
    t = pathlib.Path("public/data", f).read_text()
    urls |= set(re.findall(r'"(?:url|source_url)":\s*"(https?://[^"]+)"', t))
urls |= set(re.findall(r'href="(https?://[^"]+)"', pathlib.Path("src/app/pages/Overview.tsx").read_text()))
def chk(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 DH-Research"}), timeout=40, context=ssl.create_default_context())
        return u, r.status, ""
    except Exception as e:
        return u, getattr(e, "code", 0), f"{type(e).__name__}: {str(e)[:90]}"
with cf.ThreadPoolExecutor(6) as ex: res = sorted(ex.map(chk, urls), key=lambda x: (x[1] == 200, x[0]))
pathlib.Path("data/metadata/link_check.json").write_text(json.dumps(res, indent=0))
print(sum(1 for r in res if r[1] == 200), "of", len(res), "returned 200")
for r in res:
    if r[1] != 200: print(r)
