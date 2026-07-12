import importlib.util
import json
import os
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nexus_release", ROOT / "nexus.py")
nexus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nexus)


def test_unknown_target_is_rejected_with_suggestion(tmp_path):
    (tmp_path / "nexus.yml").write_text("targets: [claud]\npackages: []\nmcps: []\n")

    with pytest.raises(nexus.ManifestValidationError, match="Unknown target 'claud'"):
        nexus.Config(tmp_path).data


def test_dashboard_has_useful_preinit_state_and_no_absolute_paths(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    cfg = nexus.Config(tmp_path)

    model = nexus.build_dashboard_model(cfg)
    encoded = json.dumps(model)

    assert model["lifecycle"]["stage"] == "uninitialized"
    assert model["lifecycle"]["next_action"] == "initialize"
    assert model["actions"]["can_deploy"] is False
    assert str(tmp_path) not in encoded
    assert str(home) not in encoded


def test_inline_targets_are_replaced_without_duplicate_key(tmp_path):
    cfg = nexus.Config(tmp_path)
    cfg.yml_path.write_text("name: demo\ntargets: [codex]\npackages: []\nmcps: []\n")

    nexus.update_manifest_targets(cfg, ["claude", "cursor"])
    saved = cfg.yml_path.read_text()

    assert saved.count("targets:") == 1
    assert yaml.safe_load(saved)["targets"] == ["claude", "cursor"]


def test_clean_plan_preserves_unmanaged_github_metadata(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    (tmp_path / "nexus.yml").write_text("targets: [claude]\npackages: []\nmcps: []\n")
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: CI\n")
    cache_skill = tmp_path / ".nexus" / "cache" / "pkg" / "skill"
    cache_skill.mkdir(parents=True)
    skill_dir = home / ".claude" / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "managed").symlink_to(cache_skill)
    nexus.TARGET_REGISTRY["claude"]["skills"] = skill_dir
    cfg = nexus.Config(tmp_path)

    plan = nexus.build_clean_plan(cfg)
    nexus.cmd_clean(cfg, SimpleNamespace(dry_run=True, yes=False))

    assert any(item["type"] == "symlink" for item in plan["items"])
    assert workflow.read_text() == "name: CI\n"
    assert (skill_dir / "managed").is_symlink()


def test_project_dir_resolution_precedence(tmp_path, monkeypatch):
    explicit = tmp_path / "explicit"
    env_dir = tmp_path / "env"
    explicit.mkdir()
    env_dir.mkdir()
    monkeypatch.setenv("NEXUS_PROJECT_DIR", str(env_dir))

    assert nexus.resolve_project_dir(str(explicit)) == explicit.resolve()
    assert nexus.resolve_project_dir() == env_dir.resolve()


def test_public_repository_metadata_and_examples_are_valid():
    required = [
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
        "CHANGELOG.md",
        "docs/quickstart.md",
        "docs/release-checklist.md",
        "examples/README.md",
        ".github/workflows/ci.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative

    with open(ROOT / "pyproject.toml", "rb") as handle:
        metadata = tomllib.load(handle)
    assert metadata["project"]["name"] == "agent-nexus"
    assert metadata["project"]["scripts"]["nexus"] == "nexus:main"

    for example in (ROOT / "examples").glob("*.yml"):
        assert isinstance(yaml.safe_load(example.read_text()), dict), example
