"""
Regression tests verifying the ecc-tools generated AI configuration files
have been removed from the repository.

These tests guard against accidental re-introduction of the deleted files.
The PR removed all ecc-tools generated outputs:
  - .agents/skills/HyperAgents/SKILL.md
  - .agents/skills/HyperAgents/agents/openai.yaml
  - .claude/ecc-tools.json
  - .claude/homunculus/instincts/inherited/HyperAgents-instincts.yaml
  - .claude/identity.json
  - .claude/skills/HyperAgents/SKILL.md
  - .codex/AGENTS.md
  - .codex/agents/docs-researcher.toml
  - .codex/agents/explorer.toml
  - .codex/agents/reviewer.toml
  - .codex/config.toml
"""

import os
import unittest

# Resolve the repository root relative to this file (tests/ lives one level down)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def repo_path(*parts: str) -> str:
    """Return an absolute path inside the repository root."""
    return os.path.join(REPO_ROOT, *parts)


class TestAgentsSkillsRemoved(unittest.TestCase):
    """Verify .agents/skills/HyperAgents/* files were deleted."""

    def test_agents_skill_md_does_not_exist(self):
        path = repo_path(".agents", "skills", "HyperAgents", "SKILL.md")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_agents_openai_yaml_does_not_exist(self):
        path = repo_path(".agents", "skills", "HyperAgents", "agents", "openai.yaml")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_agents_hyperagents_skill_dir_does_not_exist(self):
        """The entire .agents/skills/HyperAgents directory should be gone."""
        path = repo_path(".agents", "skills", "HyperAgents")
        self.assertFalse(
            os.path.isdir(path),
            f"Deleted directory should not exist: {path}",
        )

    def test_agents_skills_dir_does_not_exist(self):
        """With HyperAgents removed, .agents/skills should not exist."""
        path = repo_path(".agents", "skills")
        self.assertFalse(
            os.path.isdir(path),
            f"Directory should not exist after cleanup: {path}",
        )

    def test_agents_dir_does_not_exist(self):
        """The top-level .agents directory should be absent after cleanup."""
        path = repo_path(".agents")
        self.assertFalse(
            os.path.isdir(path),
            f"Directory should not exist after cleanup: {path}",
        )


class TestClaudeEccFilesRemoved(unittest.TestCase):
    """Verify .claude/ ecc-tools generated files were deleted."""

    def test_ecc_tools_json_does_not_exist(self):
        path = repo_path(".claude", "ecc-tools.json")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_identity_json_does_not_exist(self):
        path = repo_path(".claude", "identity.json")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_claude_skill_md_does_not_exist(self):
        path = repo_path(".claude", "skills", "HyperAgents", "SKILL.md")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_hyperagents_instincts_yaml_does_not_exist(self):
        path = repo_path(
            ".claude",
            "homunculus",
            "instincts",
            "inherited",
            "HyperAgents-instincts.yaml",
        )
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_claude_skills_hyperagents_dir_does_not_exist(self):
        path = repo_path(".claude", "skills", "HyperAgents")
        self.assertFalse(
            os.path.isdir(path),
            f"Deleted directory should not exist: {path}",
        )

    def test_claude_homunculus_inherited_dir_does_not_exist(self):
        path = repo_path(".claude", "homunculus", "instincts", "inherited")
        self.assertFalse(
            os.path.isdir(path),
            f"Deleted directory should not exist: {path}",
        )

    def test_claude_dir_does_not_exist(self):
        """The .claude directory itself should be absent (all its files were ecc-tools managed)."""
        path = repo_path(".claude")
        self.assertFalse(
            os.path.isdir(path),
            f"Directory should not exist after cleanup: {path}",
        )


class TestCodexFilesRemoved(unittest.TestCase):
    """Verify .codex/ ecc-tools generated files were deleted."""

    def test_codex_agents_md_does_not_exist(self):
        path = repo_path(".codex", "AGENTS.md")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_codex_config_toml_does_not_exist(self):
        path = repo_path(".codex", "config.toml")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_codex_explorer_toml_does_not_exist(self):
        path = repo_path(".codex", "agents", "explorer.toml")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_codex_reviewer_toml_does_not_exist(self):
        path = repo_path(".codex", "agents", "reviewer.toml")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_codex_docs_researcher_toml_does_not_exist(self):
        path = repo_path(".codex", "agents", "docs-researcher.toml")
        self.assertFalse(
            os.path.exists(path),
            f"Deleted file should not exist: {path}",
        )

    def test_codex_agents_dir_does_not_exist(self):
        path = repo_path(".codex", "agents")
        self.assertFalse(
            os.path.isdir(path),
            f"Deleted directory should not exist: {path}",
        )

    def test_codex_dir_does_not_exist(self):
        """The entire .codex directory should be absent after cleanup."""
        path = repo_path(".codex")
        self.assertFalse(
            os.path.isdir(path),
            f"Directory should not exist after cleanup: {path}",
        )


