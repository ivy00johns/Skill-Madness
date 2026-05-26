# Assumption audit

A thinking move for surfacing invisible assumptions before launch.

Pre-deploy checklists verify artifacts. This move goes one level up: it asks what you believe to be true about the environment, the users, and the system — and whether any of those beliefs are load-bearing and unverified.

## The move

Before signing off on any deployment, work through this sequence:

1. **List explicit assumptions.** What have you written down or said aloud about how this deployment will behave? ("The migration is idempotent." "The third-party API is up." "Traffic will be under 1000 req/min for the first week.") Aim for at least five.
2. **Surface implicit assumptions.** What have you been assuming without stating? Common hiding spots:
   - Infrastructure: "The new service will be assigned to the same network as the old one."
   - Users: "Existing users will tolerate the new onboarding flow."
   - Data: "The production database schema matches staging."
   - Dependencies: "The library version in the lock file is the one that will be installed."
3. **Find the most dangerous if wrong.** Of everything on both lists, which single assumption — if false — would cause the most serious failure? Write it down explicitly: "If [assumption] is wrong, then [consequence]."
4. **Define a test for each.** For each assumption, answer: can you verify it before deploying? If yes, add it to the deploy checklist. If no, decide: is this assumption risky enough to block the deploy, or can it be monitored and responded to post-deploy?
5. **Go / no-go on the dangerous one.** The most-dangerous-if-wrong assumption must be either verified or explicitly accepted as a known risk with a rollback plan. If it's unverified and unacceptable risk, block the deploy.

## When to use it

- Before any production deployment
- Before Phase 3 (design / define agents) in an orchestrated build — catching a bad assumption at design time is far cheaper than catching it after agents have built against it
- Any time you are "pretty sure" something will work but haven't confirmed it

## What it prevents

Most surprise outages trace back to an assumption that felt too obvious to state. The move forces the assumption into the open where it can be tested or consciously accepted.

## Worked example

Deploying a new background job that processes a queue:

**Explicit assumptions:**
- The queue has fewer than 10K items in it at deploy time
- The worker process has permission to write to the output bucket
- The job is idempotent — safe to run twice on the same item

**Implicit assumptions:**
- The message format in production matches the message format in staging
- The output bucket already exists (not created on first write)
- The memory limit on the worker process is sufficient for the largest item in the queue

**Most dangerous if wrong:** "The message format in production matches staging." If wrong, every job will fail silently and the queue will back up.

**Test:** Run one item manually in production before enabling the worker at scale. Takes 5 minutes. Add to deploy checklist.

**Verdict:** Go — once the format spot-check passes.
