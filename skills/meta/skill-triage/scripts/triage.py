#!/usr/bin/env python3
"""triage.py — score skill routing with TypeSafe's Jev decision model.

Jev answers typed questions (choice / noul / score) about a state and returns
probabilities instead of prose. This script turns a skill catalog into Jev
Choice criteria and uses it three ways:

  route       pick the skill for one request (two-stage: wide rank + gated rerank)
  check       measure routing accuracy against labeled cases or a routing table
  collisions  probe each skill with its OWN trigger phrases; report which other
              skill's description wins them (description collisions)

`check` and `collisions` rank on name + description only — the same text a host
sees when it decides whether to load a skill — so a miss there is a description
problem, not a body problem. `route` adds a body excerpt on the shortlist.

Usage:
  triage.py route "keep fixing the tests until green, I'm going to bed"
  triage.py check --cases cases.json [--fail-under 0.8]
  triage.py check --from-routing-table skills/meta/skill-explorer/references/routing-table.md
  triage.py collisions [--skill madness --skill skill-explorer]
  common: [--root DIR ...] [--only NAME ...] [--model M] [--env-file PATH]
          [--json] [--dry-run] [--limit N] [--concurrency N]

Credentials (read from the environment, never printed; first key found wins):
  VENICE_API_KEY     -> https://api.venice.ai/api/v1/systemone   (default; cost estimated)
  TYPESAFE_API_KEY   -> https://api.typesafe.ai/v1/systemone
  OPENROUTER_API_KEY -> https://openrouter.ai/api/v1/systemone
  JEV_PROVIDER       force one provider: venice | typesafe | openrouter
  TYPESAFE_BASE_URL  https override of the TypeSafe base URL only; never read
                     from --env-file, so a key can't be sent to a planted host
  JEV_MODEL          model id (default jev-latest; pin e.g. jev-1.13 for
                     comparable check runs — the served model is always reported)

Every request sends the request text and the catalog's descriptions to the
provider. Pure python3 stdlib. Exit codes: 0 ok, 1 below --fail-under,
2 argument error, 3 API rejected the request, 4 Jev unavailable (no key,
401/402/403 — e.g. a zero balance — unreachable, or still rate-limited after
retries). Exit 4 means "route without Jev", never "stop".
"""

import argparse
import http.client
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Thresholds live here, in one place, so a human can review and tune them.
GATE_THRESHOLD = 0.30   # mean gate noul below this -> "no skill needed"
FITS_THRESHOLD = 0.30   # best per-candidate fits noul below this -> no winner
SHORTLIST = 3           # candidates carried from the wide rank into the rerank
EXCERPT_CHARS = 700     # SKILL.md body characters shown per shortlisted skill
LOW_MARGIN = 0.20       # check/collisions: a correct win by less than this is flagged
MAX_CRITERIA = 255      # Jev's per-Choice option ceiling

SKIP_DIRS = {"archive", "in-progress", "node_modules"}

# Checked in order; the first key present wins. All serve POST <base>/v1/systemone.
PROVIDERS = [
    ("venice", "VENICE_API_KEY", "https://api.venice.ai/api"),
    ("typesafe", "TYPESAFE_API_KEY", "https://api.typesafe.ai"),
    ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api"),
]
UNAVAILABLE = 4  # exit code: Jev can't be reached or paid for -> caller routes without it
UNAVAILABLE_HTTP = {401, 402, 403, 429, 500, 502, 503, 529}  # 429/5xx only after retries
VENICE_USD_PER_M_INPUT = 0.042  # from Venice /models jev-latest spec, 2026-10-24
DEFAULT_ROOT = Path(__file__).resolve().parents[3]  # repo skills/


# ---------------------------------------------------------------- catalog

def _frontmatter(text):
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def _field(fm, key):
    """Pull one top-level scalar or block scalar out of YAML frontmatter."""
    lines = fm.splitlines()
    for i, line in enumerate(lines):
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if not m:
            continue
        value = m.group(1).strip()
        if value[:1] in ("|", ">"):
            block = []
            for nxt in lines[i + 1:]:
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                block.append(nxt.strip())
            return " ".join(b for b in block if b)
        return value.strip("'\"")
    return ""


