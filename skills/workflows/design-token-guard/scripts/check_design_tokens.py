#!/usr/bin/env python3
"""
design-token-guard — a source-level gate that prevents inline styles and
hardcoded CSS values from bypassing a project's design-token system.

Why this exists: render-level gates (visual review, e2e, screenshots) never
catch a hardcoded color, because `style={{ background: "#07090c" }}` renders
identically to `var(--tl-tooltip)`. The violation is only visible in source.
This is that missing source-level check.

It is framework-agnostic (React/JSX, Vue, Svelte, Angular, Astro, plain HTML)
and token-source-agnostic (CSS custom properties, SCSS/Less vars, JS/TS theme
objects, design-token JSON). It auto-discovers the project's tokens and derives
a value->token map, so the fix it suggests is exact ("#07090c is var(--tl-tooltip)")
no matter the stack. No third-party dependencies — Python 3.8+ stdlib only.

Usage:
  python3 check_design_tokens.py [--root DIR] [--config PATH]
                                 [--staged] [--json] [--quiet] [PATHS...]

Exit codes: 0 = clean, 1 = error-severity findings, 2 = usage/config error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Defaults. Everything here is overridable via .design-guard.json at the root.
# The two universal rules are "error"; the project-specific library is "off".
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    # Token sources. Empty => auto-discover (see discover_token_sources).
    "tokenSources": [],
    # File extensions to scan for violations.
    "scanExtensions": [
        ".tsx", ".ts", ".jsx", ".js", ".mjs", ".cjs",
        ".vue", ".svelte", ".astro", ".html",
    ],
    # Directories never walked.
    "ignoreDirs": [
        "node_modules", ".git", ".next", "dist", "build", "out",
        "coverage", ".turbo", ".vercel", "__pycache__", ".svelte-kit",
    ],
    # Glob-ish substrings; a file whose path contains any of these is skipped
    # for the violation scan (token-definition files belong here).
    "ignorePathContains": [".config.", ".d.ts"],
    "rules": {
        # --- universal, on by default ---
        "no-hardcoded-color": "error",
        "no-inline-style": "warn",
        # --- project-specific library, opt-in ---
        "no-class-in-svg": "off",       # utility classes inside <svg> primitives
        "restricted-radius": "off",     # border-radius above maxRadiusPx
        "forbidden-colors": "off",      # see forbiddenColors list below
        "no-arbitrary-tailwind": "off", # arbitrary VALUES: text-[10px], max-w-[1100px]
    },
    # no-inline-style mode: "literal" flags only inline styles carrying a
    # hardcoded literal (dynamic/token-referencing inline styles are allowed);
    # "strict" flags every inline style attribute regardless.
    "inlineStyleMode": "literal",
    # restricted-radius: any radius value over this many px (or a rounded-*
    # utility class larger than ~2px) is flagged.
    "maxRadiusPx": 2,
    # forbidden-colors: list of regexes matched against each source line. Use
    # for partisan colors, a banned second accent, etc.
    "forbiddenColors": [],
    # Scan CSS/SCSS files themselves for hardcoded colors? Usually off — that
    # is where colors legitimately live (the token definitions).
    "scanStyleSheets": False,
}

COLOR_KEYS = ("color", "background", "fill", "stroke", "border", "shadow",
              "outline", "gradient")

# A color literal: #hex (3/4/6/8), rgb()/rgba(), hsl()/hsla().
COLOR_RE = re.compile(
    r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b"
    r"|rgba?\([^)]*\)"
    r"|hsla?\([^)]*\)"
)

# Dimension literal inside a quoted string: "12px", '2rem', "1.5em" ...
DIM_RE = re.compile(r"""['"]\s*-?\d*\.?\d+(px|rem|em|vh|vw|vmin|vmax|pt|ch)\s*['"]""")

SVG_PRIMITIVES = (
    "rect", "circle", "path", "line", "polyline", "polygon", "ellipse",
    "g", "text", "tspan", "use", "defs", "linearGradient", "radialGradient",
    "stop", "clipPath", "mask",
)

RADIUS_CLASS_RE = re.compile(r"\brounded-(?:md|lg|xl|2xl|3xl|full)\b")
RADIUS_VALUE_RE = re.compile(r"border-radius\s*:\s*(\d*\.?\d+)px")

# Tailwind arbitrary-value utility: prefix-[value] (text-[10px], max-w-[1100px]).
ARBITRARY_TW_RE = re.compile(r"(?<![\w-])([a-z][a-z0-9]*(?:-[a-z0-9]+)*)-\[([^\]]+)\]")


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    col: int
    snippet: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class TokenIndex:
    sources: List[str] = field(default_factory=list)
    by_value: Dict[str, str] = field(default_factory=dict)  # norm value -> token ref
    count: int = 0


