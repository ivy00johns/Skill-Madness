#!/usr/bin/env node
// build.mjs — turn captured full-page screenshots into smooth scrolling walkthrough videos.
//
// Reads <outDir>/manifest.json (written by capture.mjs) and, for each render mode,
// builds one ffmpeg clip per page that pans the tall full-page screenshot through a
// viewport-sized window (hold at top → smooth linear scroll → hold at bottom), stamps a
// "// PAGE | MODE" label, then concatenates the clips into walkthrough-<mode>.mp4.
//
// The pan is the trick that makes a still screenshot feel like a real scroll-through.
// What keeps it *smooth* (and not shimmery): 60fps, crf 18, lanczos downscale, and the
// overlay y-offset is floored to whole pixels so the image never lands on a sub-pixel.
//
// Standalone:  node build.mjs --dir <outDir>
// Library:     import { build } from './build.mjs'; await build(outDir)

import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// Timing envelope, shared by every clip. holdTop/holdBottom are the still beats at each
// end of a scroll so the eye can register the page before and after the motion.
const HOLD_TOP = 1.0;
const HOLD_BOTTOM = 1.0;
const MIN_PAN = 2.5;       // even a barely-taller-than-viewport page gets a gentle pan
const STATIC_HOLD = 3.0;   // a page that fits in the viewport: just hold it, no motion
const PRESET = 'medium';
const CRF = 18;

const sh = (cmd, args) =>
  new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    p.stdout.on('data', (d) => (out += d));
    p.stderr.on('data', (d) => (err += d));
    p.on('error', reject);
    p.on('close', (code) =>
      code === 0 ? resolve(out.trim()) : reject(new Error(`${cmd} exited ${code}: ${err.trim()}`))
    );
  });

async function probeDims(file) {
  const out = await sh('ffprobe', [
    '-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height', '-of', 'csv=p=0', file,
  ]);
  const [w, h] = out.split(',').map(Number);
  return { w, h };
}

// drawtext is fussy about a handful of metacharacters; strip/escape so any label is safe.
const dt = (s) =>
  String(s).replace(/\\/g, '\\\\').replace(/:/g, '\\:').replace(/'/g, '').replace(/%/g, '\\%');

async function buildClip(clip, render, fps, workDir, idx) {
  const { outWidth: W, outWinHeight: WINH, fontSize, speed, maxPan, bg, fontFile, label: modeLabel } = render;
  const img = clip.path;
  const { w: imgW, h: imgH } = await probeDims(img);
  const effH = Math.round((imgH * W) / imgW); // image height after it's scaled to the output width
  const scrollable = effH - WINH;             // how far we can travel before hitting the bottom

  // Duration & pan time: longer pages pan longer, but clamp so a giant page doesn't drag.
  let D, panExpr;
  if (scrollable <= 0) {
    D = STATIC_HOLD;
    panExpr = '0'; // page fits the window — no scroll, just hold it
  } else {
    const pd = Math.min(Math.max(scrollable / speed, MIN_PAN), maxPan);
    D = +(HOLD_TOP + pd + HOLD_BOTTOM).toFixed(2);
    // y travels 0 → -(h-H) as t goes HOLD_TOP → HOLD_TOP+pd, held flat outside that window.
    // floor() pins the image to whole pixels each frame (kills sub-pixel shimmer on text).
    panExpr = `-floor((h-H)*clip((t-${HOLD_TOP})/${pd.toFixed(2)}\\,0\\,1))`;
  }

  const scale = `[1]scale=${W}:-2:flags=lanczos[s];[0][s]`;
  const overlay = `overlay=x=0:y='${panExpr}':shortest=1`;
  const draw = fontFile && existsSync(fontFile)
    ? `,drawtext=fontfile=${fontFile}:text='// ${dt(clip.label)}  |  ${dt(modeLabel)}':x=22:y=20:fontsize=${fontSize}:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=12`
    : '';
  const filter = `${scale}${overlay}${draw},format=yuv420p,fps=${fps}`;

  const clipPath = join(workDir, `clip_${String(idx).padStart(3, '0')}.mp4`);
  await sh('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'lavfi', '-i', `color=${bg}:s=${W}x${WINH}:r=${fps}:d=${D}`,
    '-loop', '1', '-framerate', String(fps), '-t', String(D), '-i', img,
    '-filter_complex', filter,
    '-c:v', 'libx264', '-preset', PRESET, '-crf', String(CRF),
    '-pix_fmt', 'yuv420p', '-r', String(fps), clipPath,
  ]);
  console.log(`    ${clip.label.padEnd(18)} ${D}s @ ${fps}fps  (effH=${effH}, scroll=${Math.max(scrollable, 0)}px)`);
  return clipPath;
}

async function buildRender(render, fps, outDir) {
  console.log(`\n== ${render.name.toUpperCase()} (${render.outWidth}x${render.outWinHeight}) ==`);
  const workDir = mkdtempSync(join(tmpdir(), `walkthrough-${render.name}-`));
  try {
    const clipPaths = [];
    let i = 0;
    for (const clip of render.clips) {
      clip.path = join(outDir, clip.file);
      if (!existsSync(clip.path)) {
        console.warn(`    (skip ${clip.file} — not found)`);
        continue;
      }
      clipPaths.push(await buildClip(clip, render, fps, workDir, i++));
    }
    if (!clipPaths.length) {
      console.warn(`    no clips for ${render.name}, skipping concat`);
      return null;
    }

    // concat demuxer (re-encode, so per-clip timestamps can't fight each other)
    const listFile = join(workDir, 'concat.txt');
    writeFileSync(listFile, clipPaths.map((p) => `file '${p}'`).join('\n'));
    const outFile = join(outDir, `walkthrough-${render.name}.mp4`);
    await sh('ffmpeg', [
      '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', listFile,
      '-c:v', 'libx264', '-preset', PRESET, '-crf', String(CRF),
      '-pix_fmt', 'yuv420p', '-r', String(fps), '-movflags', '+faststart', outFile,
    ]);
    const meta = await sh('ffprobe', [
      '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', outFile,
    ]);
    console.log(`  → ${outFile}  (${(+meta).toFixed(1)}s)`);
    return outFile;
  } finally {
    rmSync(workDir, { recursive: true, force: true });
  }
}

export async function build(outDir) {
  const manifestPath = join(outDir, 'manifest.json');
  if (!existsSync(manifestPath)) {
    throw new Error(`No manifest.json in ${outDir}. Run capture.mjs first (or check the path).`);
  }
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const fps = manifest.fps || 60;
  const outputs = [];
  for (const render of manifest.renders) {
    const out = await buildRender(render, fps, outDir);
    if (out) outputs.push(out);
  }
  return outputs;
}

// --- CLI ---
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const dirIdx = args.indexOf('--dir');
  const outDir = dirIdx >= 0 ? args[dirIdx + 1] : args[0];
  if (!outDir) {
    console.error('Usage: node build.mjs --dir <screenshots-dir-with-manifest.json>');
    process.exit(1);
  }
  build(outDir).then(
    (outs) => console.log(`\nDone. ${outs.length} video(s) written.`),
    (e) => { console.error(e.message); process.exit(1); }
  );
}
