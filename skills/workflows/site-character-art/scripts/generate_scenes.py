#!/usr/bin/env python3
"""Render every scene in graphics/scenes.json through nano-banana, sequentially, into versioned
candidate files, recording each prompt in graphics/inventory.json. Never overwrites a file.

Usage:
  generate_scenes.py graphics/scenes.json [--site slug] [--only hero,board] [--model <key or id>]
                     [--nb /path/to/generate_image.py] [--dry-run]

--model takes a nano-banana key (standard, pro) or any raw Gemini model id the key can reach
(for example gemini-3-pro-image, or a newer one). List what the key reaches first:
  generate_scenes.py --list-models
and use the newest image model; the script calls nano-banana's generate_image() directly, so a raw
id is not rejected by the CLI's fixed --model choices.

The nano-banana script is found from NB_SCRIPT, --nb, or the Skill-Madness checkout next to this
skill (skills/workflows/nano-banana/scripts/generate_image.py). Generation is paid: confirm the
scene list with the person before running without --dry-run.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time


def find_nb(explicit):
    if explicit:
        return pathlib.Path(explicit)
    env = os.environ.get("NB_SCRIPT")
    if env:
        return pathlib.Path(env)
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "skills" / "workflows" / "nano-banana" / "scripts" / "generate_image.py"
        if cand.is_file():
            return cand
    sys.exit("nano-banana's generate_image.py not found; pass --nb or set NB_SCRIPT")


def load_nb(nb):
    """Import nano-banana's generate_image module (it loads the key itself; never print it)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("nb_generate_image", nb)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def list_models(nb):
    import urllib.request
    load_nb(nb)
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY not set (nano-banana found none); see nano-banana's Setup")
    url = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000&key=" + key
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    for m in data.get("models", []):
        if "image" in m["name"] or "banana" in m["name"]:
            print(m["name"].split("/", 1)[1], "|", m.get("displayName", ""))


def load_inventory(path, site):
    if path.exists():
        return json.loads(path.read_text())
    return {"site": site, "generator": "", "refs": [], "entries": []}


def promoted_or_latest(inv, scene):
    entries = [e for e in inv["entries"] if e.get("scene") == scene]
    if not entries:
        return None
    promoted = [e for e in entries if e.get("status") == "promoted"]
    pick = promoted[0] if promoted else max(entries, key=lambda e: e.get("version", 0))
    return pick["file"]


def next_version(inv, scene):
    return 1 + max([e.get("version", 0) for e in inv["entries"] if e.get("scene") == scene] or [0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="?")
    ap.add_argument("--list-models", action="store_true")
    ap.add_argument("--site")
    ap.add_argument("--only")
    ap.add_argument("--model", default="pro")
    ap.add_argument("--nb")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.list_models:
        list_models(find_nb(a.nb))
        return
    if not a.scenes:
        ap.error("scenes.json is required")

    scenes_path = pathlib.Path(a.scenes).resolve()
    gdir = scenes_path.parent                      # graphics/
    root = gdir.parent                             # the site repo
    plan = json.loads(scenes_path.read_text())
    site = a.site or plan.get("site") or "site"
    inv_path = gdir / "inventory.json"
    inv = load_inventory(inv_path, site)
    nb = find_nb(a.nb)
    inv["generator"] = f"nano-banana generate_image.py, model {a.model}"
    nbmod = None if a.dry_run else load_nb(nb)
    only = set(a.only.split(",")) if a.only else None
    cand_dir = gdir / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)

    for sc in plan["scenes"]:
        name = sc["scene"]
        if only and name not in only:
            continue
        prompt = sc["prompt"].replace("{style}", plan.get("style", ""))
        for cname, line in plan.get("cast", {}).items():
            prompt = prompt.replace("{cast.%s}" % cname, line)
        refs = []
        for r in sc.get("refs", []):
            p = gdir / r
            if p.is_file():
                refs.append(p)
                continue
            pick = promoted_or_latest(inv, r)
            if pick and (root / pick).is_file():
                refs.append(root / pick)
            else:
                sys.exit(f"{name}: reference '{r}' is neither a file under graphics/ nor a rendered scene")
        version = next_version(inv, name)
        out = cand_dir / f"{site}-{name}-v{version}.png"
        while out.exists():
            version += 1
            out = cand_dir / f"{site}-{name}-v{version}.png"
        print(f"== {name} v{version} -> {out.relative_to(root)}  refs={[str(r.name) for r in refs]}")
        if a.dry_run:
            print("   (dry run)")
            continue
        try:
            nbmod.generate_image(prompt, str(out), sc.get("aspect", "4:3"), a.model,
                                 sc.get("resolution", "2K"), [str(r) for r in refs])
        except SystemExit as e:
            sys.exit(f"{name}: generation failed ({e}); inventory saved so far")
        inv["entries"].append({
            "scene": name, "file": str(out.relative_to(root)), "version": version,
            "rendered_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "aspect": sc.get("aspect", "4:3"), "model": a.model,
            "refs": [str(r.relative_to(root)) if root in r.parents else str(r) for r in refs],
            "prompt": prompt, "background": sc.get("background", "black"),
            "alt": sc.get("alt", ""), "section": sc.get("section", ""),
            "status": "candidate", "notes": "",
        })
        inv_path.write_text(json.dumps(inv, indent=2) + "\n")
        time.sleep(2)
    if not a.dry_run:
        inv_path.write_text(json.dumps(inv, indent=2) + "\n")
        print(f"inventory: {inv_path.relative_to(root)}")


if __name__ == "__main__":
    main()