class TestNoEccToolsArtifactsAnywhere(unittest.TestCase):
    """Broader checks that ecc-tools artefacts are fully absent."""

    def test_no_ecc_tools_json_anywhere(self):
        """ecc-tools.json should not appear anywhere in the repo."""
        for root, _dirs, files in os.walk(REPO_ROOT):
            # Skip the .git directory to avoid false positives from git objects
            _dirs[:] = [d for d in _dirs if d != ".git"]
            for name in files:
                self.assertNotEqual(
                    name,
                    "ecc-tools.json",
                    f"ecc-tools.json found unexpectedly at: {os.path.join(root, name)}",
                )

    def test_no_hyperagents_instincts_yaml_anywhere(self):
        """HyperAgents-instincts.yaml should not appear anywhere in the repo."""
        for root, _dirs, files in os.walk(REPO_ROOT):
            _dirs[:] = [d for d in _dirs if d != ".git"]
            for name in files:
                self.assertNotEqual(
                    name,
                    "HyperAgents-instincts.yaml",
                    f"HyperAgents-instincts.yaml found unexpectedly at: {os.path.join(root, name)}",
                )

    def test_no_claude_identity_json_at_repo_root_level(self):
        """.claude/identity.json should not exist."""
        path = repo_path(".claude", "identity.json")
        self.assertFalse(os.path.exists(path))

    def test_ecc_tools_managed_paths_all_absent(self):
        """All paths that were listed in ecc-tools.json managedFiles are absent."""
        managed_files = [
            ".claude/skills/HyperAgents/SKILL.md",
            ".agents/skills/HyperAgents/SKILL.md",
            ".agents/skills/HyperAgents/agents/openai.yaml",
            ".claude/identity.json",
            ".codex/config.toml",
            ".codex/AGENTS.md",
            ".codex/agents/explorer.toml",
            ".codex/agents/reviewer.toml",
            ".codex/agents/docs-researcher.toml",
            ".claude/homunculus/instincts/inherited/HyperAgents-instincts.yaml",
        ]
        for rel_path in managed_files:
            abs_path = repo_path(*rel_path.split("/"))
            with self.subTest(path=rel_path):
                self.assertFalse(
                    os.path.exists(abs_path),
                    f"ecc-tools managed file should not exist: {abs_path}",
                )


class TestNegativeBoundary(unittest.TestCase):
    """Boundary / negative tests to strengthen confidence in cleanup state."""

    def test_deleted_toml_files_absent(self):
        """None of the three Codex agent TOML configs should exist."""
        toml_paths = [
            repo_path(".codex", "agents", "explorer.toml"),
            repo_path(".codex", "agents", "reviewer.toml"),
            repo_path(".codex", "agents", "docs-researcher.toml"),
            repo_path(".codex", "config.toml"),
        ]
        for path in toml_paths:
            with self.subTest(path=path):
                self.assertFalse(os.path.exists(path))

    def test_deleted_yaml_files_absent(self):
        """YAML config files deleted in the PR should not exist."""
        yaml_paths = [
            repo_path(".agents", "skills", "HyperAgents", "agents", "openai.yaml"),
            repo_path(
                ".claude",
                "homunculus",
                "instincts",
                "inherited",
                "HyperAgents-instincts.yaml",
            ),
        ]
        for path in yaml_paths:
            with self.subTest(path=path):
                self.assertFalse(os.path.exists(path))

    def test_deleted_json_files_absent(self):
        """JSON config files deleted in the PR should not exist."""
        json_paths = [
            repo_path(".claude", "ecc-tools.json"),
            repo_path(".claude", "identity.json"),
        ]
        for path in json_paths:
            with self.subTest(path=path):
                self.assertFalse(os.path.exists(path))

    def test_deleted_markdown_files_absent(self):
        """Markdown files deleted in the PR should not exist."""
        md_paths = [
            repo_path(".agents", "skills", "HyperAgents", "SKILL.md"),
            repo_path(".claude", "skills", "HyperAgents", "SKILL.md"),
            repo_path(".codex", "AGENTS.md"),
        ]
        for path in md_paths:
            with self.subTest(path=path):
                self.assertFalse(os.path.exists(path))

    def test_repo_root_still_exists(self):
        """Sanity check: the repository root must still exist."""
        self.assertTrue(os.path.isdir(REPO_ROOT))

    def test_core_repo_files_unaffected(self):
        """Core repository files must not have been removed by the cleanup."""
        core_files = [
            repo_path("README.md"),
            repo_path("requirements.txt"),
            repo_path("Dockerfile"),
        ]
        for path in core_files:
            with self.subTest(path=path):
                self.assertTrue(
                    os.path.exists(path),
                    f"Core repo file must still exist: {path}",
                )


if __name__ == "__main__":
    unittest.main()