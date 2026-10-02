# Host-friction log — live non-Claude audit subject

## Session boundary and evidence grades

This was Buffy through Freebuff, not Claude Code. Exact underlying provider/model identity, account tier, context-window limit and token price were **not verified**; do not label this audit “DeepSeek” or “GPT Luna” based on the owner's prior runs. Tool **availability** is established by the session's exposed interfaces; runtime behavior only by calls actually made.

**Encountered instruction** means read during this audit, not that the corresponding build/deploy skill was executed. **Observed limitation** means the session tool response or recorded command showed it. The audit did not attempt a coordinated application build, a paid skill-creator optimization, schedule creation, publishing or signed-in UI testing. Therefore absence of those receipts is not smoothed into a successful fallback.

Repo instructions [AGENTS](../../../AGENTS.md#L1) require Markdownlint, root credentials and `.workspaces/` for actual skill evaluation workspaces. They do not themselves require Claude tools. The owner's narrower write boundary permits **only this audit folder**, so source fixtures/tests/generated outputs use audit-local copies and fake HOME. No canonical content was edited.

## Claude-only instructions encountered versus this session

| Instruction / exact excerpt and source | Missing or mismatched interface here | What happened instead / proof consequence |
|---|---|---|
| “For a cheap route, just invoke. Use the Skill tool” [madness:82](../../../skills/meta/madness/SKILL.md#L82) | No Claude `Skill` or slash-command dispatch interface | Read canonical skill files directly through native file tool for static audit. This is inspection, **not successful auto-trigger/invocation evidence** |
| “Spawn agents in parallel … dispatch with general-purpose” [orchestrator:110](../../../skills/orchestrator/SKILL.md#L110) | No Agent/Task spawn or isolated subagent interface | Inspected all roles serially. Parallel independent file/tool calls are not workers. Cannot claim independently reviewed output |
| “Spawn QE agent … mandatory, not optional” [orchestrator:111](../../../skills/orchestrator/SKILL.md#L111) | No independent QE child | Ran objective repository gates and adversarial script fixtures; default-refute was same-context static analysis, explicitly **not an independent evaluator** |
| “Workflow mode … deterministic JS … Workflow tool” [orchestrator:121](../../../skills/orchestrator/SKILL.md#L121); [workflow reference](../../../skills/orchestrator/references/workflow-orchestration.md#L1) | No native Workflow `agent/parallel/pipeline` engine | Did not fabricate a workflow or opt in from model identity. Proposed state/adapters in reports only; native Claude behavior retained |
| “Native Agent Teams (tmux, TeammateTool, inbox, shared task list)” [orchestrator:127](../../../skills/orchestrator/SKILL.md#L127) | No teams/messages/native shared task claims; no TeamCreate/SendMessage/TaskCreate interface | Used native todo tracking for auditor objectives and disk reports. A todo list is not team delivery/locking/ownership |
| “TaskCompleted … TeammateIdle” [task-loop hooks:5–6](../../../skills/loops/orchestrator-task-loop/references/hooks.md#L5) | No such lifecycle callbacks | Inspected hook templates/manifest; no callbacks fired. File status transitions proposed, not claimed installed enforcement |
| “/goal … loop until done” [primitives:18](../../../skills/loops/loop-controller/references/primitives.md#L18) | No `/goal` native exit blocker | Finite externally supervised commands for tests; did not run an autonomous fix loop. Positive exit statuses prove those commands only |
| “/loop 5m …” [primitives:59](../../../skills/loops/loop-controller/references/primitives.md#L59) and durable schedules in loop instructions | No session scheduler, CronCreate/ScheduleWakeup interface | No recurring job created. Reports distinguish approved cron/CI/one-shot proposal from an equivalent native schedule |
| “Stop-hook gate running script Y” [authoring:88](../../../skills/loops/loop-controller/references/authoring.md#L88) | No blocking session Stop/SubagentStop authority | Directly executed audit-local hook fixture and recorded exit status. This establishes script fail-open behavior, **not installed host Stop behavior**. Native file-change hook tool is not a universal completion blocker |
| “When the AskUserQuestion for output location fires” [vault-integration:29](../../../skills/workflows/repo-deep-dive/references/vault-integration.md#L29) | Named Claude tool absent; semantic structured question **available** as `ask_questions` | Output location already specified by owner, so no unnecessary question. No need to downgrade to prose or invent inability |
| Native progress/task tracking (TodoWrite-style workflow) | Named TodoWrite absent; native `write_todos` **available and used** | Tracked multi-step audit with actual todo tool. No shared-agent task semantics inferred |
| “Call the Artifact tool with the file path…” [artifact-publish:65](../../../skills/workflows/artifact-publish/SKILL.md#L65) | No Claude Artifact publication tool | Wrote Markdown deliverables; did not publish, create a URL, silently make content public, or treat local preview as hosted Artifact |
| Exact `mcp__plugin_playwright_playwright__browser_*` allowed tools [render-sanity:22–27](../../../skills/workflows/render-sanity/SKILL.md#L22) | Those exact MCP names not exposed | Native visible Browser panel has snapshot/screenshot/click/console/network tools, but no live site was required for this static audit. No headless/source-inferred UI verdict claimed |
| “All UI validation … NON-HEADLESS Playwright … inferred instead of observed” [orchestrator:114](../../../skills/orchestrator/SKILL.md#L114) | Generic browser tooling is not proof a requested Playwright host route is installed | Preserved visible-observation requirement in recommendations. Four-page **source guard** escape is not a rendered visual-quality test |
| “/sync-skills … global availability” [CLAUDE:16](../../../CLAUDE.md#L16) | No slash-command invocation and global-home write permission | Read sync code; did not symlink actual HOME. Seven-host/97-Codex claim unverified at this HEAD |
| `hermes chat … -s test_skill_name` plus install/uninstall [creator run_eval:65–77](../../../skills/workflows/skill-creator/scripts/run_eval.py#L65) | Hermes execution/paid credentials and global-install authority not established | Mocked only query-call boundary to prove description unused; no actual Hermes request. Trigger/efficacy success not claimed |
| Resource at `~/.claude/skills/...` [nano-banana:70](../../../skills/workflows/nano-banana/SKILL.md#L70) | Installed Claude path cannot be assumed | Read repo-local source; no image API call or paid generation. Report explicit SKILL_ROOT/secret-loader contract rather than copy root credentials |

A same-model second session could be independent if clean/scoped; a different provider in the same contaminated context is not. Neither was run here. Lack of native plumbing did not prevent extensive static audit, but does block honest claims of coordinated builds, external final acceptance or unattended universality.

## Connector discovery, not silent capability invention

Connected tool discovery was searched before concluding there was no direct replacement. Browser-specific discovery on open-design returned project metadata/login-status rather than Playwright browser control. A broad search for isolated workers/team/schedule/Stop/Artifact returned service-specific design/file and Cloudflare/Supabase tools, not Claude-compatible worker/queue/Stop contracts. Another design search exposed artifact **reading** and design recipes; those are not automatically equivalent to isolated project workers or Claude publication.

**Observed session output:** `search_mcp_tools` returned those named interfaces; no service operations were called. Search is not an exhaustive proof that no future/configured connector could implement the capability; the precise claim is **no equivalent interface established in this audit**. Open-design recipes run within that service and require their own task/authority contract; they are not a reason to send the repo there. Cloud/database operations are out of scope. No account identifiers, credentials, cookies or service state copied into this report.

## Execution / environment friction and actual recovery

| Event | Observed result / instruction conflict | Recovery and limitation |
|---|---|---|
| Existing gates versus read-only output constraint | Tests generate/modify fixtures; some hardcode `/tmp`; conversion defaults canonical integrations | New audit-local source snapshot + `TMPDIR`/`BATS_TMPDIR` + mktemp shim + explicit audit `--out`; actual HOME untouched. [audit_checks](evidence/audit_checks.py). This is not an iterative `/skill-creator` workspace |
| Worktree bootstrap versus owner-only-folder writes | Managed worktree has different HEAD from main; root environment absent | Read `git worktree list --porcelain`; no dependency/env install needed for static checks, no secrets loaded. [baseline](evidence/baseline.txt). Paid probes blocked rather than import credentials |
| Background tool mode | Earlier call reported BACKGROUND execution unsupported in this session transport, despite exposed schema | Used an audit-local Python subprocess with output-to-file and retained PID, then a supervised rerun that saved true returncode. Availability-schema alone does not prove execution mode works |
| Long full suite / output buffering | First buffered terminal attempt exceeded 600 seconds with no usable output | Detached audit-local run produced TAP; its process exit was unavailable and reported UNVERIFIED. Corrected supervised run saved exit 0 and full TAP. No false “passed” inferred from silence |
| Initial scanner failure | First snapshot TAP test306 failed; tracked `.scan-skills-ignore` absent from snapshot | Auditor corrected copied input only. Scanner 15/15 + full339 pass/7skip. [original](evidence/test-summary.json), [correction](evidence/refutation-checks.txt#L2), [corrected](evidence/corrected-test-summary.json). Not a repo regression |
| Python schema library unavailable | Seven actual PSFS tests SKIP; skill lint warns advisory | No package install outside audit. Use available PyYAML/manual proposal structural checks; full JSON Schema validation **UNVERIFIED locally**. CI installs library; no accusation of broken CI |
| Large combined file reads | `read_files` reports combined estimated-token cap (20,000), or 50,000-character window clipping | Search by line and reread relevant windows, rather than infer omitted text. Complete numbered evidence retained; no universal “read unlimited context” assumption |
| Generated integrations in orientation | Required `integrations/claude-code/hooks.json` absent/ignored baseline | Read canonical hook source and generated fresh audit-local output. No stale committed integrations claim; [baseline](evidence/baseline.txt), [sequential](evidence/convert-sequential.txt) |
| macOS xargs parallel conversion | Exit 1 command line too long under long worktree/audit path | Kept error receipt; exercised worker directly inside snapshot to isolate independent context bug. Did not bypass into canonical default integration output |
| Installer dry-run fixture setup | First worker attempt missing manifest failed before useful write-path check | Copied fresh manifest **to snapshot only**, reran fake HOME and reproduced writes under dry-run. Earlier failure not cited as proof of safety |
| Staged guard fixture setup | A nested directory inside the repo is not truly non-git; first attempted setup invalid | Replaced with mocked `git` exit2 and recorded warning + empty scan + exit0. [receipt:137](evidence/refutation-checks.txt#L137); don't call initial fixture a reproduction |
| Markdownlint runner | No project package install required; already cached Node CLI used with root config | Lint only authored report Markdown; copied canonical/generated scratch not rewritten to make its preexisting style lintable. [final validation](evidence/report-validation.txt) |
| No application runtime | This repository audit isn't an application build; no dev server/port chosen | No browser/live UI required and no listener collision. Actual host discovery, installed hook firing and UI observations remain UNVERIFIED |
| No external incident artifacts or paid model tasks | Owner's Luna incident provided as narrative, not project/transcript | Reproduced smaller deterministic guard escapes; causal compatibility analysis supported, 40+ page/model behavior independently UNVERIFIED |

The unsupported-background/timeout events were observed in earlier tool responses; those raw transport responses are not persisted as separate files. They are labeled session observations here, not replayable repo defects. Replayable command receipts are linked separately above.

## What this host did support

- Native file read/write/edit, code search and directory discovery; report-only edits succeeded.
- Terminal executes bounded commands with cwd and exit receipts; shell-script/Python fixtures usable.
- Native todo tracking used; structured human question interface present (no unresolved decision needed).
- Web search/read URL available; current official model/host/pattern docs checked without shell curl or paid API calls.
- Native Browser panel tools exposed, but not exercised for site quality; no reason to pretend browser capability absent.
- Connector discovery available; no need to invoke cloud services simply because credentials may exist there.

## Host-neutral lessons tied to the library

Publish execution mode and proof quality before acting, not after a failure. Role doctrine should not disappear because a named Claude dispatch tool is missing. Tool name translation is insufficient: isolated context, stable task claims, scheduler durability, fail-closed gates and budget cancellation need semantic contracts. Use actual available question/todo/browser substitutes where they satisfy the requirement, but refuse false equivalence for independent QE and unattended Stop control.

This log is primary evidence of a useful but non-equivalent non-Claude run. It supports read-only audit portability, not universal build/loop efficacy. No fix/intake was attempted.
