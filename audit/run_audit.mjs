// Automated accessibility audit of civic portal landing pages.
// axe-core rules plus scripted probes. It only loads pages: no forms are submitted,
// no accounts are used, and TLS errors are recorded as findings, not bypassed.
// Run from audit/:  node run_audit.mjs [urls.json]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const axeSource = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const OUT = path.resolve('../data/raw/shared/accessibility_audit');
fs.mkdirSync(path.join(OUT, 'screenshots'), { recursive: true });
const targets = JSON.parse(fs.readFileSync(process.argv[2] || 'urls.json', 'utf8'));
const resultFile = path.join(OUT, 'results.json');
const results = fs.existsSync(resultFile) ? JSON.parse(fs.readFileSync(resultFile, 'utf8')) : {};

const probes = () => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const text = (document.body?.innerText || '').replace(/\s+/g, ' ').trim();
  const controls = [...document.querySelectorAll('a,button,option,[role=button],[role=menuitem],label,li')]
    .map((e) => (e.innerText || e.textContent || '').trim())
    .filter((t) => t.length > 0 && t.length < 25);
  const hrefs = [...document.querySelectorAll('a[href]')].map((a) => a.getAttribute('href') || '');
  const has = (re, hrefRe) => controls.some((t) => re.test(t)) || (!!hrefRe && hrefs.some((h) => hrefRe.test(h)));
  const script = (re) => (text.match(re) || []).length;
  return {
    title: document.title,
    htmlLang: document.documentElement.getAttribute('lang'),
    viewportMeta: document.querySelector('meta[name=viewport]')?.getAttribute('content') || null,
    zoomBlocked: /user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b/i.test(document.querySelector('meta[name=viewport]')?.getAttribute('content') || ''),
    languageControls: {
      english: has(/^(english|eng|en)$/i, /\/en\/?$|[?&]lang=en\b/i),
      kannada: has(/^ಕನ್ನಡ$|^kannada$/i, /\/kn\/?$|[?&]lang=kn\b/i),
      telugu: has(/^తెలుగు$|^telugu$/i, /\/te\/?$|[?&]lang=te\b/i),
      urdu: has(/^اردو$|^urdu$/i, /\/ur\/?$|[?&]lang=ur\b/i),
      tamil: has(/^தமிழ்$|^tamil$/i, /\/ta\/?$|[?&]lang=ta\b/i),
      hindi: has(/^हिन्दी$|^हिंदी$|^hindi$/i, /\/hi\/?$|[?&]lang=hi\b/i),
      googleTranslate: !!document.querySelector('.goog-te-combo,#google_translate_element,.gtranslate_wrapper'),
      bhashini: !!document.querySelector('[src*="bhashini"],[class*="bhashini"],[id*="bhashini"]'),
    },
    scriptChars: {
      latin: script(/[A-Za-z]/g), kannada: script(/[ಀ-೿]/g), telugu: script(/[ఀ-౿]/g),
      arabic: script(/[؀-ۿ]/g), devanagari: script(/[ऀ-ॿ]/g),
    },
    skipLink: [...document.querySelectorAll('a[href^="#"]')].some((a) => /skip|main content/i.test(a.textContent || '')),
    accessibilityWidget: has(/accessibility|screen reader|a\+|a-/i),
    counts: {
      words: text.split(' ').length,
      links: [...document.querySelectorAll('a[href]')].filter(visible).length,
      formInputs: [...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(visible).length,
      h1: document.querySelectorAll('h1').length,
      landmarks: document.querySelectorAll('main,nav,header,footer,[role=main],[role=navigation]').length,
      images: document.images.length,
    },
    authSignals: {
      passwordField: !!document.querySelector('input[type=password]'),
      otpMention: /\bOTP\b/.test(text),
      loginMention: /\b(login|log in|sign in)\b/i.test(text),
      captcha: /captcha/i.test(document.documentElement.innerHTML.slice(0, 500000)),
      aadhaarMention: /aadhaar|aadhar/i.test(text),
    },
    textSample: text.slice(0, 400),
  };
};

async function keyboardProbe(page) {
  const seen = [];
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate(() => {
      const e = document.activeElement;
      if (!e || e === document.body) return null;
      const s = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      return {
        tag: e.tagName,
        visible: r.width > 0 && r.height > 0,
        ring: (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none',
      };
    }).catch(() => null);
    if (info) seen.push(info);
  }
  return {
    tabPresses: 20,
    focusLanded: seen.length,
    focusOnVisibleElement: seen.filter((s) => s.visible).length,
    focusRingDetected: seen.filter((s) => s.ring).length,
  };
}

const browser = await chromium.launch({ channel: 'chrome', headless: true });
for (const t of targets) {
  if (results[t.id]?.status === 'audited') continue;
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'en-IN' });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on('pageerror', () => consoleErrors.push(1));
  const rec = { id: t.id, requestedUrl: t.url, auditedAt: new Date().toISOString() };
  try {
    let resp;
    try {
      resp = await page.goto(t.url, { waitUntil: 'domcontentloaded', timeout: 50000 });
    } catch (first) {
      rec.firstAttemptError = String(first.message).split('\n')[0].slice(0, 120);
      await page.waitForTimeout(15000);
      resp = await page.goto(t.url, { waitUntil: 'domcontentloaded', timeout: 50000 });
    }
    await page.waitForLoadState('networkidle', { timeout: 12000 }).catch(() => {});
    rec.httpStatus = resp?.status() ?? null;
    rec.finalUrl = page.url();
    rec.httpsFinal = page.url().startsWith('https://');
    await page.evaluate(axeSource);
    const axe = await page.evaluate(() => window.axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
      resultTypes: ['violations', 'incomplete'],
    }));
    const slim = (v) => ({
      id: v.id, impact: v.impact, help: v.help, tags: v.tags.filter((x) => x.startsWith('wcag') || x.startsWith('cat.')),
      nodes: v.nodes.length, sample: v.nodes[0]?.target?.join(' ').slice(0, 120) ?? null,
    });
    rec.axe = { version: axe.testEngine.version, violations: axe.violations.map(slim), incomplete: axe.incomplete.map(slim), passes: axe.passes.length };
    rec.probes = await page.evaluate(probes);
    await page.screenshot({ path: path.join(OUT, 'screenshots', `${t.id}.jpg`), type: 'jpeg', quality: 55 });
    rec.keyboard = await keyboardProbe(page);
    await page.setViewportSize({ width: 320, height: 800 });
    await page.waitForTimeout(600);
    rec.reflow320 = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      horizontalOverflow: document.documentElement.scrollWidth > 340,
    }));
    rec.scriptErrors = consoleErrors.length;
    rec.status = 'audited';
  } catch (e) {
    rec.status = 'failed';
    rec.error = String(e.message).split('\n')[0].slice(0, 200);
  }
  results[t.id] = rec;
  fs.writeFileSync(resultFile, JSON.stringify(results, null, 1));
  const v = rec.axe?.violations ?? [];
  console.log(t.id, rec.status, rec.httpStatus ?? rec.error, rec.finalUrl ?? '', 'rules:', v.length, 'nodes:', v.reduce((a, x) => a + x.nodes, 0));
  await ctx.close();
}
await browser.close();
