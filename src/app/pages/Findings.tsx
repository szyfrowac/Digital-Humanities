import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useJson, CITY_COLOR, fmt, type City } from '../data';
import { Badge, CityName, Ext, Loading, PageHead } from '../ui';

function Compare({ rows, unit, max }: { rows: any[]; unit: string; max?: number }) {
  return (
    <div style={{ width: '100%', height: 56 * rows.length + 60 }}>
      <ResponsiveContainer>
        <BarChart data={rows} layout="vertical" margin={{ left: 4, right: 56, top: 0, bottom: 0 }} barGap={2}>
          <CartesianGrid horizontal={false} stroke="#c3d0d3" />
          <XAxis type="number" domain={[0, max ?? 'auto']} tick={{ fill: '#465962', fontSize: 13 }} unit={unit} />
          <YAxis type="category" dataKey="name" width={185} tick={{ fill: '#13242c', fontSize: 13 }} />
          <Tooltip formatter={(v: number) => `${v}${unit}`} />
          <Legend verticalAlign="top" height={28} />
          {(['Bengaluru', 'Hyderabad'] as const).map((c) => (
            <Bar key={c} dataKey={c} fill={CITY_COLOR[c.toLowerCase() as City]} barSize={14} radius={[0, 3, 3, 0]} isAnimationActive={false}>
              <LabelList dataKey={c} position="right" formatter={(v: number) => `${v}${unit}`} style={{ fill: '#13242c', fontSize: 12 }} />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
const Table = ({ rows, unit }: { rows: any[]; unit: string }) => (
  <details className="mt-2"><summary>Table view</summary>
    <div className="tscroll"><table className="tbl mt-2"><thead><tr><th scope="col">Measure</th><th scope="col" className="num">Bengaluru</th><th scope="col" className="num">Hyderabad</th></tr></thead>
      <tbody>{rows.map((r) => <tr key={r.name}><td>{r.name}</td><td className="num">{r.Bengaluru}{unit}</td><td className="num">{r.Hyderabad}{unit}</td></tr>)}</tbody></table></div>
  </details>
);

export function Findings() {
  const { data, error } = useJson('findings.json');
  const a = useJson('analysis.json');
  const inv = useJson<any[]>('layers.json');
  if (!data || !a.data || !inv.data) return <div className="page"><PageHead title="Preliminary findings" /><Loading error={error || a.error || inv.error} /></div>;
  const charts: Record<string, { rows: any[]; unit: string; max?: number }> = data.charts;
  return (
    <div className="page">
      <PageHead title="Preliminary findings">
        <p>These are starting points for discussion, drawn from public data and automated tests. None of them comes from talking to citizens, and none proves a cause.</p>
      </PageHead>
      {data.findings.map((f: any, i: number) => (
        <section key={f.id} className="sec">
          <div className="flex flex-wrap items-center gap-2 mb-2"><Badge kind="preliminary">Preliminary finding {i + 1}</Badge>{f.kinds.map((k: any) => <Badge key={k} kind={k} />)}</div>
          <h2 style={{ fontSize: '1.75rem', maxWidth: '38ch' }}>{f.title}</h2>
          <div className="grid lg:grid-cols-2 gap-x-10 gap-y-4 mt-4">
            <div className="prose-body">
              <h3 className="text-lg mt-0">Research question</h3><p>{f.question}</p>
              <h3 className="text-lg mt-4">Evidence</h3><p>{f.evidence}</p>
              <h3 className="text-lg mt-4">Interpretation</h3><p>{f.interpretation}</p>
              <h3 className="text-lg mt-4">Limitations</h3><p>{f.limitations}</p>
            </div>
            <div>
              {f.chart && charts[f.chart] && <>
                <h3 className="text-lg mb-2">{f.chart_title}</h3>
                <Compare {...charts[f.chart]} />
                <Table rows={charts[f.chart].rows} unit={charts[f.chart].unit} />
              </>}
              <h3 className="text-lg mt-4 mb-1">Supporting data</h3>
              <ul className="small list-disc pl-4">{f.datasets.map((d: any) => <li key={d.url}><Ext href={d.url}>{d.label}</Ext></li>)}</ul>
            </div>
          </div>
        </section>
      ))}
      <section className="sec">
        <h2>All map layers and their dates</h2>
        <p className="prose-body mb-3">Date differences limit every comparison above. Full provenance, checksums and quality counts are in <code>data/metadata</code>.</p>
        <div className="tscroll">
          <table className="tbl" style={{ minWidth: 760 }}>
            <thead><tr><th scope="col">City</th><th scope="col">Layer</th><th scope="col">Date</th><th scope="col" className="num">Records</th><th scope="col" className="num">In study area</th><th scope="col">Publisher and licence</th></tr></thead>
            <tbody>{inv.data.map((l) => <tr key={l.city + l.id}><td><CityName city={l.city} /></td><td><Ext href={l.source_url}>{l.label}</Ext></td><td>{l.vintage}</td><td className="num">{fmt(l.count)}</td><td className="num">{fmt(l.in_study_area)}</td><td className="small">{l.publisher}. {l.licence}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
