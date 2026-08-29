---
name: emanager
description: "Turn a plugin idea into an installable, host-verified plugin with a five-stage workflow, provenance-aware requirements, vertical tasks, independent reviews, and resumable evidence. Use when the user asks to create, build, ship, install, or verify a Codex plugin or skill plugin."
---

# Emanager

Plugin Manager is the operating procedure for building plugins. Treat the target project as a
small audited delivery, not as a conversation transcript. Keep all durable state in
`.plugin-manager/state.json`; write human-readable artifacts beside it when useful. If work is
interrupted, read state first and resume at the first incomplete gate.

## Non-negotiable rules

- Separate writing and reviewing. A reviewer gets a fresh context and reads files and evidence
  directly; it must not rely on the builder's summary.
- A claim is not a pass without evidence. Source code, a successful build, or a local launch is not
  proof of installation or host execution.
- During development do not install into, mutate, or exercise a real host. Host contact is reserved
  for the checker stage.
- Every required host is verified independently. A pass on one host never covers another.
- A blocker finding must be resolved and re-verified before its task or delivery gate can pass.
- Route findings to the layer that caused them: code -> task/development, missing task -> plan,
  wrong behavior model -> design, changed or ambiguous intent -> requirements.

Use the bundled state helper for durable bookkeeping:

```text
python scripts/plugin_manager.py init --project-root <target> --name <plugin-name> --hosts <host-a> <host-b>
python scripts/plugin_manager.py verify --project-root <target>
```

The helper is advisory: do not claim a gate passed until the referenced evidence exists and is
readable.

## Stage 1: Plugin Spike Builder

Interview for intent and acceptance, one decision at a time. Ask about users, trigger phrases,
inputs/outputs, boundaries, supported hosts, privacy, and what "done" means. Do not make the user
choose implementation details that can be decided later.

For each requirement write a stable ID and exactly one provenance label:

- `user_stated`: directly said or confirmed by the user.
- `agent_inferred`: a clearly marked inference; ask for confirmation when it changes scope.
- `industry_default`: a platform or quality default; cite the source or explain why it is the
  default.

Also record `confidence` (`explicit`, `inferred`, or `default`), open questions, and acceptance
evidence. Never silently convert an inference into a user requirement. The stage passes when all
scope-changing questions are answered or explicitly deferred, and every requirement has a source,
confidence, and observable acceptance check.

## Stage 2: Interaction Runtime Design

Classify decisions before asking them:

1. **Product trade-off**: ask the user to choose (scope, UX, latency, privacy, compatibility).
2. **Architecture proposal**: choose a conservative design, state alternatives and consequences,
   then ask only for confirmation when the choice changes product behavior or risk.
3. **Platform fact**: verify against current official Codex/plugin documentation yourself. Record
   URL, date checked, and the exact constraint. Never ask the user to guess platform mechanics.

Produce a runtime contract: trigger and entrypoint, message/data flow, state locations, failure and
retry behavior, permissions, observability, and a host capability matrix. Mark unsupported hosts or
features explicitly. The stage passes when the contract is internally consistent and each required
platform claim has evidence.

## Stage 3: Plugin Dive Planner

Plan vertically. Each task must produce a thin, runnable slice with its own acceptance checks,
fixtures, and verification command. Avoid front-end/back-end buckets. Order tasks so the first one
proves the smallest end-to-end path (manifest -> skill/runtime -> observable result), then add
capabilities, failure handling, persistence, and polish.

Every task record includes: purpose, files owned, preconditions, command to run, expected result,
evidence to attach, and rollback boundary. A task is independently acceptable only when its checks
can run without unfinished sibling tasks (or the dependency is named and already passed).

## Stage 4: Plugin Builder

Implement the smallest end-to-end path first. For each task, follow this loop:

1. Build the slice and keep changes within its file ownership.
2. Run machine self-checks (format/lint/tests/manifest validation as applicable) and attach raw
   output plus environment details to the task evidence.
3. Open a fresh reviewer context. It reads the requirement, task contract, changed files, and
   evidence directly.
4. Reviewer writes a complete finding for every issue: violated requirement, evidence location,
   severity (`blocker`, `major`, `minor`, `info`), impact, concrete fix, and re-test procedure.
5. Fix findings, rerun the exact checks, and mark the finding resolved with new evidence. Only then
   mark the task `passed`.

Do not touch a real host in this stage. "Works locally" is a development observation, not host
acceptance.

## Stage 5: Plugin Checker

The checker is the only stage allowed to contact real hosts. Run in this order:

1. Full static checks and plugin manifest validation.
2. Install the plugin into each required host, recording command, version, and output.
3. Execute the complete user flow on each host independently; capture observable evidence (logs,
   screenshots, or transcripts) and negative-path behavior.
4. Run a fresh full audit over requirements, design, plan, code, evidence, and host matrix.

If a finding appears, route it to its originating layer and resume that stage's loop. Do not blindly
restart the project. Delivery is allowed only when all three conditions hold simultaneously:

- every required host has an independent verification pass;
- all required acceptance items have evidence;
- all blocker findings are resolved and re-verified.

## State and recovery

Use `.plugin-manager/state.json` as the source of truth. Keep phase, gate status, task status,
finding status, host verification, timestamps, and evidence paths current after every meaningful
action. Never delete a finding; append a resolution and re-verification record. A resumed run starts
by checking for stale `in_progress` work and asking whether to continue or reopen it.

When reporting progress, show the current phase, the next incomplete gate, blockers, and the exact
evidence still missing. At delivery, summarize the host matrix and link the state/evidence files.
