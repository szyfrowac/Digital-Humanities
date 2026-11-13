import { useMemo } from 'react';
import { useJson, CITY_COLOR, CITY_LABEL, fmt, type City } from '../data';
import { Badge, CityName, Ext, Loading } from '../ui';

const KM_PER_PX = 0.118;
function project(fc: any, kmPerPx: number) {
  let minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
  for (const f of fc.features) for (const p of f.geometry.coordinates) for (const r of p) for (const [x, y] of r) {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
  }
  const lat0 = (minY + maxY) / 2;
  const kx = 111.32 * Math.cos(lat0 * Math.PI / 180) / kmPerPx, ky = 110.57 / kmPerPx;
  const W = (maxX - minX) * kx, H = (maxY - minY) * ky;
  const paths = fc.features.map((f: any) => f.geometry.coordinates.map((p: any) => p.map((r: any) =>
    'M' + r.map(([x, y]: number[]) => `${((x - minX) * kx).toFixed(1)},${((maxY - y) * ky).toFixed(1)}`).join('L') + 'Z').join('')).join(''));
  return { W, H, paths };
}
function Plate({ city, wardsFc, area, wards }: { city: City; wardsFc: any; area: number; wards: number }) {
    const p = useMemo(() => project(wardsFc, KM_PER_PX), [wardsFc]);
  return (
    <figure className="m-0">
      <svg viewBox={`-2 -2 ${p.W + 4} ${p.H + 4}`} width={Math.round(p.W)} style={{ maxWidth: '100%', height: 'auto', display: 'block' }} role="img"
        aria-label={`Outline of ${CITY_LABEL[city]} showing ${wards} wards, drawn at the same scale as the other city.`}>
        <path d={p.paths.join('')} fill={CITY_COLOR[city]} fillOpacity={0.13} stroke={CITY_COLOR[city]} strokeWidth={0.75} />
      </svg>
      <figcaption className="mt-2"><strong className="font-display text-xl">{CITY_LABEL[city]}</strong><br />
        <span className="small">{wards} wards, {fmt(Math.round(area))} km² in this study</span></figcaption>
    </figure>
  );
}

