#!/usr/bin/env python3
"""Raw -> processed -> analysis. Run from project root:
    .venv/bin/python -I src/data/process.py

Principles enforced here:
  * raw files are only read, never changed
  * a record is never silently dropped: exclusions go to data/processed/excluded_records.csv
  * duplicates are flagged (qa_duplicate), and excluded from counts by explicit rule
  * personal fields (operator names, mobile numbers) never leave data/raw
"""
import bisect, collections, csv, glob, io, json, math, pathlib, statistics, xml.etree.ElementTree as ET, zipfile
import openpyxl, xlrd

ROOT = pathlib.Path.cwd()
RAW, PROC, META, WEB = ROOT/"data/raw", ROOT/"data/processed", ROOT/"data/metadata", ROOT/"public/data"
for d in (PROC/"bengaluru", PROC/"hyderabad", META, WEB/"layers"):
    d.mkdir(parents=True, exist_ok=True)
FETCH = {e["id"]: e for e in json.loads((META/"fetch_log.json").read_text())}
BBOX = {"bengaluru": (12.5, 77.2, 13.5, 78.0), "hyderabad": (17.0, 78.0, 17.9, 79.0)}
PII_FIELDS = {"applicant_name", "csc_id", "Mobileno", "NODAL_OFFI", "Contact_No", "OPR"}

def one(pattern):
    return sorted(glob.glob(str(RAW/pattern)))[0]

# ---------- readers ----------
def kml_records(path):
    root = ET.parse(path).getroot()
    ns = root.tag.split("}")[0] + "}"
    out = []
    for p in root.iter(ns + "Placemark"):
        f = {}
        for s in p.iter():
            if s.get("name"):
                v = s.text
                if v is None or not v.strip():
                    x = s.find(ns + "value")
                    v = x.text if x is not None else ""
                f[s.get("name")] = (v or "").strip()
        if p.findtext(ns + "name"):
            f.setdefault("_name", p.findtext(ns + "name").strip())
        coords = [tuple(map(float, c.split(",")[:2])) for e in p.iter(ns + "coordinates") for c in (e.text or "").split()]
        rings = []
        for poly in p.iter(ns + "Polygon"):
            for b in poly.iter(ns + "outerBoundaryIs"):
                for e in b.iter(ns + "coordinates"):
                    rings.append([tuple(map(float, c.split(",")[:2])) for c in e.text.split()])
        pt = next(p.iter(ns + "Point"), None)
        out.append({"f": f, "pt": coords[0] if pt is not None and coords else None, "rings": rings})
    return out

def centroid(ring):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        c = x0*y1 - x1*y0
        a += c; cx += (x0+x1)*c; cy += (y0+y1)*c
    if abs(a) < 1e-14:
        return ring[0]
    return (cx/(3*a), cy/(3*a))

def biggest(rings):
    return max(rings, key=lambda r: abs(sum(x0*y1-x1*y0 for (x0, y0), (x1, y1) in zip(r, r[1:]))))

def kml_points(path, name=None, keep=()):
    recs = []
    for r in kml_records(path):
        pt = r["pt"] or (centroid(biggest(r["rings"])) if r["rings"] else None)
        recs.append({"lon": pt[0] if pt else None, "lat": pt[1] if pt else None,
                     "name": name(r["f"]) if name else "", "props": {k: r["f"].get(k, "") for k in keep}})
    return recs

def geojson_points(path, name, keep=()):
    recs = []
    for x in json.load(open(path))["features"]:
        c = (x.get("geometry") or {}).get("coordinates") or (None, None)
        p = x["properties"]
        recs.append({"lon": c[0], "lat": c[1], "name": name(p), "props": {k: p.get(k, "") for k in keep}})
    return recs

def osm_points(city, test):
    recs = []
    for e in json.load(open(RAW/f"{city}/osm_{city}/overpass.json"))["elements"]:
        t = e.get("tags", {})
        if not test(t):
            continue
        c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
        recs.append({"lat": c["lat"], "lon": c["lon"], "name": t.get("name", ""),
                     "props": {"osm_id": f'{e["type"]}/{e["id"]}', "wheelchair": t.get("wheelchair", "not tagged"), "operator": t.get("operator", "")}})
    return recs

def is_metro(t):
    n = t.get("name", "")
    return t.get("railway") == "station" and "(u/c)" not in n

# ---------- layer registry ----------
OC = "OpenCity Urban Data Portal"
OSM = "OpenStreetMap contributors (via Overpass API)"
OSMDATE = "Retrieved 2026-11-04"
L = []
def layer(city, lid, label, cat, vintage, vkind, publisher, origin, lic, sid, url, recs, note="", health=None):
    L.append(dict(city=city, id=lid, label=label, category=cat, vintage=vintage, vintage_kind=vkind, publisher=publisher,
                  origin=origin, licence=lic, source_id=sid, source_url=url, recs=recs, note=note, health=health))

