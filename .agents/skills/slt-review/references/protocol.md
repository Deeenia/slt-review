# Protocol

## Luna packet

```text
Boundary: .slt-review/boundary.md
Outcome: <requested result>
Done when: <Sol-derived observable criteria>
Write scope: <exact paths or a narrow path pattern>
Do not touch: <relevant exclusions>
Verification: <one proportionate command or procedure>
Context: <only facts Luna needs>
```

Luna must read the boundary before editing. Reject conflicting or unbounded packets instead of guessing.

## Luna result

```text
Status: PASS | BLOCKED
BOUNDARY_ACK: .slt-review/boundary.md
Changed: <exact paths, including newly created files>
Verification: <command and raw output>
Blocker: <none or concrete reason>
```

Do not require hashes, manifests, commits, identity attestations, or repeated evidence collection. `Changed` is the authoritative review scope. Include untracked files by listing their paths directly; ordinary `git diff` is not required to establish their existence.

## Terra packet

Do not include Luna's messages, rationale, self-assessment, confidence, or preferred verdict.

```text
Boundary: .slt-review/boundary.md
Original outcome: <requested result>
Done when: <Sol-derived observable criteria>
Review scope: <Luna's exact changed paths>
Raw verification: <command and raw output>
Focus: correctness, regressions, scope, and missing task-relevant tests
```

## Terra result

```text
Status: PASS | FIX | BLOCKED
Findings:
  - Location: <path and tight line reference>
    Evidence: <observable problem>
    Impact: <what can fail>
    Required fix: <bounded correction>
Coverage: <criteria reviewed>
Blocker: <none or concrete reason>
```

Terra reviews the listed files read-only. Do not rerun Luna's successful verification by default. Run one targeted read-only check only if a concrete uncertainty prevents a verdict. Style preferences alone do not justify `FIX`.

## Sol final gate

- Accept `PASS` when Luna reports successful verification and Terra reports `PASS` for the same changed paths.
- Do not rerun verification or independently re-review the implementation.
- On `FIX`, return only the bounded finding to Luna. Permit one correction cycle and one fresh Terra re-review.
- Exclude `.slt-review/**` from the product result.
- Report user-visible roles only as `Sol`, `Luna`, and `Terra`.
