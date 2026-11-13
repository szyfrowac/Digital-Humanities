// Re-check links that failed in Python, using Chrome with normal certificate validation.
import { chromium } from 'playwright';
import fs from 'node:fs';
const res = JSON.parse(fs.readFileSync('../data/metadata/link_check.json'));
const bad = res.filter((r) => r[1] !== 200).map((r) => r[0]);
const b = await chromium.launch({ channel: 'chrome', headless: true });
const out = [];
for (const u of bad) {
  const p = await (await b.newContext()).newPage();
  try { const r = await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 }); out.push([u, r.status(), 'chrome']); console.log(r.status(), u); }
  catch (e) { out.push([u, 0, String(e.message).split('\n')[0].slice(0, 90)]); console.log('FAIL', u, String(e.message).split('\n')[0].slice(0, 90)); }
  await p.close();
}
fs.writeFileSync('../data/metadata/link_check_chrome.json', JSON.stringify(out, null, 0));
await b.close();