CKAN = "https://data.opencity.in/dataset/"
PD = "OpenCity tag: other-pd (public domain). Verify with original publisher before reuse."
NS = "Not specified on the portal"

blr, hyd = "bengaluru", "hyderabad"
layer(blr, "bus_stops", "BMTC bus stops", "Transport", "Undated", "undated", OC, "KGIS (Karnataka GIS)", NS, "blr_bus_stops", CKAN+"bengaluru-bus-stops-and-routes",
      kml_points(one("bengaluru/blr_bus_stops/*"), lambda f: f.get("kgisbmtcbusstopname", ""), ("status",)),
      "The portal calls this year unknown. The 'status' field is undocumented, so all records are shown.")
layer(blr, "metro", "Namma Metro stations", "Transport", OSMDATE, "current", OSM, "OpenStreetMap", "ODbL 1.0", "osm_bengaluru", "https://www.openstreetmap.org/",
      osm_points(blr, is_metro), "Community-mapped. No official BMRCL GTFS feed was found on the portals we checked.")
layer(blr, "uphc", "Urban Public Health Centres", "Healthcare", "Undated", "undated", OC, "BBMP", PD, "blr_uphc", CKAN+"bengaluru-urban-public-health-centres",
      kml_points(one("bengaluru/blr_uphc/*"), lambda f: f.get("UPHC", ""), ("Zone", "ward")),
      "Published under BBMP before the 2025 transition to GBA. Named-officer and phone fields removed.", health="primary")
layer(blr, "namma_clinics", "Namma Clinics", "Healthcare", "2026", "dated", OC, "Karnataka / GBA corporations (via OpenCity)", PD, "blr_namma_clinics", CKAN+"bengaluru-urban-public-health-centres",
      geojson_points(one("bengaluru/blr_namma_clinics/*"), lambda p: p.get("Name of the Namma Clinic", ""), ("Corporation name", "Name of UPHC", "Namma clinic located ward name/ number")), health="primary")
layer(blr, "referral", "UCHC referral hospitals", "Healthcare", "Undated", "undated", OC, "KGIS / BBMP", PD, "blr_referral", CKAN+"bengaluru-urban-public-health-centres",
      kml_points(one("bengaluru/blr_referral/*"), lambda f: f.get("UCHC_HospitalName", "")), health="referral")
layer(blr, "toilets", "BBMP public toilets", "Sanitation", "Undated", "undated", OC, "KGIS / BBMP", NS, "blr_toilets", CKAN+"bengaluru-public-toilets",
      kml_points(one("bengaluru/blr_toilets/*"), lambda f: f.get("ToiletName", "") or "Public toilet"), "Names are blank in the source.")
layer(blr, "csc", "Customer Service Centre records", "Government access", "Undated", "undated", OC, "KSRSAC", PD, "blr_csc", CKAN+"grama-one-centres-in-karnataka-and-bengaluru",
      kml_points(one("bengaluru/blr_csc/*"), lambda f: "Customer Service Centre", ("app_stage",)),
      "Operator names and IDs removed. The app_stage code is undocumented, so these are registry records, not confirmed open centres.")
layer(blr, "grama_one", "Grama One centres", "Government access", "Synced 2023", "dated", OC, "KSRSAC", PD, "blr_grama_one", CKAN+"grama-one-centres-in-karnataka-and-bengaluru",
      kml_points(one("bengaluru/blr_grama_one/*"), lambda f: f.get("VillageName", ""), ("SubdistrictName", "LocalBodyName_GPName")),
      "A rural-facing scheme in Bengaluru Urban district, largely outside the city. Mobile numbers removed.")
layer(blr, "slums", "Slum locations", "Context", "Undated", "undated", OC, "BBMP / health department listing", PD, "blr_slums", CKAN+"bengaluru-urban-slums",
      geojson_points(one("bengaluru/blr_slums/*"), lambda p: p.get("Name of the Slum", ""), ("UPHC Covering Ward Name",)),
      "Point locations of settlements listed by the source. Not a measure of residents' circumstances.")

hyd_stops = [{"lat": float(r["stop_lat"]) if r["stop_lat"] else None, "lon": float(r["stop_lon"]) if r["stop_lon"] else None, "name": r["stop_name"], "props": {"zone": r["zone_id"]}}
             for r in csv.DictReader(open(one("hyderabad/hyd_bus_stops_csv/*"), encoding="utf-8-sig"))]
