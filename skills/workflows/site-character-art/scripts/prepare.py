#!/usr/bin/env python3
"""Turn promoted candidates into web-ready webp under public/art/, recording outputs in the
inventory. Needs Pillow.

  black mode: every pixel with all channels <= THRESH becomes pure black (0,0,0); the build
              places it with mix-blend-mode: screen + a radial mask on a #000 page.
  alpha mode: luminance 0..RAMP becomes alpha 0..255 (RGBA webp), for marks and non-black pages.
  cutout mode: only near-black pixels CONNECTED TO THE IMAGE BORDER become transparent (flood fill),
              with a 1px feather, so dark shadows inside the character stay opaque. Use for a
              character that moves over drawn lines or other art, where screen blend would let
              the lines show through its body.

Usage: prepare.py graphics/inventory.json [--out public/art] [--quality 82] [--widths 1200,800]
"""
import argparse
import json
import pathlib
import sys

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
except ImportError:
    sys.exit("Pillow is required: python3 -m pip install Pillow")

THRESH = 6
RAMP = 24


def _max_channel(rgb):
    r, g, b = rgb.split()
    return ImageChops.lighter(r, ImageChops.lighter(g, b))


BLACK_POINT = 16  # model "black" measures 7-13 in corners; a levels crush makes it page black


def _levels(rgb, bp):
    lut = [0 if v <= bp else round((v - bp) * 255 / (255 - bp)) for v in range(256)]
    return rgb.point(lut * 3)


def to_black(im, bp=None):
    rgb = _levels(im.convert("RGB"), BLACK_POINT if bp is None else bp)
    keep = _max_channel(rgb).point(lambda v: 255 if v > THRESH else 0)
    return Image.composite(rgb, Image.new("RGB", rgb.size, (0, 0, 0)), keep)


def to_cutout(im, thresh=14):
    rgb = _levels(im.convert("RGB"), BLACK_POINT)
    w, h = rgb.size
    dark = _max_channel(rgb).point(lambda v: 255 if v <= thresh else 0)
    pad = Image.new("L", (w + 2, h + 2), 255)
    pad.paste(dark, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    bg = pad.crop((1, 1, w + 1, h + 1)).point(lambda v: 255 if v == 128 else 0)
    alpha = ImageChops.invert(bg).filter(ImageFilter.GaussianBlur(1.1))
    rgba = Image.composite(rgb, Image.new("RGB", rgb.size, (0, 0, 0)), ImageChops.invert(bg))
    rgba.putalpha(alpha)
    return rgba


def to_alpha(im):
    rgb = im.convert("RGB")
    lum = rgb.convert("L").point(lambda v: 255 if v >= RAMP else int(v * 255 / RAMP))
    rgba = rgb.copy()
    rgba.putalpha(lum)
    return rgba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--out", default="public/art")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--widths", default="1200,800")
    ap.add_argument("--black-point", type=int, default=16,
                    help="levels black point; channels at or below it become 0 (page black)")
    a = ap.parse_args()
    globals()["BLACK_POINT"] = a.black_point
    inv_path = pathlib.Path(a.inventory).resolve()
    root = inv_path.parent.parent
    out_dir = (root / a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    inv = json.loads(inv_path.read_text())
    widths = [int(w) for w in a.widths.split(",") if w]
    for e in inv["entries"]:
        if e.get("status") != "promoted":
            continue
        src = root / e["file"]
        im = Image.open(src)
        mode = e.get("background", "black")
        im = {"alpha": to_alpha, "cutout": to_cutout}.get(mode, to_black)(im)
        outputs = {"width": im.size[0], "height": im.size[1]}
        base = out_dir / e["scene"]
        for i, w in enumerate(widths):
            target = im if w >= im.size[0] else im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS)
            path = base.with_name(f"{e['scene']}.webp") if i == 0 else base.with_name(f"{e['scene']}-{w}.webp")
            target.save(path, "WEBP", quality=a.quality, method=6)
            outputs["webp" if i == 0 else f"webp_{w}"] = str(path.relative_to(root))
            print(f"{e['scene']}: {path.relative_to(root)} {target.size[0]}x{target.size[1]} {path.stat().st_size // 1024}KB ({mode})")
        e["outputs"] = outputs
    inv_path.write_text(json.dumps(inv, indent=2) + "\n")
    print(f"updated {inv_path.relative_to(root)}")


if __name__ == "__main__":
    main()
