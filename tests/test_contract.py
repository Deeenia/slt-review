from __future__ import annotations

import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from manage import digest, install, uninstall  # noqa: E402
from validate_repo import EXPECTED_AGENTS, RETIRED_AGENTS, validate_repository  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_repository_validation(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_only_luna_and_terra_agents_exist(self) -> None:
        agent_dir = ROOT / ".codex" / "agents"
        self.assertEqual({path.name for path in agent_dir.glob("*.toml")}, set(EXPECTED_AGENTS))
        for filename in RETIRED_AGENTS:
            self.assertFalse((agent_dir / filename).exists())

    def test_cross_model_pair_and_permissions(self) -> None:
        agent_dir = ROOT / ".codex" / "agents"
        luna = tomllib.loads((agent_dir / "luna-worker.toml").read_text(encoding="utf-8"))
        terra = tomllib.loads((agent_dir / "terra-reviewer.toml").read_text(encoding="utf-8"))
        self.assertNotEqual(luna["model"], terra["model"])
        self.assertEqual(luna["sandbox_mode"], "workspace-write")
        self.assertEqual(terra["sandbox_mode"], "read-only")
        self.assertEqual(luna["nickname_candidates"], ["Luna"])
        self.assertEqual(terra["nickname_candidates"], ["Terra"])

    def test_normal_path_is_two_calls_without_duplicate_verification(self) -> None:
        skill_dir = ROOT / ".agents" / "skills" / "slt-review"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        protocol = (skill_dir / "references" / "protocol.md").read_text(encoding="utf-8")
        self.assertIn("exactly two child-agent calls", skill)
        self.assertIn("Sol must not reread all files", skill)
        self.assertIn("Do not rerun verification", protocol)
        self.assertNotIn("Risk-scaled modes", skill)
        self.assertNotIn("SHA-256", skill)
        self.assertNotIn("## Identity handshake", skill)

    def test_boundary_is_minimal_and_unprotected(self) -> None:
        skill_dir = ROOT / ".agents" / "skills" / "slt-review"
        skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        template = (skill_dir / "references" / "boundary-template.md").read_text(encoding="utf-8")
        self.assertIn(".slt-review/boundary.md", skill)
        self.assertNotIn(".codex/orchestrations", skill + template)
        self.assertNotIn("Run ID", template)
        self.assertNotIn("Boundary SHA", template)

    def test_internal_surfaces_are_english_only(self) -> None:
        paths = [ROOT / "AGENTS.md"]
        paths.extend((ROOT / ".agents").rglob("*.md"))
        paths.extend((ROOT / ".agents").rglob("*.yaml"))
        paths.extend((ROOT / ".codex" / "agents").glob("*.toml"))
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.read_text(encoding="utf-8").isascii())


class InstallerLifecycleTests(unittest.TestCase):
    def test_install_is_idempotent_and_uninstall_removes_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            codex_home = Path(temp) / ".codex"
            install(codex_home, force=False)
            install(codex_home, force=False)
            manifest = json.loads((codex_home / "slt-review-install.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["targets"]), 3)
            uninstall(codex_home, force=False)
            self.assertFalse((codex_home / "skills" / "slt-review").exists())
            self.assertFalse((codex_home / "agents" / "luna-worker.toml").exists())

    def test_upgrade_migrates_legacy_name_and_retires_old_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            codex_home = Path(temp) / ".codex"
            legacy_skill = codex_home / "skills" / "cross-review-control"
            legacy_skill.mkdir(parents=True)
            (legacy_skill / "SKILL.md").write_text("legacy skill\n", encoding="utf-8")
            (codex_home / "agents").mkdir(parents=True)
            retired = codex_home / "agents" / "sol-auditor.toml"
            retired.write_text("managed old agent\n", encoding="utf-8")
            legacy_manifest = {
                "project": "cross-review-control",
                "version": "0.5.0",
                "targets": [
                    {"path": str(legacy_skill), "sha256": digest(legacy_skill)},
                    {"path": str(retired), "sha256": digest(retired)},
                ],
            }
            legacy_manifest_path = codex_home / "cross-review-control-install.json"
            legacy_manifest_path.write_text(json.dumps(legacy_manifest), encoding="utf-8")
            install(codex_home, force=False)
            self.assertFalse(legacy_skill.exists())
            self.assertFalse(retired.exists())
            self.assertFalse(legacy_manifest_path.exists())
            self.assertTrue((codex_home / "skills" / "slt-review").exists())
            self.assertTrue((codex_home / "slt-review-install.json").exists())

    def test_force_backs_up_modified_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            codex_home = Path(temp) / ".codex"
            install(codex_home, force=False)
            target = codex_home / "agents" / "luna-worker.toml"
            target.write_text(target.read_text(encoding="utf-8") + "\n# local edit\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                install(codex_home, force=False)
            install(codex_home, force=True)
            self.assertTrue(list((codex_home / "backups" / "slt-review").rglob("luna-worker.toml")))


if __name__ == "__main__":
    unittest.main()
