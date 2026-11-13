// Lighthouse accessibility audit, desktop preset, one saved JSON and HTML report per page.
// Certificate errors are recorded, never bypassed. Run from audit/: node run_lighthouse.mjs [urls.json]
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const OUT = path.resolve('../data/raw/shared/lighthouse');
fs.mkdirSync(OUT, { recursive: true });
const targets = JSON.parse(fs.readFileSync(process.argv[2] || 'urls.json', 'utf8'));
const summaryFile = path.join(OUT, 'summary.json');
const summary = fs.existsSync(summaryFile) ? JSON.parse(fs.readFileSync(summaryFile, 'utf8')) : {};
const FOCUS = ['color-contrast', 'image-alt', 'button-name', 'link-name', 'label', 'html-has-lang', 'heading-order', 'aria-allowed-attr', 'aria-roles', 'aria-valid-attr', 'aria-valid-attr-value', 'aria-required-attr', 'aria-required-children', 'aria-required-parent', 'select-name', 'document-title', 'frame-title', 'meta-viewport', 'target-size'];
for (const t of targets) {
  if (summary[t.id]?.score != null) continue;
  const base = path.join(OUT, t.id);
  const rec = { id: t.id, requestedUrl: t.url, auditedAt: new Date().toISOString() };
  try {
    execFileSync('npx', ['lighthouse', t.url, '--quiet', '--preset=desktop', '--only-categories=accessibility', '--output=json', '--output=html', `--output-path=${base}`, '--chrome-flags=--headless=new --no-first-run', '--max-wait-for-load=45000'], { timeout: 180000, env: { ...process.env, CHROME_PATH: '/usr/bin/google-chrome' }, stdio: ['ignore', 'ignore', 'pipe'] });
    const r = JSON.parse(fs.readFileSync(`${base}.report.json`, 'utf8'));
    rec.lighthouseVersion = r.lighthouseVersion;
    rec.finalUrl = r.finalDisplayedUrl;
    rec.score = r.categories.accessibility.score == null ? null : Math.round(r.categories.accessibility.score * 100);
    rec.runtimeError = r.runtimeError?.code ?? null;
    rec.failed = Object.values(r.audits).filter((a) => a.score === 0 && a.scoreDisplayMode !== 'informative' && a.scoreDisplayMode !== 'manual').map((a) => ({ id: a.id, items: a.details?.items?.length ?? 0 }));
    rec.focus = Object.fromEntries(FOCUS.map((k) => [k, r.audits[k] ? { score: r.audits[k].score, items: r.audits[k].details?.items?.length ?? 0 } : null]));
    rec.status = rec.score == null ? 'no-score' : 'audited';
  } catch (e) {
    rec.status = 'failed';
    rec.error = String(e.stderr || e.message).split('\n').filter(Boolean).slice(-1)[0]?.slice(0, 220);
  }
  summary[t.id] = rec;
  fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 1));
  console.log(t.id, rec.status, rec.score ?? rec.runtimeError ?? rec.error ?? '');
}