def _skill_files(root):
    """SKILL.md files at a skill root: <root>/<skill>/ or <root>/<cat>/<skill>/."""
    found = []
    for depth in ("*/SKILL.md", "*/*/SKILL.md"):
        for path in root.glob(depth):
            if SKIP_DIRS.intersection(path.relative_to(root).parts):
                continue
            found.append(path)
    if (root / "SKILL.md").is_file():
        found.append(root / "SKILL.md")
    return sorted(set(found))


def load_catalog(roots, only=None):
    catalog = {}
    for root in roots:
        for path in _skill_files(root):
            fm, body = _frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            name = _field(fm, "name")
            desc = _field(fm, "description")
            if not name or not desc or name in catalog:
                continue
            catalog[name] = {"description": desc, "body": body.strip(), "path": str(path)}
    if only:
        missing = sorted(set(only) - set(catalog))
        if missing:
            die(f"--only names not in catalog: {', '.join(missing)}")
        catalog = {k: v for k, v in catalog.items() if k in only}
    if not catalog:
        die("no skills found; pass --root pointing at a skills directory")
    if len(catalog) > MAX_CRITERIA:
        die(f"{len(catalog)} skills exceeds Jev's {MAX_CRITERIA}-option Choice limit; narrow with --only")
    return catalog


TRIGGER_MARKER = re.compile(r"triggers? on|trigger:|triggers include|use when", re.I)


def trigger_phrases(description):
    """Quoted trigger phrases from a description, e.g. Trigger on: "commit", "open a PR".

    Quotes before a trigger marker are usually prose ("tests pass", "modified"),
    so when a marker exists only quotes after it count.
    """
    marker = TRIGGER_MARKER.search(description)
    text = description[marker.start():] if marker else description
    # Match every quoted span with no length limit, then filter: a length bound
    # inside the regex pairs the closing quote of a short span with the next
    # opening quote and turns the prose between them into a "phrase".
    phrases = (p.strip() for p in re.findall(r"[\"“]([^\"”]*)[\"”]", text))
    return [p for p in phrases if 3 <= len(p) <= 120 and not p.startswith("/")]


# ---------------------------------------------------------------- API

class Client:
    def __init__(self, model, env_file=None, retries=8, timeout=60):
        if env_file:
            _load_env_file(env_file)
        model = model or os.environ.get("JEV_MODEL", "jev-latest")
        self.retries, self.timeout = retries, timeout
        self.lock = threading.Lock()
        forced = os.environ.get("JEV_PROVIDER")
        candidates = [p for p in PROVIDERS if not forced or p[0] == forced]
        if not candidates:
            die(f"JEV_PROVIDER={forced} is not one of: {', '.join(p[0] for p in PROVIDERS)}")
        for name, env, base in candidates:
            key = os.environ.get(env)
            if key:
                break
        else:
            die("jev unavailable: no " + ", ".join(env for _, env, _ in candidates) +
                " in the environment (pass --env-file to load one from a .env)", UNAVAILABLE)
        self.key = key
        self.provider = name
        override = os.environ.get("TYPESAFE_BASE_URL") if name == "typesafe" else None
        if override and not override.startswith("https://"):
            die("TYPESAFE_BASE_URL must be an https:// URL")
        self.url = (override or base).rstrip("/") + "/v1/systemone"
        self.model = model
        self.calls = 0
        self.cost = 0.0
        self.served = set()

    def ask(self, state, questions):
        retries = self.retries
        body = json.dumps({"model": self.model, "state": state, "questions": questions}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read())
                if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
                    raise ValueError("response has no answers map")
                break
            except urllib.error.HTTPError as err:
                if err.code in (429, 500, 502, 503, 529) and attempt < retries - 1:
                    time.sleep(_backoff(err.headers, attempt))
                    continue
                detail = err.read().decode(errors="replace")[:300]
                raise ApiError(f"HTTP {err.code} from {self.provider}: {detail}",
                               unavailable=err.code in UNAVAILABLE_HTTP) from None
            except urllib.error.URLError as err:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ApiError(f"cannot reach {self.url}: {err.reason}", unavailable=True) from None
            except (TimeoutError, ConnectionError, http.client.HTTPException) as err:
                if attempt < retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise ApiError(f"connection to {self.provider} failed: {err!r}", unavailable=True) from None
            except ValueError as err:  # includes JSONDecodeError: an HTML proxy page, a truncated body
                raise ApiError(f"unusable response from {self.provider}: {err}", unavailable=True) from None
        usage = data.get("usage") or {}
        if "cost" in usage:
            cost = float(usage["cost"] or 0)
        elif self.provider == "venice":
            # Venice omits cost; its model spec prices Jev input-only.
            cost = usage.get("input_tokens", 0) * VENICE_USD_PER_M_INPUT / 1e6
        else:
            cost = 0.0
        with self.lock:
            self.calls += 1
            self.cost += cost
            if data.get("model"):
                self.served.add(data["model"])
        return data["answers"]


