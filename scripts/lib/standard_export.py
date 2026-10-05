#!/usr/bin/env python3
"""Agent Skills export adapter; canonical Claude/PSFS sources are never rewritten."""
import argparse
import json
from pathlib import Path
import re
import yaml

NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
CORE = ("name", "description", "license", "compatibility")


def load(content):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.DOTALL)
    if not match:
        raise ValueError("Missing frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a mapping")
    return data, content[match.end():]  # tolerant loader retains unknown keys


def export(content):
    data, body = load(content)
    name = data.get("name", "")
    if not isinstance(name, str) or len(name) > 64 or not NAME.fullmatch(name):
        raise ValueError("Invalid Agent Skills kebab-case name")
    if not isinstance(data.get("description"), str) or not 0 < len(data["description"]) <= 1024:
        raise ValueError("Invalid description")
    out = {key: data[key] for key in CORE if key in data}
    tools = data.get("allowed-tools", data.get("allowed_tools"))
    if tools is not None:
        if isinstance(tools, list) and all(isinstance(t, str) and t and not any(c.isspace() for c in t) for t in tools):
            out["allowed-tools"] = " ".join(tools)
        elif isinstance(tools, str):
            out["allowed-tools"] = tools
        else:
            raise ValueError("Tools cannot be represented as a space-delimited string")
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict) or any(not isinstance(k, str) for k in metadata):
        raise ValueError("metadata must have string keys")
    encoded = {k: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in metadata.items()}
    for key, value in data.items():
        if key not in (*CORE, "metadata", "allowed-tools", "allowed_tools"):
            encoded["psfs." + key] = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    if encoded:
        out["metadata"] = encoded
    return "---\n" + yaml.safe_dump(out, sort_keys=False, allow_unicode=True) + "---\n" + body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = export(args.source.read_text(encoding="utf-8"))
    args.destination.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
