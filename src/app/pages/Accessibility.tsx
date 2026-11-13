import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useJson, CITY_COLOR, CITY_LABEL, type City } from '../data';
import { Badge, CityName, Ext, Loading, PageHead } from '../ui';

const BAND: Record<string, { label: string; color: string }> = {
  'Red (under 50)': { label: 'Red', color: 'var(--serious)' },
  'Yellow (50 to 79)': { label: 'Yellow', color: '#c98500' },
  'Green (80 and over)': { label: 'Green', color: 'var(--good)' },
};
function Score({ page }: { page: any }) {
  if (!page || page.lighthouse_score == null) return <span className="small">Not scored</span>;
  const b = BAND[page.band];
  return <span style={{ whiteSpace: 'nowrap' }}>{page.lighthouse_score} <span className="small"><span className="cityMark" style={{ background: b.color, marginLeft: 4, marginRight: 3 }} aria-hidden="true" />{b.label}</span></span>;
}

const STAGES = ['Discovery', 'Navigation', 'Authentication', 'Form completion', 'Submission', 'Tracking', 'Service completion'];

export function Accessibility() {
  const { data, error } = useJson('audit.json');
  const j = useJson('journeys.json');
  const sc = useJson('scores.json');
  const [persona, setPersona] = useState(0);
  if (!data || !j.data || !sc.data) return <div className="page"><PageHead title="Accessibility analysis" /><Loading error={error || j.error || sc.error} /></div>;
  const p = j.data.personas[persona];
  const lh = sc.data;
  const lhPage = (id: string) => lh.pages.find((x: any) => x.id === id);
  const typeRows = lh.brief.filter((b: any) => b.bengaluru != null || b.hyderabad != null).map((b: any) => ({ name: b.type, Bengaluru: b.bengaluru, Hyderabad: b.hyderabad }));
  const chart = data.categories.map((c: any) => ({ name: c.label, Bengaluru: c.bengaluru, Hyderabad: c.hyderabad }));
  return (
    <div className="page">
      <PageHead title="Accessibility analysis">
        <p>We ran axe-core {data.axe_version} against WCAG 2.0, 2.1 and 2.2 Level A and AA rules on {data.counts.audited} official pages on {data.audit_date}, and added scripted checks for keyboard focus, reflow and language controls. We also ran Lighthouse {lh.version} on the same pages.</p>
        <p>Automated tools catch only part of what WCAG requires. A low count does not mean a site is accessible, and no disabled person has tested these portals for this study yet.</p>
      </PageHead>

      <section className="sec">
        <h2>Which problems appear on each city's pages</h2>
        <p className="prose-body mb-3">Share of audited pages with at least one failure in each category: {data.counts.bengaluru} pages in Bengaluru, {data.counts.hyderabad} in Hyderabad. Bars show how widespread a problem is, not how severe. The sample was chosen by task and several pages share a website, so these are not independent counts or a census of each city's websites.</p>
        <div style={{ width: '100%', height: 54 * chart.length + 70 }}>
          <ResponsiveContainer>
            <BarChart data={chart} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }} barGap={2}>
              <CartesianGrid horizontal={false} stroke="#c3d0d3" />
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fill: '#465962', fontSize: 13 }} />
              <YAxis type="category" dataKey="name" width={170} tick={{ fill: '#13242c', fontSize: 13 }} />
              <Tooltip formatter={(v: number) => `${v}% of audited pages`} />
              <Legend verticalAlign="top" height={30} />
              <Bar dataKey="Bengaluru" fill={CITY_COLOR.bengaluru} barSize={13} radius={[0, 3, 3, 0]} isAnimationActive={false} />
              <Bar dataKey="Hyderabad" fill={CITY_COLOR.hyderabad} barSize={13} radius={[0, 3, 3, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <details className="mt-3"><summary>Table view of this chart</summary>
          <div className="tscroll mt-2"><table className="tbl"><thead><tr><th scope="col">Category</th><th scope="col">WCAG reference</th><th scope="col" className="num">Bengaluru</th><th scope="col" className="num">Hyderabad</th></tr></thead>
            <tbody>{data.categories.map((c: any) => <tr key={c.label}><td>{c.label}</td><td className="small">{c.wcag}</td><td className="num">{c.bengaluru}%</td><td className="num">{c.hyderabad}%</td></tr>)}</tbody></table></div>
        </details>
      </section>

      <section className="sec">
        <h2>Lighthouse scores</h2>
        <p className="prose-body mb-3">On pages built for a specific service, Bengaluru's median score is {lh.cities.bengaluru.median} across {lh.cities.bengaluru.pages} pages, and Hyderabad's is {lh.cities.hyderabad.median} across {lh.cities.hyderabad.pages}. {lh.cities.bengaluru.red + lh.cities.hyderabad.red === 0 ? 'No page scored red.' : `${lh.cities.bengaluru.red + lh.cities.hyderabad.red} pages scored red.`} These samples are small, and many pages are only the first sign-in step of a service. <Badge kind="measured" /></p>
        <div className="grid gap-8 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <div>
            <h3 className="text-lg mb-2">Scores by service</h3>
            <div style={{ width: '100%', height: 62 * typeRows.length + 70 }}>
              <ResponsiveContainer>
                <BarChart data={typeRows} layout="vertical" margin={{ left: 4, right: 36, top: 0, bottom: 4 }} barGap={2}>
                  <CartesianGrid horizontal={false} stroke="#c3d0d3" />
                  <XAxis type="number" domain={[0, 100]} ticks={[0, 50, 80, 100]} tick={{ fill: '#465962', fontSize: 13 }} />
                  <YAxis type="category" dataKey="name" width={150} tick={{ fill: '#13242c', fontSize: 13 }} />
                  <Tooltip formatter={(v: number) => `${v} out of 100`} />
                  <Legend verticalAlign="top" height={30} />
                  {(['Bengaluru', 'Hyderabad'] as const).map((c) => (
                    <Bar key={c} dataKey={c} fill={CITY_COLOR[c.toLowerCase() as City]} barSize={15} radius={[0, 3, 3, 0]} isAnimationActive={false}>
                      <LabelList dataKey={c} position="right" style={{ fill: '#13242c', fontSize: 12 }} />
                    </Bar>
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="small mt-1">The Bengaluru grievance bar is missing because bbmp.sahaaya.in failed with a certificate error. We found no web page for a Bengaluru pet licence, or for e-waste pickup in either city. e-Janma uses one page for birth and death certificates.</p>
            <details className="mt-3"><summary>Table view of this chart</summary>
              <div className="tscroll mt-2"><table className="tbl"><thead><tr><th scope="col">Service</th><th scope="col" className="num">Bengaluru</th><th scope="col" className="num">Hyderabad</th></tr></thead>
                <tbody>{lh.brief.map((b: any) => <tr key={b.type}><td>{b.type}</td><td className="num">{b.bengaluru ?? (b.bengaluru_id ? 'Not scored' : 'No web page found')}</td><td className="num">{b.hyderabad ?? (b.hyderabad_id ? 'Not scored' : 'No web page found')}</td></tr>)}</tbody></table></div>
            </details>
          </div>
          <div>
            <h3 className="text-lg mb-2">Service pages by band</h3>
            <table className="tbl">
              <thead><tr><th scope="col">Band</th><th scope="col" className="num"><CityName city="bengaluru" /></th><th scope="col" className="num"><CityName city="hyderabad" /></th></tr></thead>
              <tbody>
                <tr><td>Green (80 and over)</td><td className="num">{lh.cities.bengaluru.green}</td><td className="num">{lh.cities.hyderabad.green}</td></tr>
                <tr><td>Yellow (50 to 79)</td><td className="num">{lh.cities.bengaluru.yellow}</td><td className="num">{lh.cities.hyderabad.yellow}</td></tr>
                <tr><td>Red (under 50)</td><td className="num">{lh.cities.bengaluru.red}</td><td className="num">{lh.cities.hyderabad.red}</td></tr>
                <tr><td>Lowest score</td><td className="num">{lh.cities.bengaluru.min}</td><td className="num">{lh.cities.hyderabad.min}</td></tr>
                <tr><td>Highest score</td><td className="num">{lh.cities.bengaluru.max}</td><td className="num">{lh.cities.hyderabad.max}</td></tr>
              </tbody>
            </table>
            <p className="prose-body mt-4">A high score does not mean a page is accessible. Lighthouse summarises automated checks from one run: Ahara scored 96 with 6 contrast failures flagged. Several pages also share a website, so these figures do not rank the cities.</p>
          </div>
        </div>
      </section>

      <section className="sec">
        <h2>Every page we tested</h2>
        <p className="prose-body mb-3">Results apply only to the page and date shown, and to what appears before sign-in. <Badge kind="measured" /></p>
        <div className="tscroll">
          <table className="tbl" style={{ minWidth: 1090 }}>
            <caption>Lighthouse is the 0 to 100 accessibility score. Rules failed counts distinct WCAG rules in axe-core. Elements counts every failing element on the page. Focus ring counts the 20 Tab presses that showed a detectable outline or shadow.</caption>
            <thead><tr><th scope="col">Page</th><th scope="col">City</th><th scope="col">Lighthouse</th><th scope="col" className="num">Rules failed</th><th scope="col" className="num">Elements</th><th scope="col">Critical or serious rules</th><th scope="col">Page language declared</th><th scope="col">Language controls found</th><th scope="col" className="num">Focus ring</th><th scope="col">Reflow at 320 px</th></tr></thead>
            <tbody>
              {data.pages.map((r: any) => (
                <tr key={r.id}>
                  <td><Ext href={r.url}>{r.label}</Ext></td>
                  <td>{r.city === 'national' ? 'National' : <CityName city={r.city as City} />}</td>
                  <td><Score page={lhPage(r.id)} /></td>
                  {r.status === 'audited' ? <>
                    <td className="num">{r.rules}</td><td className="num">{r.nodes}</td><td className="small">{r.severe.join(', ') || 'None'}</td>
                    <td>{r.htmlLang || <Badge kind="failed">Missing</Badge>}</td><td className="small">{r.languages.join(', ') || 'None detected'}</td>
                    <td className="num">{r.focusRing}/20</td><td>{r.overflow ? 'Scrolls sideways' : 'Fits'}</td>
                  </> : <td colSpan={7}><Badge kind="failed" /> <span className="small">{r.error}. Our browser refused the connection. Recheck by hand before citing.</span></td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <details className="mt-4"><summary>What was tested by a person</summary>
          <p className="prose-body mt-2">Nothing on this table was checked by a screen-reader user or a human auditor. Still required: screen-reader passes with NVDA or TalkBack, text resizing to 200%, plain-language review in Kannada, Telugu and Urdu, and the quality of each translation. A "language control found" means a control exists, not that the translated service is complete.</p>
        </details>
      </section>

      <section className="sec">
        <h2>Language: the people a control does not reach</h2>
        <div className="prose-body mb-4"><p>{j.data.language_note}</p></div>
        <div className="grid gap-8 md:grid-cols-2">
          {(['bengaluru', 'hyderabad'] as City[]).map((c) => (
            <div key={c}>
              <h3 className="text-lg mb-2"><CityName city={c} /></h3>
              <table className="tbl"><caption>Mother tongue, Census 2011 (C-16)</caption>
                <thead><tr><th scope="col">Language</th><th scope="col" className="num">Share</th><th scope="col" className="num">Audited pages with a control</th></tr></thead>
                <tbody>{data.language_reach[c].map((l: any) => <tr key={l.language}><td>{l.language}</td><td className="num">{l.pct}%</td><td className="num">{l.pages} of {data.counts[c]}</td></tr>)}</tbody>
              </table>
            </div>
          ))}
        </div>
      </section>

      <section className="sec">
        <h2>Three citizen journeys</h2>
        <p className="prose-body">These personas are research devices. <strong>They are not real people, and we did not observe anyone using these portals.</strong> Each friction point links a hypothesis to an automated result where one exists; the rest are questions for fieldwork.</p>
        <div className="flex flex-wrap gap-2 my-4" role="group" aria-label="Choose a persona">
          {j.data.personas.map((x: any, i: number) => <button key={x.name} type="button" className="btn" aria-pressed={persona === i} onClick={() => setPersona(i)}>{x.short}</button>)}
        </div>
        <Badge kind="hypothetical" />
        <h3 className="text-2xl mt-3">{p.name}</h3>
        <p className="prose-body mt-1">{p.summary}</p>
        <ol className="mt-5">
          {STAGES.map((s, i) => {
            const st = p.stages.find((x: any) => x.stage === s);
            return (
              <li key={s} className="grid md:grid-cols-[170px_1fr] gap-x-4 py-3" style={{ borderTop: '1px solid var(--rule)' }}>
                <div className="font-display font-semibold text-lg"><span aria-hidden="true" style={{ color: 'var(--muted)' }}>{i + 1} </span>{s}</div>
                <div>
                  <p>{st.friction}</p>
                  <p className="small mt-1">{st.measured ? <><Badge kind="measured">Evidence</Badge> {st.evidence}</> : <><Badge kind="hypothetical">Untested</Badge> {st.evidence}</>}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </section>
      <p className="small pb-8">{CITY_LABEL.bengaluru} and {CITY_LABEL.hyderabad} results are snapshots. Sites change without notice, so re-run <code>audit/run_audit.mjs</code> before citing them.</p>
    </div>
  );
}