class ApiError(RuntimeError):
    def __init__(self, msg, unavailable=False):
        super().__init__(msg)
        self.unavailable = unavailable


def _backoff(headers, attempt):
    """Seconds to wait: Retry-After, else the provider's reset stamp (epoch ms), else exponential."""
    try:
        if headers.get("Retry-After"):
            return min(float(headers["Retry-After"]), 65)
        resets = [float(headers[h]) for h in ("x-ratelimit-reset-tokens", "x-ratelimit-reset-requests")
                  if headers.get(h)]
        if resets:
            return min(max(max(resets) / 1000 - time.time(), 1) + 0.5, 65)
    except (TypeError, ValueError):
        pass
    return min(2 ** attempt, 30)


def _load_env_file(path):
    for line in Path(path).expanduser().read_text().splitlines():
        m = re.match(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$", line)
        if m and m.group(1) in [env for _, env, _ in PROVIDERS] + ["JEV_MODEL"]:
            os.environ.setdefault(m.group(1), m.group(2).strip().strip("'\""))


# ---------------------------------------------------------------- questions

def wide_choice(catalog):
    return {"type": "choice",
            "instructions": "Which skill should the agent load to handle this request?",
            "criteria": {name: s["description"] for name, s in catalog.items()}}


GATES = {
    "acts_on_user_system": ("Does the request ask the agent to act on the user's files, repo, "
                            "tools or accounts rather than only discuss something?", False),
    "would_follow_documented_procedure": ("Would a careful expert handle this by following a "
                                          "documented multi-step procedure?", False),
    "prose_suffices": ("Could this be fully handled by a short direct answer with no special "
                       "procedure?", True),
}


def ranked(answer):
    probs = answer.get("probabilities") or {}
    return sorted(probs.items(), key=lambda kv: kv[1], reverse=True)


def route(client, catalog, request):
    state = {"request": request}
    questions = {"which": wide_choice(catalog)}
    questions.update({k: {"type": "noul", "instructions": q} for k, (q, _) in GATES.items()})
    wide = client.ask(state, questions)

    gate = sum((1 - wide[k]["noul"]) if inv else wide[k]["noul"]
               for k, (_, inv) in GATES.items()) / len(GATES)
    top = ranked(wide.get("which", {}))[:SHORTLIST]
    result = {"request": request, "gate": round(gate, 3),
              "shortlist": [{"skill": n, "p": round(p, 3)} for n, p in top],
              "winner": None, "reason": ""}
    if gate < GATE_THRESHOLD:
        result["reason"] = f"gate {gate:.2f} < {GATE_THRESHOLD}: request likely needs no skill"
        return result
    if not top:
        result["reason"] = "Jev returned no probability distribution; no winner"
        return result

    short = {n: catalog[n] for n, _ in top}
    rerank = {"which": {"type": "choice",
                        "instructions": "Which of these skills best fits the request?",
                        "criteria": {n: f"{s['description']}\n\n{s['body'][:EXCERPT_CHARS]}"
                                     for n, s in short.items()}}}
    for n, s in short.items():
        rerank[f"fits::{n}"] = {"type": "noul", "instructions":
                                f"Is the skill '{n}' a good fit for this request? Skill: {s['description']}"}
    second = client.ask(state, rerank)
    fits = {n: round(second[f"fits::{n}"]["noul"], 3) for n in short}
    result["fits"] = fits
    result["confidence"] = round(second["which"].get("confidence", 0), 3)
    best = max(fits, key=fits.get)
    if fits[best] < FITS_THRESHOLD:
        result["reason"] = f"best fit {fits[best]:.2f} < {FITS_THRESHOLD}: no shortlisted skill fits"
        return result
    pick = second["which"].get("choice")
    if pick in fits and fits[pick] >= FITS_THRESHOLD:
        result["winner"], result["reason"] = pick, "rerank choice"
    else:  # the rerank's pick failed its own fit check; trust the skill that passed
        result["winner"], result["reason"] = best, f"rerank pick {pick} failed its fit check; best fit"
    return result


# ---------------------------------------------------------------- check / collisions

def load_cases(path):
    data = json.loads(Path(path).read_text())
    cases = data.get("cases", data) if isinstance(data, dict) else data
    out = []
    for c in cases:
        expect = c["expect"]
        out.append({"prompt": c["prompt"], "expect": [expect] if isinstance(expect, str) else list(expect)})
    return out


def cases_from_routing_table(path, catalog):
    """Rows like: | "commit these changes" / "git commit" | `git-commit` or `x` | notes |"""
    cases, skipped = [], []
    for line in Path(path).read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0].startswith(("\"", "“")):
            continue
        targets = re.findall(r"`([^`]+)`", cells[1])
        names = [t.split()[0] for t in targets if t.split()[0] in catalog]
        phrases = re.findall(r"[\"“]([^\"”]+)[\"”]", cells[0])
        if not names:
            skipped.extend(phrases)
            continue
        cases.extend({"prompt": p, "expect": names} for p in phrases)
    return cases, skipped


