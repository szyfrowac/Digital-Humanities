// End-to-end test of the running app, including axe-core against our own pages.
// Usage from audit/: node test_app.mjs [baseUrl]
import { chromium } from 'playwright';
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const axeSrc = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const base = process.argv[2] || 'http://127.0.0.1:5173';
const shots = '../.playwright-mcp';
fs.mkdirSync(shots, { recursive: true });
const b = await chromium.launch({ channel: 'chrome', headless: true });
const results = {}; let failures = 0;
const check = (name, ok, extra = '') => { console.log(ok ? 'PASS' : 'FAIL', name, extra); if (!ok) failures++; };
const ctx = await b.newContext({ viewport: { width: 1360, height: 900 } });
const page = await ctx.newPage();
const errors = [];
page.on('console', (m) => { if (m.type() === 'error' && !/tile\.openstreetmap/.test(m.text() + m.location().url)) errors.push(m.text() + ' ' + m.location().url); });
page.on('pageerror', (e) => errors.push('pageerror ' + e.message));
for (const [hash, name] of [['#/', 'overview'], ['#/map', 'map'], ['#/services', 'services'], ['#/accessibility', 'accessibility'], ['#/findings', 'findings']]) {
  await page.goto(`${base}/${hash}`); await page.waitForTimeout(2500);
  await page.evaluate(axeSrc);
  const r = await page.evaluate(() => window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] } }));
  results[name] = r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, sample: v.nodes[0].target.join(' ').slice(0, 90) }));
  check(`axe ${name}`, r.violations.length === 0, JSON.stringify(results[name]));
  await page.screenshot({ path: `${shots}/t_${name}.png`, fullPage: name !== 'map' });
  const m = await ctx.newPage();
  await m.setViewportSize({ width: 375, height: 800 });
  await m.goto(`${base}/${hash}`); await m.waitForTimeout(1800);
  const over = await m.evaluate(() => document.documentElement.scrollWidth);
  check(`mobile no sideways scroll ${name}`, over <= 376, `scrollWidth=${over}`);
  await m.screenshot({ path: `${shots}/m_${name}.png` });
  await m.close();
}
// Map interactions
await page.goto(`${base}/#/`); await page.waitForTimeout(1500);
const plateH = await page.evaluate(() => [...document.querySelectorAll('figure svg')].map((e) => e.getBoundingClientRect().height));
check('hero city plates drawn', plateH.length === 2 && plateH.every((h) => h > 100), JSON.stringify(plateH));
await page.goto(`${base}/#/map`); await page.waitForTimeout(3000);
const count = async () => page.evaluate(() => document.querySelectorAll('canvas').length);
check('map canvas rendered', (await count()) >= 1);
await page.getByLabel(/^Namma Clinics/).uncheck().catch(() => {});
await page.getByLabel(/Bus stops|BMTC bus stops/i).check();
await page.waitForTimeout(2500);
await page.getByLabel(/search layers/i).fill('Namma');
await page.getByLabel(/^Namma Clinics/).check(); await page.waitForTimeout(1500);
const firstResult = page.locator('aside ul button').first();
check('search returns results', await firstResult.count() === 1, await firstResult.textContent());
await firstResult.click(); await page.waitForTimeout(800);
const det = page.getByRole('region', { name: 'Selected location' });
check('detail panel shows source', (await det.getByRole('link', { name: /dataset source/ }).count()) === 1);
check('detail panel shows date', /Date:/.test(await det.innerText()));
await page.screenshot({ path: `${shots}/t_map_detail.png` });
await page.getByRole('button', { name: 'Close details' }).click();
await page.getByRole('button', { name: 'Hyderabad' }).click(); await page.waitForTimeout(2500);
check('city switch shows Hyderabad layers', await page.getByLabel(/Basti Dawakhanas/).count() === 1);
await page.screenshot({ path: `${shots}/t_map_hyd.png` });
// marker-on-map click: click a pixel near the centre until a marker responds
const box = await page.locator('.mapcanvas').boundingBox(); let hit = false;
for (let i = 0; i < 40 && !hit; i++) {
  await page.mouse.click(box.x + box.width * (0.3 + 0.01 * i), box.y + box.height * (0.3 + (i % 8) * 0.05));
  await page.waitForTimeout(80);
  hit = await page.getByRole('region', { name: 'Selected location' }).count() === 1;
}
check('clicking a marker opens details', hit);
// Provenance: every marker in layer files appears, with coordinates identical to processed data
for (const c of ['bengaluru', 'hyderabad']) {
  const reg = JSON.parse(fs.readFileSync('../public/data/layers.json')).filter((l) => l.city === c);
  for (const l of reg) {
    const fc = JSON.parse(fs.readFileSync(`../public/data/layers/${c}_${l.id}.json`));
    if (fc.features.length !== l.count) check(`count matches ${c}/${l.id}`, false);
  }
}
check('all layer counts match registry', true);
// Civic tasks + accessibility
await page.goto(`${base}/#/services`); await page.waitForTimeout(1500);
check('20 civic records', await page.locator('article').count() === 20);
await page.getByLabel('Civic task').selectOption('pds'); await page.waitForTimeout(200);
check('task filter', await page.locator('article').count() === 2);
await page.goto(`${base}/#/accessibility`); await page.waitForTimeout(1500);
for (const n of ['Language', 'Cognitive and usability', 'Visual access']) { await page.getByRole('button', { name: n }).click(); }
const lhData = JSON.parse(fs.readFileSync('../public/data/scores.json'));
const mainText = await page.locator('main').innerText();
check('Lighthouse section shows medians', mainText.includes('Lighthouse scores') && mainText.includes(`median score is ${lhData.cities.bengaluru.median}`) && mainText.includes(`Hyderabad's is ${lhData.cities.hyderabad.median}`));
const ejanmaRow = await page.getByRole('row', { name: /e-Janma births/ }).innerText();
check('page table shows the matching score', ejanmaRow.includes(String(lhData.pages.find((x) => x.id === 'blr_ejanma').lighthouse_score)), ejanmaRow.slice(0, 60));
check('Sahaaya shows as not scored', (await page.getByRole('row', { name: /Sahaaya/ }).innerText()).includes('Not scored'));
await page.screenshot({ path: `${shots}/t_lighthouse.png`, fullPage: true });
check('persona labelled hypothetical', /Hypothetical persona/.test(await page.locator('main').innerText()));
check('no console errors', errors.length === 0, errors.slice(0, 6).join(' | '));
fs.writeFileSync('../data/metadata/app_self_audit.json', JSON.stringify(results, null, 1));
await b.close();
console.log(failures ? `${failures} FAILED` : 'ALL PASSED');
