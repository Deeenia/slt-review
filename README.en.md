# SLT Review

[中文](README.md) | [English](README.en.md)

A cost- and latency-first Codex skill. Sol plans and bounds the task, Luna performs the implementation at lower cost, and Terra independently reviews the result to reduce single-model bias.

```text
Active Sol: one planning pass
    ↓
Luna: one implementation and verification pass
    ↓
Fresh Terra: one independent read-only review
    ↓
Sol: summarize immediately, no re-verification
```

The normal successful path uses exactly two child-agent calls: one Luna and one Terra.

## Boundaries

- Sol derives scope and writes a short `.slt-review/boundary.md`.
- Luna reads the boundary, implements the complete bounded change, and runs the single most relevant verification once.
- A fresh Terra reviews Luna's exact changed files read-only and does not rerun successful verification by default.
- After Terra passes, Sol returns the result without rereading the full implementation, rebuilding snapshots, hashing evidence, or rerunning tests.
- If Terra finds a concrete defect, Luna gets at most one correction followed by one fresh Terra review.
- Terra does not participate in implementation or act as an implementer's sole reviewer. The workflow returns `BLOCKED` when Luna cannot execute safely.

## Cost and latency strategy

- Use the higher-capability Sol only for requirement analysis, task planning, boundary definition, and final synthesis.
- Assign the main coding work to Luna to reduce implementation cost.
- Have Terra review Luna's actual changes from a different model perspective to catch omissions and biased assumptions.
- Keep the normal successful path to one Luna call and one Terra call.
- Do not repeat successful verification by default; allow one correction and fresh review only when Terra reports a concrete defect.

The boundary lives in the ordinary workspace rather than the protected `.codex` directory and is excluded from product results.

## Roles

| Display | Model | Permission | Responsibility |
|---|---|---|---|
| Sol | Sol selected for the active Desktop task | Current workspace | Plan and summarize; never edit product files |
| Luna | `gpt-5.6-luna` | `workspace-write` | Implement and verify once |
| Terra | `gpt-5.6-terra` | `read-only` | Independent review |

## Install

Requires Python 3.11+.

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\validate.ps1
python -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install.ps1 -Force
```

macOS/Linux:

```bash
sh scripts/validate.sh
python3 -m unittest discover -s tests -v
sh scripts/install.sh --force
```

Restart Codex Desktop, open a fresh Sol task, and state only the desired result:

```text
$slt-review

Create a Python random number generator for 0-1000.
```

The user does not need to specify tests, risk, or an orchestration mode.

## Structure

```text
.agents/skills/slt-review/
├─ SKILL.md
├─ agents/openai.yaml
└─ references/
   ├─ protocol.md
   └─ boundary-template.md

.codex/agents/
├─ luna-worker.toml
└─ terra-reviewer.toml
```

## License

Apache License 2.0. No endorsement by OpenAI is implied.
