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


def test_mcp_sync_preserves_unmanaged_servers_and_local_env_secrets(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    mcp_path = tmp_path / "fake-mcp.json"

    cfg.mcp_path = lambda _target: mcp_path
    mcp_path.write_text(json.dumps({
        "mcpServers": {
            "user-only": {"command": "custom"},
            "github": {
                "type": "stdio",
                "command": "/old/npx",
                "args": ["old"],
                "env": {
                    "GITHUB_TOKEN": "real-token",
                    "LOCAL_ONLY": "keep",
                },
                "localSetting": True,
            },
        },
    }))

    deployer = nexus.Deployer(cfg)
    deployer.sync_mcps([{
        "name": "github",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
    }])

    data = json.loads(mcp_path.read_text())
    servers = data["mcpServers"]
    assert servers["user-only"] == {"command": "custom"}
    assert servers["github"]["args"] == ["-y", "@modelcontextprotocol/server-github"]
    assert servers["github"]["env"]["GITHUB_TOKEN"] == "real-token"
    assert servers["github"]["env"]["LOCAL_ONLY"] == "keep"
    assert servers["github"]["localSetting"] is True


def test_codex_mcp_sync_preserves_placeholder_env_from_existing_managed_block(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.yml_path = tmp_path / "nexus.personal.yml"
    deployer = nexus.Deployer(cfg)
    mcp_path = tmp_path / "config.toml"
    mcp_path.write_text(
        '[profile.default]\n'
        'model = "gpt-5"\n\n'
        '# BEGIN NEXUS MANAGED MCP SERVERS\n'
        '# generated\n\n'
        '[mcp_servers."github"]\n'
        'command = "/old/npx"\n'
        'args = ["old"]\n\n'
        '[mcp_servers."github".env]\n'
        'GITHUB_TOKEN = "real-token"\n'
        'LOCAL_ONLY = "keep"\n'
        '# END NEXUS MANAGED MCP SERVERS\n'
    )

    deployer._sync_mcps_for_codex([
        {
            "name": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
        }
    ], mcp_path)

    output = mcp_path.read_text()
    assert '[profile.default]' in output
    assert 'GITHUB_TOKEN = "real-token"' in output
    assert 'LOCAL_ONLY = "keep"' in output
    assert '@modelcontextprotocol/server-github' in output


def test_codex_mcp_prune_removes_stale_managed_server_from_toml_block(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["codex"]
    mcp_path = tmp_path / "config.toml"
    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "codex_toml"
    cfg.yml_path = tmp_path / "nexus.personal.yml"
    deployer = nexus.Deployer(cfg)
    mcp_path.write_text(
        '[profile.default]\n'
        'model = "gpt-5"\n\n'
        '# BEGIN NEXUS MANAGED MCP SERVERS\n'
        '# generated\n\n'
        '[mcp_servers."keep"]\n'
        'command = "npx"\n'
        'args = ["keep"]\n\n'
        '[mcp_servers."stale"]\n'
        'command = "npx"\n'
        'args = ["stale"]\n\n'
        '[mcp_servers."stale".env]\n'
        'TOKEN = "real-token"\n'
        '# END NEXUS MANAGED MCP SERVERS\n'
    )

    deployer.prune_mcps(
        {"keep"},
        {"mcps": {"managed": [{"name": "keep"}, {"name": "stale"}]}},
    )

    output = mcp_path.read_text()
    assert '[profile.default]' in output
    assert '[mcp_servers."keep"]' in output
    assert "stale" not in output
    assert "# BEGIN NEXUS MANAGED MCP SERVERS" in output
    assert "# END NEXUS MANAGED MCP SERVERS" in output


def test_lockfile_records_only_actual_managed_mcps(tmp_path):
    manifest = {
        "mcps": [
            {"name": "always"},
            {"name": "optional-inline", "optional": True},
        ],
        "optional_mcps": [
            {"name": "github"},
        ],
    }

    lock = nexus.generate_lockfile([], manifest, [], tmp_path)

    assert lock["mcps"]["managed"] == [{"name": "always"}]


def test_lockfile_records_accepted_optional_mcps(tmp_path):
    lock = nexus.generate_lockfile(
        [],
        {},
        [],
        tmp_path,
        [
            {"name": "always"},
            {"name": "github", "optional": True},
        ],
    )

    assert lock["mcps"]["managed"] == [
        {"name": "always"},
        {"name": "github", "optional": True},
    ]


def test_init_creates_personal_manifest_from_example(tmp_path, capsys):
    (tmp_path / "nexus.example.yml").write_text("name: example\n")
    cfg = nexus.Config(tmp_path)

    nexus.cmd_init(cfg, SimpleNamespace(force=False))

    assert (tmp_path / "nexus.personal.yml").read_text() == "name: example\n"
    captured = capsys.readouterr()
    assert "Created nexus.personal.yml" in captured.err


def test_init_refuses_to_overwrite_existing_personal_manifest(tmp_path):
    (tmp_path / "nexus.example.yml").write_text("name: example\n")
    (tmp_path / "nexus.personal.yml").write_text("name: personal\n")
    cfg = nexus.Config(tmp_path)

    try:
        nexus.cmd_init(cfg, SimpleNamespace(force=False))
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("cmd_init should refuse to overwrite without --force")

    assert (tmp_path / "nexus.personal.yml").read_text() == "name: personal\n"


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


def test_package_targets_limit_skill_deployment_and_pruning(tmp_path):
    codex_home = tmp_path / "codex-home"
    cfg = _fake_cfg(tmp_path, codex_home)
    cfg.targets = ["codex", "fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    fake_skill_dir = tmp_path / "fake-skills"

    def skill_path(target):
        if target == "codex":
            return codex_home / "skills"
        if target == "fake":
            return fake_skill_dir
        return None

    cfg.skill_path = skill_path
    skill = tmp_path / "pkg" / "skills" / "example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: example\n---\n")
    deployer = nexus.Deployer(cfg)

    deployer.deploy_skills([{
        "name": "pkg",
        "targets": ["fake"],
        "skills": [{"name": "example", "path": str(skill)}],
    }])

    assert not (codex_home / "skills" / "example").exists()
    assert (fake_skill_dir / "example").is_symlink()

    stale = codex_home / "skills" / "example"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.symlink_to(skill)
    prev_lock = {"packages": [{
        "name": "pkg",
        "discovered": {"skills": ["example"]},
        "deployed_to": ["codex", "fake"],
    }]}

    deployer.prune_skills([{
        "name": "pkg",
        "targets": ["fake"],
        "skills": [{"name": "example", "path": str(skill)}],
    }], prev_lock)

    assert not stale.exists()
    assert (fake_skill_dir / "example").is_symlink()


def test_skill_without_overrides_links_to_source_skill(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    deployer = nexus.Deployer(cfg)

    deployer.deploy_skills([{
        "name": "pkg",
        "path": str(tmp_path / "cache" / "pkg"),
        "skills": [{"name": "example", "path": str(skill)}],
    }])

    link = cfg.skill_path("codex") / "example"
    assert link.is_symlink()
    assert link.resolve() == skill
    assert not cfg.generated_skill_path("codex", "example").exists()


def test_codex_agents_openai_override_creates_generated_skill_dir(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    deployer = nexus.Deployer(cfg)

    deployer.deploy_skills([_overlay_pkg(skill, targets=["codex"])])

    generated = cfg.generated_skill_path("codex", "example")
    link = cfg.skill_path("codex") / "example"
    assert generated.is_dir()
    assert (generated / "SKILL.md").is_file()
    assert link.is_symlink()
    assert link.resolve() == generated

    metadata = nexus.Deployer._load_yaml_mapping(generated / "agents" / "openai.yaml")
    assert metadata["policy"]["allow_implicit_invocation"] is False


def test_codex_only_overlay_leaves_other_targets_linked_to_source(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["codex", "fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    deployer = nexus.Deployer(cfg)

    deployer.deploy_skills([_overlay_pkg(skill, targets=["codex"])])

    codex_link = cfg.skill_path("codex") / "example"
    fake_link = cfg.skill_path("fake") / "example"
    assert codex_link.resolve() == cfg.generated_skill_path("codex", "example")
    assert fake_link.resolve() == skill


def test_agents_openai_override_merges_existing_metadata(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    agents_dir = skill / "agents"
    agents_dir.mkdir()
    (agents_dir / "openai.yaml").write_text(
        "interface:\n"
        "  display_name: Existing Name\n"
        "  extra: keep-me\n"
        "policy:\n"
        "  existing: true\n"
    )
    deployer = nexus.Deployer(cfg)
    pkg = _overlay_pkg(skill, targets=["codex"])
    pkg["skill_overrides"]["example"]["agents_openai"]["interface"] = {
        "short_description": "Explicit example."
    }

    deployer.deploy_skills([pkg])

    metadata = nexus.Deployer._load_yaml_mapping(
        cfg.generated_skill_path("codex", "example") / "agents" / "openai.yaml"
    )
    assert metadata == {
        "interface": {
            "display_name": "Existing Name",
            "extra": "keep-me",
            "short_description": "Explicit example.",
        },
        "policy": {
            "allow_implicit_invocation": False,
            "existing": True,
        },
    }


def test_override_targets_cannot_add_package_excluded_target(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["codex", "fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    deployer = nexus.Deployer(cfg)
    pkg = _overlay_pkg(skill, targets=["codex"])
    pkg["targets"] = ["fake"]

    deployer.deploy_skills([pkg])

    assert not (cfg.skill_path("codex") / "example").exists()
    assert (cfg.skill_path("fake") / "example").resolve() == skill
    assert not cfg.generated_skill_path("codex", "example").exists()


def test_generate_lockfile_records_skill_overlays(tmp_path):
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    lock = nexus.generate_lockfile([_overlay_pkg(skill, targets=["codex"])], {}, ["codex"], tmp_path)

    assert lock["packages"][0]["overlays"] == [{
        "skill": "example",
        "target": "codex",
        "type": "agents_openai",
        "path": str(tmp_path / ".nexus" / "generated" / "codex" / "skills" / "example"),
    }]


def test_dry_run_mentions_skill_overlays(tmp_path, capsys):
    pkg = tmp_path / "pkg"
    _write_skill(pkg / "skills" / "example", "example")
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.packages = [{
        "path": "pkg",
        "skill_overrides": {
            "example": {
                "targets": ["codex"],
                "agents_openai": {
                    "policy": {"allow_implicit_invocation": False},
                },
            },
        },
    }]
    cfg.data = {"packages": cfg.packages, "mcps": [], "targets": ["codex"]}

    nexus.cmd_sync(cfg, SimpleNamespace(all=False, dry_run=True, yes=False))

    captured = capsys.readouterr()
    assert "skill: example -> codex (overlay: agents_openai)" in captured.err


def test_doctor_validates_generated_skill_overlays(tmp_path, capsys):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    generated = cfg.generated_skill_path("codex", "example")
    generated.mkdir(parents=True)
    (generated / "SKILL.md").write_text("---\nname: example\n---\n")
    (generated / "agents").mkdir()
    (generated / "agents" / "openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n"
    )
    cfg.skill_path("codex").mkdir(parents=True)
    (cfg.skill_path("codex") / "example").symlink_to(generated)
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{
            "name": "pkg",
            "discovered": {"skills": ["example"]},
            "deployed_to": ["codex"],
            "overlays": [{
                "skill": "example",
                "target": "codex",
                "type": "agents_openai",
                "path": str(generated),
            }],
        }],
        "mcps": {"managed": []},
    }, cfg.lockfile_path)

    nexus.cmd_doctor(cfg, SimpleNamespace())

    captured = capsys.readouterr()
    assert "Skill overlays: 1 generated" in captured.err


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


def _write_skill(path: Path, name: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n# {name}\n")
    return path


def _overlay_pkg(skill: Path, targets: list[str] | None = None) -> dict:
    override = {
        "agents_openai": {
            "policy": {"allow_implicit_invocation": False},
        },
    }
    if targets is not None:
        override["targets"] = targets
    return {
        "name": "pkg",
        "path": str(skill.parents[1]),
        "skills": [{"name": "example", "path": str(skill)}],
        "skill_overrides": {"example": override},
    }


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
        self.nexus_dir = repo_dir / ".nexus"
        self.cache_dir = self.nexus_dir / "cache"
        self.lockfile_path = repo_dir / "nexus.lock.yml"
        self.yml_path = repo_dir / "nexus.yml"
        self.targets = ["codex"]
        self.packages = []
        self.data = {"packages": [], "mcps": [], "targets": ["codex"]}
        self._codex_home = codex_home

    def skill_path(self, target: str) -> Path | None:
        if target == "codex":
            return self._codex_home / "skills"
        return self.repo_dir / f"{target}-skills"

    def generated_skill_path(self, target: str, skill_name: str) -> Path:
        return self.nexus_dir / "generated" / target / "skills" / skill_name

    def codex_hooks_path(self) -> Path:
        return self._codex_home / "hooks.json"

    def mcp_path(self, _target: str) -> Path | None:
        return None

    def mcp_format(self, _target: str) -> str:
        return "mcp_servers_json"

    def load_lockfile(self):
        if not self.lockfile_path.exists():
            return None
        import yaml

        with open(self.lockfile_path) as f:
            return yaml.safe_load(f)

    @property
    def mcps(self):
        return []

    @property
    def optional_mcps(self):
        return []