layer(hyd, "bus_stops", "TGSRTC bus stops", "Transport", "Undated", "undated", OC, "TSRTC / Telangana open data", PD, "hyd_bus_stops_csv", CKAN+"hyderabad-bus-stops", hyd_stops)
z = zipfile.ZipFile(one("hyderabad/hyd_metro_gtfs/*"))
hm = [r for r in csv.DictReader(io.TextIOWrapper(z.open("stops.txt"), encoding="utf-8-sig"))]
stations = [r for r in hm if r.get("location_type") == "1"]
layer(hyd, "metro", "Hyderabad Metro stations", "Transport", "GTFS, July 2026", "dated", OC, "HMRL / Open Data Telangana", PD, "hyd_metro_gtfs", CKAN+"hyderabad-metro-rail-gtfs",
      [{"lat": float(r["stop_lat"]), "lon": float(r["stop_lon"]), "name": r["stop_name"], "props": {}} for r in stations], "Official GTFS feed; station-level entries only.")
hc = kml_records(one("hyderabad/hyd_health_centres/*"))
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None
PRIMARY = {"Basti Dawakhana", "Urban Primary Health Centre", "Primary Health Centre"}
def hc_recs(pred):
    return [{"lat": r["pt"][1] if r["pt"] else None, "lon": r["pt"][0] if r["pt"] else None, "name": r["f"].get("Facility", ""),
             "props": {"type": r["f"].get("Facility_T", ""), "district": r["f"].get("District", ""), "department": r["f"].get("HOD", ""), "address": r["f"].get("Address", "")}}
            for r in hc if pred(r["f"].get("Facility_T", ""))]
layer(hyd, "health_primary", "Basti Dawakhanas and UPHCs", "Healthcare", "Undated", "undated", OC, "TRAC Telangana", PD, "hyd_health_centres", CKAN+"hyderabad-public-health-centres",
      hc_recs(lambda t: t in PRIMARY), "Extends into Medchal, Rangareddy and Sangareddy districts.", health="primary")
layer(hyd, "health_other", "Government hospitals and AYUSH", "Healthcare", "Undated", "undated", OC, "TRAC Telangana", PD, "hyd_health_centres", CKAN+"hyderabad-public-health-centres",
      hc_recs(lambda t: t not in PRIMARY), health="referral")
layer(hyd, "hospitals_2018", "All hospitals (GHMC list)", "Healthcare", "2018", "dated", OC, "Telangana open data / GHMC", PD, "hyd_hospitals", CKAN+"hyderabad-public-health-centres",
      kml_points(one("hyderabad/hyd_hospitals/*"), lambda f: f.get("Address", ""), ("Wardno_Name", "Circleno_Name", "Category")),
      "Public and private facilities are not distinguished; not comparable with Bengaluru's public-only layers.")
layer(hyd, "toilets", "Public toilets", "Sanitation", "September 2018", "dated", OC, "Telangana open data / GHMC", PD, "hyd_toilets", CKAN+"hyderabad-public-toilets",
      kml_points(one("hyderabad/hyd_toilets/*"), lambda f: f.get("Assessor_Address", "") or "Public toilet", ("Wardno_Name",)))
layer(hyd, "annapurna", "Annapurna meal centres", "Food access", "2018", "dated", OC, "Telangana open data / GHMC", PD, "hyd_annapurna", CKAN+"hyderabad-annapurna-meals",
      kml_points(one("hyderabad/hyd_annapurna/*"), lambda f: f.get("Address", ""), ("Wardno_Name",)), "Subsidised meal sites. These are not PDS shops.")
layer(hyd, "community_halls", "Community halls", "Government access", "2018", "dated", OC, "Telangana open data / GHMC", PD, "hyd_community_halls", CKAN+"hyderabad-community-halls",
      kml_points(one("hyderabad/hyd_community_halls/*"), lambda f: f.get("_Address", ""), ("Wardno_Name",)))
slum_hyd = []
for r in kml_records(one("hyderabad/hyd_slums/*")):
    pt = centroid(biggest(r["rings"])) if r["rings"] else None
    slum_hyd.append({"lon": pt[0] if pt else None, "lat": pt[1] if pt else None, "name": r["f"].get("SLUMNAME", ""),
                     "props": {"notified": r["f"].get("NOTIFIED_N", ""), "population": r["f"].get("TOTAL_POPU", "")}})
layer(hyd, "slums", "Slum locations", "Context", "Undated", "undated", OC, "TRAC Telangana", PD, "hyd_slums", CKAN+"hyderabad-slums", slum_hyd,
      "Polygon centroids computed by this project. Not a measure of residents' circumstances.")
