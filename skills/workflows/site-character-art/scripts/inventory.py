#!/usr/bin/env python3
"""Record what the candidates really are: format (sniffed, not the extension), size, corner and
edge darkness, sha1. Adds entries for files the inventory doesn't know and fills `measured` on
every entry. Warns when a glow reaches the image edge.

Usage: inventory.py graphics/candidates graphics/inventory.json
Pillow is optional; without it width/height and darkness are left as null ("unverified").
"""
import hashlib
import json
import pathlib
import re
import sys

try:
    from PIL import Image
except ImportError:  # measured fields stay null
    Image = None

EDGE_WARN = 24


def sniff(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def measure(path):
    data = path.read_bytes()
    m = {"format": sniff(data), "bytes": len(data), "sha1": hashlib.sha1(data).hexdigest(),
         "width": None, "height": None, "corners_max": None, "edge_max": None, "alpha": None}
    if Image is None:
        return m
    im = Image.open(path)
    m["alpha"] = im.mode in ("RGBA", "LA")
    im = im.convert("RGB")
    w, h = im.size
    m["width"], m["height"] = w, h
    px = im.load()
    s = 8
    corners = [(0, 0), (w - s, 0), (0, h - s), (w - s, h - s)]
    cmax = 0
    for cx, cy in corners:
        for x in range(cx, cx + s):
            for y in range(cy, cy + s):
                cmax = max(cmax, max(px[x, y]))
    emax = 0
    for x in range(w):
        emax = max(emax, max(px[x, 0]), max(px[x, h - 1]))
    for y in range(h):
        emax = max(emax, max(px[0, y]), max(px[w - 1, y]))
    m["corners_max"], m["edge_max"] = cmax, emax
    return m


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cand = pathlib.Path(sys.argv[1]).resolve()
    inv_path = pathlib.Path(sys.argv[2]).resolve()
    root = inv_path.parent.parent
    inv = json.loads(inv_path.read_text()) if inv_path.exists() else {"site": "", "entries": []}
    known = {e["file"]: e for e in inv["entries"]}
    for f in sorted(cand.iterdir()):
        if f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        rel = str(f.relative_to(root))
        e = known.get(rel)
        if e is None:
            mm = re.match(r"(.+?)-(.+)-v(\d+)(?:-\d+)?\.", f.name)
            e = {"scene": mm.group(2) if mm else f.stem, "file": rel,
                 "version": int(mm.group(3)) if mm else 1, "status": "candidate", "alt": "", "prompt": "", "notes": ""}
            inv["entries"].append(e)
            known[rel] = e
        e["measured"] = measure(f)
        m = e["measured"]
        flag = ""
        if m["edge_max"] is not None and m["edge_max"] > EDGE_WARN:
            flag = f"  WARN lit edge ({m['edge_max']})"
        dims = f"{m['width']}x{m['height']}" if m["width"] else "size unverified"
        print(f"{rel}: {m['format']} {dims} corners<={m['corners_max']} edge<={m['edge_max']} {e['status']}{flag}")
    promoted = {}
    for e in inv["entries"]:
        if e.get("status") == "promoted":
            promoted.setdefault(e["scene"], []).append(e["file"])
    for scene, files in promoted.items():
        if len(files) > 1:
            print(f"WARN scene '{scene}' has {len(files)} promoted files: {files}")
    inv_path.write_text(json.dumps(inv, indent=2) + "\n")
    print(f"wrote {inv_path.relative_to(root)} ({len(inv['entries'])} entries)")


if __name__ == "__main__":
    main()
