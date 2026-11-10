#!/usr/bin/env python3
"""Turn a plan's cards into Andon cards whose notes tell the run which skills to load.

Andon gives a run the card's title and notes as its prompt. It has a native per-card `skill` field, but capture can't
set it, it holds one skill, and the machine catalog behind it skips symlinked skills (every Skill-Madness skill on a
`/sync-skills` machine). Until Andon reads skills natively, the skills go in the notes, as the first thing the run
reads. This script writes that block the same way every time, checks the names, and captures the cards.

Input is a JSON file (see references/plan-to-cards.md for the full shape):

  {"team": "Web", "project": "Login revamp", "recipe": "code-change", "group": null,
   "plan": "docs/plans/login.md",
   "cards": [{"key": "api", "title": "Add the session endpoint", "goal": "...", "where": "...",
              "done": ["..."], "skills": [{"name": "contract-author", "why": "spec first"}, "fix-until-green"],
              "depends_on": []}]}

Usage:
  push_cards.py cards.json                 # dry run: print every card's notes and the capture it would send
  push_cards.py cards.json --send          # capture them, in dependency order; writes cards.receipt.json
  push_cards.py cards.json --send          # again after a failure: resumes, skipping cards the receipt says landed
  push_cards.py cards.json --send --again  # ignore the receipt and capture every card again

Auth: ANDON_CAPTURE_TOKEN (or captureToken in the agent config, or ~/.config/andon/capture.env). URL:
ANDON_CAPTURE_URL, else the agent config's apiUrl + /functions/v1/capture. The agent config is read from
ANDON_CONFIG_DIR, ~/.andon/agent, then ~/.config/andon. The token is never printed.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SHELVES = [Path("~/.claude/skills").expanduser(), Path("~/.agents/skills").expanduser()]
CONFIG_DIRS = [os.environ.get("ANDON_CONFIG_DIR"), "~/.andon/agent", "~/.config/andon"]
MAX_NOTES = 20000  # well under the board's limits; a card this long should be split


def die(msg: str, code: int = 2):
    print(f"push_cards: {msg}", file=sys.stderr)
    sys.exit(code)


def agent_config() -> dict:
    for d in CONFIG_DIRS:
        if not d:
            continue
        p = Path(d).expanduser() / "config.json"
        if p.is_file():
            try:
                return json.loads(p.read_text())
            except json.JSONDecodeError:
                die(f"{p} is not valid JSON")
    return {}


def capture_env() -> dict:
    p = Path("~/.config/andon/capture.env").expanduser()
    out = {}
    if p.is_file():
        for line in p.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def endpoint() -> tuple:
    cfg, env = agent_config(), capture_env()
    token = os.environ.get("ANDON_CAPTURE_TOKEN") or cfg.get("captureToken") or env.get("ANDON_CAPTURE_TOKEN")
    url = os.environ.get("ANDON_CAPTURE_URL") or env.get("ANDON_CAPTURE_URL")
    if not url and (cfg.get("apiUrl") or cfg.get("supabaseUrl")):
        url = f"{(cfg.get('apiUrl') or cfg.get('supabaseUrl')).rstrip('/')}/functions/v1/capture"
    return url, token, cfg.get("boardUrl")


def skill_entry(s) -> dict:
    if isinstance(s, str):
        return {"name": s, "why": ""}
    if isinstance(s, dict) and s.get("name"):
        return {"name": s["name"], "why": s.get("why", "")}
    die(f"a skill must be a name or {{name, why}}: {s!r}")


def find_skill(name: str):
    """(path, symlinked) for the first shelf that has the skill, else (None, False)."""
    for shelf in SHELVES:
        p = shelf / name
        if (p / "SKILL.md").is_file():
            return p, p.is_symlink()
    return None, False


def order(cards: list) -> list:
    """Dependency order (a card after everything it depends on); refuses unknown keys and cycles."""
    by_key = {c["key"]: c for c in cards}
    for c in cards:
        for d in c.get("depends_on", []):
            if d not in by_key:
                die(f'card "{c["key"]}" depends on "{d}", which is not in this file')
    done, out, visiting = set(), [], set()

    def visit(c):
        if c["key"] in done:
            return
        if c["key"] in visiting:
            die(f'dependency cycle through "{c["key"]}"')
        visiting.add(c["key"])
        for d in c.get("depends_on", []):
            visit(by_key[d])
        visiting.discard(c["key"])
        done.add(c["key"])
        out.append(c)

    for c in cards:
        visit(c)
    return out


def skills_block(skills: list) -> str:
    lines = [
        "## Skills to use",
        "",
        "Load each of these skills before you start, and follow it. They are Skill-Madness skills installed on this",
        "machine.",
        "",
    ]
    for s in skills:
        lines.append(f"- `{s['name']}`" + (f": {s['why']}" if s["why"] else ""))
    lines += [
        "",
        "How to load one:",
        "",
        "1. Claude Code: invoke it by name (the Skill tool, or `/<name>`).",
        "2. If it isn't listed (Codex, Gemini, or a run with its own Claude home): read",
        "   `~/.claude/skills/<name>/SKILL.md` (or `~/.agents/skills/<name>/SKILL.md`) and follow it.",
        "3. If the andon tool `use_skill` finds the name, call it too, so the board records that the skill was used.",
        "",
        "In your final report, name the skills you loaded and any you could not find.",
    ]
    return "\n".join(lines)


def render_notes(card: dict, keys: dict, titles: dict, plan: str) -> str:
    parts = []
    skills = [skill_entry(s) for s in card.get("skills", [])]
    if skills:
        parts.append(skills_block(skills))
    if card.get("goal"):
        parts.append(f"## Goal\n\n{card['goal'].strip()}")
    if card.get("where"):
        parts.append(f"## Where to look\n\n{card['where'].strip()}")
    if card.get("done"):
        items = card["done"] if isinstance(card["done"], list) else [card["done"]]
        parts.append("## Done when\n\n" + "\n".join(f"- [ ] {d}" for d in items))
    deps = card.get("depends_on", [])
    if deps:
        named = [f'"{titles[d]}"' + (f" ({keys[d]})" if keys.get(d) else "") for d in deps]
        parts.append("## Depends on\n\nStart only after these cards are done: " + ", ".join(named) + ". If one isn't, "
                     "say so in your report instead of doing its work.")
    if card.get("notes"):
        parts.append(card["notes"].strip())
    if plan:
        parts.append(f"## Source plan\n\n{plan}")
    return "\n\n".join(parts)


def post(url: str, token: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "authorization": f"Bearer {token}", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"status": r.status, **json.loads(r.read() or b"{}")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.read().decode(errors="replace")[:300]}
    except urllib.error.URLError as e:
        return {"status": 0, "error": str(e.reason)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--send", action="store_true", help="capture the cards (default: dry run)")
    ap.add_argument("--again", action="store_true", help="capture even though a receipt for this file exists")
    ap.add_argument("--allow-unknown-skills", action="store_true", help="capture although a skill isn't installed here")
    a = ap.parse_args()

    src = Path(a.file)
    try:
        spec = json.loads(src.read_text())
    except (OSError, json.JSONDecodeError) as e:
        die(f"can't read {src}: {e}")
    cards = spec.get("cards") or die("no cards in the file")
    for i, c in enumerate(cards):
        if not c.get("title"):
            die(f"card {i + 1} has no title")
        c.setdefault("key", f"card-{i + 1}")
    if len({c["key"] for c in cards}) != len(cards):
        die("two cards share a key")

    # Every skill named must be on this machine's shelf, or the run can't load it.
    problems, symlinked = [], set()
    for c in cards:
        if not c.get("skills"):
            print(f'warn: "{c["title"]}" names no skills; the run will choose its own', file=sys.stderr)
        for s in (skill_entry(x) for x in c.get("skills", [])):
            path, link = find_skill(s["name"])
            if not path:
                problems.append(f'"{c["title"]}": skill "{s["name"]}" is not in ~/.claude/skills or ~/.agents/skills')
            elif link:
                symlinked.add(s["name"])
    for p in problems:
        print(f"{'warn' if a.allow_unknown_skills else 'error'}: {p}", file=sys.stderr)
    if problems and not a.allow_unknown_skills:
        die("fix the skill names (or pass --allow-unknown-skills)")
    if symlinked:
        print(f"note: {len(symlinked)} skill(s) are symlinks, which Andon's catalog skips, so `use_skill` won't find them;"
              " the notes tell the run to read them by path instead.", file=sys.stderr)

    # A receipt from an earlier --send: cards it records as landed are skipped (and their keys reused), so a retry
    # after a failure resumes instead of duplicating the board. --again ignores it.
    receipt = src.with_suffix(".receipt.json")
    landed = {}
    if receipt.exists() and not a.again:
        try:
            landed = {x["key"]: x for x in json.loads(receipt.read_text()).get("cards", []) if x.get("status") == 201}
        except (OSError, json.JSONDecodeError, KeyError):
            die(f"{receipt} is unreadable; fix or move it, or pass --again")
        if landed and len(landed) == len(cards):
            die(f"{receipt}: every card already landed (pass --again to capture them all again)")

    url, token, board = endpoint()
    if a.send and (not url or not token):
        die("no capture token or URL: set ANDON_CAPTURE_TOKEN (Settings -> Connections -> Developer -> Capture "
            "tokens on the board) and, if the agent config has no apiUrl, ANDON_CAPTURE_URL")

    plan, keys, results, group_ref = spec.get("plan", ""), {}, [], spec.get("group")
    titles = {c["key"]: c["title"] for c in cards}
    for c in order(cards):
        if c["key"] in landed:
            prev = landed[c["key"]]
            keys[c["key"]] = prev.get("card_key") or ""
            results.append(prev)
            if group_ref == "new" and (prev.get("group") or {}).get("id"):
                group_ref = prev["group"]["id"]
            print(f"skip {keys[c['key']] or '-':8} {c['title']}  (landed earlier)")
            continue
        notes = render_notes(c, keys, titles, plan)
        if len(notes) > MAX_NOTES:
            die(f'"{c["title"]}" notes are {len(notes)} chars; split the card')
        body = {k: v for k, v in {
            "title": c["title"], "notes": notes, "team": c.get("team", spec.get("team")),
            "project": c.get("project", spec.get("project")), "recipe": c.get("recipe", spec.get("recipe")),
            "template": c.get("template", spec.get("template")), "group": group_ref, "url": c.get("url"),
        }.items() if v}
        if not a.send:
            print(f"=== {c['key']}: {c['title']}")
            print(json.dumps({k: v for k, v in body.items() if k != "notes"}))
            print(notes)
            print()
            continue
        r = post(url, token, body)
        ok = r.get("status") == 201
        key = r.get("card_key") or ""
        keys[c["key"]] = key
        link = f"{board.rstrip('/')}{r['path']}" if ok and board and r.get("path") else r.get("path")
        results.append({"key": c["key"], "title": c["title"], "status": r.get("status"), "card_key": key,
                        "card_id": r.get("card_id"), "link": link, "group": r.get("group"),
                        "group_error": r.get("group_error"), "error": r.get("error")})
        print(f"{'ok ' if ok else 'ERR'} {key or '-':8} {c['title']}  {link or r.get('error', '')}")
        if r.get("group_error"):
            print(f"    not grouped: {r['group_error']}")
        # `new` makes one planned group around the first card; the rest join it by id, so they ship in one PR.
        if ok and group_ref == "new" and (r.get("group") or {}).get("id"):
            group_ref = r["group"]["id"]
        if not ok:
            break
    if a.send:
        receipt.write_text(json.dumps({"source": str(src), "cards": results}, indent=2) + "\n")
        print(f"receipt: {receipt}")
        if any(x["status"] != 201 for x in results):
            sys.exit(1)
        print("Next: check each card on the board (team, project, recipe stuck), then press Run or `andon run <KEY>`.")


if __name__ == "__main__":
    main()