for city in (blr, hyd):
    for lid, label, cat, t in [("osm_hospital", "Hospitals (OSM)", "Healthcare", lambda t: t.get("amenity") == "hospital"),
                               ("osm_clinic", "Clinics (OSM)", "Healthcare", lambda t: t.get("amenity") == "clinic"),
                               ("osm_toilets", "Public toilets (OSM)", "Sanitation", lambda t: t.get("amenity") == "toilets"),
                               ("osm_post", "Post offices (OSM)", "Government access", lambda t: t.get("amenity") == "post_office"),
                               ("osm_gov", "Government offices (OSM)", "Government access", lambda t: t.get("office") == "government" or t.get("amenity") == "townhall")]:
        layer(city, lid, label, cat, OSMDATE, "current", OSM, "OpenStreetMap", "ODbL 1.0", f"osm_{city}", "https://www.openstreetmap.org/", osm_points(city, t),
              "Same query, same day, both cities. Completeness depends on volunteer mapping; a missing point does not mean no facility.")

# ---------- cleaning ----------
excl, quality = [], []
for l in L:
    box = BBOX[l["city"]]; seen = set(); clean = []
    miss = oob = dup = 0
    for r in l["recs"]:
        if r["lat"] is None or r["lon"] is None:
            miss += 1; excl.append((l["city"], l["id"], r["name"], "", "", "missing coordinates")); continue
        if not (box[0] <= r["lat"] <= box[2] and box[1] <= r["lon"] <= box[3]):
            oob += 1; excl.append((l["city"], l["id"], r["name"], r["lat"], r["lon"], "outside city bounding box")); continue
        key = (round(r["lat"], 5), round(r["lon"], 5), r["name"].lower().strip())
        r["qa_duplicate"] = key in seen
        dup += r["qa_duplicate"]; seen.add(key)
        clean.append(r)
    l["clean"] = clean
    l["q"] = dict(raw=len(l["recs"]), missing_coords=miss, out_of_bounds=oob, duplicates_flagged=dup, blank_names=sum(1 for r in clean if not r["name"].strip()))
with open(PROC/"excluded_records.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["city", "layer", "name", "lat", "lon", "reason"]); w.writerows(excl)

# ---------- wards ----------
def poly_area_km2(ring):
    lat0 = sum(p[1] for p in ring)/len(ring)
    k = 111.32
    pts = [(x*k*math.cos(math.radians(lat0)), y*110.57) for x, y in ring]
    return abs(sum(x0*y1-x1*y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:])))/2

def dp(pts, eps):
    if len(pts) < 4: return pts
    if pts[0] == pts[-1]:  # a closed ring has no baseline: simplify two halves
        m = len(pts)//2
        return dp(pts[:m+1], eps)[:-1] + dp(pts[m:], eps)
    a, b = pts[0], pts[-1]; dmax = 0; idx = 0
    for i in range(1, len(pts)-1):
        p = pts[i]; dx, dy = b[0]-a[0], b[1]-a[1]
        n = math.hypot(dx, dy) or 1e-12
        d = abs(dy*(p[0]-a[0])-dx*(p[1]-a[1]))/n
        if d > dmax: dmax, idx = d, i
    if dmax > eps:
        return dp(pts[:idx+1], eps)[:-1] + dp(pts[idx:], eps)
    return [a, b]

wards = {blr: [], hyd: []}
for r in kml_records(one("bengaluru/blr_gba_wards/*")):
    f = r["f"]; wards[blr].append({"name": f.get("ward_name", ""), "name_local": f.get("ward_name_kn", ""), "group": f"{f.get('Corporation','')} Corporation", "pop": num(f.get("TOT_P")), "rings": r["rings"]})
for r in kml_records(one("hyderabad/hyd_wards/*")):
    f = r["f"]; wards[hyd].append({"name": f.get("ward", ""), "name_local": "", "group": f.get("ZONE", ""), "pop": None, "rings": r["rings"]})

def in_ring(x, y, ring):
    c = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        if (y0 > y) != (y1 > y) and x < (x1-x0)*(y-y0)/(y1-y0)+x0:
            c = not c
    return c
for city, ws in wards.items():
    for w in ws:
        xs = [p[0] for rg in w["rings"] for p in rg]; ys = [p[1] for rg in w["rings"] for p in rg]
        w["bb"] = (min(xs), min(ys), max(xs), max(ys))
        w["area"] = sum(poly_area_km2(rg) for rg in w["rings"])
def ward_of(city, lon, lat):
    for i, w in enumerate(wards[city]):
        b = w["bb"]
        if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and any(in_ring(lon, lat, rg) for rg in w["rings"]):
            return i
    return None
