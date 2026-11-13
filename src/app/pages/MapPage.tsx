import { useEffect, useMemo, useRef, useState } from 'react';
import L from 'leaflet';
import { CITY_LABEL, loadJson, useJson, fmt, type City } from '../data';
import { Ext, Loading } from '../ui';

const CAT: Record<string, string> = {
  Healthcare: '#e0366f', Transport: '#2a78d6', Sanitation: '#0f8f62', 'Government access': '#6250d6', 'Food access': '#c98500', Context: '#55666e',
};
const CENTER: Record<City, [number, number]> = { bengaluru: [12.97, 77.59], hyderabad: [17.4, 78.47] };
const DEFAULTS: Record<City, string[]> = { bengaluru: ['uphc', 'namma_clinics', 'metro'], hyderabad: ['health_primary', 'metro'] };
const SKIP_KEYS = new Set(['name', 'in_study_area']);

export function MapPage() {
  const { data: registry, error } = useJson<any[]>('layers.json');
  const [city, setCity] = useState<City>('bengaluru');
  const [on, setOn] = useState<Record<string, string[]>>(DEFAULTS);
  const [q, setQ] = useState('');
  const [sel, setSel] = useState<any>(null);
  const [feats, setFeats] = useState<Record<string, any>>({});
  const [tileFail, setTileFail] = useState(false);
  const node = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const group = useRef<L.LayerGroup | null>(null);
  const wards = useRef<L.GeoJSON | null>(null);
  const cityLayers = useMemo(() => (registry ?? []).filter((l) => l.city === city), [registry, city]);
  const active = on[city] ?? [];

  useEffect(() => {
    if (!node.current || map.current) return;
    const m = L.map(node.current, { preferCanvas: true, zoomControl: true }).setView(CENTER.bengaluru, 11);
    const t = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>', maxZoom: 19 });
    let fails = 0;
    t.on('tileerror', () => { fails += 1; if (fails > 6) setTileFail(true); });
    t.addTo(m);
    group.current = L.layerGroup().addTo(m);
    map.current = m;
    return () => { m.remove(); map.current = null; };
  }, [!!registry]);

  useEffect(() => {
    const m = map.current; if (!m) return;
    m.setView(CENTER[city], 11);
    setSel(null);
    let live = true;
    loadJson(`${city}_wards.json`).then((fc) => {
      if (!live || !map.current) return;
      wards.current?.remove();
      wards.current = L.geoJSON(fc, { style: { color: '#465962', weight: 0.6, fillOpacity: 0 }, interactive: false } as any).addTo(m);
    });
    return () => { live = false; };
  }, [city, !!registry]);

  useEffect(() => {
    let live = true;
    Promise.all(active.map((id) => loadJson(`layers/${city}_${id}.json`).then((fc) => [id, fc] as const))).then((pairs) => {
      if (!live || !group.current) return;
      setFeats((f) => ({ ...f, ...Object.fromEntries(pairs.map(([id, fc]) => [`${city}_${id}`, fc])) }));
      group.current.clearLayers();
      for (const [id, fc] of pairs) {
        const meta = cityLayers.find((l) => l.id === id); if (!meta) continue;
        const color = CAT[meta.category];
        const community = meta.publisher.startsWith('OpenStreetMap');
        const dense = fc.features.length > 1500;
        for (const f of fc.features) {
          const [lon, lat] = f.geometry.coordinates;
          L.circleMarker([lat, lon], { radius: dense ? 2.5 : 4.5, color, weight: community ? 1.75 : 1, fillColor: community ? '#fff' : color, fillOpacity: community ? 0.9 : 0.85 })
            .on('click', () => setSel({ f, meta })).addTo(group.current!);
        }
      }
    });
    return () => { live = false; };
  }, [city, active.join(','), cityLayers]);

  const toggle = (id: string) => setOn((o) => {
    const cur = o[city] ?? [];
    return { ...o, [city]: cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id] };
  });
  const results = useMemo(() => {
    const t = q.trim().toLowerCase(); if (t.length < 2) return [];
    const out: any[] = [];
    for (const id of active) {
      const fc = feats[`${city}_${id}`]; if (!fc) continue;
      const meta = cityLayers.find((l) => l.id === id);
      for (const f of fc.features) if ((f.properties.name || '').toLowerCase().includes(t)) { out.push({ f, meta }); if (out.length >= 40) return out; }
    }
    return out;
  }, [q, active.join(','), feats, city, cityLayers]);
  const jump = (r: any) => { setSel(r); const [lon, lat] = r.f.geometry.coordinates; map.current?.setView([lat, lon], 16); };

  if (!registry) return <div className="page py-10"><h1 id="page-title" tabIndex={-1} className="text-4xl mb-4">City map</h1><Loading error={error} /></div>;
  const vintages = cityLayers.filter((l) => active.includes(l.id)).map((l) => l.vintage);
  const uniqueV = [...new Set(vintages)];
  const cats = [...new Set(cityLayers.map((l) => l.category))] as string[];
  const shown = cityLayers.filter((l) => active.includes(l.id)).reduce((a, l) => a + l.count, 0);
  return (
    <div className="mapwrap">
      <aside className="mapside p-4" style={{ background: 'var(--surface)', borderRight: '1px solid var(--rule)' }}>
        <h1 id="page-title" tabIndex={-1} className="text-3xl mb-3">City map</h1>
        <p className="lg:hidden mb-3"><a href="#map-stage" onClick={(e) => { e.preventDefault(); document.getElementById('map-stage')?.scrollIntoView(); }}>Jump to the map</a></p>
        <div role="group" aria-label="Choose a city" className="flex mb-3">
          {(['bengaluru', 'hyderabad'] as City[]).map((c) => <button key={c} type="button" className="btn flex-1" aria-pressed={city === c} onClick={() => { setCity(c); setQ(''); }}>{CITY_LABEL[c]}</button>)}
        </div>
        <p className="small mb-3" aria-live="polite">{fmt(shown)} real locations on view. Each comes from a listed source. A filled marker is an official or portal dataset; a hollow one is community-mapped OpenStreetMap data.</p>
        <div className="mb-4 p-2 small" style={{ border: '1px solid var(--muted)', color: 'var(--ink)' }}>
          <strong>Check the dates before comparing.</strong> Layers range from 2018 to 2026 and many are undated, so a gap between cities may only reflect an older list. The OSM layers use one query on one day for both cities. {uniqueV.length > 1 && <>On view now: {uniqueV.join('; ')}.</>}
        </div>
        <label htmlFor="mapsearch" className="font-semibold block mb-1">Search layers that are switched on</label>
        <input id="mapsearch" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="For example, Malleshwaram" className="w-full px-2 py-1.5 mb-1" style={{ border: '1px solid var(--muted)', background: '#fff' }} />
        {q.trim().length >= 2 && (
          <div className="mb-3">
            <p className="small" aria-live="polite">{results.length === 0 ? 'No matches. Try another spelling or switch on more layers.' : `${results.length}${results.length === 40 ? ' or more' : ''} matches`}</p>
            <ul className="max-h-48 overflow-y-auto mt-1">
              {results.map((r, i) => <li key={i}><button type="button" className="text-left w-full py-1 underline" style={{ color: 'var(--link)', background: 'none', border: 0, cursor: 'pointer' }} onClick={() => jump(r)}>{r.f.properties.name || 'Unnamed'} <span className="small">({r.meta.label})</span></button></li>)}
            </ul>
          </div>
        )}
        {cats.map((cat) => (
          <fieldset key={cat} className="mb-3 mt-3" style={{ border: 0, padding: 0 }}>
            <legend className="font-display font-semibold text-lg">{cat}</legend>
            {cityLayers.filter((l) => l.category === cat).map((l) => {
              const community = l.publisher.startsWith('OpenStreetMap');
              return (
                <label key={l.id} className="layerrow">
                  <input type="checkbox" checked={active.includes(l.id)} onChange={() => toggle(l.id)} style={{ marginTop: 5 }} />
                  <span className="swatch" aria-hidden="true" style={{ borderColor: CAT[cat], background: community ? '#fff' : CAT[cat] }} />
                  <span>{l.label}<br /><span className="small">{fmt(l.count)} records. {l.vintage}</span></span>
                  <span />
                </label>
              );
            })}
          </fieldset>
        ))}
        <details className="mt-2 small"><summary>Why are ration shops and MeeSeva centres missing?</summary>
          <p className="mt-1">We did not find a verified downloadable location dataset for ration shops or MeeSeva centres, so they are not on the map. MeeSeva shows its own centres map, which we have not extracted. No markers have been invented to fill the gap. Absence here is a gap in our data and is not evidence that a service is missing.</p>
        </details>
      </aside>
      <div className="mapstage" id="map-stage">
        <div ref={node} className="mapcanvas" role="application" aria-label={`Map of ${CITY_LABEL[city]}. Use the search box and layer list for a keyboard alternative to the markers.`} />
        {tileFail && <p className="detail small" style={{ top: 12, bottom: 'auto', right: 12 }} role="status">The background map is not available here. Ward outlines and markers still use project data.</p>}
        {sel && (
          <section className="detail" aria-label="Selected location">
            <div className="flex justify-between gap-2 items-start">
              <h2 className="text-xl">{sel.f.properties.name || 'Unnamed in source'}</h2>
              <button type="button" className="btn" style={{ padding: '2px 8px' }} onClick={() => setSel(null)} aria-label="Close details">Close</button>
            </div>
            <p className="small mt-1">{sel.meta.label}. {sel.f.properties.in_study_area ? 'Inside the ward study area.' : 'Outside the ward study area.'}</p>
            <dl className="mt-2 text-sm">
              {Object.entries(sel.f.properties).filter(([k]) => !SKIP_KEYS.has(k)).map(([k, v]) => (
                <div key={k} className="flex gap-2"><dt className="font-semibold">{k.replace(/_/g, ' ')}:</dt><dd style={{ overflowWrap: 'anywhere' }}>{String(v)}</dd></div>
              ))}
              <div className="flex gap-2"><dt className="font-semibold">Coordinates:</dt><dd>{sel.f.geometry.coordinates[1]}, {sel.f.geometry.coordinates[0]}</dd></div>
            </dl>
            <p className="small mt-2"><strong>Date:</strong> {sel.meta.vintage}<br /><strong>Published by:</strong> {sel.meta.publisher}. Origin stated: {sel.meta.origin}.<br /><strong>Licence:</strong> {sel.meta.licence}</p>
            {sel.meta.note && <p className="small mt-1">{sel.meta.note}</p>}
            <p className="small mt-1"><Ext href={sel.meta.source_url}>View the dataset source</Ext></p>
          </section>
        )}
      </div>
    </div>
  );
}
