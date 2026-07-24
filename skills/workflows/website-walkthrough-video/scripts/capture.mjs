#!/usr/bin/env node
// capture.mjs — screenshot every route of a site at desktop + mobile widths, full-page.
//
// For each render mode and each route it: sets the viewport, navigates, scrolls the whole
// page once (so lazy-loaded images and on-scroll animations have fired before we shoot),
// returns to the top, waits a beat to settle, then takes a full-page screenshot. It also
// samples the <body> background color so the video's letterbox matches the site instead of
// flashing black. Finally it writes manifest.json describing every clip for build.mjs.
//
// Standalone:  node capture.mjs --config site.json
// Library:     import { capture } from './capture.mjs'; await capture(config)

import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { join, isAbsolute, dirname } from 'node:path';

// Sensible presets. A site config usually only needs baseUrl + routes; these fill the rest.
// width/winHeight describe the *capture* viewport; outWidth is the video's pixel width
// (mobile is shot at 390 and rendered at 780 so phone text stays crisp). speed is the pan
// rate in output px/sec — bigger = faster scroll; maxPan caps the longest single clip.
const DEFAULT_MODES = [
  { name: 'desktop', width: 1440, winHeight: 810, outWidth: 1440, deviceScaleFactor: 1, isMobile: false, fontSize: 24, speed: 200, maxPan: 11, label: 'DESKTOP' },
  { name: 'mobile',  width: 390,  winHeight: 844, outWidth: 780,  deviceScaleFactor: 1, isMobile: true,  fontSize: 30, speed: 620, maxPan: 16, label: 'MOBILE' },
];
const DEFAULT_FONT = '/System/Library/Fonts/Supplemental/Arial.ttf';
const DEFAULT_BG = '0x0B0B0C';

const slugify = (path) => {
  const s = path.replace(/^https?:\/\/[^/]+/, '').replace(/[#?].*$/, '').replace(/^\/|\/$/g, '');
  return s ? s.replace(/[^a-z0-9]+/gi, '-').toLowerCase() : 'home';
};
const labelize = (slug) => slug.replace(/[-_]+/g, ' ').toUpperCase();

function rgbToHex(css) {
  const m = String(css).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const parts = m[1].split(',').map((x) => parseFloat(x.trim()));
  const [r, g, b, a = 1] = parts;
  if (a === 0) return null; // transparent — caller falls back to default
  const hx = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0');
  return `0x${hx(r)}${hx(g)}${hx(b)}`;
}

async function autoScroll(page) {
  // Walk down the page in steps so IntersectionObserver / lazy <img> loaders all fire,
  // then snap back to the top for a clean full-page shot.
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let y = 0;
      const step = Math.max(300, Math.floor(window.innerHeight * 0.8));
      const timer = setInterval(() => {
        window.scrollBy(0, step);
        y += step;
        if (y >= document.body.scrollHeight + window.innerHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 80);
    });
  });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);
}

async function settle(page, settleMs) {
  // A full-page screenshot can only ever catch an entrance animation mid-flight, so wait
  // for the things that actually decide whether a pixel is final: webfonts (text reflows
  // and FOUT-swaps late) and every <img> having decoded (lazy tiles report complete only
  // after their bytes land). Both are best-effort — a stalled image must not block a shoot.
  await page.evaluate(async () => {
    await (document.fonts ? document.fonts.ready.catch(() => {}) : Promise.resolve());
    await Promise.all(
      Array.from(document.images)
        .filter((img) => !img.complete)
        .map((img) => new Promise((res) => {
          img.addEventListener('load', res, { once: true });
          img.addEventListener('error', res, { once: true });
        }))
    );
  }).catch(() => {});
  await page.waitForTimeout(settleMs);
}

