import type { ReactNode } from 'react';
import { CITY_COLOR, CITY_LABEL, type City } from './data';

export type Kind = 'measured' | 'primary' | 'secondary' | 'derived' | 'hypothetical' | 'notverified' | 'failed' | 'preliminary';
const KINDS: Record<Kind, { label: string; cls: string; icon: string }> = {
  measured: { label: 'Measured by automated test', cls: '', icon: '◆' },
  primary: { label: 'Primary source', cls: '', icon: '■' },
  secondary: { label: 'Secondary source', cls: '', icon: '□' },
  derived: { label: 'Derived by this project', cls: '', icon: '△' },
  hypothetical: { label: 'Hypothetical persona', cls: 'hyp', icon: '○' },
  notverified: { label: 'Not verified', cls: 'nv', icon: '?' },
  failed: { label: 'Could not load', cls: 'bad', icon: '!' },
  preliminary: { label: 'Preliminary', cls: 'hyp', icon: '○' },
};
export function Badge({ kind, children }: { kind: Kind; children?: ReactNode }) {
  const k = KINDS[kind];
  return <span className={`badge ${k.cls}`}><span aria-hidden="true">{k.icon}</span>{children ?? k.label}</span>;
}
export const CityName = ({ city }: { city: City }) => (
  <span style={{ whiteSpace: 'nowrap' }}><span className="cityMark" style={{ background: CITY_COLOR[city] }} aria-hidden="true" />{CITY_LABEL[city]}</span>
);
export function Loading({ error }: { error?: string }) {
  return <p className="small" role={error ? 'alert' : 'status'}>{error ? `${error}. Check that the app is served from the project folder.` : 'Loading data…'}</p>;
}
export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="pt-10 pb-8">
      <h1 tabIndex={-1} id="page-title" className="text-[2.5rem] md:text-[3.25rem]">{title}</h1>
      {children && <div className="prose-body mt-3">{children}</div>}
    </header>
  );
}
export const Ext = ({ href, children }: { href: string; children: ReactNode }) => <a href={href} target="_blank" rel="noreferrer noopener">{children}<span className="sr-only"> (opens in a new tab)</span></a>;
