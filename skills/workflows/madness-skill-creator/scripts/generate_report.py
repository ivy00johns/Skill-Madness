#!/usr/bin/env python3
"""Render the current loop interface as a local, dependency-free HTML report."""
import argparse
import html
import json
from pathlib import Path
import sys


def generate_html(data: dict, auto_refresh: bool = False, skill_name: str = "") -> str:
    esc = lambda value: html.escape(str(value))
    def rows(results):
        output = []
        for result in results:
            status = "ERROR / UNVERIFIED" if result.get("errors", 0) or result.get("pass") is None else "PASS" if result["pass"] else "FAIL"
            output.append(f"<tr><td>{esc(result['query'])}</td><td>{status}</td><td>{result.get('triggers', 0)}/{result.get('valid_runs', result.get('runs', 0))} valid runs; {result.get('errors', 0)} errors</td></tr>")
        return "".join(output)
    parts = ["<!doctype html><html lang='en'><meta charset='utf-8'>",
             "<meta http-equiv='refresh' content='5'>" if auto_refresh else "",
             "<title>Skill description evaluation</title><style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.5rem}pre{white-space:pre-wrap}</style>",
             f"<h1>{esc(skill_name)} — Skill description evaluation</h1>",
             "<p>Train feedback tunes descriptions. Dev scores select the candidate. The final held-out test is reported separately and never selects a winner. Errors are unverified, not negative triggers.</p>",
             f"<p>Selected iteration: {esc(data.get('best_iteration', 'pending'))}; selection score: {esc(data.get('selection_score', 'pending'))}</p>",
             f"<pre>{esc(data.get('best_description', 'pending'))}</pre>"]
    for entry in data.get("history", []):
        parts.append(f"<h2>Iteration {entry['iteration']}</h2><pre>{esc(entry['description'])}</pre>")
        for label in ("train", "dev"):
            parts.append(f"<h3>{label.title()}</h3><table><tr><th>Query</th><th>Status</th><th>Observation</th></tr>{rows(entry.get(label + '_results', []))}</table>")
    final = data.get("final_test_results")
    parts.append("<h2>Final held-out test</h2>")
    if final:
        parts.append(f"<p>Score: {esc(data.get('held_out_test_score') or 'UNVERIFIED')}</p><table>{rows(final['results'])}</table>")
    else:
        parts.append("<p>NOT RUN — no held-out outcome has been consulted.</p>")
    parts.append("</html>")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("-o", "--output")
    parser.add_argument("--skill-name", default="")
    args = parser.parse_args()
    data = json.load(sys.stdin) if args.input == "-" else json.loads(Path(args.input).read_text())
    text = generate_html(data, skill_name=args.skill_name)
    if args.output:
        Path(args.output).write_text(text)
    else:
        print(text)


if __name__ == "__main__":
    main()
