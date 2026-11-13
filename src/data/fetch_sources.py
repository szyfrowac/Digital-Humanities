#!/usr/bin/env python3
"""Download every registered source, keeping originals untouched.

Each file goes in data/raw/<city>/<id>/, and the outcome of every attempt
(including failures) is recorded in data/metadata/fetch_log.json.

Run from the project root:  python3 -I src/data/fetch_sources.py
"""
import datetime as dt
import hashlib
import json
import pathlib
import ssl
import time
import urllib.request

ROOT = pathlib.Path.cwd()
UA = "DH-Research-CanYouAccessYourCity/0.1 (academic project)"
OC = "https://data.opencity.in/dataset/"
CENSUS = "https://censusindia.gov.in/nada/index.php/catalog/"

# id, city, source page, download URL
SOURCES = [
    # --- Bengaluru ---
    ("blr_bus_stops", "bengaluru", OC + "bengaluru-bus-stops-and-routes", OC + "8bcca4f2-7392-4ecb-ba1e-28dccd987c34/resource/c8fda6d4-0caa-40ec-ab5a-236984974745/download/bmtc_bus_stops.kml"),
    ("blr_metro", "bengaluru", OC + "bengaluru-metro-stations", OC + "746940cd-cca7-45f5-a3bc-8b0034663605/resource/86e5641c-496c-43fa-8143-bae5f255afc4/download"),
    ("blr_uphc", "bengaluru", OC + "bengaluru-urban-public-health-centres", OC + "b7a0a3ea-36b4-4706-9f63-b139097e089e/resource/6a3d171d-dd83-490d-95c3-81f748b2d292/download"),
    ("blr_namma_clinics", "bengaluru", OC + "bengaluru-urban-public-health-centres", OC + "b7a0a3ea-36b4-4706-9f63-b139097e089e/resource/9005167b-69f2-4448-abd9-03df4c7613f1/download"),
    ("blr_referral", "bengaluru", OC + "bengaluru-urban-public-health-centres", OC + "b7a0a3ea-36b4-4706-9f63-b139097e089e/resource/8db365cf-ab88-47f0-914c-558e4bdab904/download"),
    ("blr_toilets", "bengaluru", OC + "bengaluru-public-toilets", OC + "7626ff0e-b6ff-49d2-b0b9-a2198f3af46a/resource/060ac9f2-6070-4663-b90f-2ca3edcca098/download/d062acab-be81-41ff-a762-af636f556ab1.kml"),
    ("blr_csc", "bengaluru", OC + "grama-one-centres-in-karnataka-and-bengaluru", OC + "712a2ab0-05f5-4842-b552-c4b02f10c860/resource/6f82582e-f11d-46f8-81c2-4b960e5ebf95/download/blr_csc_locations.kml"),
    ("blr_grama_one", "bengaluru", OC + "grama-one-centres-in-karnataka-and-bengaluru", OC + "712a2ab0-05f5-4842-b552-c4b02f10c860/resource/0b9f1479-d79e-4858-8751-5a95178cfe11/download/blr_urban_grama_one_locations.kml"),
    ("blr_slums", "bengaluru", OC + "bengaluru-urban-slums", OC + "7f7e9fd2-5192-4ee1-baa4-aff17ecde1cf/resource/c12b4406-6a33-4c52-832f-f8944b715312/download"),
    ("blr_wards_2011", "bengaluru", "https://github.com/datameet/Municipal_Spatial_Data/tree/master/Bangalore", "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Bangalore/BBMP.geojson"),
    ("blr_gba_wards", "bengaluru", OC + "gba-wards-delimitation-2025", OC + "863209cb-4ced-4f51-b5c5-156939c50922/resource/9013d656-8051-4e2d-9648-46efd0d86d3d/download/gba-369-wards-december-2025.kml"),
    ("blr_ward_census", "bengaluru", OC + "bengaluru-census-2011", OC + "023a1c0c-1901-4eb1-b1bf-66a900485099/resource/269cdf01-dae5-4736-8f4d-72a8e57fa3a9/download/83390055-d933-420f-82b7-608e139336c2.csv"),
    # --- Hyderabad ---
    ("hyd_bus_stops", "hyderabad", OC + "hyderabad-bus-stops", OC + "88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/a34d31f8-0dd1-4bcf-90a8-21b634fddae6/download"),
    ("hyd_bus_stops_csv", "hyderabad", OC + "hyderabad-bus-stops", OC + "88e2d145-7ec6-4666-88dd-6cf18b18312e/resource/1f531384-0f96-4d5f-b2ec-f5a2c772d758/download"),
    ("hyd_metro_gtfs", "hyderabad", OC + "hyderabad-metro-rail-gtfs", OC + "4e72c202-4cdb-4437-a629-ffcbe9519f73/resource/5fa250e1-3104-4ca7-ad31-4fa3321f6255/download/telangana_opendata_gtfs_hmrl_03_july_2026.zip"),
    ("hyd_health_centres", "hyderabad", OC + "hyderabad-public-health-centres", OC + "b5ba02a1-450b-456d-a7ea-bf1cf29c0198/resource/4872026f-6c15-4097-a90a-e77588b5c781/download"),
    ("hyd_hospitals", "hyderabad", OC + "hyderabad-public-health-centres", OC + "b5ba02a1-450b-456d-a7ea-bf1cf29c0198/resource/a59fe42b-4071-4b91-b20f-9698c20789e0/download"),
    ("hyd_toilets", "hyderabad", OC + "hyderabad-public-toilets", OC + "1c007af6-7da8-4b0a-8df5-268ea53a5967/resource/1df6f070-68a2-4267-971b-2a4759343e65/download"),
    ("hyd_annapurna", "hyderabad", OC + "hyderabad-annapurna-meals", OC + "f515c4f3-98db-41cd-94df-69c29a50749b/resource/06f75ef4-e066-4b72-995c-ec131d137b73/download"),
    ("hyd_community_halls", "hyderabad", OC + "hyderabad-community-halls", OC + "58c2db1a-98fa-4363-b360-271f1d532aba/resource/2101e7c4-311d-4b9b-a8ef-0517ab8f9795/download"),
    ("hyd_slums", "hyderabad", OC + "hyderabad-slums", OC + "7a85a3cc-5eb6-437f-8ccc-b5858cbce3e5/resource/d3b594ae-a897-47f1-b9c1-7a46f1b62c04/download"),
    ("hyd_wards", "hyderabad", OC + "hyderabad-wards-info", OC + "15cb7d8d-eed1-4aad-8cd7-f281cbf4f94f/resource/14b033e3-3721-4149-8326-cc29420e062e/download"),
    ("hyd_wards_datameet", "hyderabad", "https://github.com/datameet/Municipal_Spatial_Data/tree/master/Hyderabad", "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Hyderabad/ghmc-wards.geojson"),
    ("hyd_census", "hyderabad", OC + "hyderabad-census-2011-data", OC + "221da500-d7c8-478a-a4eb-6f2c7d76d236/resource/a2379f18-f963-4d43-990f-1fd413d19ca6/download/358642e3-9830-4b94-9a92-3b3ead853115.csv"),
    # --- Shared ---
    ("census_c16_town_ka", "shared", CENSUS + "10255", CENSUS + "10255/download/13367/DDW-C16-TOWN-STMT-MDDS-2900.XLSX"),
    ("census_c16_town_ap", "shared", CENSUS + "10254", CENSUS + "10254/download/13366/DDW-C16-TOWN-STMT-MDDS-2800.XLSX"),
    ("hyd_h14", "hyderabad", OC + "hyderabad-census-2011-data", OC + "221da500-d7c8-478a-a4eb-6f2c7d76d236/resource/25eb7fe6-e52e-4210-9fad-60421d42b3df/download/hlpca-28536-2011_h14_census.xlsx"),
    ("blr_household_assets", "bengaluru", OC + "bengaluru-census-2011", OC + "023a1c0c-1901-4eb1-b1bf-66a900485099/resource/4efdf9f5-5790-41ca-ac68-13691b31f364/download/a7c8acc4-6540-4152-9fee-aa084baac188.csv"),
    ("census_pca_slum", "shared", CENSUS + "6190", CENSUS + "6190/download/9267/slum_data_census_2011.xls"),
    ("census_pca_blr_a", "shared", CENSUS + "6763", CENSUS + "6763/download/9840/DDW_PCA2918_2011_MDDS%20with%20UI.xlsx"),
    ("census_pca_blr_b", "shared", CENSUS + "6774", CENSUS + "6774/download/9851/DDW_PCA2929_2011_MDDS%20with%20UI.xlsx"),
    ("census_pca_hyd_medak", "shared", CENSUS + "6726", CENSUS + "6726/download/9803/DDW_PCA2804_2011_MDDS%20with%20UI.xlsx"),
    ("census_pca_hyd_hyd", "shared", CENSUS + "6727", CENSUS + "6727/download/9804/DDW_PCA2805_2011_MDDS%20with%20UI.xlsx"),
    ("census_pca_hyd_ranga", "shared", CENSUS + "6728", CENSUS + "6728/download/9805/DDW_PCA2806_2011_MDDS%20with%20UI.xlsx"),
    ("census_c20_city", "shared", CENSUS + "42520", CENSUS + "42520/download/46146/PC11_C20city.xlsx"),
]


