#!/usr/bin/env node
// walkthrough.mjs — one command: capture every route, then render the walkthrough videos.
//
//   node walkthrough.mjs --config site.json
//   node walkthrough.mjs --config site.json --skip-capture   # re-render from existing PNGs
//   node walkthrough.mjs --config site.json --skip-build      # only grab screenshots
//   node walkthrough.mjs --config site.json --base-url http://localhost:8081 --out-dir /abs/out
//
// --base-url / --out-dir override the config so the same route list can target local, staging,
// or prod, and so a wrapper script can supply an absolute output path. --skip-capture is the
// fast iteration loop: tweak speed/maxPan/fontSize in the manifest (or the config) and
// re-render in seconds without re-screenshotting the whole site.

import { existsSync, readFileSync } from 'node:fs';
import { join, isAbsolute, dirname } from 'node:path';
import { capture } from './capture.mjs';
import { build } from './build.mjs';

const args = process.argv.slice(2);
const flag = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
const configPath = flag('--config') || args.find((a) => !a.startsWith('--'));
const skipCapture = args.includes('--skip-capture');
const skipBuild = args.includes('--skip-build');

if (!configPath || !existsSync(configPath)) {
  console.error('Usage: node walkthrough.mjs --config site.json [--base-url URL] [--out-dir DIR] [--skip-capture] [--skip-build]');
  process.exit(1);
}

const config = JSON.parse(readFileSync(configPath, 'utf8'));

// CLI overrides win over the config file.
const baseUrlOverride = flag('--base-url');
if (baseUrlOverride) config.baseUrl = baseUrlOverride;
const outDirOverride = flag('--out-dir');
if (outDirOverride) config.outDir = outDirOverride;

if (!config.baseUrl) { console.error('No baseUrl in config and no --base-url given.'); process.exit(1); }
if (!config.outDir) { console.error('No outDir in config and no --out-dir given.'); process.exit(1); }

const outDir = isAbsolute(config.outDir)
  ? config.outDir
  : join(dirname(configPath), config.outDir);
config.outDir = outDir;

const run = async () => {
  if (!skipCapture) {
    await capture(config);
  } else {
    console.log('Skipping capture — rebuilding from existing screenshots.');
  }
  if (!skipBuild) {
    const outs = await build(outDir);
    console.log(`\nDone. ${outs.length} walkthrough video(s):`);
    outs.forEach((o) => console.log(`  ${o}`));
  }
};

run().catch((e) => { console.error('\n' + e.message); process.exit(1); });