for l in L:
    for r in l["clean"]:
        r["ward"] = ward_of(l["city"], r["lon"], r["lat"])
    l["q"]["in_study_area"] = sum(1 for r in l["clean"] if r["ward"] is not None and not r["qa_duplicate"])
    l["q"]["outside_study_area_flagged"] = sum(1 for r in l["clean"] if r["ward"] is None)

# ---------- nearest-distance analysis (straight line, no routing) ----------
class Index:
    def __init__(self, pts, cell=0.02):
        self.cell = cell; self.g = collections.defaultdict(list)
        for lat, lon in pts:
            self.g[(int(lat/cell), int(lon/cell))].append((lat, lon))
    def nearest(self, lat, lon):
        ci, cj = int(lat/self.cell), int(lon/self.cell); best = math.inf; ring = 0
        while ring < 80:
            for i in range(ci-ring, ci+ring+1):
                for j in range(cj-ring, cj+ring+1):
                    if max(abs(i-ci), abs(j-cj)) != ring: continue
                    for a, b in self.g.get((i, j), ()):
                        d = hav(lat, lon, a, b)
                        if d < best: best = d
            if best < (ring)*self.cell*105: break
            ring += 1
        return best
def hav(a, b, c, d):
    p = math.pi/180
    h = math.sin((c-a)*p/2)**2 + math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 12742*math.asin(math.sqrt(h))

def grid(city, step_km=0.5):
    ws = wards[city]
    x0 = min(w["bb"][0] for w in ws); x1 = max(w["bb"][2] for w in ws); y0 = min(w["bb"][1] for w in ws); y1 = max(w["bb"][3] for w in ws)
    dlat = step_km/110.57; dlon = step_km/(111.32*math.cos(math.radians((y0+y1)/2)))
    out = []; y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            if ward_of(city, x, y) is not None: out.append((y, x))
            x += dlon
        y += dlat
    return out

GROUPS = {
    blr: {"primary_health": ["uphc", "namma_clinics"], "osm_health": ["osm_hospital", "osm_clinic"], "bus": ["bus_stops"], "metro": ["metro"], "toilets": ["toilets"], "osm_toilets": ["osm_toilets"]},
    hyd: {"primary_health": ["health_primary"], "osm_health": ["osm_hospital", "osm_clinic"], "bus": ["bus_stops"], "metro": ["metro"], "toilets": ["toilets"], "osm_toilets": ["osm_toilets"]},
}
def lay(city, lid):
    return next(l for l in L if l["city"] == city and l["id"] == lid)
def stats(ds):
    ds = sorted(ds)
    return {"n": len(ds), "median_km": round(statistics.median(ds), 2), "p90_km": round(ds[int(.9*len(ds))], 2),
            "share_within_1km": round(sum(d <= 1 for d in ds)/len(ds)*100, 1), "share_within_500m": round(sum(d <= .5 for d in ds)/len(ds)*100, 1)}
spatial = {}
for city in (blr, hyd):
    g = grid(city)
    slums = [(r["lat"], r["lon"]) for r in lay(city, "slums")["clean"] if r["ward"] is not None and not r["qa_duplicate"]]
    res = {"grid_cells": len(g), "slum_points_in_study_area": len(slums), "study_area_km2": round(sum(w["area"] for w in wards[city]), 1), "wards": len(wards[city]), "measures": {}}
    for key, ids in GROUPS[city].items():
        pts = [(r["lat"], r["lon"]) for i in ids for r in lay(city, i)["clean"] if not r["qa_duplicate"]]
        ix = Index(pts)
        res["measures"][key] = {"facilities_used": len(pts), "in_study_area": sum(1 for i in ids for r in lay(city, i)["clean"] if r["ward"] is not None and not r["qa_duplicate"]),
                                "city_grid": stats([ix.nearest(*c) for c in g]), "slum_points": stats([ix.nearest(*c) for c in slums])}
    spatial[city] = res
    print(city, "grid", len(g), "area", res["study_area_km2"], flush=True)

