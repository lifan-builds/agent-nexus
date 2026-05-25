import importlib.util
import json
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nexus", ROOT / "nexus.py")
nexus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nexus)


def test_antigravity_sse_uses_server_url():
    deployer = object.__new__(nexus.Deployer)
    entry = deployer._build_mcp_entry(
        {"name": "docs", "transport": "sse", "url": "https://example.com/mcp"},
        target="antigravity",
    )

    assert entry == {"serverUrl": "https://example.com/mcp"}


def test_generic_sse_keeps_standard_url_shape():
    deployer = object.__new__(nexus.Deployer)
    entry = deployer._build_mcp_entry(
        {"name": "docs", "transport": "sse", "url": "https://example.com/mcp"},
        target="cursor",
    )

    assert entry == {"type": "sse", "url": "https://example.com/mcp"}


def test_generic_http_keeps_http_transport():
    deployer = object.__new__(nexus.Deployer)
    entry = deployer._build_mcp_entry(
        {"name": "mem0", "transport": "http", "url": "https://mcp.mem0.ai/mcp"},
        target="cursor",
    )

    assert entry == {"type": "http", "url": "https://mcp.mem0.ai/mcp"}


def test_codex_http_mcp_uses_url_shape_without_sse_type():
    lines = nexus.Deployer._codex_toml_for_mcp(
        "mem0",
        {"type": "http", "url": "https://mcp.mem0.ai/mcp"},
    )

    assert lines == [
        "",
        '[mcp_servers."mem0"]',
        'url = "https://mcp.mem0.ai/mcp"',
    ]


def test_package_skill_allowlist_filters_discovered_skills():
    discovery = {
        "name": "skills",
        "skills": [
            {"name": "diagnose", "path": "/tmp/diagnose"},
            {"name": "obsidian-vault", "path": "/tmp/obsidian-vault"},
            {"name": "tdd", "path": "/tmp/tdd"},
        ],
    }

    filtered = nexus.apply_package_filters(discovery, {"skills": ["diagnose", "tdd"]})

    assert [s["name"] for s in filtered["skills"]] == ["diagnose", "tdd"]


def test_package_without_skill_allowlist_keeps_all_discovered_skills():
    discovery = {
        "name": "skills",
        "skills": [
            {"name": "diagnose", "path": "/tmp/diagnose"},
            {"name": "obsidian-vault", "path": "/tmp/obsidian-vault"},
        ],
    }

    filtered = nexus.apply_package_filters(discovery, {})

    assert [s["name"] for s in filtered["skills"]] == ["diagnose", "obsidian-vault"]


def test_discover_uses_skill_frontmatter_name(tmp_path):
    skill_dir = tmp_path / "pkg" / "agent_reach" / "skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: agent-reach\n---\n\n# Agent Reach\n")

    discovery = nexus.PackageManager.discover(tmp_path / "pkg", "Agent-Reach")

    assert discovery["skills"] == [{"name": "agent-reach", "path": str(skill_dir)}]


def test_discover_allows_explicit_hidden_sparse_skill_path(tmp_path):
    skill_dir = tmp_path / "pkg" / ".agents" / "skills" / "impeccable"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: impeccable\n---\n\n# Impeccable\n")

    discovery = nexus.PackageManager.discover(
        tmp_path / "pkg",
        "impeccable",
        [".agents/skills/impeccable"],
    )

    assert discovery["skills"] == [{"name": "impeccable", "path": str(skill_dir)}]


def test_discovers_hooks_codex_json(tmp_path):
    pkg = tmp_path / "pkg"
    hooks_dir = pkg / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "hooks-codex.json").write_text('{"hooks": {}}')

    discovery = nexus.PackageManager.discover(pkg, "pkg")

    assert discovery["hooks_codex"] == str(hooks_dir / "hooks-codex.json")


def test_codex_hooks_path_prefers_codex_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    cfg = object.__new__(nexus.Config)

    assert cfg.codex_hooks_path() == tmp_path / "codex-home" / "hooks.json"


def test_package_hook_allowlist_keeps_only_codex_hooks():
    discovery = {
        "name": "context-harness",
        "skills": [],
        "hooks_claude": "/tmp/hooks.json",
        "hooks_cursor": "/tmp/hooks-cursor.json",
        "hooks_codex": "/tmp/hooks-codex.json",
    }

    filtered = nexus.apply_package_filters(discovery, {"hooks": ["codex"]})

    assert filtered["hooks_claude"] is None
    assert filtered["hooks_cursor"] is None
    assert filtered["hooks_codex"] == "/tmp/hooks-codex.json"


def test_package_hooks_false_disables_hook_deployment():
    discovery = {
        "name": "context-harness",
        "skills": [],
        "hooks_claude": "/tmp/hooks.json",
        "hooks_cursor": "/tmp/hooks-cursor.json",
        "hooks_codex": "/tmp/hooks-codex.json",
    }

    filtered = nexus.apply_package_filters(discovery, {"hooks": False})

    assert filtered["hooks_claude"] is None
    assert filtered["hooks_cursor"] is None
    assert filtered["hooks_codex"] is None