def cases_from_triggers(catalog, skills):
    cases = []
    for name in skills or catalog:
        for phrase in trigger_phrases(catalog[name]["description"]):
            cases.append({"prompt": phrase, "expect": [name]})
    return cases


def score_cases(client, catalog, cases, concurrency):
    question = {"which": wide_choice(catalog)}

    def one(case):
        try:
            answer = client.ask({"request": case["prompt"]}, question)["which"]
        except ApiError as err:
            if err.unavailable:
                raise  # a dead key or empty account fails every case; stop the run
            return {**case, "error": str(err)}
        order = ranked(answer)
        if not order:
            return {**case, "error": "Jev returned no probability distribution"}
        got, p_got = order[0]
        p_expect = max(answer["probabilities"].get(e, 0) for e in case["expect"])
        second, runner_up = order[1] if len(order) > 1 else (None, 0)
        return {**case, "got": got, "p_got": round(p_got, 3), "p_expect": round(p_expect, 3),
                "ok": got in case["expect"], "margin": round(p_got - runner_up, 3),
                "runner_up": second, "p_runner_up": round(runner_up, 3),
                "confidence": round(answer.get("confidence", 0), 3)}

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        return list(pool.map(one, cases))


def summarize(results):
    errors = [r for r in results if "error" in r]
    results = [r for r in results if "error" not in r]
    misses = [r for r in results if not r["ok"]]
    thin = [r for r in results if r["ok"] and r["margin"] < LOW_MARGIN]
    stealers = {}
    for r in misses:
        for e in r["expect"]:
            key = f"{r['got']} <- {e}"
            stealers[key] = stealers.get(key, 0) + 1
    total = len(results) + len(errors)  # unscored cases count against accuracy
    return {"total": total, "correct": len(results) - len(misses),
            "accuracy": round((len(results) - len(misses)) / total, 3) if total else 0,
            "misses": misses, "low_margin": thin, "errors": errors,
            "stealers": dict(sorted(stealers.items(), key=lambda kv: -kv[1]))}


# ---------------------------------------------------------------- output

def die(msg, code=2):
    print(f"triage: {msg}", file=sys.stderr)
    sys.exit(code)


