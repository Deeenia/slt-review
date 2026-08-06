---
name: slt-review
description: Run a cost-efficient three-model coding workflow. Use when the user explicitly invokes $slt-review and wants the active Sol task to plan, Luna to implement, and a fresh read-only Terra to review Luna's changes for independent bias control. Accept requests in any user language.
---

# SLT Review

Optimize for the lowest practical latency and model cost while preserving one independent cross-model review. Read [references/protocol.md](references/protocol.md) and [references/boundary-template.md](references/boundary-template.md) before dispatch.

Fixed route: Sol plans -> Luna implements -> fresh read-only Terra reviews.

## Fixed roles

- Use the active Desktop task as `Sol`. Sol plans, writes the boundary, dispatches, and summarizes. Sol never edits product files, launches another Sol, or reruns Luna's verification.
- Use one fresh `luna-worker` to implement the entire bounded change and run the most relevant verification once.
- Use one fresh read-only `terra-reviewer` to inspect Luna's final files and raw verification evidence.
- Do not use Terra for implementation or Sol for an additional audit in this version.
- Never let Luna review its own implementation. Terra receives no Luna rationale, confidence, self-assessment, or preferred verdict.

## Fast path

1. Inspect the repository once, only enough to infer the requested outcome, exact write scope, exclusions, observable completion criteria, and one proportionate verification command. Do not perform a separate risk-classification or identity-proof phase.
2. Write `.slt-review/boundary.md` from the boundary template. Keep it short. This is the only project file Sol may write.
3. Launch one fresh `luna-worker` with `fork_turns="none"` and the complete task packet. Do not use a separate handshake turn.
4. Luna reads the boundary, returns `BOUNDARY_ACK` in its result, implements only the declared scope, runs the declared verification once, and returns exact changed paths plus raw output.
5. Immediately launch one fresh read-only `terra-reviewer` with `fork_turns="none"`. Send only the boundary path, original outcome, completion criteria, exact changed paths, and raw verification output.
6. If Terra returns `PASS`, Sol immediately gives the final summary. Sol must not reread all files, rebuild a candidate snapshot, recompute hashes, or rerun tests.
7. If Terra returns `FIX`, send one focused correction to the same Luna, then launch one fresh Terra review. Stop with `BLOCKED` after that correction cycle fails or if Luna cannot safely implement the requested scope.

The normal successful path contains exactly two child-agent calls: one Luna implementation call and one Terra review call.

## Efficiency rules

- Do not create run IDs, task IDs, review IDs, boundary hashes, candidate manifests, identity handshakes, risk modes, or staged dispatches.
- Do not validate command syntax in a separate preflight. Luna handles normal command failures inside its single execution call.
- Do not run the same test, lint, build, or smoke command twice on an unchanged candidate.
- Terra reviews existing evidence and files; it runs an additional read-only check only when a concrete uncertainty prevents a verdict.
- Do not revise the boundary for evidence-format issues. Rewrite it only before Luna starts or when the actual product scope changes.
- Exclude `.slt-review/**` from product diffs, review findings, and user-facing created-file summaries.
- Keep user-visible progress to three events: Sol planned, Luna finished/Terra reviewing, and final result. Add a brief heartbeat only if a child call runs longer than 60 seconds.
- Display agents only as `Sol`, `Luna`, and `Terra`. Keep internal role names inside packets. Never display generated nicknames or encoded identifiers.

## Failure boundary

Return `BLOCKED` when Luna is unavailable, Terra is unavailable, Terra is not read-only, the write scope cannot be bounded, or Luna reports that the task is too complex to execute safely. Do not silently route implementation to Terra or add a Sol auditor. Tell the user that the current lightweight version supports only Sol -> Luna -> Terra.
