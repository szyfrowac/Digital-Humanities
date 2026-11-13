# Preliminary findings

Generated from `public/data/findings.json` by `src/analysis/build_site_data.py`. Every finding is preliminary. No citizens were consulted.

## 1. Basic accessibility failures are common on official pages in both cities

**Research question.** Do official civic portals meet basic automated WCAG checks?

**Evidence.** On the 39 city pages that loaded, axe-core flagged text contrast on 13 of 16 in Bengaluru and 22 of 23 in Hyderabad. The median page failed 4 distinct rules in Bengaluru and 5 in Hyderabad. The page language was undeclared on 4 Bengaluru pages and 17 Hyderabad pages. Counted by website rather than page, that is 4 of 14 sites and 6 of 10.

**Interpretation.** These failures are ones that a developer can fix and that a site owner can check automatically. Their persistence suggests accessibility is not yet a routine part of how these sites are published. The undeclared-language gap is wider in our Hyderabad sample, on pages and on websites alike, and it matters directly to screen-reader users.

**Limitations.** Automated tools detect only some WCAG issues. We tested public pages before sign-in, selected by task, on one day. Several pages share one website or template, so page counts are not independent; the sample has more GHMC pages than any other site. No page was tested by a disabled person, and this does not rank the cities' overall digital services.

