import { useEffect, useState } from 'react';

export type City = 'bengaluru' | 'hyderabad';
export const CITY_LABEL: Record<City, string> = { bengaluru: 'Bengaluru', hyderabad: 'Hyderabad' };
export const CITY_COLOR: Record<City, string> = { bengaluru: '#1f6fc2', hyderabad: '#d4581f' };

const cache = new Map<string, Promise<any>>();
export function loadJson<T = any>(path: string): Promise<T> {
  if (!cache.has(path)) {
    cache.set(path, fetch(`${import.meta.env.BASE_URL}data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${path} (HTTP ${r.status})`);
      return r.json();
    }));
  }
  return cache.get(path)!;
}
export function useJson<T = any>(path: string | null) {
  const [state, setState] = useState<{ data?: T; error?: string }>({});
  useEffect(() => {
    if (!path) return;
    let live = true;
    setState({});
    loadJson<T>(path).then((d) => live && setState({ data: d })).catch((e) => live && setState({ error: String(e.message) }));
    return () => { live = false; };
  }, [path]);
  return state;
}
export const fmt = (n: number) => n.toLocaleString('en-IN');