export async function capture(config) {
  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    throw new Error(
      "Could not load 'playwright'. Install it once in this skill's scripts dir:\n" +
      '    cd scripts && npm install\n' +
      '(Chromium itself is usually already cached; if not: npx playwright install chromium)'
    );
  }

  const baseUrl = config.baseUrl.replace(/\/$/, '');
  const outDir = isAbsolute(config.outDir) ? config.outDir : join(process.cwd(), config.outDir);
  mkdirSync(outDir, { recursive: true });

  const modes = (config.modes && config.modes.length ? config.modes : DEFAULT_MODES).map((m) => {
    const base = DEFAULT_MODES.find((d) => d.name === m.name) || {};
    return { ...base, ...m };
  });
  const routes = config.routes.map((r, i) => {
    const path = typeof r === 'string' ? r : r.path;
    const slug = (typeof r === 'object' && r.slug) || slugify(path);
    const label = (typeof r === 'object' && r.label) || labelize(slug);
    return { path, slug, label, index: i + 1 };
  });
  const fontFile = config.fontFile || DEFAULT_FONT;
  const timeout = config.timeout || 60000;
  const reducedMotion = config.reducedMotion || 'reduce';
  const injectCss = config.injectCss || null;
  const settleMs = config.settleMs ?? 600;

  const browser = await chromium.launch({ headless: true });
  const renders = [];
  try {
    for (const mode of modes) {
      console.log(`\n== capturing ${mode.name} (${mode.width}x${mode.winHeight}) ==`);
      const context = await browser.newContext({
        viewport: { width: mode.width, height: mode.winHeight },
        deviceScaleFactor: mode.deviceScaleFactor ?? 1,
        isMobile: !!mode.isMobile,
        hasTouch: !!mode.isMobile,
        // Most sites gate their scroll-reveal / entrance animations behind a
        // prefers-reduced-motion escape hatch. Asking for it makes the site itself render
        // the settled end state, which is the only state a still frame can show honestly.
        reducedMotion,
      });
      const page = await context.newPage();
      const prefix = mode.name[0].toLowerCase();
      const clips = [];
      let bg = config.bg || null;

      for (const route of routes) {
        const url = baseUrl + (route.path.startsWith('/') ? route.path : `/${route.path}`);
        const file = `${prefix}-${String(route.index).padStart(2, '0')}-${route.slug}.png`;
        try {
          await page.goto(url, { waitUntil: 'load', timeout });
        } catch {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout }).catch(() => {});
        }
        await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
        // Inject before the scroll so forced-visible rules are in effect while lazy content
        // and observers fire, not bolted on after the layout has already settled around them.
        if (injectCss) await page.addStyleTag({ content: injectCss }).catch(() => {});
        await autoScroll(page);
        await settle(page, settleMs);
        if (!bg) {
          const css = await page.evaluate(() => getComputedStyle(document.body).backgroundColor).catch(() => null);
          bg = rgbToHex(css) || DEFAULT_BG;
        }
        await page.screenshot({ path: join(outDir, file), fullPage: true });
        clips.push({ file, label: route.label });
        console.log(`    ${file}  (${route.label})`);
      }
      await context.close();

      const outWinHeight = Math.round(mode.winHeight * (mode.outWidth / mode.width));
      renders.push({
        name: mode.name,
        label: mode.label || mode.name.toUpperCase(),
        outWidth: mode.outWidth,
        outWinHeight,
        fontSize: mode.fontSize ?? 24,
        speed: mode.speed ?? 250,
        maxPan: mode.maxPan ?? 12,
        bg: bg || DEFAULT_BG,
        fontFile,
        clips,
      });
    }
  } finally {
    await browser.close();
  }

  const manifest = { title: config.title || baseUrl, baseUrl, fps: config.fps || 60, renders };
  writeFileSync(join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log(`\nWrote ${join(outDir, 'manifest.json')} (${renders.length} render mode(s)).`);
  return { outDir, manifest };
}

// --- CLI ---
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const ci = args.indexOf('--config');
  const configPath = ci >= 0 ? args[ci + 1] : args[0];
  if (!configPath || !existsSync(configPath)) {
    console.error('Usage: node capture.mjs --config site.json');
    process.exit(1);
  }
  const config = JSON.parse(readFileSync(configPath, 'utf8'));
  // resolve outDir relative to the config file unless absolute
  if (config.outDir && !isAbsolute(config.outDir)) {
    config.outDir = join(dirname(configPath), config.outDir);
  }
  capture(config).then(
    () => console.log('Capture complete.'),
    (e) => { console.error(e.message); process.exit(1); }
  );
}