def test_codex_hook_merge_substitutes_package_root(tmp_path):
    hook_file = _write_codex_hook(
        tmp_path / "pkg",
        "SessionStart",
        'node "{{package_root}}/scripts/codex-context-hook.js" --nexus-package pkg',
    )

    merged = nexus.Deployer._merge_codex_hooks(
        [{"name": "pkg", "path": str(tmp_path / "pkg"), "hooks_codex": str(hook_file)}],
        tmp_path / "codex" / "hooks.json",
    )

    command = merged["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert command == f'node "{tmp_path / "pkg"}/scripts/codex-context-hook.js" --nexus-package pkg'


def test_deploy_codex_hooks_merges_with_temp_codex_home_and_preserves_unmanaged(tmp_path):
    codex_home = tmp_path / "codex-home"
    hooks_path = codex_home / "hooks.json"
    hooks_path.parent.mkdir()
    hooks_path.write_text(json.dumps({
        "hooks": {
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "echo user"}]},
            ],
        },
    }))
    hook_file = _write_codex_hook(
        tmp_path / "pkg",
        "SessionStart",
        'node "{{package_root}}/hook.js" --nexus-package pkg',
    )
    deployer = nexus.Deployer(_fake_cfg(tmp_path, codex_home))

    deployer.deploy_hooks([
        {"name": "pkg", "path": str(tmp_path / "pkg"), "hooks_codex": str(hook_file)}
    ])

    data = json.loads(hooks_path.read_text())
    commands = [h["command"] for group in data["hooks"]["SessionStart"] for h in group["hooks"]]
    assert "echo user" in commands
    assert f'node "{tmp_path / "pkg"}/hook.js" --nexus-package pkg' in commands


def test_deploy_codex_hooks_removes_stale_managed_hooks(tmp_path):
    codex_home = tmp_path / "codex-home"
    hooks_path = codex_home / "hooks.json"
    hooks_path.parent.mkdir()
    hooks_path.write_text(json.dumps({
        "hooks": {
            "Stop": [
                {"hooks": [{"type": "command", "command": "node old.js --nexus-package old"}]},
                {"hooks": [{"type": "command", "command": "echo user"}]},
            ],
        },
    }))
    deployer = nexus.Deployer(_fake_cfg(tmp_path, codex_home))

    deployer.deploy_hooks([])

    data = json.loads(hooks_path.read_text())
    commands = [h["command"] for group in data["hooks"]["Stop"] for h in group["hooks"]]
    assert commands == ["echo user"]


def test_deploy_codex_hooks_deduplicates_repeated_hook_entries(tmp_path):
    hook_file = _write_codex_hooks(
        tmp_path / "pkg",
        {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"type": "command", "command": "node hook.js --nexus-package pkg"}]},
                    {"hooks": [{"type": "command", "command": "node hook.js --nexus-package pkg"}]},
                ],
            },
        },
    )

    merged = nexus.Deployer._merge_codex_hooks(
        [{"name": "pkg", "path": str(tmp_path / "pkg"), "hooks_codex": str(hook_file)}],
        tmp_path / "codex" / "hooks.json",
    )

    assert len(merged["hooks"]["SessionStart"]) == 1


def test_dry_run_mentions_codex_hooks_without_writing_files(tmp_path, capsys):
    pkg = tmp_path / "pkg"
    _write_codex_hook(
        pkg,
        "SessionStart",
        'node "{{package_root}}/hook.js" --nexus-package pkg',
    )
    codex_home = tmp_path / "codex-home"
    cfg = _fake_cfg(tmp_path, codex_home)
    cfg.packages = [{"path": "pkg", "hooks": ["codex"]}]
    cfg.data = {"packages": cfg.packages, "mcps": [], "targets": ["codex"]}

    nexus.cmd_sync(cfg, SimpleNamespace(all=False, dry_run=True, yes=False))

    captured = capsys.readouterr()
    assert "hooks: pkg -> codex" in captured.err
    assert not (codex_home / "hooks.json").exists()


def _write_codex_hook(pkg: Path, event: str, command: str) -> Path:
    return _write_codex_hooks(
        pkg,
        {
            "hooks": {
                event: [
                    {"hooks": [{"type": "command", "command": command}]},
                ],
            },
        },
    )


def _write_codex_hooks(pkg: Path, data: dict) -> Path:
    hooks_dir = pkg / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "hooks-codex.json"
    hook_file.write_text(json.dumps(data))
    return hook_file


class _fake_cfg:
    def __init__(self, repo_dir: Path, codex_home: Path):
        self.repo_dir = repo_dir
        self.targets = ["codex"]
        self.packages = []
        self.data = {"packages": [], "mcps": [], "targets": ["codex"]}
        self._codex_home = codex_home

    def codex_hooks_path(self) -> Path:
        return self._codex_home / "hooks.json"

    def load_lockfile(self):
        return None

    @property
    def mcps(self):
        return []

    @property
    def optional_mcps(self):
        return []
