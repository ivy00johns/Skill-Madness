#!/usr/bin/env node
// axe_scan.mjs — run axe-core (via Playwright) on URLs at several widths and
// check 320px reflow. Resolves playwright + @axe-core/playwright from the
// CURRENT WORKING DIRECTORY (the target project), not from this skill.
//
// Exit codes: 0 = no violations at/above --fail-on, 1 = violations, 2 = could not run.

import { createRequire } from "node:module";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const HELP = `Usage: node axe_scan.mjs --url <url> [--url <url> ...] [options]

  --url <url>          Page to scan (repeatable)
  --urls-file <path>   File with one URL per line (# comments allowed)
  --widths <list>      Viewport widths, comma-separated (default 1440,320)
  --standard <s>       wcag2aa | wcag21aa | wcag22aa (default wcag22aa)
  --best-practice      Also run axe best-practice rules (reported separately)
  --fail-on <level>    minor | moderate | serious | critical | none (default serious)
  --out <dir>          Output dir (default .playwright/<run-id>/a11y)
  --storage-state <p>  Playwright storageState JSON for logged-in pages
  --help               Show this help

Install deps in the target project if missing:
  npm i -D playwright @axe-core/playwright && npx playwright install chromium

States a URL can't reach (open modal, step 3 of a form): drive them in your own
Playwright script, then run, on that page:
  const { AxeBuilder } = require('@axe-core/playwright');
  const r = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']).analyze();
`;

const TAGS = {
  wcag2aa: ["wcag2a", "wcag2aa"],
  wcag21aa: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
  wcag22aa: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
};
const IMPACT = ["minor", "moderate", "serious", "critical"];

function parseArgs(argv) {
  const o = {
    urls: [],
    widths: [1440, 320],
    standard: "wcag22aa",
    failOn: "serious",
    bestPractice: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`${a} needs a value`);
      return argv[++i];
    };
    if (a === "--help" || a === "-h") o.help = true;
    else if (a === "--url") o.urls.push(next());
    else if (a === "--urls-file")
      o.urls.push(
        ...readFileSync(next(), "utf8")
          .split("\n")
          .map((l) => l.trim())
          .filter((l) => l && !l.startsWith("#")),
      );
    else if (a === "--widths")
      o.widths = next()
        .split(",")
        .map((w) => parseInt(w, 10))
        .filter((w) => w > 0);
    else if (a === "--standard") o.standard = next();
    else if (a === "--fail-on") o.failOn = next();
    else if (a === "--out") o.out = next();
    else if (a === "--storage-state") o.storageState = next();
    else if (a === "--best-practice") o.bestPractice = true;
    else throw new Error(`unknown argument: ${a}`);
  }
  if (!TAGS[o.standard])
    throw new Error(
      `--standard must be one of ${Object.keys(TAGS).join(", ")}`,
    );
  if (o.failOn !== "none" && !IMPACT.includes(o.failOn))
    throw new Error(`--fail-on must be one of ${IMPACT.join(", ")}, none`);
  if (!o.widths.length) throw new Error("--widths parsed to nothing");
  return o;
}

function slug(url, width) {
  const u = new URL(url);
  const path =
    (u.pathname + u.search)
      .replace(/[^a-zA-Z0-9]+/g, "-")
      .replace(/^-|-$/g, "") || "root";
  return `${u.hostname}-${path}`.slice(0, 120) + `-${width}`;
}

