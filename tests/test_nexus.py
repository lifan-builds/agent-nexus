import importlib.util
import json
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nexus", ROOT / "nexus.py")
nexus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nexus)


def _run_installer(bin_dir: Path, *args: str):
    env = os.environ.copy()
    env["NEXUS_BIN_DIR"] = str(bin_dir)
    return subprocess.run(
        [str(ROOT / "scripts" / "install-local.sh"), *args],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def _cli_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    shutil.copy(ROOT / "nexus.py", checkout / "nexus.py")
    shutil.copy(ROOT / "nexus.example.yml", checkout / "nexus.example.yml")
    return checkout


def _run_cli(checkout: Path, *args: str, home: Path, codex_home: Path):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CODEX_HOME"] = str(codex_home)
    return subprocess.run(
        [sys.executable, str(checkout / "nexus.py"), *args],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_install_local_creates_reversible_wrapper_symlink(tmp_path):
    bin_dir = tmp_path / "bin"

    result = _run_installer(bin_dir)

    link_path = bin_dir / "nexus"
    assert result.returncode == 0, result.stderr
    assert link_path.is_symlink()
    assert os.readlink(link_path) == str(ROOT / "nexus.py")
    assert "scripts/install-local.sh --uninstall" in result.stdout

    uninstall = _run_installer(bin_dir, "--uninstall")

    assert uninstall.returncode == 0, uninstall.stderr
    assert not link_path.exists()


def test_install_local_refuses_to_replace_user_owned_command(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    link_path = bin_dir / "nexus"
    link_path.write_text("#!/bin/sh\n")

    result = _run_installer(bin_dir)

    assert result.returncode == 1
    assert link_path.read_text() == "#!/bin/sh\n"
    assert "Refusing to replace existing non-symlink file" in result.stderr


def test_install_local_refuses_to_replace_other_symlink_without_force(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    other = tmp_path / "other-nexus"
    other.write_text("#!/bin/sh\n")
    link_path = bin_dir / "nexus"
    link_path.symlink_to(other)

    result = _run_installer(bin_dir)

    assert result.returncode == 1
    assert os.readlink(link_path) == str(other)
    assert "Refusing to replace existing symlink" in result.stderr


def test_install_local_force_replaces_existing_command(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    link_path = bin_dir / "nexus"
    link_path.write_text("#!/bin/sh\n")

    result = _run_installer(bin_dir, "--force")

    assert result.returncode == 0, result.stderr
    assert link_path.is_symlink()
    assert os.readlink(link_path) == str(ROOT / "nexus.py")


def test_cli_smoke_init_audit_sync_dry_run_and_doctor_use_temp_home(tmp_path):
    checkout = _cli_checkout(tmp_path)
    home = tmp_path / "home"
    codex_home = tmp_path / "codex-home"

    init = _run_cli(checkout, "init", home=home, codex_home=codex_home)

    assert init.returncode == 0, init.stderr
    assert (checkout / "nexus.personal.yml").exists()

    (checkout / "nexus.personal.yml").write_text(
        "name: smoke\n"
        "packages: []\n"
        "mcps: []\n"
    )

    audit = _run_cli(checkout, "audit", "--json", "--redact-home", home=home, codex_home=codex_home)
    dry_run = _run_cli(checkout, "sync", "--dry-run", home=home, codex_home=codex_home)
    doctor = _run_cli(checkout, "doctor", home=home, codex_home=codex_home)

    assert audit.returncode == 0, audit.stderr
    assert [target["name"] for target in json.loads(audit.stdout)["targets"]] == nexus.CORE_DEFAULT_TARGETS
    assert str(home) not in audit.stdout
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Dry run - no target configs or lockfiles written." in dry_run.stderr
    assert not (checkout / "nexus.lock.yml").exists()
    assert doctor.returncode == 0, doctor.stderr
    assert "nexus doctor" in doctor.stderr
    assert not (home / ".claude").exists()
    assert not (home / ".cursor").exists()
    assert not (home / ".gemini").exists()
    assert not (codex_home / "hooks.json").exists()


def test_config_defaults_to_core_targets(tmp_path):
    (tmp_path / "nexus.yml").write_text("name: defaults\npackages: []\nmcps: []\n")

    cfg = nexus.Config(tmp_path)

    assert cfg.targets == nexus.CORE_DEFAULT_TARGETS


def test_config_wildcard_targets_expand_to_all_skill_presets(tmp_path):
    (tmp_path / "nexus.yml").write_text("name: defaults\ntargets: ['*']\npackages: []\nmcps: []\n")

    cfg = nexus.Config(tmp_path)

    assert cfg.targets == nexus.skill_target_names()
    assert "hermes" in cfg.targets
    assert "qwen-code" in cfg.targets
    assert "crush" in cfg.targets


def test_config_canonicalizes_target_aliases(tmp_path):
    (tmp_path / "nexus.yml").write_text(
        "name: aliases\n"
        "targets:\n"
        "  - claude-code\n"
        "  - openai-codex\n"
        "  - Google Antigravity\n"
        "  - cursor\n"
        "  - claude code\n"
    )

    cfg = nexus.Config(tmp_path)

    assert cfg.targets == ["claude", "codex", "antigravity", "cursor"]


def test_broad_target_presets_have_expected_skill_paths(tmp_path):
    (tmp_path / "nexus.yml").write_text("name: paths\npackages: []\nmcps: []\n")
    cfg = nexus.Config(tmp_path)

    assert cfg.skill_path("hermes") == Path.home() / ".hermes" / "skills"
    assert cfg.skill_path("qwen-code") == tmp_path / ".qwen" / "skills"
    assert cfg.skill_path("crush") == tmp_path / ".crush" / "skills"
    assert cfg.skill_path("opencode") == Path.home() / ".config" / "opencode" / "skills"
    assert cfg.skill_path("windsurf") == Path.home() / ".codeium" / "windsurf" / "skills"
    assert cfg.mcp_path("hermes") is None
    assert cfg.mcp_path("qwen-code") is None
    assert nexus.TARGET_REGISTRY["hermes"]["status"]["mcp"] == "planned"


def test_broad_target_aliases_canonicalize():
    assert nexus.canonical_targets(["hermes-agent", "qwen", "roo-code", "copilot", "kilo", "open-code"]) == [
        "hermes",
        "qwen-code",
        "roo",
        "github-copilot",
        "kilo-code",
        "opencode",
    ]


def test_dashboard_model_uses_all_default_targets(tmp_path):
    (tmp_path / "nexus.yml").write_text("name: defaults\npackages: []\nmcps: []\n")
    cfg = nexus.Config(tmp_path)

    model = nexus.build_dashboard_model(cfg)

    assert model["deployment"]["default_to_all"] is False
    assert model["deployment"]["global_targets"] == nexus.CORE_DEFAULT_TARGETS
    assert model["deployment"]["available_targets"] == list(nexus.TARGET_REGISTRY)
    assert model["summary"]["targets"] == len(nexus.CORE_DEFAULT_TARGETS)
    assert "codex" in model["deployment"]["global_targets"]
    assert "hermes" in model["deployment"]["available_targets"]


def test_cli_smoke_init_refuses_to_overwrite_existing_manifest(tmp_path):
    checkout = _cli_checkout(tmp_path)
    home = tmp_path / "home"
    codex_home = tmp_path / "codex-home"

    first = _run_cli(checkout, "init", home=home, codex_home=codex_home)
    second = _run_cli(checkout, "init", home=home, codex_home=codex_home)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    assert "already exists" in second.stderr


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


def test_claude_mcp_sync_uses_global_mcp_json_shape(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["claude"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    mcp_path = tmp_path / ".claude" / ".mcp.json"

    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "mcp_servers_json"
    mcp_path.parent.mkdir(parents=True)
    mcp_path.write_text(json.dumps({
        "mcpServers": {
            "user-only": {"command": "custom"},
        },
    }))

    deployer = nexus.Deployer(cfg)
    deployer.sync_mcps([{
        "name": "chrome-devtools",
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"],
    }])

    data = json.loads(mcp_path.read_text())
    assert "projects" not in data
    assert data["mcpServers"]["user-only"] == {"command": "custom"}
    assert data["mcpServers"]["chrome-devtools"]["args"] == [
        "-y",
        "chrome-devtools-mcp@latest",
        "--autoConnect",
    ]


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


def test_json_mcp_sync_adds_stdio_server_to_empty_config(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    mcp_path = tmp_path / "nested" / "mcp.json"
    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "mcp_servers_json"

    nexus.Deployer(cfg).sync_mcps([{
        "name": "docs",
        "command": "uvx",
        "args": ["mcp-docs"],
    }])

    assert json.loads(mcp_path.read_text()) == {
        "mcpServers": {
            "docs": {
                "type": "stdio",
                "command": "uvx",
                "args": ["mcp-docs"],
                "env": {"PATH": nexus.STANDARD_PATH},
            }
        }
    }
    assert mcp_path.read_text().endswith("\n")
    assert '\n  "mcpServers": {' in mcp_path.read_text()


def test_json_mcp_prune_removes_only_stale_managed_servers(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    mcp_path = tmp_path / "mcp.json"
    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "mcp_servers_json"
    mcp_path.write_text(json.dumps({
        "mcpServers": {
            "keep": {"command": "uvx"},
            "stale": {"command": "uvx"},
            "user": {"command": "custom"},
        }
    }))

    nexus.Deployer(cfg).prune_mcps(
        {"keep"},
        {"mcps": {"managed": [{"name": "keep"}, {"name": "stale"}]}},
    )

    servers = json.loads(mcp_path.read_text())["mcpServers"]
    assert sorted(servers) == ["keep", "user"]


def test_prune_does_not_remove_skipped_optional_mcp(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["fake"]
    cfg.data = {"packages": [], "mcps": [], "targets": cfg.targets}
    mcp_path = tmp_path / "mcp.json"
    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "mcp_servers_json"
    mcp_path.write_text(json.dumps({
        "mcpServers": {
            "always": {"command": "uvx"},
            "github": {"command": "npx"},
        }
    }))

    nexus.Deployer(cfg).prune_mcps(
        {"always"},
        {"mcps": {"managed": [{"name": "always"}]}},
    )

    assert sorted(json.loads(mcp_path.read_text())["mcpServers"]) == ["always", "github"]


def test_codex_mcp_sync_preserves_content_before_and_after_managed_block(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.yml_path = tmp_path / "nexus.personal.yml"
    mcp_path = tmp_path / "config.toml"
    mcp_path.write_text(
        '[profile.default]\n'
        'model = "gpt-5"\n\n'
        '# BEGIN NEXUS MANAGED MCP SERVERS\n'
        '[mcp_servers."old"]\n'
        'command = "old"\n'
        '# END NEXUS MANAGED MCP SERVERS\n\n'
        '[tools]\n'
        'enabled = true\n'
    )

    nexus.Deployer(cfg)._sync_mcps_for_codex([
        {"name": "docs", "command": "uvx", "args": ["mcp-docs"]}
    ], mcp_path)

    output = mcp_path.read_text()
    assert '[profile.default]\nmodel = "gpt-5"' in output
    assert '[tools]\nenabled = true' in output
    assert '[mcp_servers."docs"]' in output
    assert 'old' not in output


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


def test_package_targets_canonicalize_aliases_and_preserve_constraints():
    pkg = {"targets": ["openai-codex", "claude-code", "openai codex", "hermes-agent"]}

    assert nexus.package_targets(pkg, ["claude", "codex", "hermes"]) == ["codex", "claude", "hermes"]
    assert nexus.package_targets(pkg, ["claude"]) == ["claude"]
    assert nexus.package_targets({"targets": ["openai-codex"]}, ["claude"]) == []
    assert nexus.package_targets({"targets": ["*"]}, ["claude", "hermes"]) == ["claude", "hermes"]


def test_overlay_targets_canonicalize_aliases(tmp_path):
    skill = tmp_path / "pkg" / "skills" / "example"
    _write_skill(skill, "example")
    pkg = _overlay_pkg(skill, ["openai-codex"])

    assert nexus.overlay_targets(pkg, "example", ["codex", "claude"]) == ["codex"]
    assert nexus.skill_overlays(pkg, "example", ["codex", "claude"]) == [
        {"skill": "example", "target": "codex", "type": "agents_openai"},
    ]


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


def test_skill_frontmatter_override_creates_generated_skill_dir(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    deployer = nexus.Deployer(cfg)
    pkg = _overlay_pkg(skill, targets=["codex"])
    pkg["skill_overrides"]["example"] = {
        "targets": ["codex"],
        "skill_frontmatter": {"disable-model-invocation": True},
    }

    deployer.deploy_skills([pkg])

    generated = cfg.generated_skill_path("codex", "example")
    link = cfg.skill_path("codex") / "example"
    assert link.resolve() == generated
    assert "disable-model-invocation: true" in (generated / "SKILL.md").read_text()


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


def test_generate_lockfile_records_package_source_metadata(tmp_path):
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    pkg = {
        "name": "pkg",
        "path": str(tmp_path / ".nexus" / "cache" / "github.com" / "org" / "pkg" / "abc123"),
        "skills": [{"name": "example", "path": str(skill)}],
        "hooks_codex": str(tmp_path / "hooks-codex.json"),
        "source": {
            "type": "github",
            "repo": "org/pkg",
            "source_url": "https://github.com/org/pkg",
            "requested_ref": "main",
            "resolved_commit": "abc123",
            "cache_path": str(tmp_path / ".nexus" / "cache" / "github.com" / "org" / "pkg" / "abc123"),
            "sparse_paths": ["skills/example"],
        },
    }

    lock = nexus.generate_lockfile([pkg], {}, ["codex"], tmp_path, manifest_path=tmp_path / "nexus.personal.yml")
    entry = lock["packages"][0]

    assert lock["manifest_path"] == str(tmp_path / "nexus.personal.yml")
    assert entry["cache_path"] == pkg["path"]
    assert entry["source"] == pkg["source"]
    assert entry["hook_deployments"] == ["codex"]
    assert "floating ref 'main'" in entry["warnings"][0]


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


def test_cursor_hook_merge_deduplicates_normalized_entries(tmp_path):
    first = tmp_path / "pkg1" / "hooks" / "hooks-cursor.json"
    second = tmp_path / "pkg2" / "hooks" / "hooks-cursor.json"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text(json.dumps({
        "hooks": {
            "BeforeSubmit": [
                {"_nexus": {"package": "one"}, "command": "echo shared"},
            ]
        }
    }))
    second.write_text(json.dumps({
        "hooks": {
            "BeforeSubmit": [
                {"_nexus": {"package": "two"}, "command": "echo shared"},
                {"command": "echo unique"},
            ]
        }
    }))

    merged = nexus.Deployer._merge_hooks([first, second])

    assert merged["hooks"]["BeforeSubmit"] == [
        {"_nexus": {"package": "one"}, "command": "echo shared"},
        {"command": "echo unique"},
    ]


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
    assert "Hook review - executable hook commands to be installed" in captured.err
    assert f'node "{pkg}/hook.js" --nexus-package pkg' in captured.err
    assert "hooks: pkg -> codex" in captured.err
    assert not (codex_home / "hooks.json").exists()


def test_dashboard_model_includes_inventory_and_redacts_mcp_env(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    cfg.data = {
        "packages": [{"path": "cache/pkg"}],
        "mcps": [{
            "name": "secret-mcp",
            "command": "npx",
            "args": ["-y", "secret-mcp"],
            "env": {"API_TOKEN": "supersecret"},
        }],
        "optional_mcps": [],
        "targets": ["codex"],
    }
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{
            "name": "pkg",
            "path": str(skill.parents[1]),
            "discovered": {"skills": ["example"]},
            "deployed_to": ["codex"],
        }],
        "mcps": {"managed": [{"name": "secret-mcp"}]},
    }, cfg.lockfile_path)

    model = nexus.build_dashboard_model(cfg)
    encoded = json.dumps(model)

    assert model["summary"]["packages"] == 1
    assert model["summary"]["skills"] == 1
    assert model["summary"]["implicit_skills"] == 1
    assert model["deployment"]["global_targets"] == ["codex"]
    assert model["packages"][0]["uses_global_targets"] is True
    assert "ref" not in model["packages"][0]
    assert model["mcps"][0]["env_keys"] == ["API_TOKEN"]
    assert model["mcps"][0]["token_consumption"]["static_tokens"] > 0
    assert "supersecret" not in encoded
    assert model["skills"][0]["static_tokens"] > 0


def test_dashboard_model_handles_missing_lockfile(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}

    model = nexus.build_dashboard_model(cfg)

    assert model["meta"]["lockfile_exists"] is False
    assert any("missing" in warning for warning in model["warnings"])


def test_dashboard_model_includes_disabled_package_skills_from_cache(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    enabled = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "enabled", "enabled")
    _write_skill(tmp_path / "cache" / "pkg" / "skills" / "disabled", "disabled")
    cfg.data = {"packages": [{"path": "cache/pkg", "skills": ["enabled"]}], "mcps": [], "targets": ["codex"]}
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{
            "name": "pkg",
            "path": str(enabled.parents[1]),
            "discovered": {"skills": ["enabled"]},
            "deployed_to": ["codex"],
        }],
    }, cfg.lockfile_path)

    model = nexus.build_dashboard_model(cfg)
    inventory = {skill["name"]: skill for skill in model["packages"][0]["skill_inventory"]}

    assert set(inventory) == {"enabled", "disabled"}
    assert inventory["enabled"]["enabled"] is True
    assert inventory["disabled"]["enabled"] is False
    assert inventory["disabled"]["deployed"] is False
    assert model["summary"]["available_package_skills"] == 2
    assert model["summary"]["disabled_package_skills"] == 1



def test_dashboard_model_marks_manual_only_from_skill_overrides(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "frontmatter-only", "frontmatter-only")
    _write_skill(tmp_path / "cache" / "pkg" / "skills" / "agents-only", "agents-only")
    cfg.data = {
        "packages": [{
            "path": "cache/pkg",
            "skill_overrides": {
                "frontmatter-only": {"skill_frontmatter": {"disable-model-invocation": True}},
                "agents-only": {"agents_openai": {"policy": {"allow_implicit_invocation": False}}},
            },
        }],
        "mcps": [],
        "targets": ["codex"],
    }
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{
            "name": "pkg",
            "path": str(skill.parents[1]),
            "discovered": {"skills": ["frontmatter-only", "agents-only"]},
            "deployed_to": ["codex"],
        }],
    }, cfg.lockfile_path)

    model = nexus.build_dashboard_model(cfg)
    inventory = {skill["name"]: skill for skill in model["packages"][0]["skill_inventory"]}

    assert inventory["frontmatter-only"]["manual_only"] is True
    assert inventory["agents-only"]["manual_only"] is True
    assert model["summary"]["manual_only_package_skills"] == 2



def test_dashboard_skill_policy_save_updates_allowlist_and_preserves_secrets(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    first = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "first", "first")
    _write_skill(tmp_path / "cache" / "pkg" / "skills" / "second", "second")
    cfg.yml_path.write_text(
        "targets: [codex]\n"
        "packages:\n"
        "  - path: cache/pkg\n"
        "mcps:\n"
        "  - name: secret\n"
        "    command: npx\n"
        "    env:\n"
        "      TOKEN: keep-me\n"
    )
    cfg._data = None
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{"name": "pkg", "path": str(first.parents[1]), "discovered": {"skills": ["first"]}}],
    }, cfg.lockfile_path)

    result = nexus.update_manifest_package_skill_policy(cfg, {
        "package_index": 0,
        "package": "pkg",
        "skills": [
            {"name": "first", "enabled": True, "manual_only": False},
            {"name": "second", "enabled": False, "manual_only": False},
        ],
    })
    saved = nexus.parse_manifest_text(cfg.yml_path.read_text())

    assert result["enabled_skills"] == ["first"]
    assert saved["packages"][0]["skills"] == ["first"]
    assert saved["mcps"][0]["env"]["TOKEN"] == "keep-me"



def test_dashboard_skill_policy_save_disables_all_or_removes_allowlist(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    first = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "first", "first")
    _write_skill(tmp_path / "cache" / "pkg" / "skills" / "second", "second")
    cfg.yml_path.write_text("targets: [codex]\npackages:\n  - path: cache/pkg\n    skills: [first]\n")
    cfg._data = None
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{"name": "pkg", "path": str(first.parents[1]), "discovered": {"skills": ["first"]}}],
    }, cfg.lockfile_path)

    nexus.update_manifest_package_skill_policy(cfg, {
        "package_index": 0,
        "package": "pkg",
        "skills": [
            {"name": "first", "enabled": False, "manual_only": False},
            {"name": "second", "enabled": False, "manual_only": False},
        ],
    })
    assert nexus.parse_manifest_text(cfg.yml_path.read_text())["packages"][0]["skills"] == []

    cfg._data = None
    nexus.update_manifest_package_skill_policy(cfg, {
        "package_index": 0,
        "package": "pkg",
        "skills": [
            {"name": "first", "enabled": True, "manual_only": False},
            {"name": "second", "enabled": True, "manual_only": False},
        ],
    })
    assert "skills" not in nexus.parse_manifest_text(cfg.yml_path.read_text())["packages"][0]