**Supporting data.** [axe-core, the audit engine (results: public/data/audit.json)](https://www.deque.com/axe/); [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

## 2. A portal's language menu may not match the city's languages

**Research question.** Do language options on portals reflect the languages people in each city grew up speaking?

**Evidence.** In Census 2011, Kannada was the mother tongue of 42.1% in the BBMP area; Tamil (16.3%), Telugu (13.7%) and Urdu (13.0%) followed. In the GHMC area, Urdu was 29.5%. Our scan found a Tamil option on 0 of 16 Bengaluru pages and an Urdu option on 2 of 23 Hyderabad pages. Both Urdu pages also have a Google Translate widget, so these options may be machine translation. Translation widgets appeared on 3 and 5 pages respectively.

**Interpretation.** Portals seem to be organised around official state languages and English rather than the city's multilingual population. Language access may therefore rely on machine translation or on a helper. We read this as a political question about who a portal imagines its citizen to be, which needs testing with speakers.

**Limitations.** Mother tongue does not equal reading ability or preference, and many residents read more than one language. Our detector may miss unusual controls. We did not assess translation quality. Census data dates from 2011.

**Supporting data.** [Census 2011, C-16 town level, Karnataka](https://censusindia.gov.in/nada/index.php/catalog/10255); [Census 2011, C-16 town level, Andhra Pradesh (then including Hyderabad)](https://censusindia.gov.in/nada/index.php/catalog/10254)

## 3. A text-first portal leaves nearly two million residents across the two cities needing another route

**Research question.** How many residents does a text-based interface leave without a direct route?

**Evidence.** Census 2011 records 857,287 residents aged 7 and over as non-literate in the BBMP area (88.7% literacy) and 1,051,339 in the GHMC area (82.9%). Female literacy was 85.4% and 78.6%. Hyderabad's count is higher despite its smaller population.

**Interpretation.** High city-wide literacy can hide very large absolute numbers. For these residents, the offline counter, the assistance centre and the helper are the service. This is why we treat offline access as part of digital citizenship.

**Limitations.** The data is from 2011 and predates the current boundaries. Census literacy is self-reported and basic, and it does not measure digital literacy.

**Supporting data.** [Census 2011, PCA, Bangalore](https://censusindia.gov.in/nada/index.php/catalog/6763); [Census 2011, PCA, Hyderabad](https://censusindia.gov.in/nada/index.php/catalog/6727)

## 4. The Census shows different disability profiles, so one fix will not suit both

**Research question.** What does official data show about who needs accessible services?

**Evidence.** Census 2011 counts 251,561 disabled persons in the Bruhat Bangalore urban agglomeration and 294,072 in Hyderabad's. People recorded with a seeing disability make up 31.7% of that group in Bengaluru and 22.8% in Hyderabad. 'Any other' is 23.0% and 28.3%.

**Interpretation.** Large 'any other' shares show how much the official categories leave unnamed. The Census counted 8 categories, while the Rights of Persons with Disabilities Act 2016 recognises many more, so these numbers probably understate the need and cannot stand in for lived experience.

**Limitations.** The data is from 2011, is self-reported and uses the older disability categories, including a term that is now outdated. Urban agglomerations are wider than the study wards. We did not convert to population rates because we did not verify matching denominators.

**Supporting data.** [Census 2011, C-20 City: disabled population](https://censusindia.gov.in/nada/index.php/catalog/42520)

## 5. On our measure the two cities look similar for primary health, and they differ more for transit

**Research question.** How does straight-line nearness to public facilities compare across the two cities?

**Evidence.** The median point on a 500 m grid lies 0.73 km from a listed primary health facility in Bengaluru and 0.78 km in Hyderabad. OSM's same-day hospital and clinic data gives 0.47 and 0.54 km. For metro stations it is 2.32 and 3.53 km, and for bus stops 0.28 and 0.38 km.

**Interpretation.** The basic geography of primary care looks broadly alike, which pushes attention from where facilities are to whether people can use them. Metro distance is a true structural difference in network size. Distance is a measure of position and not of access.

**Limitations.** This is straight-line distance on an unweighted grid that includes unbuilt land. It says nothing about travel time, cost, staffing, opening hours or step-free entry. Layer dates differ, and the Bengaluru clinic list is from 2026 while the Hyderabad list is undated. Study boundaries predate each city's reorganisation.

**Supporting data.** [OpenCity: Bengaluru UPHCs and Namma Clinics](https://data.opencity.in/dataset/bengaluru-urban-public-health-centres); [OpenCity: Hyderabad public health centres](https://data.opencity.in/dataset/hyderabad-public-health-centres); [OpenStreetMap, Overpass query, 4 November 2026 (ODbL)](https://www.openstreetmap.org/); [OpenCity: Hyderabad Metro GTFS](https://data.opencity.in/dataset/hyderabad-metro-rail-gtfs)

## 6. Listed slum locations sit closer to primary health than the average grid point, which does not show better access

**Research question.** Do listed informal settlements appear spatially cut off from public primary healthcare?

**Evidence.** The median listed slum location is 0.43 km from a primary health facility in Bengaluru and 0.41 km in Hyderabad, against 0.73 and 0.78 km for the city grid. 84.4% and 90.1% of listed locations lie within 1 km.

**Interpretation.** In these lists, distance is not the obvious barrier for these settlements, and some clinics may be sited with them in mind. That moves the question to crowding, quality, cost, documents and how residents are treated, which only fieldwork can answer.

**Limitations.** The grid includes empty land, so this is a weak baseline. Lists are undated and count only recognised locations, and listing itself is a political act: unlisted settlements stay invisible here. Bengaluru's slum list names a covering UPHC for each location, so its closeness to clinics may be partly built in.

**Supporting data.** [OpenCity: Bengaluru UPHCs and Namma Clinics](https://data.opencity.in/dataset/bengaluru-urban-public-health-centres); [OpenCity: Hyderabad public health centres](https://data.opencity.in/dataset/hyderabad-public-health-centres); [OpenCity: Bengaluru urban slums](https://data.opencity.in/dataset/bengaluru-urban-slums); [OpenCity: Hyderabad slums](https://data.opencity.in/dataset/hyderabad-slums)

## 7. Whether a place is recorded as accessible depends on who has mapped it

**Research question.** How much do open maps know about physical accessibility?

**Evidence.** OSM has a wheelchair tag on 93.1% of Bengaluru metro stations against 42.9% in Hyderabad, and on 8.4% and 1.3% of hospitals. For 379 Hyderabad clinics there are 0 tags.

**Interpretation.** This measures the record, not the buildings. Silence in the data could be mistaken for absence of access or of need, and that is itself a form of invisibility. It makes the case for community accessibility mapping as a method and an outcome of this project.

**Limitations.** OSM tags are volunteer-contributed and unaudited. A difference between cities probably reflects mapper activity, and it must not be read as physical accessibility.

**Supporting data.** [OpenStreetMap, Overpass query, 4 November 2026 (ODbL)](https://www.openstreetmap.org/)

## 8. The civic record is out of step with the civic body

**Research question.** What does the state of the data itself tell us about citizenship?

**Evidence.** BBMP was replaced by GBA in September 2025, and GHMC was split in February 2026, yet the Bengaluru tax portal address still says 'bbmptax'. Hyderabad's layers from the portal date to 2018 or carry no date, and the census base is 2011. We found no verified downloadable location dataset for ration shops or MeeSeva centres; MeeSeva does show its own centres map, which we have not extracted.

**Interpretation.** Citizens and researchers alike navigate a layered archive of old names, boundaries and addresses. The services that matter most to low-income households were the hardest to locate as data, which may itself show whose access is being documented.

**Limitations.** 'Not found' reflects our search on one day, and such data may exist on portals we could not reach. News reports are secondary sources for the reorganisation dates.

**Supporting data.** [PTI via The Week: five corporations notified](https://www.theweek.in/wire-updates/national/2025/09/02/srg2-ka-new-corporations.html); [ETV Bharat: GHMC reorganised into three corporations](https://www.etvbharat.com/en/state/telangana-govt-reorganises-ghmc-into-three-separate-municipal-corporations-enn26021104131); [OpenCity data portal (full list: data/metadata/dataset_inventory.csv)](https://data.opencity.in/)