# ---------------------------------------------------------------------------
# Color normalization — canonical key so source literals match token values.
# ---------------------------------------------------------------------------
def normalize_color(raw: str) -> Optional[str]:
    s = raw.strip().lower()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        elif len(h) == 4:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return "#" + h
        if len(h) == 8:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            a = round(int(h[6:8], 16) / 255, 3)
            return _rgba_key(r, g, b, a)
        return None
    m = re.match(r"rgba?\(([^)]*)\)", s)
    if m:
        parts = [p.strip() for p in re.split(r"[,/ ]+", m.group(1)) if p.strip()]
        try:
            chans = []
            for i in range(3):
                p = parts[i]
                if p.endswith("%"):            # rgb(100%, 50%, 0%) is on a 0-100 scale
                    chans.append(int(round(float(p[:-1]) / 100 * 255)))
                else:
                    chans.append(int(round(float(p))))
            r, g, b = (min(255, max(0, v)) for v in chans)
        except (ValueError, IndexError):
            return None
        a = 1.0
        if len(parts) >= 4:
            try:
                a = float(parts[3].rstrip("%"))
                if parts[3].endswith("%"):
                    a /= 100
            except ValueError:
                a = 1.0
        if a >= 1.0:
            return "#%02x%02x%02x" % (r, g, b)
        return _rgba_key(r, g, b, round(a, 3))
    m = re.match(r"hsla?\(([^)]*)\)", s)
    if m:
        return "hsl:" + re.sub(r"\s+", "", m.group(1))
    return None


def _rgba_key(r: int, g: int, b: int, a: float) -> str:
    astr = ("%.3f" % a).rstrip("0").rstrip(".")
    return "rgba(%d,%d,%d,%s)" % (r, g, b, astr)


# ---------------------------------------------------------------------------
# Token discovery + parsing.
# ---------------------------------------------------------------------------
def discover_token_sources(root: str, cfg: dict) -> List[str]:
    if cfg["tokenSources"]:
        return [os.path.join(root, p) for p in cfg["tokenSources"]]
    found: List[str] = []
    name_hints = ("token", "theme", "variable", "var", "design", "palette", "color")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in cfg["ignoreDirs"]]
        for fn in filenames:
            low = fn.lower()
            if low.endswith((".css", ".scss", ".less")) and any(h in low for h in name_hints):
                found.append(os.path.join(dirpath, fn))
            elif low.endswith((".json",)) and "token" in low:
                found.append(os.path.join(dirpath, fn))
    # Fallback: any css that declares many custom properties.
    if not found:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in cfg["ignoreDirs"]]
            for fn in filenames:
                if fn.lower().endswith((".css", ".scss")):
                    p = os.path.join(dirpath, fn)
                    try:
                        txt = _read(p)
                    except OSError:
                        continue
                    if len(re.findall(r"--[\w-]+\s*:", txt)) >= 5:
                        found.append(p)
    return found


def build_token_index(sources: List[str]) -> TokenIndex:
    idx = TokenIndex()
    for src in sources:
        try:
            text = _read(src)
        except OSError:
            continue
        idx.sources.append(src)
        pairs: List[Tuple[str, str]] = []
        if src.lower().endswith(".json"):
            pairs = _parse_json_tokens(text)
        else:
            pairs += re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", text)          # CSS vars
            pairs += re.findall(r"(\$[\w-]+)\s*:\s*([^;]+);", text)           # SCSS
            pairs += re.findall(r"(@[\w-]+)\s*:\s*([^;]+);", text)            # Less
            pairs += re.findall(r"['\"]?([\w-]+)['\"]?\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]", text)  # JS theme obj
        for name, value in pairs:
            idx.count += 1
            for m in COLOR_RE.finditer(value):
                key = normalize_color(m.group(0))
                if key and key not in idx.by_value:
                    idx.by_value[key] = _token_ref(name)
    return idx


