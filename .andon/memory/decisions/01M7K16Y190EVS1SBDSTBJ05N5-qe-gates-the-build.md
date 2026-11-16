---
id: 01M7K16Y190EVS1SBDSTBJ05N5
kind: decisions
status: accepted
title: QE gates the build
tags: [key-design-decisions]
paths: [qa-report.json, skills/roles/qe-agent/references/qa-report-schema.json, contract_conformance/security]
source: import CLAUDE.md:51 776c73faaa229eb9
confidence: 0.7
supersedes: none
created: 2026-11-16
---

**QE gates the build** — the qe-agent outputs `qa-report.json` per `skills/roles/qe-agent/references/qa-report-schema.json`. Build blocks on CRITICAL blockers or contract_conformance/security scores < 3.