def test_dashboard_skill_policy_save_sets_and_clears_manual_only(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    skill = _write_skill(tmp_path / "cache" / "pkg" / "skills" / "example", "example")
    cfg.yml_path.write_text(
        "targets: [codex]\n"
        "packages:\n"
        "  - path: cache/pkg\n"
        "    skill_overrides:\n"
        "      example:\n"
        "        targets: [codex]\n"
        "        cost:\n"
        "          estimated_tokens_per_call: 10\n"
        "        agents_openai:\n"
        "          interface:\n"
        "            display_name: Keep Me\n"
    )
    cfg._data = None
    nexus.write_lockfile({
        "lockfile_version": 1,
        "packages": [{"name": "pkg", "path": str(skill.parents[1]), "discovered": {"skills": ["example"]}}],
    }, cfg.lockfile_path)

    nexus.update_manifest_package_skill_policy(cfg, {
        "package_index": 0,
        "package": "pkg",
        "skills": [{"name": "example", "enabled": True, "manual_only": True}],
    })
    override = nexus.parse_manifest_text(cfg.yml_path.read_text())["packages"][0]["skill_overrides"]["example"]
    assert override["skill_frontmatter"]["disable-model-invocation"] is True
    assert override["agents_openai"]["policy"]["allow_implicit_invocation"] is False
    assert override["agents_openai"]["interface"]["display_name"] == "Keep Me"
    assert override["cost"]["estimated_tokens_per_call"] == 10

    cfg._data = None
    nexus.update_manifest_package_skill_policy(cfg, {
        "package_index": 0,
        "package": "pkg",
        "skills": [{"name": "example", "enabled": True, "manual_only": False}],
    })
    override = nexus.parse_manifest_text(cfg.yml_path.read_text())["packages"][0]["skill_overrides"]["example"]
    assert "skill_frontmatter" not in override
    assert "policy" not in override["agents_openai"]
    assert override["agents_openai"]["interface"]["display_name"] == "Keep Me"
    assert override["targets"] == ["codex"]



def test_dashboard_html_includes_safety_and_api_hooks():
    html = nexus.render_dashboard_html()

    assert "/api/state" in html
    assert "/api/sync/deploy" in html
    assert "/api/packages/skills/save" in html
    assert "data-sync-action=\"dry-run\"" in html
    assert "Type deploy" in html
    assert "Manual only" in html
    assert "localhost only" in html
    assert "redacted secrets" in html
    assert "confirmed deploys" in html


def test_dashboard_manifest_validation_and_atomic_save(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    text = "name: edited\ntargets: [codex]\npackages: []\nmcps: []\n"

    assert nexus.validate_dashboard_manifest({"packages": "bad"})
    nexus.write_manifest_atomically(cfg, text)

    assert cfg.yml_path.read_text() == text
    assert nexus.parse_manifest_text(cfg.yml_path.read_text())["name"] == "edited"


def test_dashboard_redacted_manifest_text_hides_and_restores_secret_values(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.yml_path.write_text(
        "# keep this comment\n"
        "targets:\n"
        "  - codex\n"
        "mcps:\n"
        "  - name: nitan\n"
        "    command: npx\n"
        "    env:\n"
        "      PASSWORD: secret-value\n"
    )

    text = nexus.load_redacted_manifest_text(cfg)

    assert "# keep this comment" in text
    assert "secret-value" not in text
    assert "PASSWORD: REDACTED_BY_NEXUS_DASHBOARD" in text

    edited = text.replace("  - codex\n", "  - codex\n  - claude\n")
    nexus.update_manifest_from_dashboard(cfg, {"text": edited})
    saved = nexus.parse_manifest_text(cfg.yml_path.read_text())

    assert saved["targets"] == ["codex", "claude"]
    assert saved["mcps"][0]["env"]["PASSWORD"] == "secret-value"


def test_dashboard_target_policy_save_updates_targets_only(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.yml_path.write_text(
        "name: local\n"
        "targets:\n"
        "  - codex  # ~/.codex/skills\n"
        "packages:\n"
        "  - path: pkg\n"
    )

    result = nexus.update_manifest_targets(cfg, ["claude-code", "openai-codex", "cursor"])
    saved = cfg.yml_path.read_text()
    data = nexus.parse_manifest_text(saved)

    assert result["ok"] is True
    assert result["targets"] == ["claude", "codex", "cursor"]
    assert data["targets"] == ["claude", "codex", "cursor"]
    assert data["packages"] == [{"path": "pkg"}]


def test_cmd_dashboard_json_outputs_valid_json(tmp_path, capsys):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}

    nexus.cmd_dashboard(cfg, SimpleNamespace(json=True))

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["meta"]["nexus_version"] == nexus.NEXUS_VERSION


def test_dashboard_dry_run_does_not_require_confirmation(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}

    result = nexus.run_dashboard_sync_action(cfg, "dry-run", {})

    assert result["ok"] is True
    assert "Dry run" in result["stderr"]


def test_dashboard_deploy_requires_confirmation(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    result = nexus.run_dashboard_sync_action(cfg, "deploy", {"confirm": "nope"})

    assert result["ok"] is False
    assert "confirm" in result["error"]


def test_audit_empty_machine_uses_all_targets_without_manifest(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.yml_path = tmp_path / "missing.yml"
    cfg.lockfile_path = tmp_path / "missing.lock.yml"
    cfg.targets = ["codex"]
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}

    model = nexus.build_audit_model(cfg, redact_home=True)

    assert [target["name"] for target in model["targets"]] == ["claude", "cursor", "antigravity", "codex"]
    assert model["meta"]["manifest_exists"] is False
    assert model["meta"]["lockfile_exists"] is False


def test_audit_json_redacts_env_values_and_classifies_mcp_servers(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["claude"]
    cfg.data = {"packages": [], "mcps": [], "targets": ["claude"]}
    cfg.yml_path.write_text("targets: [claude]\n")
    mcp_path = tmp_path / ".claude" / ".mcp.json"
    mcp_path.parent.mkdir()
    mcp_path.write_text(json.dumps({
        "mcpServers": {
            "managed": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "managed"],
                "env": {"TOKEN": "secret-value"},
            },
            "user": {"type": "sse", "url": "https://example.com/mcp"},
        },
    }))
    cfg.mcp_path = lambda _target: mcp_path
    nexus.write_lockfile({"mcps": {"managed": [{"name": "managed"}]}}, cfg.lockfile_path)

    model = nexus.build_audit_model(cfg)
    encoded = json.dumps(model)
    servers = {server["name"]: server for server in model["targets"][0]["mcp"]["servers"]}

    assert model["targets"][0]["mcp"]["managed"] == ["managed"]
    assert model["targets"][0]["mcp"]["unmanaged"] == ["user"]
    assert servers["managed"]["env_keys"] == ["TOKEN"]
    assert "secret-value" not in encoded


def test_audit_codex_managed_block_and_hooks(tmp_path):
    codex_home = tmp_path / "codex-home"
    cfg = _fake_cfg(tmp_path, codex_home)
    cfg.targets = ["codex"]
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}
    cfg.yml_path.write_text("targets: [codex]\n")
    mcp_path = tmp_path / "config.toml"
    mcp_path.write_text(
        '# BEGIN NEXUS MANAGED MCP SERVERS\n'
        '[mcp_servers."managed"]\n'
        'command = "npx"\n'
        'args = ["-y", "managed"]\n'
        '# END NEXUS MANAGED MCP SERVERS\n\n'
        '[mcp_servers."user"]\n'
        'url = "https://example.com/mcp"\n'
    )
    cfg.mcp_path = lambda _target: mcp_path
    cfg.mcp_format = lambda _target: "codex_toml"
    hooks_path = codex_home / "hooks.json"
    hooks_path.parent.mkdir()
    hooks_path.write_text(json.dumps({
        "hooks": {
            "SessionStart": [
                {"hooks": [
                    {"type": "command", "command": "node hook.js --nexus-package pkg"},
                    {"type": "command", "command": "echo user"},
                ]}
            ]
        }
    }))

    target = nexus.build_audit_model(cfg)["targets"][0]

    assert target["mcp"]["managed"] == ["managed"]
    assert target["mcp"]["unmanaged"] == ["user"]
    assert target["hooks"]["managed"] == 1
    assert target["hooks"]["unmanaged"] == 1


def test_audit_skill_symlink_and_unmanaged_detection(tmp_path):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")
    cfg.targets = ["codex"]
    cfg.data = {"packages": [], "mcps": [], "targets": ["codex"]}
    cfg.yml_path.write_text("targets: [codex]\n")
    source = _write_skill(tmp_path / ".nexus" / "cache" / "github.com" / "org" / "pkg" / "abc" / "skills" / "managed", "managed")
    skill_dir = cfg.skill_path("codex")
    skill_dir.mkdir(parents=True)
    (skill_dir / "managed").symlink_to(source)
    (skill_dir / "stale").symlink_to(tmp_path / "missing")
    (skill_dir / "user-skill").mkdir()

    skills = nexus.build_audit_model(cfg)["targets"][0]["skills"]

    assert skills["nexus_symlinks"] == ["managed"]
    assert skills["stale_symlinks"] == ["stale"]
    assert skills["unmanaged_dirs"] == ["user-skill"]


def test_cmd_audit_json_outputs_valid_json(tmp_path, capsys):
    cfg = _fake_cfg(tmp_path, tmp_path / "codex-home")

    nexus.cmd_audit(cfg, SimpleNamespace(json=True, target="codex", redact_home=True))

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["targets"][0]["name"] == "codex"
    assert "secret" not in captured.out.lower()


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