export function Overview() {
  const a = useJson('analysis.json'), b = useJson('bengaluru_wards.json'), h = useJson('hyderabad_wards.json');
  if (!a.data || !b.data || !h.data) return <div className="page py-10"><Loading error={a.error || b.error || h.error} /></div>;
  const { census, spatial } = a.data;
  const kmBar = 10 / KM_PER_PX;
  const rows: { label: string; b: string; h: string; note: string }[] = [
    { label: 'Population, 2011', b: fmt(census.literacy.bengaluru.population), h: fmt(census.literacy.hyderabad.population), note: 'Census PCA, BBMP and GHMC with outgrowths' },
    { label: 'Literacy, age 7 and over', b: census.literacy.bengaluru.literacy_7plus_pct + '%', h: census.literacy.hyderabad.literacy_7plus_pct + '%', note: 'Computed from PCA' },
    { label: 'Residents aged 7+ recorded as non-literate', b: fmt(census.literacy.bengaluru.non_literate_7plus), h: fmt(census.literacy.hyderabad.non_literate_7plus), note: 'Computed from PCA' },
    { label: 'Largest mother tongue', b: `${census.language.bengaluru.top[0].language}, ${census.language.bengaluru.top[0].pct}%`, h: `${census.language.hyderabad.top[0].language}, ${census.language.hyderabad.top[0].pct}%`, note: 'Census C-16' },
    { label: 'Second-largest mother tongue', b: `${census.language.bengaluru.top[1].language}, ${census.language.bengaluru.top[1].pct}%`, h: `${census.language.hyderabad.top[1].language}, ${census.language.hyderabad.top[1].pct}%`, note: 'Census C-16' },
    { label: 'Persons recorded with a disability', b: fmt(census.disability.bengaluru.total), h: fmt(census.disability.hyderabad.total), note: 'Census C-20; urban agglomeration, a wider area than the rows above' },
  ];
  return (
    <div className="page">
      <section className="pt-10 pb-10">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,4fr)_minmax(0,8fr)] items-end">
          <div>
            <h1 tabIndex={-1} id="page-title" className="text-[3rem] md:text-[4.25rem]" style={{ lineHeight: 1.02 }}>Can you access your city?</h1>
            <p className="prose-body mt-5">Filing a complaint, paying tax or finding a clinic now often begins on a screen. We ask who that screen leaves out, comparing two Indian cities across ten everyday civic tasks.</p>
          </div>
          <div>
            <div className="flex flex-wrap gap-x-10 gap-y-6 items-end">
              <Plate city="bengaluru" wardsFc={b.data} area={spatial.bengaluru.study_area_km2} wards={spatial.bengaluru.wards} />
              <Plate city="hyderabad" wardsFc={h.data} area={spatial.hyderabad.study_area_km2} wards={spatial.hyderabad.wards} />
            </div>
            <div className="flex items-center gap-3 mt-3">
              <svg width={kmBar + 2} height="10" aria-hidden="true"><path d={`M1,1 V8 H${kmBar + 1} V1`} fill="none" stroke="var(--ink)" strokeWidth="1.25" /></svg>
              <span className="small">10 km. Both cities are drawn at the same scale.</span>
            </div>
          </div>
        </div>
      </section>

      <section className="sec two">
        <div>
          <h2 className="text-[1.75rem] mb-3">The question</h2>
          <blockquote className="prose-body m-0" style={{ fontSize: '1.25rem', lineHeight: 1.45 }}>
            How do the digital interfaces and underlying civic infrastructure of Bengaluru and Hyderabad influence citizens' ability to access essential public services, particularly across disability, language and cognitive usability barriers?
          </blockquote>
        </div>
        <div className="mt-8 md:mt-0">
          <h2 className="text-[1.75rem] mb-3">What we set out to do</h2>
          <ul className="prose-body list-disc pl-5 space-y-2">
            <li>Treat access as citizenship: who can actually use a public service, not whether it exists.</li>
            <li>Map public facilities with sources and dates in plain view.</li>
            <li>Test official portals against WCAG 2.2 with repeatable automated checks.</li>
            <li>Trace how a citizen's journey could break down, using personas clearly marked as hypothetical.</li>
          </ul>
        </div>
      </section>

      <section className="sec">
        <h2>The institutions are moving under the interfaces</h2>
        <div className="prose-body">
          <p>Both civic bodies at the centre of this study were reorganised just before it began. In Bengaluru, the Greater Bengaluru Authority and five corporations <Ext href="https://www.theweek.in/wire-updates/national/2025/09/02/srg2-ka-new-corporations.html">replaced the BBMP in September 2025</Ext>. In Hyderabad, the GHMC was <Ext href="https://www.etvbharat.com/en/state/telangana-govt-reorganises-ghmc-into-three-separate-municipal-corporations-enn26021104131">split into three corporations in February 2026</Ext>.</p>
          <p>Our datasets, ward maps and many portal addresses still carry the older structures. The Bengaluru property tax portal is still at a <code>bbmptax</code> address. For a citizen, knowing whom to ask has become part of the access problem.</p>
        </div>
        <p className="mt-3"><Badge kind="secondary">Secondary source: news reports</Badge></p>
      </section>

      <section className="sec">
        <h2>Two cities in the last Census</h2>
        <p className="prose-body mb-4">India's most recent published Census is from 2011, so these figures are fifteen years old and describe the old municipal boundaries.</p>
        <div className="tscroll">
          <table className="tbl" style={{ minWidth: 620 }}>
            <thead><tr><th scope="col">Measure</th><th scope="col" className="num"><CityName city="bengaluru" /></th><th scope="col" className="num"><CityName city="hyderabad" /></th><th scope="col">Source and scope</th></tr></thead>
            <tbody>{rows.map((r) => <tr key={r.label}><th scope="row" style={{ fontWeight: 500, borderBottom: '1px solid var(--rule)' }}>{r.label}</th><td className="num">{r.b}</td><td className="num">{r.h}</td><td className="small">{r.note}</td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="sec">
        <h2>How we worked</h2>
        <ol className="prose-body list-decimal pl-5 space-y-2">
          <li><strong>Collect.</strong> Download public datasets, keep each original file, and record its address, date and checksum.</li>
          <li><strong>Clean.</strong> Standardise fields, flag duplicates, itemise every exclusion, and remove operators' personal details.</li>
          <li><strong>Measure space.</strong> Calculate straight-line distance to the nearest facility across a 500 m grid. Distance is only a first signal: it says nothing about cost, quality, opening hours or a step at the door.</li>
          <li><strong>Audit interfaces.</strong> Run axe-core and scripted keyboard, reflow and language checks on the official portal pages. A person with lived experience of disability has not yet tested these sites.</li>
          <li><strong>Interpret.</strong> Build persona journeys and preliminary findings, with evidence, interpretation and limits kept apart.</li>
        </ol>
        <div className="flex flex-wrap gap-2 mt-5" aria-label="Evidence labels used on this site">
          <Badge kind="primary" /><Badge kind="secondary" /><Badge kind="measured" /><Badge kind="derived" /><Badge kind="hypothetical" /><Badge kind="notverified" />
        </div>
      </section>
    </div>
  );
}
