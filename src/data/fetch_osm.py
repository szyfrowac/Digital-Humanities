#!/usr/bin/env python3
"""Same-day, same-query OSM extract for both cities (ODbL). Raw responses preserved.
Run from project root: python3 -I src/data/fetch_osm.py"""
import datetime as dt, hashlib, json, pathlib, time, urllib.parse, urllib.request
ROOT = pathlib.Path.cwd()
BBOX = {"bengaluru": "12.80,77.35,13.20,77.85", "hyderabad": "17.20,78.20,17.62,78.72"}
SEL = ['node["railway"="station"]["station"="subway"]', 'node["railway"="station"]["subway"="yes"]',
       'nwr["amenity"="hospital"]', 'nwr["amenity"="clinic"]', 'nwr["amenity"="toilets"]',
       'nwr["amenity"="post_office"]', 'nwr["amenity"="townhall"]', 'nwr["office"="government"]']
for city, bb in BBOX.items():
    q = "[out:json][timeout:170];(" + "".join(f"{s}({bb});" for s in SEL) + ");out center tags;"
    url = "https://overpass-api.de/api/interpreter"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "DH-Research-CanYouAccessYourCity/0.1 (academic project)"})
            body = urllib.request.urlopen(req, timeout=180).read()
            json.loads(body)
            break
        except Exception as e:
            print(city, "retry", e, flush=True); body = None; time.sleep(30)
    folder = ROOT / f"data/raw/{city}/osm_{city}"
    folder.mkdir(parents=True, exist_ok=True)
    if body is None:
        print(city, "FAILED"); continue
    (folder / "overpass.json").write_bytes(body)
    (folder / "query.txt").write_text(q)
    meta = {"retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "endpoint": url,
            "sha256": hashlib.sha256(body).hexdigest(), "osm_base": json.loads(body)["osm3s"]["timestamp_osm_base"]}
    (folder / "meta.json").write_text(json.dumps(meta, indent=1))
    print(city, len(json.loads(body)["elements"]), meta["osm_base"], flush=True)
    time.sleep(10)
