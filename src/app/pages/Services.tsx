import { useMemo, useState } from 'react';
import { useJson, type City } from '../data';
import { Badge, CityName, Ext, Loading, PageHead } from '../ui';

function Cell({ r }: { r: any }) {
  return (
    <div>
      <p className="font-semibold"><Ext href={r.url}>{r.portal}</Ext></p>
      <p className="small">{r.operator}</p>
      <dl className="mt-2 text-sm space-y-2">
        <div><dt className="font-semibold">Online</dt><dd>{r.online.status === 'verified' ? <Badge kind="measured">Route seen on page</Badge> : <Badge kind="notverified" />} {r.online.text}</dd></div>
        <div><dt className="font-semibold">Offline</dt><dd>{r.offline.status === 'verified' ? null : <Badge kind="notverified" />} {r.offline.text}</dd></div>
        <div><dt className="font-semibold">Language controls</dt><dd>{r.language.text}</dd></div>
        <div><dt className="font-semibold">Accessibility audit</dt><dd>{r.audit.status === 'audited' ? <><Badge kind="measured">{r.audit.rules} WCAG rules failed, {r.audit.nodes} elements</Badge></> : <Badge kind="failed" />}{r.audit.note ? ` ${r.audit.note}` : ''}</dd></div>
        <div><dt className="font-semibold">Sign-in on this page</dt><dd>{r.auth}</dd></div>
        <div><dt className="font-semibold">Page load on the citizen</dt><dd>{r.complexity}</dd></div>
        {r.barriers.length > 0 && <div><dt className="font-semibold">Barriers observed</dt><dd><ul className="list-disc pl-4">{r.barriers.map((b: string) => <li key={b}>{b}</li>)}</ul></dd></div>}
        <div><dt className="font-semibold">Evidence</dt><dd><ul>{r.evidence.map((e: any) => <li key={e.url}><Ext href={e.url}>{e.label}</Ext></li>)}</ul></dd></div>
      </dl>
    </div>
  );
}

export function Services() {
  const { data, error } = useJson('civic_services.json');
  const [task, setTask] = useState('all');
  const [lang, setLang] = useState('all');
  const tasks = useMemo(() => (data?.tasks ?? []).filter((t: any) => task === 'all' || t.id === task), [data, task]);
  if (!data) return <div className="page"><PageHead title="Ten civic tasks, twenty records" /><Loading error={error} /></div>;
  const rec = (t: string, c: City) => data.records.find((r: any) => r.task === t && r.city === c);
  const match = (r: any) => lang === 'all' || r.language.offered.includes(lang);
  return (
    <div className="page">
      <PageHead title="Ten civic tasks, twenty records">
        <p>Each record names the official route we found for one task in one city, tested on {data.audit_date}. We loaded pages without signing in or submitting anything, so a route being present does not show that it works from start to finish.</p>
        <p>"Not verified" means we could not confirm the information. It does not mean the service is unavailable.</p>
      </PageHead>
      <div className="flex flex-wrap gap-4 items-end pb-6">
        <label className="block"><span className="font-semibold block mb-1">Civic task</span>
          <select value={task} onChange={(e) => setTask(e.target.value)} className="px-2 py-1.5" style={{ border: '1px solid var(--muted)', background: '#fff' }}>
            <option value="all">All ten tasks</option>{data.tasks.map((t: any) => <option key={t.id} value={t.id}>{t.title}</option>)}
          </select></label>
        <label className="block"><span className="font-semibold block mb-1">Highlight records with a language control for</span>
          <select value={lang} onChange={(e) => setLang(e.target.value)} className="px-2 py-1.5" style={{ border: '1px solid var(--muted)', background: '#fff' }}>
            <option value="all">Any language</option>{['English', 'Kannada', 'Telugu', 'Urdu', 'Hindi'].map((l) => <option key={l}>{l}</option>)}
          </select></label>
      </div>
      {tasks.map((t: any) => (
        <section key={t.id} className="sec">
          <h2>{t.title}</h2>
          <div className="grid gap-8 md:grid-cols-2 mt-3">
            {(['bengaluru', 'hyderabad'] as City[]).map((c) => {
              const r = rec(t.id, c);
              return (
                <article key={c} style={{ opacity: match(r) ? 1 : 0.45 }}>
                  <h3 className="text-lg mb-1"><CityName city={c} /></h3>
                  <Cell r={r} />
                </article>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
