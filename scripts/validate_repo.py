#!/usr/bin/env python3
from __future__ import annotations

import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "slt-review"
AGENT_DIR = REPO_ROOT / ".codex" / "agents"

EXPECTED_AGENTS = {
    "luna-worker.toml": ("luna-worker", "gpt-5.6-luna", "max", "workspace-write", ["Luna"]),
    "terra-reviewer.toml": ("terra-reviewer", "gpt-5.6-terra", "high", "read-only", ["Terra"]),
}
RETIRED_AGENTS = ("sol-controller.toml", "terra-worker.toml", "sol-auditor.toml")


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    try:
        block = text.split("---\n", 2)[1]
    except IndexError:
        return {}
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def validate_repository(root: Path = REPO_ROOT) -> list[str]:
    skill_dir = root / ".agents" / "skills" / "slt-review"
    agent_dir = root / ".codex" / "agents"
    errors: list[str] = []
    required = (
        skill_dir / "SKILL.md",
        skill_dir / "references" / "protocol.md",
        skill_dir / "references" / "boundary-template.md",
        skill_dir / "agents" / "openai.yaml",
    )
    for path in required:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")

    skill_path = required[0]
    if skill_path.is_file():
        skill = skill_path.read_text(encoding="utf-8")
        metadata = _frontmatter(skill)
        if metadata.get("name") != "slt-review":
            errors.append("SKILL.md name must be slt-review")
        if "$slt-review" not in metadata.get("description", ""):
            errors.append("SKILL.md description must include explicit invocation")
        for rule in (
            "exactly two child-agent calls",
            'fork_turns="none"',
            ".slt-review/boundary.md",
            "Sol plans -> Luna implements -> fresh read-only Terra reviews",
            "Sol must not reread all files",
        ):
            if rule not in skill:
                errors.append(f"SKILL.md missing efficiency rule: {rule}")

    metadata_path = required[3]
    if metadata_path.is_file() and "allow_implicit_invocation: false" not in metadata_path.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml must require explicit invocation")

    for filename, expected in EXPECTED_AGENTS.items():
        path = agent_dir / filename
        if not path.is_file():
            errors.append(f"missing agent config: .codex/agents/{filename}")
            continue
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"invalid TOML in {filename}: {exc}")
            continue
        actual = (
            data.get("name"),
            data.get("model"),
            data.get("model_reasoning_effort"),
            data.get("sandbox_mode"),
            data.get("nickname_candidates"),
        )
        if actual != expected:
            errors.append(f"unexpected role settings in {filename}: {actual!r}")

    for filename in RETIRED_AGENTS:
        if (agent_dir / filename).exists():
            errors.append(f"retired agent must not exist: .codex/agents/{filename}")

    luna = agent_dir / "luna-worker.toml"
    if luna.is_file():
        instructions = tomllib.loads(luna.read_text(encoding="utf-8")).get("developer_instructions", "")
        for rule in ("BOUNDARY_ACK", "Run the declared verification once", "do not review your own work"):
            if rule not in instructions:
                errors.append(f"luna-worker missing rule: {rule}")

    terra = agent_dir / "terra-reviewer.toml"
    if terra.is_file():
        instructions = tomllib.loads(terra.read_text(encoding="utf-8")).get("developer_instructions", "")
        for rule in ("Never implement or modify files", "Use Luna's raw verification without rerunning it"):
            if rule not in instructions:
                errors.append(f"terra-reviewer missing rule: {rule}")

    template = required[2]
    if template.is_file():
        text = template.read_text(encoding="utf-8")
        for heading in ("## Outcome", "## Done when", "## Luna write scope", "## Do not touch", "## Verification", "## Review route"):
            if heading not in text:
                errors.append(f"boundary template missing heading: {heading}")

    return errors


def main() -> int:
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: low-cost Sol-Luna-Terra contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
