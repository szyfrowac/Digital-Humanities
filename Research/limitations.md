# Limitations

## Comparability

- **Dataset age varies widely.** Hyderabad portal layers are mostly from 2018 or undated. Bengaluru layers run from undated to 2026. Differences in counts may reflect how recent a list is. Every map layer shows its date, and OSM provides a same-day comparison.
- **OSM is not neutral.** Mapping effort differs between cities. OSM shows 509 toilets in Bengaluru and 101 in Hyderabad, while the official lists show 613 and 574, so community coverage clearly varies.
- **Boundaries differ and have changed.** BBMP became GBA in 2025, and GHMC was split in 2026 after absorbing nearby local bodies. Our Hyderabad ward map covers about 616 km², not the roughly 2,053 km² reported after the merger.
- **Census geography differs by table.** C-16 and PCA use the municipal corporation with outgrowths. C-20 uses the wider urban agglomeration, so we do not compute disability rates.
- **The Census is old.** 2011 is the latest published baseline; figures are fifteen years out of date.

## Measurement

- Straight-line distance on an unweighted grid includes parks, lakes and other unbuilt land, and ignores roads, cost and the physical environment.
- Automated tests detect only part of WCAG. A clean result does not prove a page is accessible.
- The language scanner looks for labelled controls and common URL patterns. It can miss custom widgets, and finding a control says nothing about translation completeness.
- Pages are not independent. Several share one website or template, and GHMC contributes more pages than any other site. Findings report both page and website counts where this matters.
- A Lighthouse score is a weighted summary of automated checks from one run. A high score does not show a page is accessible: Ahara scored 96 with 6 contrast failures flagged. Scores can also vary between runs.
- Link and word counts are rough proxies for complexity, not usability scores.
- Portal availability changed within one day. `bbmp.gov.in` returned a certificate error on the first run and later redirected to the GBA site, so all portal results are snapshots.
- Nine portal addresses failed certificate verification in Python ("unable to get local issuer") yet loaded in Chrome with normal validation, which suggests incomplete server certificate chains. Some non-browser tools and older devices may therefore fail to connect. We have not confirmed the cause. `bbmp.sahaaya.in` failed in Chrome too, with a certificate name mismatch.
- Automated browsers may be treated differently from people's phones, and pages were tested on a desktop connection.

## Gaps

- **No verified location data** for ration shops or MeeSeva centres.
- **Mobile apps untested**, including Sahaaya 2.0 and MyCURE, even though apps may now be the main route.
- **Journeys stop before sign-in.** Authentication, forms, submission and tracking are unverified.
- **No user research.** Personas are hypothetical. Nothing here records anyone's experience.
- **Licences.** OpenCity marks many sets as public domain and others as unspecified. Check with the original publisher before reuse beyond this class project. OSM data is under ODbL and needs attribution.