def print_summary(summary, title):
    print(f"{title}: {summary['correct']}/{summary['total']} correct "
          f"({summary['accuracy']:.0%})")
    if summary["errors"]:
        print(f"  {len(summary['errors'])} case(s) not scored after retries "
              f"(first: {summary['errors'][0]['error']})")
    if summary["stealers"]:
        print("\nStealers (winner <- expected owner: count):")
        for k, v in summary["stealers"].items():
            print(f"  {k}: {v}")
    if summary["misses"]:
        print("\nMisses:")
        for r in summary["misses"]:
            print(f"  \"{r['prompt']}\" -> {r['got']} ({r['p_got']}), expected "
                  f"{'/'.join(r['expect'])} ({r['p_expect']})")
    if summary["low_margin"]:
        print(f"\nCorrect but thin (margin < {LOW_MARGIN}):")
        for r in summary["low_margin"]:
            print(f"  \"{r['prompt']}\" -> {r['got']} by {r['margin']} over "
                  f"{r['runner_up']} ({r['p_runner_up']})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["route", "check", "collisions"])
    ap.add_argument("request", nargs="?", help="route: the user request text")
    ap.add_argument("--root", action="append", type=Path, help="skills directory (repeatable)")
    ap.add_argument("--only", action="append", help="restrict the catalog to these skill names")
    ap.add_argument("--skill", action="append", help="collisions: probe only these skills")
    ap.add_argument("--cases", help="check: JSON list of {prompt, expect}")
    ap.add_argument("--from-routing-table", help="check: build cases from a routing-table.md")
    ap.add_argument("--model", help="model id (default: JEV_MODEL, including from --env-file, else jev-latest)")
    ap.add_argument("--env-file", help="load the API key from this .env (value never printed)")
    ap.add_argument("--limit", type=int, help="score at most N cases")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--fail-under", type=float, help="exit 1 if accuracy is below this (0-1)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be sent; no API calls")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    catalog = load_catalog(args.root or [DEFAULT_ROOT], args.only)
    criteria_chars = sum(len(n) + len(s["description"]) for n, s in catalog.items())

    if args.mode == "route":
        if not args.request:
            die("route needs the request text")
        if args.dry_run:
            print(json.dumps({"skills": len(catalog), "calls": 2,
                              "approx_input_tokens": (criteria_chars + len(args.request)) // 4 + 2000}))
            return 0
        # route is a pre-check another skill waits on: fail over to exit 4 fast.
        client = Client(args.model, args.env_file, retries=2, timeout=15)
        try:
            result = route(client, catalog, args.request)
        except ApiError as err:
            die(("jev unavailable: " if err.unavailable else "") + str(err), UNAVAILABLE if err.unavailable else 3)
        except (KeyError, TypeError, IndexError) as err:
            die(f"jev unavailable: unexpected response shape ({err!r})", UNAVAILABLE)
        result.update({"served_model": sorted(client.served), "cost": round(client.cost, 6)})
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            pick = result["winner"] or "none"
            print(f"winner: {pick}  ({result['reason']})")
            print(f"gate {result['gate']}  shortlist " +
                  ", ".join(f"{s['skill']} {s['p']}" for s in result["shortlist"]))
            if "fits" in result:
                print("fits " + ", ".join(f"{k} {v}" for k, v in result["fits"].items()))
            print(f"model {', '.join(result['served_model'])}  cost ${result['cost']}")
        return 0

    skipped = []
    if args.mode == "check":
        if args.cases:
            cases = load_cases(args.cases)
        elif args.from_routing_table:
            cases, skipped = cases_from_routing_table(args.from_routing_table, catalog)
        else:
            die("check needs --cases or --from-routing-table")
        unknown = sorted({e for c in cases for e in c["expect"]} - set(catalog))
        if unknown:
            die(f"cases expect skills not in the catalog: {', '.join(unknown)} "
                "(check ranks descriptions only; test no-skill requests with route)")
    else:
        if args.skill and set(args.skill) - set(catalog):
            die(f"--skill not in catalog: {', '.join(sorted(set(args.skill) - set(catalog)))}")
        cases = cases_from_triggers(catalog, args.skill)
    if args.limit:
        cases = cases[:args.limit]
    if not cases:
        die("no cases to score")

    if args.dry_run:
        print(json.dumps({"skills": len(catalog), "calls": len(cases),
                          "approx_input_tokens": len(cases) * (criteria_chars // 4 + 300),
                          "skipped_phrases_outside_catalog": len(skipped),
                          "sample": cases[:5]}, indent=2))
        return 0

    client = Client(args.model, args.env_file)
    try:
        results = score_cases(client, catalog, cases, args.concurrency)
    except ApiError as err:
        die(("jev unavailable: " if err.unavailable else "") + str(err), UNAVAILABLE if err.unavailable else 3)
    except (KeyError, TypeError, IndexError) as err:
        die(f"jev unavailable: unexpected response shape ({err!r})", UNAVAILABLE)
    summary = summarize(results)
    summary.update({"skills": len(catalog), "served_model": sorted(client.served),
                    "calls": client.calls, "cost": round(client.cost, 6),
                    "skipped_outside_catalog": skipped})
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_summary(summary, "check" if args.mode == "check" else "collisions")
        if skipped:
            print(f"\nSkipped {len(skipped)} routing-table phrases whose targets are outside this catalog.")
        print(f"\n{client.calls} calls, model {', '.join(summary['served_model'])}, cost ${summary['cost']}")
    if args.fail_under is not None and summary["accuracy"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