def fetch(url):
    # TLS is always verified: a source that fails verification is logged as failed.
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context()) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Disposition", "")


def main():
    log_path = ROOT / "data/metadata/fetch_log.json"
    log = {e["id"]: e for e in json.loads(log_path.read_text())} if log_path.exists() else {}
    for sid, city, page, url in SOURCES:
        folder = ROOT / "data/raw" / city / sid
        if log.get(sid, {}).get("status") == "ok" and any(folder.glob("*")):
            continue
        entry = {"id": sid, "city": city, "source_page": page, "download_url": url,
                 "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        try:
            body, final, disp = fetch(url)
            name = url.rstrip("/").split("/")[-1]
            if name == "download":
                name = disp.split("filename=")[-1].strip('"; ') if "filename=" in disp else final.rsplit("/", 1)[-1]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(body)
            entry.update(status="ok", file=str((folder / name).relative_to(ROOT)), bytes=len(body),
                         sha256=hashlib.sha256(body).hexdigest())
        except Exception as e:  # recorded, never swallowed
            entry.update(status="failed", error=f"{type(e).__name__}: {e}")
        log[sid] = entry
        print(sid, entry["status"], entry.get("bytes", entry.get("error")), flush=True)
        log_path.write_text(json.dumps(list(log.values()), indent=1))
        time.sleep(1.5)


if __name__ == "__main__":
    main()