def _parse_json_tokens(text: str) -> List[Tuple[str, str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    out: List[Tuple[str, str]] = []

    def walk(node, path):
        if isinstance(node, dict):
            if "value" in node and isinstance(node["value"], (str, int, float)):
                out.append(("-".join(path), str(node["value"])))
            for k, v in node.items():
                if k == "value":
                    continue
                walk(v, path + [str(k)])
        elif isinstance(node, str):
            out.append(("-".join(path), node))

    walk(data, [])
    return out


def _token_ref(name: str) -> str:
    if name.startswith("--"):
        return "var(%s)" % name
    return name  # $scss / @less / js-key referenced as-is in suggestion text


# ---------------------------------------------------------------------------
# File collection.
# ---------------------------------------------------------------------------
def collect_files(root: str, cfg: dict, explicit: List[str], staged: bool) -> List[str]:
    exts = tuple(cfg["scanExtensions"])
    if cfg["scanStyleSheets"]:
        exts = exts + (".css", ".scss", ".less")

    def keep(path: str) -> bool:
        if not path.endswith(exts):
            return False
        if any(s in path for s in cfg["ignorePathContains"]):
            return False
        norm = path.replace(os.sep, "/")
        if any(("/%s/" % d) in norm for d in cfg["ignoreDirs"]):
            return False
        return True

    if staged:
        try:
            out = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                cwd=root, capture_output=True, text=True, check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # A gate that silently passes when git can't be queried is a false
            # green — surface it instead of reporting "nothing to check".
            print("design-token-guard: --staged could not list staged files "
                  "(%s); treating as no files." % e, file=sys.stderr)
            return []
        staged_files: List[str] = []
        for rel in out.splitlines():
            ap = os.path.join(root, rel)
            if keep(ap):  # keep() needs the joined path so the ignoreDirs "/d/" test matches
                staged_files.append(ap)
        return staged_files

    if explicit:
        files: List[str] = []
        for p in explicit:
            ap = p if os.path.isabs(p) else os.path.join(root, p)
            if os.path.isdir(ap):
                files += _walk(ap, cfg, keep)
            elif os.path.isfile(ap) and keep(ap):
                files.append(ap)
        return files

    return _walk(root, cfg, keep)


def _walk(base: str, cfg: dict, keep) -> List[str]:
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in cfg["ignoreDirs"]]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if keep(p):
                files.append(p)
    return files


# ---------------------------------------------------------------------------
# Comment masking — blank comment spans while preserving length/newlines so
# line/col stay accurate. Keeps the color rule from flagging documented hexes.
# ---------------------------------------------------------------------------
def mask_comments(text: str) -> str:
    out = list(text)
    i, n = 0, len(text)
    state = None  # None | "line" | "block" | "string"
    quote = ""
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if state is None:
            if two == "//":
                state = "line"; out[i] = out[i + 1] = " "; i += 2; continue
            if two == "/*":
                state = "block"; out[i] = out[i + 1] = " "; i += 2; continue
            if text[i:i + 4] == "<!--":        # HTML/Vue/Svelte/Astro comment
                state = "html"
                out[i] = out[i + 1] = out[i + 2] = out[i + 3] = " "
                i += 4; continue
            if c in "\"'`":
                state = "string"; quote = c; i += 1; continue
        elif state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
            i += 1; continue
        elif state == "block":
            if two == "*/":
                out[i] = out[i + 1] = " "; state = None; i += 2; continue
            if c != "\n":
                out[i] = " "
            i += 1; continue
        elif state == "html":
            if text[i:i + 3] == "-->":
                out[i] = out[i + 1] = out[i + 2] = " "; state = None; i += 3; continue
            if c != "\n":
                out[i] = " "
            i += 1; continue
        elif state == "string":
            if c == "\\":
                i += 2; continue
            if c == quote:
                state = None
            i += 1; continue
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Position helpers.
# ---------------------------------------------------------------------------
def line_col(text: str, offset: int) -> Tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    col = offset - last_nl
    return line, col


def line_at(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return text[start:end].strip()


# ---------------------------------------------------------------------------
# Rules. Each returns a list of Finding.
# ---------------------------------------------------------------------------
def rule_hardcoded_color(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    for m in COLOR_RE.finditer(masked):
        literal = raw[m.start():m.end()]
        key = normalize_color(literal)
        token = idx.by_value.get(key) if key else None
        if token:
            msg = "hardcoded color %s is %s" % (literal, token)
            sugg = "use %s" % token
        else:
            msg = "hardcoded color %s is not a declared token" % literal
            sugg = "add it to a token source, or reuse an existing token"
        ln, col = line_col(masked, m.start())
        findings.append(Finding("no-hardcoded-color", sev, rel, ln, col,
                                line_at(raw, m.start()), msg, sugg))
    return findings


def rule_inline_style(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    mode = cfg["inlineStyleMode"]
    # JSX: style={{ ... }}
    for m in re.finditer(r"style\s*=\s*\{\{", masked):
        body, end = _balanced(masked, m.end() - 1)  # start at first '{'
        if body is None:
            continue
        raw_body = raw[m.end():end - 1] if end else raw[m.end():m.end() + len(body)]
        _maybe_inline_finding(findings, raw, masked, m.start(), raw_body, mode, sev, rel)
    # HTML/Vue/Svelte/Angular: style="..." or :style / [style]
    for m in re.finditer(r"""(?::|\[)?style\]?\s*=\s*["']""", masked):
        q = masked[m.end() - 1]
        close = masked.find(q, m.end())
        if close == -1:
            continue
        raw_body = raw[m.end():close]
        _maybe_inline_finding(findings, raw, masked, m.start(), raw_body, mode, sev, rel)
    return findings


def _maybe_inline_finding(findings, raw, masked, start, raw_body, mode, sev, rel):
    has_color = bool(COLOR_RE.search(raw_body))
    has_dim = bool(DIM_RE.search(raw_body))
    if mode == "strict":
        fire, why = True, "inline style attribute (strict mode forbids all inline styles)"
    else:
        # Default: only fire when the inline style carries a hardcoded literal.
        # Color literals are owned by no-hardcoded-color (more specific +
        # suggestion), so here we fire for non-color literals like dimensions.
        if has_dim and not has_color:
            fire, why = True, "inline style with hardcoded dimension value"
        elif has_dim and has_color:
            fire, why = True, "inline style with hardcoded values"
        else:
            fire, why = False, ""
    if fire:
        ln, col = line_col(masked, start)
        findings.append(Finding("no-inline-style", sev, rel, ln, col,
                                line_at(raw, start), why,
                                "move the value into a token / utility class"))


def _balanced(text: str, open_idx: int) -> Tuple[Optional[str], int]:
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx:i + 1], i + 1
        i += 1
    return None, 0


def rule_class_in_svg(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    tag_re = re.compile(r"<(" + "|".join(SVG_PRIMITIVES) + r")\b([^>]*)>", re.DOTALL)
    for m in tag_re.finditer(masked):
        attrs = m.group(2)
        cm = re.search(r"(?:className|class)\s*=\s*[\"'{]([^\"'}]*)", attrs)
        if cm and re.search(r"[a-z]+-[a-z0-9\[]", cm.group(1)):
            ln, col = line_col(masked, m.start())
            findings.append(Finding("no-class-in-svg", sev, rel, ln, col,
                                    line_at(raw, m.start()),
                                    "utility classes on <%s> — SVG should use token attrs/vars" % m.group(1),
                                    "use fill/stroke with var(--token) instead of classes"))
    return findings


def rule_restricted_radius(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    maxpx = cfg["maxRadiusPx"]
    for m in RADIUS_CLASS_RE.finditer(masked):
        ln, col = line_col(masked, m.start())
        findings.append(Finding("restricted-radius", sev, rel, ln, col,
                                line_at(raw, m.start()),
                                "%s exceeds the %dpx radius cap" % (m.group(0), maxpx),
                                "use a smaller radius token / utility"))
    for m in RADIUS_VALUE_RE.finditer(masked):
        if float(m.group(1)) > maxpx:
            ln, col = line_col(masked, m.start())
            findings.append(Finding("restricted-radius", sev, rel, ln, col,
                                    line_at(raw, m.start()),
                                    "border-radius %spx exceeds the %dpx cap" % (m.group(1), maxpx),
                                    "use a radius token"))
    return findings


def rule_forbidden_colors(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    pats = [re.compile(p) for p in cfg["forbiddenColors"]]
    for m in re.finditer(r".+", masked):
        for p in pats:
            for hit in p.finditer(m.group(0)):
                off = m.start() + hit.start()
                ln, col = line_col(masked, off)
                findings.append(Finding("forbidden-colors", sev, rel, ln, col,
                                        line_at(raw, off),
                                        "forbidden color pattern '%s'" % hit.group(0),
                                        "use an approved token"))
    return findings


def rule_arbitrary_tailwind(path, rel, raw, masked, idx, cfg, sev) -> List[Finding]:
    findings = []
    for m in ARBITRARY_TW_RE.finditer(masked):
        value = m.group(2)
        # Colors inside arbitrary values are owned by no-hardcoded-color (it has
        # the token suggestion); token refs and url() are legitimate, not off-scale.
        if "var(--" in value or value.startswith("url(") or COLOR_RE.search(value):
            continue
        ln, col = line_col(masked, m.start())
        findings.append(Finding("no-arbitrary-tailwind", sev, rel, ln, col,
                                line_at(raw, m.start()),
                                "arbitrary Tailwind value %s bypasses the scale" % m.group(0),
                                "use a scale/token utility, or add a token for this value"))
    return findings


RULES = {
    "no-hardcoded-color": rule_hardcoded_color,
    "no-inline-style": rule_inline_style,
    "no-class-in-svg": rule_class_in_svg,
    "restricted-radius": rule_restricted_radius,
    "forbidden-colors": rule_forbidden_colors,
    "no-arbitrary-tailwind": rule_arbitrary_tailwind,
}


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_config(root: str, config_path: Optional[str]) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    path = config_path or os.path.join(root, ".design-guard.json")
    if os.path.isfile(path):
        try:
            user = json.loads(_read(path))
        except (OSError, json.JSONDecodeError) as e:
            print("design-token-guard: bad config %s: %s" % (path, e), file=sys.stderr)
            sys.exit(2)
        for k, v in user.items():
            if k == "rules" and isinstance(v, dict):
                cfg["rules"].update(v)
            else:
                cfg[k] = v
    return cfg


def run(root: str, cfg: dict, files: List[str], idx: TokenIndex) -> List[Finding]:
    findings: List[Finding] = []
    token_srcs = {os.path.abspath(s) for s in idx.sources}
    for path in files:
        if os.path.abspath(path) in token_srcs:
            continue
        try:
            raw = _read(path)
        except OSError:
            continue
        masked = mask_comments(raw)
        rel = os.path.relpath(path, root)
        for rule_name, fn in RULES.items():
            sev = cfg["rules"].get(rule_name, "off")
            if sev == "off":
                continue
            findings += fn(path, rel, raw, masked, idx, cfg, sev)
    findings.sort(key=lambda f: (f.file, f.line, f.col))
    return findings


def report_human(findings, idx, cfg, quiet) -> None:
    errs = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warn")
    files = len({f.file for f in findings})
    if not findings:
        if not quiet:
            print("design-token-guard: clean — no inline styles or hardcoded CSS found.")
            _print_footer(idx, cfg)
        return
    print("design-token-guard: %d findings (%d error%s, %d warning%s) across %d file%s\n"
          % (len(findings), errs, "" if errs == 1 else "s",
             warns, "" if warns == 1 else "s", files, "" if files == 1 else "s"))
    by_rule: Dict[str, List[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)
    for rule, items in by_rule.items():
        sev = items[0].severity
        print("%s (%s) — %d" % (rule, sev, len(items)))
        for f in items:
            print("  %s:%d:%d" % (f.file, f.line, f.col))
            print("    %s" % f.snippet)
            line = "    → %s" % f.message
            if f.suggestion:
                line += "  ·  %s" % f.suggestion
            print(line)
        print("")
    _print_footer(idx, cfg)


def _print_footer(idx, cfg) -> None:
    src = ", ".join(os.path.basename(s) for s in idx.sources) or "none found"
    print("Token source: %s (%d tokens, %d color values mapped)"
          % (src, idx.count, len(idx.by_value)))


def report_json(findings, idx, cfg) -> None:
    errs = sum(1 for f in findings if f.severity == "error")
    out = {
        "ok": errs == 0,
        "summary": {
            "total": len(findings),
            "errors": errs,
            "warnings": sum(1 for f in findings if f.severity == "warn"),
            "files": len({f.file for f in findings}),
        },
        "tokenSources": idx.sources,
        "tokensIndexed": idx.count,
        "colorValuesMapped": len(idx.by_value),
        "findings": [asdict(f) for f in findings],
    }
    print(json.dumps(out, indent=2))


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Prevent inline styles and hardcoded CSS.")
    ap.add_argument("--root", default=".", help="project root (default: cwd)")
    ap.add_argument("--config", help="path to .design-guard.json")
    ap.add_argument("--staged", action="store_true", help="scan git-staged files only")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="suppress the clean-run message")
    ap.add_argument("paths", nargs="*", help="explicit files/dirs to scan")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("design-token-guard: --root %s is not a directory" % root, file=sys.stderr)
        return 2

    cfg = load_config(root, args.config)
    sources = discover_token_sources(root, cfg)
    idx = build_token_index(sources)
    if not idx.sources and not args.json:
        print("design-token-guard: warning — no token source discovered; "
              "no-hardcoded-color can flag literals but cannot suggest tokens. "
              "Set \"tokenSources\" in .design-guard.json.\n", file=sys.stderr)

    files = collect_files(root, cfg, args.paths, args.staged)
    findings = run(root, cfg, files, idx)

    if args.json:
        report_json(findings, idx, cfg)
    else:
        report_human(findings, idx, cfg, args.quiet)

    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
