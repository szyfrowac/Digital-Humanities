# Class walkthrough (about 8 minutes)

Before class, run `npm run build && npm run preview` and open <http://127.0.0.1:4173>. Check that map tiles load on the classroom network.

## 1. Overview (1 minute)
**Show** the two cities drawn at the same scale.
**Say:** "We are asking who a civic screen leaves out. We compare ten everyday tasks in two cities. Our datasets still use old boundaries, because both civic bodies were reorganised in the last 14 months, so the institutions are moving under the interfaces."

## 2. City map (2 minutes)
**Do:** switch on bus stops, then switch cities. Search "Namma" and open a result. Point to its date, publisher and source link.
**Say:** "Every marker comes from a listed source. Hollow markers are community-mapped. The dates differ by years, so we also ran one OpenStreetMap query on one day for both cities."
**Point out the gap:** ration shops and MeeSeva centres are absent because we found no verified location data, and we did not invent any.

## 3. Civic tasks (1 minute)
**Do:** filter to "Accessing the Public Distribution System".
**Say:** "'Not verified' means we could not confirm something. It never means a service does not exist. We stopped before sign-in and submitted nothing."

## 4. Accessibility (2 minutes)
**Do:** show the chart, then switch personas.
**Say:** "Contrast failures appear on most audited pages in both cities. These are automated results, and they catch only part of WCAG. The personas are hypothetical, and each step says whether it rests on evidence or is a fieldwork question."

## 5. Findings (2 minutes)
**Lead with these three:**
1. **Language:** among the pages sampled, we found a Tamil option on 0 of 16 Bengaluru pages and an Urdu option on 2 of 23 Hyderabad pages, despite 16.3% and 29.5% mother-tongue shares. Both Urdu pages also have Google Translate, so those options may be machine translation.
2. **Literacy:** nearly two million residents across both cities were recorded as non-literate in 2011, so the offline route matters.
3. **Distance is not access:** primary health distance looks similar in both cities, and listed slum locations are closer than the grid average. That moves the question from where clinics are to how people experience them.

## What works
- All five pages, the map with real data, search, layer controls and source details.
- 28 map layers across both cities, a 20-record comparison, and a repeatable audit covering 40 pages that loaded and 1 that did not.
- Our own pages pass automated axe-core checks and work at phone width. This has not been tested by disabled users either.

## What is incomplete
- No user testing or interviews.
- Sign-in, forms, submission and tracking untested. Mobile apps untested.
- Straight-line distance only, with no travel time or population weighting.
- Data as old as 2011, with mismatched boundaries.

## If asked
- **"Which city is better?"** This study does not rank them. Dates, samples and boundaries differ too much.
- **"Is Hyderabad's metro less accessible?"** We cannot say. OSM tagging differs, and that measures mapping.
- **"Are these scores official?"** No. They are automated results from one day. Re-run the audit before citing them.

## Next steps
Interview residents and disabled persons' organisations, do screen-reader testing with users, review translations with native speakers, audit stations in person, and model travel time.
