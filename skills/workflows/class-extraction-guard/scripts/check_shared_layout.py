#!/usr/bin/env python3
"""Shared source-layout gate: literal semantic chrome, not rendered HTML output.

Reuse class-guard discovery/config. Exact source copies are strong signals, not
proof of runtime ownership; framework-specific dynamic composition needs review.
Exit 0 clean, 1 duplicated source chrome, 2 inspection/configuration blocked.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

from check_class_extraction import iter_files, load_config
from frontend_source import chrome_blocks, fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise ValueError("root is not a directory")
    config = load_config(root, args.config)
    policy = config["sharedLayout"]
    tags = policy["tags"]
    if not isinstance(tags, list) or not tags or any(t not in ("header", "nav", "footer") for t in tags):
        raise ValueError("sharedLayout.tags must select header/nav/footer")
    if type(policy["minRepeats"]) is not int or policy["minRepeats"] < 2:
        raise ValueError("sharedLayout.minRepeats must be at least two source files")
    allowed = set()
    for entry in policy["allowlist"]:
        if not isinstance(entry, dict) or not entry.get("fingerprint") or not entry.get("reason", "").strip():
            raise ValueError("shared-layout exception requires fingerprint and reason")
        allowed.add(entry["fingerprint"])
    groups = defaultdict(list)
    scanned = 0
    for path in iter_files(root, config, args.paths, False):
        if path.endswith(".css"):
            continue
        with open(path, encoding="utf-8", errors="strict") as source:
            text = source.read()
        scanned += 1
        rel = os.path.relpath(path, root)
        for tag, normalized, line in chrome_blocks(text, tags):
            # A bare semantic wrapper isn't shared chrome. Require actual markup
            # content so page-specific <header>{children}</header> is not blocked.
            if not re.search(r"<(?:a|button|img|ul|ol|span|div|p|h[1-6])\b", normalized, re.I):
                continue
            groups[(tag, fingerprint(normalized))].append((rel, line))
    findings = []
    for (tag, key), sites in sorted(groups.items()):
        if len({s[0] for s in sites}) < policy["minRepeats"] or key in allowed:
            continue
        findings.append({"rule": "copied-shared-chrome", "severity": "error", "tag": tag,
                         "fingerprint": key, "occurrences": ["%s:%d" % site for site in sites],
                         "suggestion": "one owning partial/component/include must supply shared %s; use an approved reasoned exception for intentional independent copies" % tag})
    result = {"ok": not findings, "summary": {"errors": len(findings), "files_scanned": scanned},
              "findings": findings}
    print(json.dumps(result, indent=2) if args.json else
          "shared-layout: %d duplicate group(s), %d source files scanned" % (len(findings), scanned))
    if not args.json:
        for finding in findings:
            print("%s: %s (fingerprint=%s)" % (finding["tag"], ", ".join(finding["occurrences"]), finding["fingerprint"]))
    return 1 if findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        if "--json" in sys.argv:
            print(json.dumps({"ok": False, "status": "blocked", "error": str(exc)}))
        print("shared-layout: inspection blocked: %s" % exc, file=sys.stderr)
        sys.exit(2)