async function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`error: ${e.message}\n\n${HELP}`);
    return 2;
  }
  if (opts.help) {
    console.log(HELP);
    return 0;
  }
  if (!opts.urls.length) {
    console.error(`error: no --url given\n\n${HELP}`);
    return 2;
  }

  const req = createRequire(join(process.cwd(), "noop.js"));
  let chromium,
    AxeBuilder,
    axeVersion = "unknown",
    pwVersion = "unknown";
  try {
    ({ chromium } = req("playwright"));
    ({ AxeBuilder } = req("@axe-core/playwright"));
    try {
      axeVersion = req("axe-core/package.json").version;
    } catch {}
    try {
      pwVersion = req("playwright/package.json").version;
    } catch {}
  } catch (e) {
    console.error(
      `error: could not load playwright / @axe-core/playwright from ${process.cwd()}\n` +
        `  ${e.message.split("\n")[0]}\n` +
        `Install in the target project (ask the user first):\n` +
        `  npm i -D playwright @axe-core/playwright && npx playwright install chromium`,
    );
    return 2;
  }

  const runId = new Date()
    .toISOString()
    .replace(/[:T]/g, "-")
    .replace(/\..+/, "");
  const out = resolve(opts.out || join(".playwright", runId, "a11y"));
  mkdirSync(join(out, "results"), { recursive: true });

  const tags = TAGS[opts.standard];
  const failIdx =
    opts.failOn === "none" ? Infinity : IMPACT.indexOf(opts.failOn);
  const pages = [];
  let errors = 0;

  const browser = await chromium.launch();
  try {
    for (const url of opts.urls) {
      for (const width of opts.widths) {
        const ctx = await browser.newContext({
          viewport: { width, height: width < 600 ? 800 : 900 },
          ...(opts.storageState ? { storageState: opts.storageState } : {}),
        });
        const page = await ctx.newPage();
        const rec = { url, width, file: `results/${slug(url, width)}.json` };
        try {
          const resp = await page.goto(url, {
            waitUntil: "networkidle",
            timeout: 45000,
          });
          rec.status = resp ? resp.status() : null;
          let builder = new AxeBuilder({ page }).withTags(
            opts.bestPractice ? [...tags, "best-practice"] : tags,
          );
          const r = await builder.analyze();
          const reflow = await page.evaluate(() => ({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
          }));
          rec.reflowOverflow =
            width <= 320 && reflow.scrollWidth > reflow.clientWidth + 1
              ? reflow
              : null;
          const isBp = (v) =>
            v.tags.includes("best-practice") &&
            !v.tags.some((t) => t.startsWith("wcag"));
          rec.violations = r.violations
            .filter((v) => !isBp(v))
            .map((v) => ({
              id: v.id,
              impact: v.impact,
              help: v.help,
              helpUrl: v.helpUrl,
              sc: v.tags
                .filter((t) => /^wcag\d{3,}$/.test(t))
                .map((t) => `${t[4]}.${t[5]}.${t.slice(6)}`),
              count: v.nodes.length,
              targets: v.nodes.slice(0, 10).map((n) => n.target.join(" ")),
            }));
          rec.bestPractice = r.violations.filter(isBp).map((v) => ({
            id: v.id,
            impact: v.impact,
            count: v.nodes.length,
          }));
          rec.incomplete = r.incomplete.map((v) => ({
            id: v.id,
            help: v.help,
            count: v.nodes.length,
          }));
          writeFileSync(
            join(out, rec.file),
            JSON.stringify({ url, width, reflow, ...r }, null, 2),
          );
        } catch (e) {
          rec.error = e.message.split("\n")[0];
          errors++;
        } finally {
          await ctx.close();
        }
        pages.push(rec);
      }
    }
  } finally {
    await browser.close();
  }

  let failing = 0;
  const counts = Object.fromEntries(IMPACT.map((k) => [k, 0]));
  for (const p of pages) {
    for (const v of p.violations || []) {
      counts[v.impact] = (counts[v.impact] || 0) + 1;
      if (IMPACT.indexOf(v.impact) >= failIdx) failing++;
    }
    if (p.reflowOverflow && failIdx <= IMPACT.indexOf("serious")) failing++;
  }

  const summary = {
    runId,
    standard: opts.standard,
    tags,
    axeVersion,
    playwrightVersion: pwVersion,
    failOn: opts.failOn,
    counts,
    failing,
    errors,
    pages,
  };
  writeFileSync(join(out, "summary.json"), JSON.stringify(summary, null, 2));

  const md = [
    `# axe scan — ${runId}`,
    ``,
    `Standard: ${opts.standard} (tags: ${tags.join(", ")}) · axe-core ${axeVersion} · Playwright ${pwVersion}`,
    `Violations by impact: critical ${counts.critical} · serious ${counts.serious} · moderate ${counts.moderate} · minor ${counts.minor}`,
    `Pages that could not be scanned: ${errors}`,
    ``,
    `> Automated results only. A clean scan is not conformance: complete the manual checks`,
    `> (references/manual-checks.md) and move every "incomplete" item to the manual list.`,
    ``,
  ];
  for (const p of pages) {
    md.push(`## ${p.url} @ ${p.width}px`);
    if (p.error) {
      md.push(`- **SCAN FAILED:** ${p.error}`, ``);
      continue;
    }
    if (p.reflowOverflow)
      md.push(
        `- **Reflow (1.4.10):** page scrolls horizontally at ${p.width}px (scrollWidth ${p.reflowOverflow.scrollWidth} > ${p.reflowOverflow.clientWidth}). Check whether the overflowing content is exempt (data table, map).`,
      );
    for (const v of p.violations)
      md.push(
        `- [${v.impact}] \`${v.id}\` ${v.help} (${v.sc.join(", ") || "no SC tag"}): ${v.count} node(s), e.g. \`${v.targets[0] || ""}\``,
      );
    if (!p.violations.length && !p.reflowOverflow)
      md.push(`- no automated violations`);
    if (p.incomplete.length)
      md.push(
        `- needs manual review (axe incomplete): ${p.incomplete.map((v) => `\`${v.id}\`×${v.count}`).join(", ")}`,
      );
    if (p.bestPractice.length)
      md.push(
        `- best-practice (not WCAG failures): ${p.bestPractice.map((v) => `\`${v.id}\`×${v.count}`).join(", ")}`,
      );
    md.push(``);
  }
  writeFileSync(join(out, "summary.md"), md.join("\n"));

  console.log(`wrote ${join(out, "summary.md")}`);
  console.log(
    `violations: critical ${counts.critical}, serious ${counts.serious}, moderate ${counts.moderate}, minor ${counts.minor}; scan errors: ${errors}`,
  );
  if (errors) return 2;
  return failing ? 1 : 0;
}

main().then(
  (code) => process.exit(code),
  (e) => {
    console.error(`error: ${e.stack || e}`);
    process.exit(2);
  },
);
