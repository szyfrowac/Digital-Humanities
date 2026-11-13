# Project progress log

All dates are 4 November 2026.

## Phase 1: Reconnaissance (done)
- The project directory was empty, so the stack was chosen fresh: React, TypeScript, Vite, Tailwind, Leaflet, Recharts; Python pipeline.
- MCP servers found by `claude mcp list`: `playwright` (browser automation; connected), `academic-search` (Crossref-style search; connected), `claude.ai Claude Docs` and `claude.ai Google Drive` (connected, not relevant to data collection). There is no government-data or GIS MCP server, so data came from public APIs over HTTPS.

## Phase 2: Dataset discovery (done)
- OpenCity CKAN API: facility layers for both cities.
- Census NADA: C-16 town tables, C-20 City, PCA by district, PCA Slum.
- OSM Overpass: same-day extract after initial failures.
- Unavailable: verified ration shop and MeeSeva locations; Telangana Open Data API; official BMRCL GTFS.

## Phase 3: Processing (done)
- Pipeline with provenance, exclusions log, duplicate flags and personal-data removal.
- Cross-check: PCA and C-16 population totals must match exactly, enforced by an assertion.
- Independent brute-force check reproduces slum-distance medians.
- A side note raised during the work flagged that dataset ages differ. In response, every layer shows its date and OSM provides a same-day comparison.

## Phase 4: Audit (done)
- Three runs. The first exposed weak language detection and a meaningless readability score. The second lacked Tamil, Bengaluru's second language. The third is the one reported.
- The audit initially tried to bypass TLS errors. A permission control blocked it, and verified TLS is now required, with failures recorded as results.

## Phase 5: Application (done)
- Five pages built. Visual review caught a ring-simplification bug that blanked ward outlines, and a basemap that now requires an API key. Both fixed; basemap is now OSM.
- Self-audit found our own WCAG 2.2 target-size failures. Fixed.

## Phase 6: Validation (done)
- `audit/test_app.mjs` passes on the production build: all pages, map interactions, 20 records, no console errors, no sideways scrolling at 375 px, and axe-core with no violations on any page.
- Links checked in Python and Chrome, with results in `data/metadata`. One dead deep link replaced; one reset connection recorded as a barrier.

## Phase 7: Lighthouse and WAVE
- Lighthouse complete: 30 pages scored, Sahaaya failed on its certificate, and the `bbmp.gov.in` duplicate is excluded from the merged results. Shown on the Accessibility page.
- Task-specific pages added after review, including MeeSeva and Seva Sindhu routes. BuildNow could not be scored in Lighthouse after a retry; its axe result is recorded.
- WAVE API paused after two tests, with 98 of 100 credits left. WAVE extension results by hand are pending.

## Remaining
User research, sign-in journeys, mobile apps, travel-time analysis, ration shop and MeeSeva locations, human accessibility review.
