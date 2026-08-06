#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_repo import REPO_ROOT, validate_repository


PROJECT = "slt-review"
LEGACY_PROJECTS = ("cross-review-control",)
VERSION = "1.0.0"
AGENT_FILES = (
    "luna-worker.toml",
    "terra-reviewer.toml",
)


def codex_home_from(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.is_file():
        hasher.update(path.read_bytes())
        return hasher.hexdigest()
    if path.is_dir():
        for item in sorted(p for p in path.rglob("*") if p.is_file()):
            hasher.update(item.relative_to(path).as_posix().encode("utf-8"))
            hasher.update(b"\0")
            hasher.update(item.read_bytes())
            hasher.update(b"\0")
        return hasher.hexdigest()
    return "missing"


def ensure_under(path: Path, parent: Path) -> None:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise RuntimeError(f"refusing target outside Codex home: {path}") from exc


def target_map(codex_home: Path) -> list[tuple[Path, Path]]:
    sources = [(REPO_ROOT / ".agents" / "skills" / PROJECT, codex_home / "skills" / PROJECT)]
    sources.extend(
        (REPO_ROOT / ".codex" / "agents" / name, codex_home / "agents" / name)
        for name in AGENT_FILES
    )
    return sources


def backup(path: Path, codex_home: Path, backup_root: Path) -> None:
    ensure_under(path, codex_home)
    relative = path.resolve().relative_to(codex_home.resolve())
    destination = backup_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, destination)
    elif path.is_file():
        shutil.copy2(path, destination)


def remove_target(path: Path, codex_home: Path) -> None:
    ensure_under(path, codex_home)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def copy_target(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def validate_or_raise() -> None:
    errors = validate_repository()
    if errors:
        raise RuntimeError("repository validation failed:\n- " + "\n- ".join(errors))


def install(codex_home: Path, force: bool) -> None:
    validate_or_raise()
    mappings = target_map(codex_home)
    manifest_path = codex_home / f"{PROJECT}-install.json"
    legacy_manifest_paths = [codex_home / f"{name}-install.json" for name in LEGACY_PROJECTS]
    previous_records: list[dict[str, str]] = []
    for previous_path in (manifest_path, *legacy_manifest_paths):
        if not previous_path.is_file():
            continue
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
        if previous.get("project") not in (PROJECT, *LEGACY_PROJECTS):
            raise RuntimeError("install manifest belongs to another project")
        previous_records.extend(previous.get("targets", []))

    current_targets = {str(target.resolve()) for _, target in mappings}
    stale_records = [record for record in previous_records if str(Path(record["path"]).resolve()) not in current_targets]
    conflicts = [target for source, target in mappings if target.exists() and digest(source) != digest(target)]
    conflicts.extend(
        Path(record["path"])
        for record in stale_records
        if Path(record["path"]).exists() and digest(Path(record["path"])) != record["sha256"]
    )
    if conflicts and not force:
        names = "\n- ".join(str(path) for path in conflicts)
        raise RuntimeError(f"existing modified targets would be replaced or retired; rerun with --force to back them up:\n- {names}")

    backup_root = codex_home / "backups" / PROJECT / timestamp()
    for record in stale_records:
        path = Path(record["path"])
        ensure_under(path, codex_home)
        if not path.exists():
            continue
        if digest(path) != record["sha256"]:
            backup(path, codex_home, backup_root)
        remove_target(path, codex_home)

    records: list[dict[str, str]] = []
    for source, target in mappings:
        ensure_under(target, codex_home)
        if target.exists() and digest(source) != digest(target):
            backup(target, codex_home, backup_root)
        if target.exists():
            remove_target(target, codex_home)
        copy_target(source, target)
        records.append({"path": str(target), "sha256": digest(target)})

    manifest = {
        "project": PROJECT,
        "version": VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "targets": records,
    }
    codex_home.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    for legacy_path in legacy_manifest_paths:
        if legacy_path.is_file():
            legacy_path.unlink()
    print(f"Installed {PROJECT} into {codex_home}")
    if backup_root.exists():
        print(f"Backed up replaced files to {backup_root}")


def uninstall(codex_home: Path, force: bool) -> None:
    manifest_path = codex_home / f"{PROJECT}-install.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"install manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("project") != PROJECT:
        raise RuntimeError("install manifest belongs to another project")

    records = manifest.get("targets", [])
    changed: list[Path] = []
    for record in records:
        path = Path(record["path"])
        ensure_under(path, codex_home)
        if path.exists() and digest(path) != record["sha256"]:
            changed.append(path)
    if changed and not force:
        names = "\n- ".join(str(path) for path in changed)
        raise RuntimeError(f"installed targets were modified; rerun with --force to back them up before removal:\n- {names}")

    backup_root = codex_home / "backups" / PROJECT / f"uninstall-{timestamp()}"
    for path in changed:
        backup(path, codex_home, backup_root)
    for record in records:
        path = Path(record["path"])
        if path.exists():
            remove_target(path, codex_home)
    manifest_path.unlink()
    print(f"Uninstalled {PROJECT} from {codex_home}")
    if backup_root.exists():
        print(f"Backed up modified files to {backup_root}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate, install, or uninstall SLT Review.")
    parser.add_argument("action", choices=("check", "install", "uninstall"))
    parser.add_argument("--codex-home", help="Override the Codex home directory.")
    parser.add_argument("--force", action="store_true", help="Back up and replace/remove conflicting managed targets.")
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    args = parse_args()
    try:
        if args.action == "check":
            validate_or_raise()
            print("PASS: repository is ready to install.")
        elif args.action == "install":
            install(codex_home_from(args.codex_home), args.force)
        else:
            uninstall(codex_home_from(args.codex_home), args.force)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
