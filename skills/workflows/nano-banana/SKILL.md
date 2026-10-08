---
name: nano-banana
version: 1.6.0
description: >
  Generate images using Google's Nano Banana (Gemini Image Generation) API and save them to the project. Use whenever
  the user asks to generate images, create product photos, hero banners, or lifestyle shots, mentions "Nano Banana" /
  "generate an image" / "make a banner", or wants batch image generation. Also trigger for any AI image task using
  Gemini models — even casual phrasings like "let's do images" or "make me a picture of".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
composes_with: ["frontend-agent", "docs-agent"]
spawned_by: []
---

# Nano Banana Image Generation

Generate images using Google's Gemini Image Generation API and save them directly into the project.

## How It Works

Nano Banana is Google's native image generation built into Gemini models. It accepts text prompts and returns high-quality photorealistic images. The API returns base64-encoded image data which gets decoded and saved to disk.

### Model

The bundled script uses `gemini-2.5-flash-image` — Google's current image generation model. It handles product photos, hero banners, lifestyle shots, and detail close-ups well at ~$0.04/image.

> **Note:** The script also accepts `--model flash` and `--model pro` for future model tiers as Google releases them. If those fail, fall back to `standard`.

### Supported Aspect Ratios

- **3:4** — Product cards / catalog grid (768x1024px)
- **16:9** — Hero / banner (1920x1080px)
- **1:1** — Detail / texture close-ups (1024x1024px)
- **4:5** — Lifestyle / editorial (1080x1350px)
- Also: 1:4, 1:8, 2:3, 3:2, 4:1, 4:3, 5:4, 8:1, 9:16, 21:9

## Setup — credential injection, never credential discovery

**Do not pre-check for the key with `env | grep` or `find`, and never ask the user to supply a key before you have actually run the script.** The script finds the key by itself, and a manual check will lie to you.

Exported `GEMINI_API_KEY` takes precedence. Native symlinks resolve to the canonical checkout and retain its single root `.env` loader. An installed copy does not inherit credentials: the owner must inject the key or explicitly select an approved root `.env` with `ATS_ENV_FILE`. Never search home/ancestor/per-skill env files or copy credentials into a bundle. Resource availability does not authorize paid image calls; obtain task/provider/budget approval before generation.

**The workflow is just: run the script.** It is self-sufficient about the key. The *only* trustworthy signal that the key is truly absent is the script exiting with its own `GEMINI_API_KEY ... is not set` error (which also prints the `.env` files it searched). Treat that error — and nothing else — as "key missing." Only then guide the user:

1. Get a key at [Google AI Studio](https://aistudio.google.com/apikey)
2. Add `GEMINI_API_KEY=...` to the skills repo-root `.env` (see `.env.example`), or `export GEMINI_API_KEY=...` in the shell.

## Generating Images

### Step 1: Identify What to Generate

When the user asks for image generation, figure out exactly what's needed:

- **Single image**: The user describes what they want. Help them refine the prompt if needed.
- **Batch of images**: If the project has a prompts document or image manifest, check it for pending items.
- **Custom image**: Help the user craft a detailed prompt (see Prompt Crafting below).

### Step 2: Find and Run the Script

The script lives under this skill's actual resource root. Set `SKILL_ROOT` from the installed prompt's resource contract (or the canonical skill directory):

```bash
# Resolve SKILL_ROOT from the actual installed resource root / .ats-runtime.json.
# Do not assume Claude home. Reading --help is offline; generation is paid.
python3 "$SKILL_ROOT/scripts/generate_image.py" --help
```

Then run it:

```bash
python3 <script-path>/generate_image.py \
  --prompt "the full prompt text" \
  --output "path/to/output.png" \
  --aspect-ratio "3:4" \
  --model standard \
  --resolution 2K
```

**Parameters:**

- `--prompt` — The full prompt text (quote it carefully in the shell)
- `--output` — Where to save the file (use `.png` — the API returns PNG data)
- `--aspect-ratio` — Match the intended use (default: 3:4)
- `--model` — `standard` (default), `flash`, or `pro`
- `--resolution` — `512`, `1K`, `2K` (default), or `4K`

**For batch generation**, run images sequentially — the API has rate limits so avoid parallel calls.

### Step 3: Verify and Report

After generation:

1. **Check the file exists** and has reasonable size (images are typically 1-2MB)
2. **Let the user review** — mention the file path so they can open it
3. **Update any project tracking** if the project maintains an image manifest or prompts doc

### Step 4: Handle Issues

- **API key missing**: Trust this *only* if the **script itself** printed `GEMINI_API_KEY ... is not set` — never your own `grep`/`find` (see Setup for why that lies). If it genuinely is missing, guide the user to [Google AI Studio](https://aistudio.google.com/apikey) and to add it to the repo-root `.env`.
- **Rate limited**: Wait a moment and retry, or suggest the user try again shortly
- **Bad output**: Re-run with a tweaked prompt. Common fixes:
  - Add "Photorealistic" if output looks illustrated
  - Be more specific about lighting, materials, and setting
  - Try a different aspect ratio if composition feels off
- **Model error / timeout**: Fall back to `--model standard` which is the most reliable

## Prompt Crafting

Good prompts make the difference between generic and stunning output. When helping users write prompts:

**Structure**: Open with shot type and subject, then add material/texture details, setting, lighting, and composition notes.

**Example — Product shot:**
> Create a photorealistic editorial product photograph of a leather messenger bag laid on an aged oak table. The bag is made from full-grain vegetable-tanned leather with visible patina and hand-stitched details. Warm side lighting from a tall window casts soft directional shadows. Shot on a medium format camera with natural lighting. No AI artifacts. Photorealistic. Clean composition, suitable for e-commerce product grid.

**Example — Hero banner:**
> A dramatic wide-angle photograph of a mountain trail at golden hour. Warm amber sunlight cuts through pine trees, casting long shadows across the rocky path. Atmospheric fog in the valley below creates depth. Cinematic composition, editorial quality. Photorealistic.

**Prompt modifiers** (append as needed):

- Higher realism: "Shot on a medium format camera with natural lighting. No AI artifacts. Photorealistic."
- Product catalog: "Clean composition, suitable for e-commerce product grid."
- Style consistency: "Maintain the same [describe lighting], [describe surface], and [describe photography style]."

The key elements that improve output quality:

- **Specific materials** (full-grain leather, rough-woven wool, brushed brass) rather than generic descriptions
- **Lighting direction** (side lighting, golden hour, warm torchlight) rather than just "good lighting"
- **Setting details** that ground the image (aged oak table, stone courtyard, misty forest)
- **Photography framing** (medium format, editorial, cinematic) to set the visual quality bar

## Reference Files

- `references/imagen-4-prompting.md` — deep-dive prompt engineering guide for Imagen 4 (the model behind Nano Banana). Read this when default output isn't hitting the mark, or when working with text-in-image, complex compositions, or specific photography styles. Covers the SCULPT framework, contextual priming techniques, the `enhancePrompt` parameter, and natural-language patterns that beat keyword soup.
- `references/example-project-config.md` — pattern for documenting per-project image conventions (paths, prompt style guide, anti-pattern modifiers, tracking spreadsheet). Suggest this to the user when starting a project that will generate many images, so the project's prompts stay consistent across sessions.
