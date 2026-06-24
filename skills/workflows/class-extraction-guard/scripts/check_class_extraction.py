#!/usr/bin/env python3
"""
class-extraction-guard — a source-level gate that catches utility-class soup:
the same long run of utility classes (`flex items-center gap-1.5 text-fg-muted
transition-colors hover:text-accent`) copy-pasted inline across many files
instead of extracted into a named class / component.

Why this exists: design-token-guard checks *which values* styling uses (tokens
vs hardcoded hex). It passes correctly-tokenized utilities by construction. But a
correctly-tokenized utility string repeated 9× inline is still a DRY/maintenance
problem — and it renders identically to an extracted version, so render-sanity
and ux-review (pixel gates) never see it either. It lives only in source, exactly
in the seam between the pixel gates and the value gate. This is that missing
*organization* check — the sibling to design-token-guard.

It is framework-agnostic (React/JSX, Vue, Svelte, Astro, plain HTML; and string
args to clsx / cn / classNames / cva / tv / twMerge). No third-party deps —
Python 3.8+ stdlib only.

Usage:
  python3 check_class_extraction.py [--root DIR] [--config PATH]
                                    [--staged] [--json] [--quiet]
                                    [--baseline PATH] [--write-baseline] [PATHS...]

Exit codes: 0 = clean (no error-severity findings), 1 = error-severity findings,
2 = usage/config error. (Mirrors design-token-guard so it drops into the same
orchestrator wave-gate snippet unchanged.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Defaults. Everything here is overridable via .class-guard.json at the root.
# The one default-on rule is "warning" (non-blocking) — utility-soup is a
# preference-y standard, so adopting the gate should never block a build on day
# one. Flip a rule to "error" (and scaffold it at the bootstrap wave) when you
# want it to hard-gate a greenfield project from commit #1.
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "scanExtensions": [
        ".tsx", ".ts", ".jsx", ".js", ".mjs", ".cjs",
        ".vue", ".svelte", ".astro", ".html",
    ],
    "ignoreDirs": [
        "node_modules", ".git", ".next", "dist", "build", "out",
        "coverage", ".turbo", ".vercel", "__pycache__", ".svelte-kit",
        ".cache", "storybook-static",
    ],
    # A class string must have at least this many utility tokens to count at all.
    "minUtilities": 4,
    # repeated-class-string fires when the same (order-normalized) string appears
    # in at least this many distinct call-sites.
    "minRepeats": 3,
    # long-class-string fires on a single string with at least this many tokens.
    "maxUtilities": 12,
    # Strings to never flag (exact, order-normalized match) — escape hatches.
    "allowlist": [],
    # Tokens that mark a string as already-abstracted (named/@apply classes). Used
    # by the opt-in abstraction-defeat rule. Regex, matched per token.
    "namedClassPattern": "",
    "rules": {
        "repeated-class-string": "warning",   # the strong signal: copy-paste soup
        "long-class-string": "off",           # opt-in: one-off mega-strings
        "abstraction-defeat": "off",          # opt-in: utilities glued onto a named class
    },
}

SEVERITY_RANK = {"off": 0, "warning": 1, "error": 2}

# ---------------------------------------------------------------------------
# Class-string extraction
# ---------------------------------------------------------------------------
# className="..." / className='...' / class="..." (Vue/Svelte/Astro/HTML)
_ATTR_RE = re.compile(
    r"""\b(?:className|class)\s*=\s*(?:\{?\s*)?(["'`])(?P<val>(?:(?!\1).)*?)\1""",
    re.DOTALL,
)
# string-literal args to class combinators: clsx("..."), cn('...'), cva("...")
_COMBINATOR_CALL_RE = re.compile(
    r"\b(?:clsx|cn|classNames|cx|cva|tv|twMerge|twJoin)\s*\((?P<args>[^)]*)\)",
    re.DOTALL,
)
_STR_LITERAL_RE = re.compile(r"""(["'`])(?P<val>(?:(?!\1).)*?)\1""", re.DOTALL)

# A token that looks like a CSS utility class (Tailwind-ish or kebab). Lets us
# ignore prose strings the combinator pass might grab.
_UTILITY_TOKEN_RE = re.compile(r"^[a-z!@\[]?[\w:\-./\[\]%#()&!]*$", re.IGNORECASE)


@dataclass
class ClassString:
    raw: str
    file: str
    line: int


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    string: str
    count: int
    occurrences: List[str]
    suggestion: str


def _looks_like_classes(value: str) -> bool:
    """A whitespace-split value where most tokens look like utility classes."""
    tokens = [t for t in value.split() if t]
    if not tokens:
        return False
    classy = sum(1 for t in tokens if _UTILITY_TOKEN_RE.match(t))
    return classy >= max(1, int(len(tokens) * 0.7))


def _has_interpolation(value: str) -> bool:
    # Skip dynamic strings we can't tokenize reliably.
    return "${" in value or "{{" in value


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def extract_class_strings(text: str, rel_path: str) -> List[ClassString]:
    out: List[ClassString] = []
    seen_spans: List[Tuple[int, int]] = []

    for m in _ATTR_RE.finditer(text):
        val = m.group("val")
        if _has_interpolation(val) or not _looks_like_classes(val):
            continue
        out.append(ClassString(val.strip(), rel_path, _line_of(text, m.start())))
        seen_spans.append((m.start(), m.end()))

    for call in _COMBINATOR_CALL_RE.finditer(text):
        args = call.group("args")
        base = call.start("args")
        for sm in _STR_LITERAL_RE.finditer(args):
            val = sm.group("val")
            if _has_interpolation(val) or not _looks_like_classes(val):
                continue
            # Only count multi-token literals here — single utilities in a cn()
            # call are normal composition, not soup.
            if len([t for t in val.split() if t]) < 2:
                continue
            out.append(ClassString(val.strip(), rel_path, _line_of(text, base + sm.start())))

    return out


def normalize(value: str) -> str:
    """Order-independent key: a sorted set of tokens. Two elements with the same
    utilities in a different order are the same extraction candidate."""
    return " ".join(sorted(set(t for t in value.split() if t)))


def token_count(value: str) -> int:
    return len(set(t for t in value.split() if t))


# ---------------------------------------------------------------------------
# Config + file discovery
# ---------------------------------------------------------------------------
def load_config(root: str, explicit: Optional[str]) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    path = explicit or os.path.join(root, ".class-guard.json")
    if os.path.isfile(path):
        try:
            user = json.load(open(path, encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"class-extraction-guard: bad config {path}: {e}", file=sys.stderr)
            sys.exit(2)
        for k, v in user.items():
            if k == "rules" and isinstance(v, dict):
                cfg["rules"].update(v)
            else:
                cfg[k] = v
    return cfg


def iter_files(root: str, cfg: dict, paths: List[str], staged: bool) -> List[str]:
    exts = tuple(cfg["scanExtensions"])
    ignore = set(cfg["ignoreDirs"])

    if staged:
        try:
            out = subprocess.run(
                ["git", "-C", root, "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True, text=True, check=True,
            ).stdout.split("\n")
        except (subprocess.CalledProcessError, FileNotFoundError):
            out = []
        return [os.path.join(root, p) for p in out if p.strip().endswith(exts)]

    targets = paths or [root]
    found: List[str] = []
    for t in targets:
        t = t if os.path.isabs(t) else os.path.join(root, t)
        if os.path.isfile(t):
            if t.endswith(exts):
                found.append(t)
            continue
        for dirpath, dirnames, filenames in os.walk(t):
            dirnames[:] = [d for d in dirnames if d not in ignore]
            for fn in filenames:
                if fn.endswith(exts):
                    found.append(os.path.join(dirpath, fn))
    return found


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def analyze(strings: List[ClassString], cfg: dict, baseline: set) -> List[Finding]:
    rules = cfg["rules"]
    allow = set(normalize(a) for a in cfg.get("allowlist", []))
    findings: List[Finding] = []

    # Group by normalized key for repeated-class-string.
    groups: Dict[str, List[ClassString]] = {}
    for cs in strings:
        if token_count(cs.raw) < cfg["minUtilities"]:
            continue
        key = normalize(cs.raw)
        if key in allow:
            continue
        groups.setdefault(key, []).append(cs)

    if rules.get("repeated-class-string", "off") != "off":
        sev = rules["repeated-class-string"]
        for key, occ in groups.items():
            if len(occ) < cfg["minRepeats"]:
                continue
            if key in baseline:
                continue
            occ_sorted = sorted(occ, key=lambda c: (c.file, c.line))
            first = occ_sorted[0]
            findings.append(Finding(
                rule="repeated-class-string", severity=sev,
                file=first.file, line=first.line,
                string=first.raw, count=len(occ),
                occurrences=[f"{c.file}:{c.line}" for c in occ_sorted],
                suggestion=(
                    f"this {token_count(first.raw)}-utility combo appears {len(occ)}× — "
                    f"extract it into a named class (@apply / a CSS component) or a shared "
                    f"component so the markup reads as intent, not soup"
                ),
            ))

    if rules.get("long-class-string", "off") != "off":
        sev = rules["long-class-string"]
        seen_long: set = set()
        for cs in strings:
            tc = token_count(cs.raw)
            if tc < cfg["maxUtilities"]:
                continue
            key = normalize(cs.raw)
            if key in allow or key in baseline or key in seen_long:
                continue
            seen_long.add(key)
            findings.append(Finding(
                rule="long-class-string", severity=sev,
                file=cs.file, line=cs.line, string=cs.raw, count=1,
                occurrences=[f"{cs.file}:{cs.line}"],
                suggestion=(
                    f"{tc} utilities on one element — even once, this is hard to scan; "
                    f"consider a named class or splitting the element"
                ),
            ))

    if rules.get("abstraction-defeat", "off") != "off" and cfg.get("namedClassPattern"):
        sev = rules["abstraction-defeat"]
        named = re.compile(cfg["namedClassPattern"])
        seen_def: set = set()
        for cs in strings:
            toks = [t for t in cs.raw.split() if t]
            has_named = any(named.match(t) for t in toks)
            utils = [t for t in toks if not named.match(t)]
            if not has_named or len(set(utils)) < cfg["minUtilities"]:
                continue
            key = normalize(cs.raw)
            if key in allow or key in baseline or key in seen_def:
                continue
            seen_def.add(key)
            findings.append(Finding(
                rule="abstraction-defeat", severity=sev,
                file=cs.file, line=cs.line, string=cs.raw, count=1,
                occurrences=[f"{cs.file}:{cs.line}"],
                suggestion=(
                    "a named/@apply class already carries this element's identity, yet "
                    f"{len(set(utils))} inline utilities are glued on top — fold them into "
                    "the named class or a variant instead of defeating the abstraction"
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Baseline (ratchet mode)
# ---------------------------------------------------------------------------
def load_baseline(path: Optional[str]) -> set:
    if not path or not os.path.isfile(path):
        return set()
    try:
        data = json.load(open(path, encoding="utf-8"))
        return set(data.get("normalized", []))
    except (json.JSONDecodeError, OSError):
        return set()


def write_baseline(path: str, strings: List[ClassString], cfg: dict) -> None:
    groups: Dict[str, int] = {}
    for cs in strings:
        if token_count(cs.raw) < cfg["minUtilities"]:
            continue
        groups[normalize(cs.raw)] = groups.get(normalize(cs.raw), 0) + 1
    keys = [k for k, n in groups.items() if n >= cfg["minRepeats"]]
    json.dump({"normalized": sorted(keys)}, open(path, "w", encoding="utf-8"), indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Catch utility-class soup (repeated inline class strings).")
    ap.add_argument("--root", default=".")
    ap.add_argument("--config")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--baseline")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    cfg = load_config(root, args.config)
    files = iter_files(root, cfg, args.paths, args.staged)

    all_strings: List[ClassString] = []
    for fp in files:
        try:
            text = open(fp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        rel = os.path.relpath(fp, root)
        all_strings.extend(extract_class_strings(text, rel))

    if args.write_baseline:
        bpath = args.baseline or os.path.join(root, ".class-guard-baseline.json")
        write_baseline(bpath, all_strings, cfg)
        print(f"class-extraction-guard: wrote baseline ({bpath})")
        return 0

    baseline = load_baseline(args.baseline or os.path.join(root, ".class-guard-baseline.json"))
    findings = analyze(all_strings, cfg, baseline)

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    summary = {"errors": errors, "warnings": warnings, "files_scanned": len(files)}

    if args.json:
        print(json.dumps({
            "summary": summary,
            "findings": [f.__dict__ for f in findings],
        }, indent=2))
    elif not args.quiet:
        if not findings:
            print(f"class-extraction-guard: clean ({len(files)} files scanned)")
        else:
            for f in sorted(findings, key=lambda x: (-x.count, x.file)):
                tag = "ERROR" if f.severity == "error" else "warn "
                print(f"[{tag}] {f.rule}  {f.file}:{f.line}  (×{f.count})")
                print(f"        {f.string}")
                print(f"        → {f.suggestion}")
                if f.count > 1:
                    print(f"        sites: {', '.join(f.occurrences[:8])}"
                          + (" …" if len(f.occurrences) > 8 else ""))
            print(f"\nclass-extraction-guard: {errors} error(s), {warnings} warning(s), "
                  f"{len(files)} files scanned")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
