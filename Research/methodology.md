# Methodology

Status: preliminary, classroom MVP. Fieldwork has not begun.

## Evidence types

Every result is labelled as one of these on the site.

| Label | Meaning |
|---|---|
| Primary source | Published by the originating authority, such as Census tables |
| Secondary source | News or a republishing portal |
| Measured by automated test | Output of axe-core or our scripted probes |
| Derived by this project | Calculated by us from the above |
| Hypothetical persona | A research device, not an observed person |
| Not verified | We could not confirm it. This never means "unavailable" |

## Data pipeline

1. `src/data/fetch_sources.py` and `src/data/fetch_osm.py` download sources to `data/raw/<city>/<source>/`, logging URL, time and SHA-256 in `data/metadata/fetch_log.json`. TLS is always verified.
2. `src/data/process.py` normalises fields and writes GeoJSON. Records with missing or implausible coordinates are itemised in `data/processed/excluded_records.csv`. Exact duplicates (name plus coordinates to five decimals) are flagged and left out of counts.
3. Personal fields (`applicant_name`, `csc_id`, `Mobileno`, `OPR`, `NODAL_OFFI`, `Contact_No`) are removed from all processed outputs.
4. `src/analysis/build_site_data.py` joins results into the JSON the site reads, so numbers in findings come from data rather than being typed by hand.

## Spatial analysis

- **Study areas:** GBA 369-ward map (December 2025) for Bengaluru; GHMC 155-feature ward map (2022) for Hyderabad. Facilities outside are kept, flagged and still count as "nearest", which avoids an edge effect.
- **Measure:** great-circle distance from each point of a 500 m grid, and from each listed slum location, to the nearest facility in a group. Reported as median, 90th percentile and share within 1 km.
- **Comparison groups:** primary health means UPHCs and Namma Clinics in Bengaluru, and Basti Dawakhanas, UPHCs and one PHC in Hyderabad. OSM hospitals and clinics use one query on one day for both cities, as a check against differences in dataset age.
- **Verification:** slum medians were reproduced with an independent brute-force calculation.
- **Not claimed:** proximity is not accessibility. Travel time, affordability, physical access, staffing and opening hours are separate and unmeasured. Wards are not compared directly, because their sizes and number differ.

## Accessibility audit

- **Tools:** axe-core with WCAG 2.0, 2.1 and 2.2 A/AA tags, in headless Chrome driven by Playwright (`audit/run_audit.mjs`).
- **Scripted probes:** 20 Tab presses to detect focus and a visible ring; reflow at 320 px; viewport zoom settings; declared page language; language controls; skip links; sign-in signals; counts of links, fields and words.
- **Sample:** about 40 public pages, including general portal pages and service-specific pages listed in `data/metadata/audit_url_list.csv`. Only pages reachable without signing in; nothing was submitted. TLS errors were recorded as results rather than bypassed.
- **Dropped measure:** an English Flesch readability score gave meaningless values on bilingual pages (down to about -105) and was removed.
- **Excluded from findings:** failures on URLs we guessed. Only addresses that official sources point to count as evidence.
- **Not done:** human screen-reader testing, 200% text-resize testing, translation review, or any test with disabled users.

## Lighthouse and WAVE

- **Lighthouse 12.8.2** ran locally with the desktop preset and the accessibility category only (`audit/run_lighthouse.mjs`). Reports are in `data/raw/shared/lighthouse/`, and scores are merged into `data/processed/audit_scores.csv`.
- The colour bands follow the course brief: red under 50, yellow 50 to 79, green 80 and over. Its later section uses 75 as the green cut-off, so state which one you use.
- **WAVE API** results are not used. WAVE fetches pages from WebAIM's servers. One test timed out, and another received a page titled "Error Page" instead of the GHMC site, so that record is marked invalid. The WAVE browser extension, run by hand, is the planned route.

## Citizen journeys

Three hypothetical personas move through seven stages: discovery, navigation, authentication, form completion, submission, tracking and service completion. Each friction point is either tied to an automated result or marked as an untested fieldwork question. No participants were involved.

## Ethics

- No citizen data was collected, and no accounts were created.
- Operators' and officers' names and phone numbers in public files are excluded from every output, and `data/raw` is ignored by git. Do not republish it.
- Slum locations are public government listings. They are shown as context and must not be read as a description of residents.
