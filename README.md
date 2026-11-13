# Can You Access Your City?

Digital accessibility and inclusive citizenship in Bengaluru and Hyderabad. A digital humanities research MVP with an interactive map, a comparison of ten civic tasks, a WCAG audit, persona journeys and preliminary findings.

**Status:** preliminary class research. No user testing has taken place.

## Run the app

You need Node 22 (tested on v22.23.3). The processed data is already in `public/data`, so nothing else is required.

```bash
npm install
npm run dev
```

Open <http://127.0.0.1:5173>.

To run the production build, which is the safest option for a demo:

```bash
npm run build
npm run preview
```

Open <http://127.0.0.1:4173>.

The background map needs internet access for OpenStreetMap tiles. Without it, ward outlines, markers and all other pages still work.

## Rebuild the data

You need Python 3.10 or later. Run these from the project root.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

python3 -I src/data/fetch_sources.py          # skips files already downloaded
python3 -I src/data/fetch_osm.py              # same-day OSM extract; retries if Overpass is busy
.venv/bin/python -I src/data/process.py       # cleaning and spatial analysis
python3 -I src/data/write_source_register.py

cd audit && npm install && node run_audit.mjs urls.json && cd ..
#  To force a full re-audit, first delete data/raw/shared/accessibility_audit/results.json
python3 -I src/analysis/build_site_data.py    # site JSON and Research/findings.md
cd audit && node run_lighthouse.mjs urls.json && cd ..
python3 -I src/analysis/build_scores.py        # merges Lighthouse and WAVE into data/processed/audit_scores.csv
```

The audit uses installed Google Chrome through Playwright and takes about seven minutes.

## Test

With the app running:

```bash
cd audit
node test_app.mjs http://127.0.0.1:5173   # end-to-end checks and axe-core on our own pages
cd ..
python3 -I audit/check_links.py           # checks cited URLs
```

## Project layout

| Path | Contents |
|---|---|
| `src/app/` | React and TypeScript application |
| `src/data/` | Download and processing scripts |
| `src/analysis/` | Joins audit and analysis results into site data |
| `audit/` | Accessibility audit and app tests |
| `public/data/` | Data the site reads |
| `data/raw/` | Original files, unchanged. **Contains operators' names and phone numbers, so do not publish it.** Ignored by git |
| `data/processed/` | Cleaned GeoJSON, `civic_services.csv`, `excluded_records.csv`, `analysis.json` |
| `data/metadata/` | `dataset_inventory.csv`, `source_register.csv`, `data_quality_report.md`, `fetch_log.json`, link checks |
| `Research/` | Methodology, research questions, findings, limitations |
| `PRESENTATION_WALKTHROUGH.md` | Class demo script |
| `PROJECT_PROGRESS.md` | Work log |

## Data licences

OpenStreetMap data is © OpenStreetMap contributors, under ODbL 1.0. OpenCity tags many datasets as public domain and leaves others unspecified, so check with the original publisher before reuse. Census tables are from the Office of the Registrar General, India.