# ---------- census ----------
def xl(path):
    return list(openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
census = {"disability": {}, "language": {}, "literacy": {}, "digital_assets": {}, "slum_pca": {}}
TYPES = ["In seeing", "In hearing", "In speech", "In movement", "Mental retardation (Census term)", "Mental illness", "Any other", "Multiple disability"]
for r in xl(one("shared/census_c20_city/*")):
    if r[5] == "Total" and r[3] in ("Hyderabad UA", "Bruhat Bangalore UA"):
        c = hyd if "Hyderabad" in r[3] else blr
        census["disability"][c] = {"area": r[3], "total": r[6], "by_type": {t: r[9+3*i] for i, t in enumerate(TYPES)}}
for c, file, name in ((hyd, "census_c16_town_ap", "GHMC (M Corp. + OG) (Part)"), (blr, "census_c16_town_ka", "BBMP (M Corp. + OG) (Part)")):
    totals = collections.Counter()
    for r in xl(one(f"shared/{file}/*"))[6:]:
        if r[4] == name and str(r[5]).endswith("000"):
            totals[str(r[6]).strip().split(" ", 1)[-1].title()] += r[7]
    t = sum(totals.values())
    census["language"][c] = {"area": name.replace(" (Part)", "") + " (all parts summed)", "total": t,
                             "top": [{"language": k, "count": v, "pct": round(v/t*100, 1)} for k, v in totals.most_common(8)]}
for c, files, name in ((blr, ["census_pca_blr_a"], "BBMP (M Corp. + OG) (Part)"), (hyd, ["census_pca_hyd_hyd", "census_pca_hyd_ranga", "census_pca_hyd_medak"], "GHMC (M Corp. + OG) (Part)")):
    s = collections.Counter()
    for fi in files:
        rows = xl(one(f"shared/{fi}/*")); h = {k: i for i, k in enumerate(rows[0])}
        for r in rows[1:]:
            if r[h["Level"]] == "TOWN" and r[h["Name"]] == name:
                for k in ("No_HH", "TOT_P", "TOT_F", "TOT_M", "P_06", "F_06", "M_06", "P_LIT", "F_LIT", "M_LIT"):
                    s[k] += r[h[k]]
    assert s["TOT_P"] == census["language"][c]["total"], (c, s["TOT_P"], census["language"][c]["total"])  # PCA and C-16 must agree
    census["literacy"][c] = {"area": name.replace(" (Part)", ""), "population": s["TOT_P"], "households": s["No_HH"],
                             "literacy_7plus_pct": round(s["P_LIT"]/(s["TOT_P"]-s["P_06"])*100, 1),
                             "female_literacy_7plus_pct": round(s["F_LIT"]/(s["TOT_F"]-s["F_06"])*100, 1),
                             "male_literacy_7plus_pct": round(s["M_LIT"]/(s["TOT_M"]-s["M_06"])*100, 1),
                             "non_literate_7plus": s["TOT_P"]-s["P_06"]-s["P_LIT"]}
B = list(csv.DictReader(open(one("bengaluru/blr_household_assets/*"), encoding="utf8", errors="replace")))
b = next(r for r in B if r["Area Name"] == "District - Bangalore" and list(r.values())[3] == "Urban")
ks = list(b.keys())
census["digital_assets"][blr] = {"area": "Bangalore district, urban households", "computer_with_internet_pct": float(b[ks[6]]), "computer_no_internet_pct": float(b[ks[7]]), "mobile_only_pct": float(b[ks[9]]), "landline_and_mobile_pct": float(b[ks[10]]), "no_assets_pct": float(b[ks[15]])}
R = xl(one("hyderabad/hyd_h14/*"))
hr = next(r for r in R[7:] if r[8] == "District - Hyderabad" and r[9] == "Urban")
census["digital_assets"][hyd] = {"area": "Hyderabad district, urban households", "computer_with_internet_pct": hr[129], "computer_no_internet_pct": hr[130], "mobile_only_pct": hr[132], "landline_and_mobile_pct": hr[133], "no_assets_pct": hr[138]}
sh = xlrd.open_workbook(one("shared/census_pca_slum/*")).sheet_by_index(0)
head = sh.row_values(0); hi = {k: i for i, k in enumerate(head)}
for i in range(sh.nrows):
    row = sh.row_values(i)
    if row[2] in ("GHMC (M Corp. + OG) (Part)", "BBMP (M Corp. + OG) (Part)"):
        c = hyd if "GHMC" in row[2] else blr
        census["slum_pca"][c] = {"area": row[2], "slum_population": int(row[hi["TOT_P"]]), "slum_households": int(row[hi["No_HH"]]),
                                 "slum_literacy_7plus_pct": round(row[hi["P_LIT"]]/(row[hi["TOT_P"]]-row[hi["P_06"]])*100, 1)}
# OSM tagging evidence
def wheelchair(city):
    out = {}
    for lid in ("metro", "osm_hospital", "osm_clinic", "osm_toilets", "osm_post", "osm_gov"):
        if city == hyd and lid == "metro":
            recs = osm_points(city, is_metro)
        else:
            recs = lay(city, lid)["recs"]
        c = collections.Counter(r["props"].get("wheelchair", "not tagged") for r in recs)
        out[lid] = {"total": len(recs), "yes": c["yes"]+c["designated"], "limited": c["limited"], "no": c["no"], "not_tagged": c["not tagged"]}
    return out
osm_access = {c: wheelchair(c) for c in (blr, hyd)}

# ---------- outputs ----------
def fc(features):
    return {"type": "FeatureCollection", "features": features}
for city, ws in wards.items():
    feats = []
    counts = collections.defaultdict(collections.Counter)
    for l in L:
        if l["city"] == city:
            for r in l["clean"]:
                if r["ward"] is not None and not r["qa_duplicate"]:
                    counts[r["ward"]][l["id"]] += 1
    for i, w in enumerate(ws):
        polys = [[[[round(x, 5), round(y, 5)] for x, y in dp(rg, 0.00018)]] for rg in w["rings"]]
        ph = sum(counts[i][k] for k in GROUPS[city]["primary_health"])
        feats.append({"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": polys},
                      "properties": {"name": w["name"], "name_local": w["name_local"], "group": w["group"], "population_2011_based": w["pop"], "area_km2": round(w["area"], 2),
                                     "primary_health": ph, "bus_stops": counts[i]["bus_stops"], "toilets": counts[i]["toilets"]}})
    (PROC/city/"wards.geojson").write_text(json.dumps(fc(feats)))
    (WEB/f"{city}_wards.json").write_text(json.dumps(fc(feats), separators=(",", ":"), ensure_ascii=False))
    zero = sum(1 for f in feats if f["properties"]["primary_health"] == 0)
    spatial[city]["wards_with_no_primary_health"] = zero
