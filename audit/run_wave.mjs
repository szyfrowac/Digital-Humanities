// WAVE audit through WebAIM's official API. Each page uses 2 credits (reporttype=2, item counts by type).
// Key: set WAVE_API_KEY, or put it alone in audit/.wave_key (git-ignored). Never hard-code it.
// Run from audit/: node run_wave.mjs [urls.json]     Add --limit=1 to test one page first.
import fs from 'node:fs';
import path from 'node:path';
const key = process.env.WAVE_API_KEY || (fs.existsSync('.wave_key') ? fs.readFileSync('.wave_key', 'utf8').trim() : '');
if (!key) { console.error('No WAVE key found. Set WAVE_API_KEY or create audit/.wave_key. Get a key at https://wave.webaim.org/api/'); process.exit(2); }
const args = process.argv.slice(2);
const limit = Number(args.find((a) => a.startsWith('--limit='))?.split('=')[1] ?? Infinity);
const list = args.find((a) => !a.startsWith('--')) || 'urls.json';
const OUT = path.resolve('../data/raw/shared/wave');
fs.mkdirSync(OUT, { recursive: true });
const file = path.join(OUT, 'results.json');
const results = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
let used = 0;
for (const t of JSON.parse(fs.readFileSync(list, 'utf8'))) {
  if (results[t.id]?.status === 'audited' || used >= limit) continue;
  used++;
  const rec = { id: t.id, requestedUrl: t.url, auditedAt: new Date().toISOString() };
  try {
    const r = await fetch(`https://wave.webaim.org/api/request?key=${encodeURIComponent(key)}&reporttype=2&url=${encodeURIComponent(t.url)}`, { signal: AbortSignal.timeout(280000) });
    const j = await r.json();
    if (j.status?.success && /error page|access denied|forbidden|not found|blocked|unavailable/i.test(j.statistics.pagetitle || '')) {
      // WAVE fetches pages from its own servers, and some portals may refuse them. Never record that as an audit of the portal.
      Object.assign(rec, { status: 'invalid', reason: `WAVE received a page titled "${j.statistics.pagetitle}"`, creditsRemaining: j.statistics.creditsremaining });
    } else if (j.status?.success) {
      const c = j.categories;
      const item = (cat, id) => c[cat]?.items?.[id]?.count ?? 0;
      Object.assign(rec, {
        status: 'audited', pageTitle: j.statistics.pagetitle, finalUrl: j.statistics.pageurl, waveUrl: j.statistics.waveurl, creditsRemaining: j.statistics.creditsremaining,
        errors: c.error.count, contrastErrors: c.contrast.count, alerts: c.alert.count, features: c.feature.count, structure: c.structure.count, aria: c.aria.count,
        missingAlt: item('error', 'alt_missing') + item('error', 'alt_link_missing') + item('error', 'alt_input_missing') + item('error', 'alt_area_missing') + item('error', 'alt_map_missing') + item('error', 'alt_spacer_missing'),
        missingFormLabels: item('error', 'label_missing') + item('error', 'label_empty') + item('error', 'label_multiple'),
        emptyButtons: item('error', 'button_empty'), emptyLinks: item('error', 'link_empty'), emptyHeadings: item('error', 'heading_empty'),
        missingLanguage: item('error', 'language_missing'), noHeadings: item('alert', 'heading_missing'), skippedHeadingLevel: item('alert', 'heading_skipped'),
        h1: item('structure', 'h1'), h2: item('structure', 'h2'), h3: item('structure', 'h3'), raw: c,
      });
    } else {
      rec.status = 'failed';
      rec.error = String(j.status?.error ?? `HTTP ${r.status}`).slice(0, 200);
      if (/key|credit/i.test(rec.error)) { console.error('Stopping:', rec.error); process.exit(3); }
    }
  } catch (e) { rec.status = 'failed'; rec.error = String(e.message).slice(0, 200); }
  results[t.id] = rec;
  fs.writeFileSync(file, JSON.stringify(results, null, 1));
  console.log(t.id, rec.status, rec.status !== 'audited' && rec.reason ? rec.reason : rec.status === 'audited' ? `errors ${rec.errors}, contrast ${rec.contrastErrors}, alt ${rec.missingAlt}, labels ${rec.missingFormLabels}, credits left ${rec.creditsRemaining}` : rec.error);
  await new Promise((s) => setTimeout(s, 1500));
}
