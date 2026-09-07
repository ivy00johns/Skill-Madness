#!/usr/bin/env python3
"""check_prose_slop.py - deterministic lexical gate for AI-slop prose tells.

Scans prose files (Markdown by default) for the mechanical subset of AI-writing
tells: em/en dashes, banned vocabulary, banned phrases, negative parallelism,
and sycophantic filler. Judgment-level tells (rule-of-three rhythm, vague
attribution, inflated symbolism) are out of scope here - the SKILL.md judgment
pass owns those. This script is the layer a pre-commit hook or CI step can run.

Usage:
  check_prose_slop.py --root .                 # scan the tree
  check_prose_slop.py docs/post.md             # scan specific paths
  check_prose_slop.py --staged                 # only git-staged files
  git log -1 --format=%B | check_prose_slop.py --stdin   # commit msg / PR body
  check_prose_slop.py --root . --json          # machine-readable, for gates

Exit code 1 when error-severity findings exist, else 0. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG_FILENAME = ".prose-guard.json"

DEFAULT_EXTENSIONS = [".md", ".mdx", ".markdown", ".txt", ".rst"]
DEFAULT_SKIP_PATHS = [
    "node_modules", ".git", "dist", "build", "out", "vendor",
    "CHANGELOG.md", "LICENSE", "LICENSE.md",
]

# Severity per rule. "error" fails the gate, "warn" reports, "off" disables.
DEFAULT_RULES = {
    "no-em-dash": "error",
    "banned-phrases": "error",
    "sycophancy": "error",
    "banned-vocabulary": "warn",
    "negative-parallelism": "warn",
}

# word -> replacement hint. Word-boundary, case-insensitive.
BANNED_VOCABULARY = {
    "delve": "dig into / examine",
    "delves": "digs into / examines",
    "leverage": "use",
    "leverages": "uses",
    "leveraging": "using",
    "utilize": "use",
    "utilizes": "uses",
    "utilizing": "using",
    "seamless": "smooth (or cut it)",
    "seamlessly": "smoothly (or cut it)",
    "tapestry": "cut it - name the actual things",
    "unleash": "release / enable",
    "harness": "use",
    "harnessing": "using",
    "elevate": "improve / raise",
    "elevates": "improves / raises",
    "landscape": "field / space (or name the actual market)",
    "game-changer": "state the actual change",
    "cutting-edge": "new (or name the technique)",
    "transformative": "show the change instead",
    "groundbreaking": "new (or show what broke ground)",
    "paradigm": "model / approach",
    "synergy": "cut it - say who gains what",
    "empower": "let / enable",
    "empowers": "lets / enables",
    "empowering": "letting / enabling",
    "streamline": "simplify",
    "streamlines": "simplifies",
    "unprecedented": "new / first (only if literally true)",
    "testament": "evidence / sign",
    "pivotal": "key",
    "foster": "encourage / build",
    "fosters": "encourages / builds",
    "realm": "area",
    "embark": "start",
    "boasts": "has",
    "furthermore": "also (or just start the sentence)",
    "moreover": "also (or just start the sentence)",
}

# name -> (compiled regex, hint). Case-insensitive.
BANNED_PHRASES = [
    ("throat-clearing-opener",
     r"in today'?s (?:fast-paced|rapidly|ever-|digital|modern|dynamic|competitive)",
     "delete the opener; start with the actual point"),
    ("not-only-but-also",
     r"\bnot only\b.{0,80}\bbut(?: also)?\b",
     "make one direct claim instead of the paired construction"),
    ("worth-noting",
     r"\bit(?: is|'s) worth noting\b",
     "if it's worth noting, just note it"),
    ("testament-to",
     r"\ba testament to\b",
     "state the evidence directly"),
    ("look-no-further",
     r"\blook no further\b",
     "delete; recommend the thing directly"),
    ("lets-dive-in",
     r"\blet'?s dive in\b",
     "delete; start with the content"),
    ("ever-evolving",
     r"\bever-(?:evolving|changing|growing)\b",
     "name what actually changed"),
]

SYCOPHANCY_PHRASES = [
    ("great-question", r"\bgreat question\b"),
    ("excellent-point", r"\bexcellent (?:question|point)\b"),
    ("absolutely-right", r"\byou'?re absolutely right\b"),
    ("hope-this-helps", r"\bi hope this helps\b"),
    ("happy-to-help", r"\b(?:i'?m )?happy to help\b"),
]

NEGATIVE_PARALLELISM = [
    ("isnt-just",
     r"(?:\b(?:is|are|was|were)n'?t|\b(?:is|are|was|were) not|'s not|'re not)"
     r" (?:just|only|merely|simply)\b",
     "make the positive claim directly; drop the setup"),
]

EM_DASH_RE = re.compile(r"[—–]")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")
URL_RE = re.compile(r"https?://\S+")
HTML_COMMENT_LINE_RE = re.compile(r"<!--.*?-->")


def blank_out(match: re.Match) -> str:
    return " " * (match.end() - match.start())


class Finding:
    def __init__(self, rule, severity, path, line, col, snippet, hint):
        self.rule = rule
        self.severity = severity
        self.path = path
        self.line = line
        self.col = col
        self.snippet = snippet
        self.hint = hint

    def as_dict(self):
        return {
            "rule": self.rule, "severity": self.severity,
            "file": str(self.path), "line": self.line, "col": self.col,
            "snippet": self.snippet, "hint": self.hint,
        }


def load_config(root: Path, explicit: str | None) -> dict:
    path = Path(explicit) if explicit else root / CONFIG_FILENAME
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"warning: could not read config {path}: {exc}", file=sys.stderr)
    return {}


def build_ruleset(config: dict):
    rules = dict(DEFAULT_RULES)
    rules.update(config.get("rules", {}))

    vocab = dict(BANNED_VOCABULARY)
    for word in config.get("extraVocabulary", []):
        vocab.setdefault(word.lower(), "rewrite in plain language")
    for word in config.get("allowVocabulary", []):
        vocab.pop(word.lower(), None)
    vocab_re = None
    if vocab:
        alt = "|".join(re.escape(w) for w in sorted(vocab, key=len, reverse=True))
        vocab_re = re.compile(rf"\b(?:{alt})\b", re.IGNORECASE)

    phrases = [(n, re.compile(p, re.IGNORECASE), h) for n, p, h in BANNED_PHRASES]
    for entry in config.get("extraPhrases", []):
        try:
            phrases.append((entry.get("name", "custom-phrase"),
                            re.compile(entry["pattern"], re.IGNORECASE),
                            entry.get("hint", "rewrite in plain language")))
        except (re.error, KeyError) as exc:
            print(f"warning: bad extraPhrases entry {entry}: {exc}", file=sys.stderr)

    syco = [(n, re.compile(p, re.IGNORECASE)) for n, p in SYCOPHANCY_PHRASES]
    negp = [(n, re.compile(p, re.IGNORECASE), h) for n, p, h in NEGATIVE_PARALLELISM]
    return rules, vocab, vocab_re, phrases, syco, negp


def iter_prose_lines(text: str, config: dict):
    """Yield (lineno, scannable_line). Skips fenced code, frontmatter,
    blockquotes (quoted content is exempt by default), and blanks out
    inline code, link targets, URLs, and HTML comments."""
    exempt_quotes = config.get("exemptBlockquotes", True)
    scan_frontmatter = config.get("scanFrontmatter", False)
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    in_frontmatter = False
    for idx, raw in enumerate(lines, start=1):
        stripped = raw.lstrip()
        if idx == 1 and raw.strip() == "---" and not scan_frontmatter:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if raw.strip() in ("---", "..."):
                in_frontmatter = False
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        if exempt_quotes and stripped.startswith(">"):
            continue
        line = INLINE_CODE_RE.sub(blank_out, raw)
        line = LINK_TARGET_RE.sub(blank_out, line)
        line = URL_RE.sub(blank_out, line)
        line = HTML_COMMENT_LINE_RE.sub(blank_out, line)
        yield idx, line


def scan_text(text: str, path, rules, vocab, vocab_re, phrases, syco, negp, config):
    findings = []

    def add(rule, line, col, snippet, hint):
        sev = rules.get(rule, "off")
        if sev != "off":
            findings.append(Finding(rule, sev, path, line, col, snippet.strip(), hint))

    for lineno, line in iter_prose_lines(text, config):
        for m in EM_DASH_RE.finditer(line):
            add("no-em-dash", lineno, m.start() + 1, line,
                "replace with ' - ', a comma, or parentheses")
        if vocab_re:
            for m in vocab_re.finditer(line):
                word = m.group(0).lower()
                add("banned-vocabulary", lineno, m.start() + 1, line,
                    f"'{m.group(0)}' is an AI-vocabulary tell; try: {vocab.get(word, 'plain language')}")
        for name, rx, hint in phrases:
            for m in rx.finditer(line):
                add("banned-phrases", lineno, m.start() + 1, line, f"{name}: {hint}")
        for name, rx in syco:
            for m in rx.finditer(line):
                add("sycophancy", lineno, m.start() + 1, line,
                    f"{name}: delete the filler; answer directly")
        for name, rx, hint in negp:
            for m in rx.finditer(line):
                add("negative-parallelism", lineno, m.start() + 1, line, f"{name}: {hint}")
    return findings


def collect_files(root: Path, paths, staged: bool, config: dict):
    extensions = config.get("extensions", DEFAULT_EXTENSIONS)
    skip = config.get("skipPaths", DEFAULT_SKIP_PATHS)

    def skipped(p: Path) -> bool:
        parts = set(p.parts)
        return any(s in parts or p.name == s for s in skip)

    if staged:
        try:
            out = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                capture_output=True, text=True, cwd=root, check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"error: --staged requires git: {exc}", file=sys.stderr)
            sys.exit(2)
        candidates = [root / line for line in out.splitlines() if line.strip()]
    elif paths:
        candidates = []
        for p in paths:
            pp = Path(p)
            candidates.extend(pp.rglob("*") if pp.is_dir() else [pp])
    else:
        candidates = list(root.rglob("*"))

    return sorted(
        p for p in candidates
        if p.is_file() and p.suffix.lower() in extensions and not skipped(p.relative_to(root) if p.is_absolute() and root in p.parents else p)
    )


def render_report(findings):
    by_rule = {}
    for f in findings:
        by_rule.setdefault((f.rule, f.severity), []).append(f)
    for (rule, sev), items in sorted(by_rule.items()):
        print(f"{rule} ({sev}) - {len(items)}")
        for f in items:
            print(f"  {f.path}:{f.line}:{f.col}")
            print(f"    {f.snippet[:120]}")
            print(f"    -> {f.hint}")
    errors = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    print(f"\n{errors} error(s), {warns} warning(s)"
          if findings else "clean: no slop tells found")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="files/dirs to scan (default: --root tree)")
    ap.add_argument("--root", default=".", help="project root (config + default scan)")
    ap.add_argument("--config", help="explicit config path")
    ap.add_argument("--staged", action="store_true", help="only git-staged files")
    ap.add_argument("--stdin", action="store_true", help="scan text from stdin (commit msg, PR body)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    config = load_config(root, args.config)
    ruleset = build_ruleset(config)
    rules, vocab, vocab_re, phrases, syco, negp = ruleset

    findings = []
    if args.stdin:
        findings = scan_text(sys.stdin.read(), "<stdin>", rules, vocab, vocab_re,
                             phrases, syco, negp, config)
    else:
        for path in collect_files(root, args.paths, args.staged, config):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"warning: could not read {path}: {exc}", file=sys.stderr)
                continue
            findings.extend(scan_text(text, path, rules, vocab, vocab_re,
                                      phrases, syco, negp, config))

    if args.json:
        errors = sum(1 for f in findings if f.severity == "error")
        warns = sum(1 for f in findings if f.severity == "warn")
        print(json.dumps({
            "ok": errors == 0,
            "summary": {"errors": errors, "warnings": warns, "total": len(findings)},
            "findings": [f.as_dict() for f in findings],
        }, indent=2))
        return 1 if errors else 0

    errors = render_report(findings)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