registry = []
for l in L:
    feats = []
    for r in l["clean"]:
        if r["qa_duplicate"]:
            continue
        p = {k: v for k, v in r["props"].items() if k not in PII_FIELDS and v not in ("", None)}
        p["name"] = r["name"]; p["in_study_area"] = r["ward"] is not None
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(r["lon"], 5), round(r["lat"], 5)]}, "properties": p})
    (PROC/l["city"]/f"{l['id']}.geojson").write_text(json.dumps(fc(feats), ensure_ascii=False))
    (WEB/"layers"/f"{l['city']}_{l['id']}.json").write_text(json.dumps(fc(feats), separators=(",", ":"), ensure_ascii=False))
    registry.append({k: l[k] for k in ("city", "id", "label", "category", "vintage", "vintage_kind", "publisher", "origin", "licence", "source_id", "source_url", "note")} |
                    {"count": len(feats), "in_study_area": l["q"]["in_study_area"], "quality": l["q"],
                     "retrieved_at": FETCH.get(l["source_id"], {}).get("retrieved_at", "2026-11-04"), "sha256": FETCH.get(l["source_id"], {}).get("sha256", "")})
(WEB/"layers.json").write_text(json.dumps(registry, indent=1, ensure_ascii=False))
(WEB/"analysis.json").write_text(json.dumps({"spatial": spatial, "census": census, "osm_access": osm_access}, indent=1, ensure_ascii=False))
(PROC/"analysis.json").write_text(json.dumps({"spatial": spatial, "census": census, "osm_access": osm_access}, indent=1, ensure_ascii=False))
with open(META/"dataset_inventory.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["dataset_name", "city", "category", "publisher", "origin_stated_by_portal", "source_url", "download_url", "format_in_project", "vintage", "vintage_kind", "geographic_resolution", "records_after_cleaning", "records_in_study_area", "licence", "downloadable", "integrated", "limitations", "retrieved_at", "sha256"])
    for x in registry:
        fl = FETCH.get(x["source_id"], {})
        w.writerow([x["label"], x["city"], x["category"], x["publisher"], x["origin"], x["source_url"], fl.get("download_url", "Overpass API query; see data/raw"), "GeoJSON", x["vintage"], x["vintage_kind"], "Point", x["count"], x["in_study_area"], x["licence"], "yes", "yes", x["note"], x["retrieved_at"], x["sha256"]])
EXTRA = [
 ("Census 2011 C-20 City: disabled population by type", "shared", "census_c20_city", "Urban agglomeration", "Disability", "Bruhat Bangalore UA and Hyderabad UA rows used. Older categories. Self-reported."),
 ("Census 2011 C-16 town level: mother tongue, Karnataka", "bengaluru", "census_c16_town_ka", "Town", "Language", "BBMP (M Corp. + OG) parts summed. Mother tongue is not reading ability."),
 ("Census 2011 C-16 town level: mother tongue, Andhra Pradesh", "hyderabad", "census_c16_town_ap", "Town", "Language", "GHMC (M Corp. + OG) parts summed across districts. Hyderabad was in Andhra Pradesh in 2011."),
 ("Census 2011 PCA: Bangalore district", "bengaluru", "census_pca_blr_a", "Ward/town", "Literacy", "Total reconciled exactly with C-16."),
 ("Census 2011 PCA: Bangalore Rural district", "bengaluru", "census_pca_blr_b", "Ward/town", "Literacy", "Downloaded; contains no BBMP rows used in the totals."),
 ("Census 2011 PCA: Hyderabad district", "hyderabad", "census_pca_hyd_hyd", "Ward/town", "Literacy", "One of three districts summed for GHMC. Reconciled with C-16."),
 ("Census 2011 PCA: Rangareddy district", "hyderabad", "census_pca_hyd_ranga", "Ward/town", "Literacy", "One of three districts summed for GHMC."),
 ("Census 2011 PCA: Medak district", "hyderabad", "census_pca_hyd_medak", "Ward/town", "Literacy", "One of three districts summed for GHMC."),
 ("Census 2011 PCA Slum: town level", "shared", "census_pca_slum", "Town", "Demographics", "State slum definitions differ. Rows are labelled (Part). Downloaded and processed; not used in published findings."),
 ("Census 2011 HH-14: Hyderabad household assets", "hyderabad", "hyd_h14", "District", "Digital access", "Computers and phones in 2011 only; predates mass smartphone use. Processed; not used in published findings."),
 ("Census 2011 household assets: Bengaluru", "bengaluru", "blr_household_assets", "District", "Digital access", "Same limits as HH-14. Processed; not used in published findings."),
 ("GBA 369 wards with population, December 2025", "bengaluru", "blr_gba_wards", "Ward polygon", "Boundaries", "Study area for Bengaluru. Population field is on a 2011 base and was not independently verified."),
 ("Greater Hyderabad wards map, 2022", "hyderabad", "hyd_wards", "Ward polygon", "Boundaries", "Study area for Hyderabad. Predates the 2026 reorganisation."),
 ("BBMP wards (DataMeet)", "bengaluru", "blr_wards_2011", "Ward polygon", "Boundaries", "Reference only. Not used in the analysis."),
 ("GHMC wards (DataMeet / OSM)", "hyderabad", "hyd_wards_datameet", "Ward polygon", "Boundaries", "Reference only. Not used in the analysis."),
 ("Bengaluru ward census 2011", "bengaluru", "blr_ward_census", "Ward", "Demographics", "198-ward base. Reference only."),
 ("Hyderabad census 2011 (district wards)", "hyderabad", "hyd_census", "Ward", "Demographics", "Hyderabad district only. Reference only."),
 ("Hyderabad bus stops KML", "hyderabad", "hyd_bus_stops", "Point", "Transport", "Duplicate of the CSV without names. CSV used instead."),
 ("Bengaluru metro stations KML, April 2023", "bengaluru", "blr_metro", "Point", "Transport", "Superseded by same-day OSM extract, because new lines have opened since."),
]
with open(META/"dataset_inventory.csv", "a", newline="") as f:
    w = csv.writer(f)
    for name, city, sid, res, cat, note in EXTRA:
        fl = FETCH[sid]
        w.writerow([name, city, cat, "Office of the Registrar General, India" if name.startswith("Census") else "OpenCity / DataMeet (see source URL)", "", fl["source_page"], fl["download_url"], "Original format in data/raw", "2011" if "2011" in name else "See name", "dated", res, "", "", "Check publisher terms", "yes", "yes" if "Reference only" not in note else "no", note, fl["retrieved_at"], fl["sha256"]])
lines = ["# Data quality report", "", "Generated by `src/data/process.py`. Do not edit by hand.", "",
         "Exclusions are itemised in `data/processed/excluded_records.csv`. Duplicates are exact matches on name plus coordinates to five decimal places; they are flagged and left out of counts.", "",
         "| City | Layer | Vintage | Raw | No coordinates | Outside bounding box | Duplicates | Blank names | In study area | Outside study area (kept, flagged) |", "|---|---|---|---|---|---|---|---|---|---|"]
for x in registry:
    q = x["quality"]
    lines.append(f"| {x['city']} | {x['label']} | {x['vintage']} | {q['raw']} | {q['missing_coords']} | {q['out_of_bounds']} | {q['duplicates_flagged']} | {q['blank_names']} | {q['in_study_area']} | {q['outside_study_area_flagged']} |")
lines += ["", "## Personal data", "", "These source fields hold named individuals' details and are removed from all processed and web outputs: `applicant_name`, `csc_id` (CSC operators), `Mobileno`, `OPR` (Grama One operators), `NODAL_OFFI`, `Contact_No` (UPHC officers). The raw files still contain them, so `data/raw` must not be republished."]
(META/"data_quality_report.md").write_text("\n".join(lines)+"\n")
print(json.dumps({"spatial": spatial, "census": census, "osm_access": osm_access}, indent=0)[:9000])
for x in registry: print(x["city"], x["id"], x["count"], x["in_study_area"], x["quality"])
