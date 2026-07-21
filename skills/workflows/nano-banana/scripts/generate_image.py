#!/usr/bin/env python3
"""
Generate an image using Google's Nano Banana (Gemini Image Generation) API.

Usage:
    python generate_image.py --prompt "your prompt" --output path/to/output.jpg [--aspect-ratio 3:4] [--model pro] [--resolution 2K]

Environment:
    GEMINI_API_KEY - Required. Your Google AI Studio API key.
"""

import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.request
import urllib.error

# Resolve GEMINI_API_KEY from a .env if it isn't already exported.
#
# WHY THIS IS CAREFUL: this skill directory is usually a *symlink* into a separate
# repo (e.g. ~/.claude/skills/nano-banana -> ~/Repos/.../Skill-Madness/.../nano-banana),
# and the key lives in that repo's ROOT .env — OUTSIDE ~/.claude/skills. Path(__file__)
# .resolve() follows the symlink, so we search from the REAL on-disk location. We then
# walk every ancestor of both the resolved script dir and the current working directory
# (plus ~/.env), so the key is found no matter how the repo is laid out. The nearest
# .env that defines the key wins; we never overwrite a key already in the environment.
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


def _candidate_env_files():
    """Yield .env paths to search, nearest-first, de-duplicated."""
    seen = set()
    roots = [_SCRIPT_DIR]
    try:
        roots.append(pathlib.Path.cwd().resolve())
    except OSError:
        pass
    for root in roots:
        for directory in [root, *root.parents]:
            candidate = directory / ".env"
            if candidate not in seen:
                seen.add(candidate)
                yield candidate
    home_env = pathlib.Path.home() / ".env"
    if home_env not in seen:
        yield home_env


# Record where we looked so a genuine miss produces an actionable error (not a mystery).
_SEARCHED_ENV_FILES = []
if not os.environ.get("GEMINI_API_KEY"):
    for _candidate in _candidate_env_files():
        _SEARCHED_ENV_FILES.append(str(_candidate))
        if not _candidate.exists():
            continue
        try:
            for line in _candidate.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == "GEMINI_API_KEY":
                    os.environ["GEMINI_API_KEY"] = value.strip().strip("\"'")
                    break
        except OSError:
            continue
        if os.environ.get("GEMINI_API_KEY"):
            break

MODELS = {
    "standard": "gemini-2.5-flash-image",
    "flash": "gemini-2.5-flash-image",  # fallback to standard until a faster 2.5 tier ships
    # Nano Banana Pro (Gemini 3 Pro Image), released 2025-11-20: SOTA text rendering,
    # stronger prompt adherence, and native image editing (accepts input images).
    # Same generativelanguage generateContent endpoint as 2.5 Flash.
    "pro": "gemini-3-pro-image-preview",
    "nano-banana-pro": "gemini-3-pro-image-preview",
}

VALID_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
    "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
]

VALID_RESOLUTIONS = ["512", "1K", "2K", "4K"]


def _image_part(path: str) -> dict:
    """Build an inlineData part from a local image, sniffing mime by CONTENT.

    Content-sniffing matters: this pipeline saves JPEG bytes into .png filenames,
    so trusting the extension would mislabel the mime and the API would reject it.
    """
    data = pathlib.Path(path).read_bytes()
    if data[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    else:
        mime = "image/jpeg" if pathlib.Path(path).suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return {"inlineData": {"mimeType": mime, "data": base64.b64encode(data).decode("ascii")}}


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "3:4",
                   model_key: str = "standard", resolution: str = "2K",
                   input_images: list | None = None) -> dict:
    """Call Nano Banana API and save the resulting image.

    If input_images is given, they are sent as inlineData parts before the text
    prompt (image editing / composition) — only image-capable models (e.g. pro /
    nano-banana-pro = Gemini 3 Pro Image) honor them.
    """

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        if _SEARCHED_ENV_FILES:
            print("Searched these .env files (nearest-first) and found no GEMINI_API_KEY:", file=sys.stderr)
            for path in _SEARCHED_ENV_FILES:
                print(f"  - {path}", file=sys.stderr)
        print("Add GEMINI_API_KEY=... to one of the above (or export it), or get a key at "
              "https://aistudio.google.com/apikey", file=sys.stderr)
        sys.exit(1)

    model_id = MODELS.get(model_key, model_key)
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        print(f"Warning: '{aspect_ratio}' may not be supported. Valid: {VALID_ASPECT_RATIOS}", file=sys.stderr)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

    parts = [_image_part(p) for p in (input_images or [])]
    parts.append({"text": prompt})

    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
            }
        }
    }

    # Note: resolution parameter is not currently supported by the API
    # Keeping the CLI flag for future compatibility but not sending it

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        f"{url}?key={api_key}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"Generating image with {model_id}...")
    print(f"  Aspect ratio: {aspect_ratio}")
    print(f"  Resolution: {resolution}")
    print(f"  Output: {output_path}")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "No details"
        print(f"API Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract image from response
    candidates = result.get("candidates", [])
    if not candidates:
        print("Error: No candidates in response.", file=sys.stderr)
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)

    image_data = None
    text_response = None

    for candidate in candidates:
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if "inlineData" in part:
                image_data = part["inlineData"]
            elif "text" in part:
                text_response = part["text"]

    if not image_data:
        print("Error: No image data in response.", file=sys.stderr)
        if text_response:
            print(f"Model response: {text_response}", file=sys.stderr)
        print(json.dumps(result, indent=2)[:2000], file=sys.stderr)
        sys.exit(1)

    # Decode and save
    raw = base64.b64decode(image_data["data"])
    mime = image_data.get("mimeType", "image/png")

    # Save with the requested filename regardless of mime type
    # (API returns PNG but sites handle PNG-data in .jpg files fine)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(raw)

    size_kb = len(raw) / 1024
    print(f"Saved {size_kb:.0f}KB image ({mime}) to {output_path}")

    if text_response:
        print(f"Model note: {text_response}")

    return {
        "output_path": output_path,
        "size_bytes": len(raw),
        "mime_type": mime,
        "model": model_id,
        "text_response": text_response,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate images with Nano Banana (Gemini Image API)")
    parser.add_argument("--prompt", required=True, help="The image generation prompt")
    parser.add_argument("--output", required=True, help="Output file path (e.g., public/images/products/monk.jpg)")
    parser.add_argument("--aspect-ratio", default="3:4", help=f"Aspect ratio. Valid: {VALID_ASPECT_RATIOS}")
    parser.add_argument("--model", default="standard", choices=list(MODELS.keys()),
                        help="Model: standard/flash (Gemini 2.5 Flash Image), pro/nano-banana-pro (Gemini 3 Pro Image)")
    parser.add_argument("--resolution", default="2K", choices=VALID_RESOLUTIONS, help="Output resolution")
    parser.add_argument("--input-image", action="append", dest="input_images", default=None,
                        help="Input image to edit/compose from (repeatable). Only image-capable models "
                             "(pro / nano-banana-pro) use them; ignored by 2.5 Flash.")

    args = parser.parse_args()
    generate_image(args.prompt, args.output, args.aspect_ratio, args.model, args.resolution, args.input_images)


if __name__ == "__main__":
    main()
