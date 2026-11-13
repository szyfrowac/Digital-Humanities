import { useEffect, useState } from 'react';
import { Overview } from './pages/Overview';
import { MapPage } from './pages/MapPage';
import { Services } from './pages/Services';
import { Accessibility } from './pages/Accessibility';
import { Findings } from './pages/Findings';

const ROUTES = [
  { id: '', label: 'Overview', C: Overview },
  { id: 'map', label: 'City map', C: MapPage },
  { id: 'services', label: 'Civic tasks', C: Services },
  { id: 'accessibility', label: 'Accessibility', C: Accessibility },
  { id: 'findings', label: 'Findings', C: Findings },
];
const current = () => window.location.hash.replace(/^#\/?/, '');

export function App() {
  const [route, setRoute] = useState(current());
  useEffect(() => {
    const on = () => setRoute(current());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  const r = ROUTES.find((x) => x.id === route) ?? ROUTES[0];
  useEffect(() => {
    document.title = r.id ? `${r.label}: Can You Access Your City?` : 'Can You Access Your City?';
    window.scrollTo(0, 0);
    const t = setTimeout(() => document.getElementById('page-title')?.focus(), 30);
    return () => clearTimeout(t);
  }, [r.id, r.label]);
  return (
    <>
      <a className="skip" href="#main" onClick={(e) => { e.preventDefault(); document.getElementById('page-title')?.focus(); }}>Skip to main content</a>
      <header style={{ background: 'var(--surface)', borderBottom: '1px solid var(--rule)' }}>
        <div className="page flex flex-wrap items-baseline gap-x-8">
          <a href="#" style={{ textDecoration: 'none', color: 'var(--ink)' }} className="font-display text-xl font-semibold py-2">Can You Access Your City?</a>
          <nav aria-label="Main" className="nav flex gap-5 overflow-x-auto">
            {ROUTES.map((x) => <a key={x.id} href={`#${x.id}`} aria-current={x.id === r.id ? 'page' : undefined}>{x.label}</a>)}
          </nav>
        </div>
      </header>
      <main id="main"><r.C /></main>
      {r.id !== 'map' && (
        <footer className="page small py-8" style={{ borderTop: '1px solid var(--rule)' }}>
          Preliminary class research, November 2026. No user testing has taken place. Facility data: OpenCity and OpenStreetMap contributors (ODbL). Census data: Office of the Registrar General, India.
        </footer>
      )}
    </>
  );
}
