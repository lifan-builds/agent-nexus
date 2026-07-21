#!/usr/bin/env python3
"""nexus — Agent environment manager.

Manages skills, hooks, and MCP servers across multiple AI IDEs from a nexus manifest.
Single-file, single-dependency (PyYAML) replacement for nexus.sh.
"""

import argparse
import contextlib
import difflib
import html
import io
import json
import hashlib
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

NEXUS_VERSION = "0.2.0"


class NexusError(Exception):
    """Base error for user-facing Nexus failures."""


class ManifestNotFoundError(NexusError):
    """Raised when an operation requires a Nexus manifest."""


class ManifestValidationError(NexusError):
    """Raised when a Nexus manifest is invalid."""


SAFE_STARTER_TEMPLATE = """name: {name}
version: 1.0.0

targets:
  - claude
  - cursor
  - antigravity
  - codex

packages: []
mcps: []
optional_mcps: []
"""

# ---------------------------------------------------------------------------
# Target registry — data-driven, not hardcoded case/switch
# ---------------------------------------------------------------------------
TARGET_REGISTRY = {
    "claude": {
        "display": "Claude Code",
        "skills": Path.home() / ".claude" / "skills",
        "mcp": Path.home() / ".claude.json",
        "mcp_format": "mcp_servers_json",
        "default": True,
        "status": {"skills": "implemented", "mcp": "implemented", "hooks": "implemented"},
    },
    "cursor": {
        "display": "Cursor",
        "skills": Path.home() / ".cursor" / "skills",
        "mcp": Path.home() / ".cursor" / "mcp.json",
        "mcp_format": "mcp_servers_json",
        "default": True,
        "status": {"skills": "implemented", "mcp": "implemented", "hooks": "implemented"},
    },
    "antigravity": {
        "display": "Google Antigravity",
        "skills": Path.home() / ".gemini" / "antigravity" / "skills",
        "mcp": Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
        "mcp_format": "mcp_servers_json",
        "default": True,
        "status": {"skills": "implemented", "mcp": "implemented", "hooks": "unsupported"},
    },
    "codex": {
        "display": "Codex",
        "skills": Path.home() / ".codex" / "skills",
        "mcp": Path.home() / ".codex" / "config.toml",
        "mcp_format": "codex_toml",
        "default": True,
        "status": {"skills": "implemented", "mcp": "implemented", "hooks": "implemented"},
    },
    "adal": {"display": "AdaL", "skills": Path(".adal/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "amp": {"display": "Amp", "skills": Path.home() / ".config" / "agents" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "augment": {"display": "Augment", "skills": Path.home() / ".augment" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "cline": {"display": "Cline", "skills": Path.home() / ".agents" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "codebuddy": {"display": "CodeBuddy", "skills": Path(".codebuddy/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "command-code": {"display": "Command Code", "skills": Path(".commandcode/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "continue": {"display": "Continue", "skills": Path.home() / ".continue" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "crush": {"display": "Crush", "skills": Path(".crush/skills"), "mcp": Path.home() / ".config" / "crush" / "crush.json", "mcp_format": "mcp_servers_json", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "droid": {"display": "Droid", "skills": Path(".factory/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "gemini-cli": {"display": "Gemini CLI", "skills": Path.home() / ".gemini" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "github-copilot": {"display": "GitHub Copilot", "skills": Path.home() / ".copilot" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "goose": {"display": "Goose", "skills": Path.home() / ".config" / "goose" / "skills", "mcp": Path.home() / ".config" / "goose" / "config.yaml", "mcp_format": "yaml_planned", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "hermes": {"display": "Hermes Agent", "skills": Path.home() / ".hermes" / "skills", "mcp": Path.home() / ".hermes" / "config.yaml", "mcp_format": "yaml_planned", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "iflow-cli": {"display": "iFlow CLI", "skills": Path(".iflow/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "junie": {"display": "Junie", "skills": Path.home() / ".junie" / "skills", "mcp": Path.home() / ".junie" / "mcp.json", "mcp_format": "mcp_servers_json", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "kilo-code": {"display": "Kilo Code", "skills": Path(".kilocode/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "kimi-code": {"display": "Kimi Code CLI", "skills": Path(".agents/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "kiro-cli": {"display": "Kiro CLI", "skills": Path.home() / ".kiro" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "kode": {"display": "Kode", "skills": Path(".kode/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "mcpjam": {"display": "MCPJam", "skills": Path(".mcpjam/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "mistral-vibe": {"display": "Mistral Vibe", "skills": Path(".vibe/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "mux": {"display": "Mux", "skills": Path(".mux/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "neovate": {"display": "Neovate", "skills": Path(".neovate/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "openclaw": {"display": "OpenClaw", "skills": Path.home() / ".openclaw" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "opencode": {"display": "OpenCode", "skills": Path.home() / ".config" / "opencode" / "skills", "mcp": Path.home() / ".config" / "opencode" / "opencode.json", "mcp_format": "jsonc_planned", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "openhands": {"display": "OpenHands", "skills": Path.home() / ".openhands" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "pi": {"display": "Pi", "skills": Path(".pi/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "pochi": {"display": "Pochi", "skills": Path(".pochi/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "qoder": {"display": "Qoder", "skills": Path(".qoder/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "qwen-code": {"display": "Qwen Code", "skills": Path(".qwen/skills"), "mcp": Path.home() / ".qwen" / "settings.json", "mcp_format": "mcp_servers_json", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "replit": {"display": "Replit", "skills": Path.home() / ".config" / "agents" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "roo": {"display": "Roo Code", "skills": Path.home() / ".roo" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "trae": {"display": "Trae", "skills": Path.home() / ".trae" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "trae-cn": {"display": "Trae CN", "skills": Path(".trae/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "warp": {"display": "Warp", "skills": Path.home() / ".agents" / "skills", "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
    "windsurf": {"display": "Windsurf", "skills": Path.home() / ".codeium" / "windsurf" / "skills", "mcp": Path.home() / ".codeium" / "windsurf" / "mcp_config.json", "mcp_format": "mcp_servers_json", "status": {"skills": "implemented", "mcp": "planned", "hooks": "unsupported"}},
    "zencoder": {"display": "Zencoder", "skills": Path(".zencoder/skills"), "status": {"skills": "implemented", "mcp": "unsupported", "hooks": "unsupported"}},
}

CORE_DEFAULT_TARGETS = [name for name, entry in TARGET_REGISTRY.items() if entry.get("default")]

TARGET_ALIASES = {
    "claude-code": "claude",
    "google-antigravity": "antigravity",
    "gemini": "gemini-cli",
    "gemini-antigravity": "antigravity",
    "openai-codex": "codex",
    "codex-cli": "codex",
    "copilot": "github-copilot",
    "github-copilot": "github-copilot",
    "hermes-agent": "hermes",
    "kilo": "kilo-code",
    "kilocode": "kilo-code",
    "kilo-code": "kilo-code",
    "kiro": "kiro-cli",
    "kiro-cli": "kiro-cli",
    "kimi": "kimi-code",
    "kimi-code": "kimi-code",
    "mistral": "mistral-vibe",
    "mistral-vibe": "mistral-vibe",
    "openai": "codex",
    "open-code": "opencode",
    "roocode": "roo",
    "roo-code": "roo",
    "qwen": "qwen-code",
    "qwen-cli": "qwen-code",
    "qwen-code": "qwen-code",
}


def skill_target_names() -> list[str]:
    return [name for name, entry in TARGET_REGISTRY.items() if entry.get("skills")]


def _target_key(value: str) -> str:
    return "-".join(value.strip().lower().replace("_", " ").split())


def canonical_target_name(target: str) -> str:
    raw = target.strip()
    key = _target_key(raw)
    if key in TARGET_ALIASES:
        return TARGET_ALIASES[key]
    if key in TARGET_REGISTRY:
        return key
    return raw


def canonical_targets(value, default: list[str] | None = None) -> list[str]:
    if value is None:
        raw_targets = list(default or [])
    elif value is False:
        return []
    elif isinstance(value, str):
        raw_targets = [value]
    else:
        raw_targets = list(value or [])
    targets = []
    seen = set()
    for target in raw_targets:
        if not isinstance(target, str) or not target.strip():
            continue
        canonical = canonical_target_name(target)
        expanded = skill_target_names() if canonical == "*" else [canonical]
        for candidate in expanded:
            if candidate not in seen:
                seen.add(candidate)
                targets.append(candidate)
    return targets


def validate_target_values(value, field: str = "targets") -> list[dict]:
    if value is None or value is False:
        return []
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list):
        return [{"field": field, "message": f"{field} must be a list of target names"}]
    errors = []
    choices = sorted(TARGET_REGISTRY)
    for index, target in enumerate(values):
        target_field = f"{field}[{index}]"
        if not isinstance(target, str) or not target.strip():
            errors.append({"field": target_field, "message": "Target must be a non-empty string"})
            continue
        canonical = canonical_target_name(target)
        if canonical == "*" or canonical in TARGET_REGISTRY:
            continue
        normalized = _target_key(target)
        suggestion = difflib.get_close_matches(normalized, choices, n=1, cutoff=0.55)
        hint = f" Did you mean '{suggestion[0]}'?" if suggestion else ""
        errors.append({
            "field": target_field,
            "message": f"Unknown target '{target}'.{hint} See docs/targets.md for supported targets.",
        })
    return errors


def validate_mcp_target_values(value, field: str) -> list[dict]:
    """Validate MCP filters without weakening broad skills-target support."""
    errors = validate_target_values(value, field)
    if errors or value is None or value is False:
        return errors
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list):
        return errors

    implemented = set(mcp_target_names())
    seen = set()
    for index, target in enumerate(values):
        if not isinstance(target, str) or not target.strip():
            continue
        canonical = canonical_target_name(target)
        target_field = f"{field}[{index}]"
        if canonical != "*" and canonical not in implemented:
            errors.append({
                "field": target_field,
                "message": f"Target '{target}' does not have an implemented MCP writer.",
            })
            continue
        if canonical in seen:
            errors.append({
                "field": target_field,
                "message": f"Duplicate MCP target resolves to '{canonical}'.",
            })
            continue
        seen.add(canonical)
    return errors

# Standard PATH for MCP env (restricted environments may lack it)
STANDARD_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
BLUE = "\033[1;34m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
DIM = "\033[0;37m"
RESET = "\033[0m"


def info(msg):
    print(f"{BLUE}==>{RESET} {msg}", file=sys.stderr)


def ok(msg):
    print(f"{GREEN}  +{RESET} {msg}", file=sys.stderr)


def warn(msg):
    print(f"{YELLOW}  !{RESET} {msg}", file=sys.stderr)


def removed(msg):
    print(f"{RED}  -{RESET} {msg}", file=sys.stderr)


def unchanged(msg):
    print(f"{DIM}  ={RESET} {msg}", file=sys.stderr)


def confirm(prompt: str) -> bool:
    try:
        reply = input(f"{YELLOW}  ?{RESET} {prompt} [y/N] ")
    except EOFError:
        return False
    return reply.strip().lower() in ("y", "yes")


def skill_name_from_file(skill_file: Path, fallback: str) -> str:
    """Use SKILL.md frontmatter name when present, otherwise the directory name."""
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError:
        return fallback
    if not text.startswith("---\n"):
        return fallback
    end = text.find("\n---", 4)
    if end == -1:
        return fallback
    try:
        import yaml

        metadata = yaml.safe_load(text[4:end]) or {}
    except Exception:
        return fallback
    name = metadata.get("name") if isinstance(metadata, dict) else None
    return name if isinstance(name, str) and name.strip() else fallback


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
class Config:
    """Loads and provides access to the nexus manifest and repo paths."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.yml_path = self._resolve_manifest_path()
        self.nexus_dir = repo_dir / ".nexus"
        self.cache_dir = self.nexus_dir / "cache"
        self.lockfile_path = self._resolve_lockfile_path()
        self._data = None

    def _resolve_manifest_path(self) -> Path:
        personal = self.repo_dir / "nexus.personal.yml"
        if personal.exists():
            return personal
        return self.repo_dir / "nexus.yml"

    def _resolve_lockfile_path(self) -> Path:
        if self.yml_path.name == "nexus.personal.yml":
            return self.repo_dir / "nexus.personal.lock.yml"
        return self.repo_dir / "nexus.lock.yml"

    @property
    def manifest_exists(self) -> bool:
        return self.yml_path.exists()

    @property
    def data(self) -> dict:
        if self._data is None:
            self._data = self._load(required=True)
        return self._data

    def data_or_empty(self) -> dict:
        if self._data is None:
            self._data = self._load(required=False)
        return self._data

    def _load(self, required: bool = True) -> dict:
        try:
            import yaml
        except ImportError as exc:
            raise NexusError("PyYAML is required. Install it with: python -m pip install pyyaml") from exc
        if not self.yml_path.exists():
            if required:
                raise ManifestNotFoundError(
                    f"No Nexus manifest found in {self.repo_dir}. Run 'nexus init' to create a safe starter."
                )
            return {}
        try:
            with open(self.yml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            raise ManifestValidationError(f"Could not parse {self.yml_path.name}: {exc}") from exc
        if not isinstance(data, dict):
            raise ManifestValidationError("Manifest must be a YAML mapping")
        errors = validate_dashboard_manifest(data)
        if errors:
            raise ManifestValidationError(errors[0]["message"])
        return data

    def manifest_revision(self) -> str | None:
        if not self.yml_path.exists():
            return None
        return hashlib.sha256(self.yml_path.read_bytes()).hexdigest()

    @property
    def targets(self) -> list[str]:
        return canonical_targets(self.data_or_empty().get("targets"), CORE_DEFAULT_TARGETS)

    def safe_targets(self) -> list[str]:
        return self.targets

    @property
    def packages(self) -> list[dict]:
        return self.data.get("packages", [])

    @property
    def mcps(self) -> list[dict]:
        return self.data.get("mcps", [])

    @property
    def optional_mcps(self) -> list[dict]:
        return self.data.get("optional_mcps", [])

    def _target_path(self, target: str, key: str) -> Path | None:
        entry = TARGET_REGISTRY.get(canonical_target_name(target))
        if not entry:
            return None
        path = entry.get(key)
        if not path:
            return None
        path = Path(path)
        return path if path.is_absolute() else self.repo_dir / path

    def skill_path(self, target: str) -> Path | None:
        return self._target_path(target, "skills")

    def mcp_path(self, target: str) -> Path | None:
        target = canonical_target_name(target)
        entry = TARGET_REGISTRY.get(target) or {}
        if entry.get("status", {}).get("mcp") != "implemented":
            return None
        return self._target_path(target, "mcp")

    def mcp_format(self, target: str) -> str | None:
        entry = TARGET_REGISTRY.get(canonical_target_name(target)) or {}
        if entry.get("status", {}).get("mcp") != "implemented":
            return None
        return entry.get("mcp_format", "mcp_servers_json")

    def codex_hooks_path(self) -> Path:
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home:
            return Path(codex_home) / "hooks.json"
        return Path.home() / ".codex" / "hooks.json"

    def generated_skill_path(self, target: str, skill_name: str) -> Path:
        return self.nexus_dir / "generated" / target / "skills" / skill_name

    def load_lockfile(self) -> dict | None:
        if not self.lockfile_path.exists():
            return None
        try:
            import yaml
            with open(self.lockfile_path) as f:
                return yaml.safe_load(f)
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Package manager — fetch + cache + discover
# ---------------------------------------------------------------------------
class PackageManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def fetch(self, repo: str, ref: str, sparse_paths: list[str] | None = None, ephemeral_root: Path | None = None) -> Path | None:
        org, repo_name = repo.split("/", 1)
        sha = self._resolve_sha(repo, ref)
        if not sha:
            warn(f"Could not resolve ref '{ref}' for {repo}")
            return None
        cache_key = sha
        if sparse_paths:
            sparse_hash = hashlib.sha256("\n".join(sorted(sparse_paths)).encode()).hexdigest()[:12]
            cache_key = f"{sha}-sparse-{sparse_hash}"
        persistent_path = self.cfg.cache_dir / "github.com" / org / repo_name / cache_key
        persistent_marker = persistent_path.parent / f"{cache_key}.fetched"
        if persistent_marker.exists():
            unchanged(f"{repo}@{sha[:7]} (cached{', sparse' if sparse_paths else ''})")
            return persistent_path
        base = ephemeral_root if ephemeral_root is not None else self.cfg.cache_dir
        cache_path = base / "github.com" / org / repo_name / cache_key
        marker = None if ephemeral_root is not None else cache_path.parent / f"{cache_key}.fetched"
        info(f"Fetching {repo}@{ref} ({sha[:7]}) [{'temporary' if ephemeral_root is not None else 'persistent'}]...")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.parent / f"{cache_key}.tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        try:
            self._clone(repo, ref, tmp, sparse_paths)
        except subprocess.CalledProcessError:
            try:
                self._clone(repo, None, tmp, sparse_paths)
                subprocess.run(["git", "fetch", "--depth=1", "origin", sha], cwd=str(tmp), capture_output=True, check=True)
                subprocess.run(["git", "checkout", sha], cwd=str(tmp), capture_output=True, check=True)
            except subprocess.CalledProcessError:
                warn(f"Failed to fetch {repo}@{ref}")
                if tmp.exists():
                    shutil.rmtree(tmp)
                return None
        git_dir = tmp / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        if cache_path.exists():
            shutil.rmtree(cache_path)
        tmp.rename(cache_path)
        if marker is not None:
            marker.touch()
        ok(f"{repo}@{sha[:7]} ({'inspected' if ephemeral_root is not None else 'fetched'})")
        return cache_path

    def _clone(self, repo: str, ref: str | None, tmp: Path, sparse_paths: list[str] | None):
        cmd = ["git", "clone", "--depth=1"]
        if sparse_paths:
            cmd.extend(["--filter=blob:none", "--sparse"])
        if ref:
            cmd.extend(["--branch", ref])
        cmd.extend([f"https://github.com/{repo}", str(tmp)])
        subprocess.run(cmd, capture_output=True, check=True)
        if sparse_paths:
            subprocess.run(
                ["git", "sparse-checkout", "set", "--no-cone", *sparse_paths],
                cwd=str(tmp), capture_output=True, check=True,
            )

    def _resolve_sha(self, repo: str, ref: str) -> str | None:
        import re
        if re.fullmatch(r"[0-9a-f]{40}", ref):
            return ref

        for ref_pattern in [ref, f"refs/tags/{ref}"]:
            try:
                result = subprocess.run(
                    ["git", "ls-remote", f"https://github.com/{repo}", ref_pattern],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split()[0]
            except subprocess.TimeoutExpired:
                pass
        return None

    @staticmethod
    def discover(pkg_path: Path, pkg_name: str, sparse_paths: list[str] | None = None) -> dict:
        result = {
            "name": pkg_name,
            "path": str(pkg_path),
            "skills": [],
            "hooks_claude": None,
            "hooks_cursor": None,
            "hooks_codex": None,
            "commands": [],
            "agents": [],
        }

        skip = {".git", "node_modules", "__pycache__", "tests", "test"}
        allowed_hidden_roots = {
            Path(path).parts[0]
            for path in sparse_paths or []
            if Path(path).parts and Path(path).parts[0].startswith(".")
        }
        for root, dirs, files in os.walk(pkg_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in skip and (not d.startswith(".") or d in allowed_hidden_roots)
            ]
            if "SKILL.md" in files:
                name = os.path.basename(root)
                if os.path.normpath(root) == os.path.normpath(str(pkg_path)):
                    name = pkg_name
                name = skill_name_from_file(Path(root) / "SKILL.md", name)
                result["skills"].append({"name": name, "path": root})

        # Hooks
        for pattern in ["hooks/hooks.json", "hooks.json"]:
            p = pkg_path / pattern
            if p.is_file():
                result["hooks_claude"] = str(p)
                break

        for pattern in ["hooks/hooks-cursor.json", "hooks-cursor.json"]:
            p = pkg_path / pattern
            if p.is_file():
                result["hooks_cursor"] = str(p)
                break

        for pattern in ["hooks/hooks-codex.json", "hooks-codex.json"]:
            p = pkg_path / pattern
            if p.is_file():
                result["hooks_codex"] = str(p)
                break

        # Commands
        commands_dir = pkg_path / "commands"
        if commands_dir.is_dir():
            result["commands"] = [f.stem for f in commands_dir.iterdir() if f.suffix == ".md"]

        # Agents
        agents_dir = pkg_path / "agents"
        if agents_dir.is_dir():
            result["agents"] = [f.stem for f in agents_dir.iterdir() if f.suffix == ".md"]

        return result


def apply_package_filters(discovery: dict, pkg_spec: dict) -> dict:
    """Restrict discovered assets using optional manifest allowlists."""
    allowed_skills = pkg_spec.get("skills")
    if allowed_skills is not None:
        allowed = set(allowed_skills)
        discovered = {s["name"] for s in discovery.get("skills", [])}
        for missing in sorted(allowed - discovered):
            warn(f"{discovery['name']}: requested skill '{missing}' was not discovered")
        discovery["skills"] = [s for s in discovery.get("skills", []) if s["name"] in allowed]

    allowed_hooks = pkg_spec.get("hooks")
    if allowed_hooks is not None:
        discovered_hooks = {
            "claude": "hooks_claude",
            "cursor": "hooks_cursor",
            "codex": "hooks_codex",
        }
        if allowed_hooks is False or allowed_hooks == []:
            allowed = set()
        elif isinstance(allowed_hooks, str):
            allowed = {allowed_hooks}
        else:
            allowed = set(allowed_hooks)
        for missing in sorted(allowed - set(discovered_hooks)):
            warn(f"{discovery['name']}: requested hook target '{missing}' is not supported")
        for hook_name, key in discovered_hooks.items():
            if hook_name not in allowed:
                discovery[key] = None
    if "targets" in pkg_spec:
        discovery["targets"] = pkg_spec["targets"]
    if "skill_overrides" in pkg_spec:
        discovery["skill_overrides"] = pkg_spec["skill_overrides"] or {}
    return discovery


def package_targets(pkg: dict, default_targets: list[str]) -> list[str]:
    configured = pkg.get("targets")
    defaults = canonical_targets(default_targets)
    if configured is None:
        return defaults
    requested = canonical_targets(configured)
    default_set = set(defaults)
    return [target for target in requested if target in default_set]


def mcp_target_names() -> list[str]:
    """Return targets with implemented MCP configuration writers."""
    return [
        name
        for name, entry in TARGET_REGISTRY.items()
        if entry.get("status", {}).get("mcp") == "implemented"
    ]


def mcp_targets(mcp: dict, default_targets: list[str]) -> list[str]:
    """Return configured MCP targets, constrained to implemented manifest targets."""
    implemented = set(mcp_target_names())
    defaults = [
        target
        for target in canonical_targets(default_targets)
        if target not in TARGET_REGISTRY or target in implemented
    ]
    configured = mcp.get("targets")
    if configured is None:
        return defaults
    requested = canonical_targets(configured)
    default_set = set(defaults)
    return [target for target in requested if target in default_set]


def _configured_targets(value) -> list[str]:
    return canonical_targets(value)


def skill_override(pkg: dict, skill_name: str) -> dict:
    overrides = pkg.get("skill_overrides") or {}
    override = overrides.get(skill_name)
    return override if isinstance(override, dict) else {}


MATERIALIZED_OVERLAY_TYPES = ("agents_openai", "skill_frontmatter")


def overlay_types(pkg: dict, skill_name: str) -> list[str]:
    override = skill_override(pkg, skill_name)
    return [
        overlay_type
        for overlay_type in MATERIALIZED_OVERLAY_TYPES
        if isinstance(override.get(overlay_type), dict)
    ]


def overlay_targets(pkg: dict, skill_name: str, default_targets: list[str]) -> list[str]:
    if not overlay_types(pkg, skill_name):
        return []

    pkg_targets = package_targets(pkg, default_targets)
    requested = skill_override(pkg, skill_name).get("targets")
    if requested is None:
        return list(pkg_targets)

    allowed = set(pkg_targets)
    return [target for target in _configured_targets(requested) if target in allowed]


def skill_overlays(pkg: dict, skill_name: str, default_targets: list[str]) -> list[dict]:
    return [
        {"skill": skill_name, "target": target, "type": overlay_type}
        for target in overlay_targets(pkg, skill_name, default_targets)
        for overlay_type in overlay_types(pkg, skill_name)
    ]


def generated_skill_path(cfg, target: str, skill_name: str) -> Path:
    if hasattr(cfg, "generated_skill_path"):
        return cfg.generated_skill_path(target, skill_name)
    nexus_dir = getattr(cfg, "nexus_dir", cfg.repo_dir / ".nexus")
    return nexus_dir / "generated" / target / "skills" / skill_name


def deep_merge(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    return override

# ---------------------------------------------------------------------------
# Deployer — skills, hooks, MCPs, with pruning
# ---------------------------------------------------------------------------
class Deployer:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # -- Skills --

    def deploy_skills(self, discoveries: list[dict]) -> int:
        count = 0
        for pkg in discoveries:
            for skill in pkg.get("skills", []):
                name = skill["name"]
                path = Path(skill["path"])
                deployed_to = []
                for target in package_targets(pkg, self.cfg.targets):
                    target_dir = self.cfg.skill_path(target)
                    if not target_dir:
                        continue
                    deploy_path = self._skill_deploy_path(pkg, skill, target, path)
                    target_dir.mkdir(parents=True, exist_ok=True)
                    link = target_dir / name
                    if link.is_symlink() or not link.exists():
                        link.unlink(missing_ok=True)
                        link.symlink_to(deploy_path)
                        deployed_to.append(target)
                    else:
                        warn(f"{link} exists and is not a symlink, skipping")
                ok(f"{name} -> {','.join(deployed_to)}")
                count += 1
        return count

    def _skill_deploy_path(self, pkg: dict, skill: dict, target: str, source_path: Path) -> Path:
        name = skill["name"]
        if target not in overlay_targets(pkg, name, self.cfg.targets):
            return source_path
        override = skill_override(pkg, name)
        return self._materialize_skill_overlay(source_path, name, target, override)

    def _materialize_skill_overlay(
        self,
        source_path: Path,
        skill_name: str,
        target: str,
        override: dict,
    ) -> Path:
        generated = generated_skill_path(self.cfg, target, skill_name)
        if generated.is_symlink() or generated.is_file():
            generated.unlink()
        elif generated.exists():
            shutil.rmtree(generated)

        generated.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, generated, symlinks=True)

        skill_frontmatter = override.get("skill_frontmatter") or {}
        if skill_frontmatter:
            self._apply_skill_frontmatter(generated / "SKILL.md", skill_frontmatter)

        agents_openai = override.get("agents_openai") or {}
        if agents_openai:
            metadata_path = generated / "agents" / "openai.yaml"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            existing = self._load_yaml_mapping(metadata_path)
            merged = deep_merge(existing, agents_openai)
            self._write_yaml(metadata_path, merged)
        return generated

    @staticmethod
    def _apply_skill_frontmatter(path: Path, frontmatter: dict):
        import yaml

        text = path.read_text(encoding="utf-8") if path.exists() else ""
        existing = {}
        body = text
        if text.startswith("---\n"):
            parts = text.split("---\n", 2)
            if len(parts) == 3:
                data = yaml.safe_load(parts[1]) or {}
                existing = data if isinstance(data, dict) else {}
                body = parts[2]

        merged = deep_merge(existing, frontmatter)
        dumped = yaml.safe_dump(merged, default_flow_style=False, sort_keys=False).rstrip()
        path.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")

    @staticmethod
    def _load_yaml_mapping(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            import yaml

            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _write_yaml(path: Path, data: dict):
        import yaml

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=True)

    def prune_skills(self, discoveries: list[dict], prev_lock: dict | None):
        """Remove symlinks for packages no longer in the manifest."""
        if not prev_lock:
            return

        current_by_target = {target: set() for target in self.cfg.targets}
        for pkg in discoveries:
            for target in package_targets(pkg, self.cfg.targets):
                for skill in pkg.get("skills", []):
                    current_by_target.setdefault(target, set()).add(skill["name"])

        prev_by_target = {target: set() for target in self.cfg.targets}
        for pkg in prev_lock.get("packages", []):
            deployed_to = pkg.get("deployed_to") or self.cfg.targets
            for target in deployed_to:
                if target not in prev_by_target:
                    continue
                for skill_name in pkg.get("discovered", {}).get("skills", []):
                    prev_by_target[target].add(skill_name)

        for target in self.cfg.targets:
            stale = prev_by_target.get(target, set()) - current_by_target.get(target, set())
            if not stale:
                continue
            target_dir = self.cfg.skill_path(target)
            if not target_dir or not target_dir.exists():
                continue
            for name in stale:
                link = target_dir / name
                if link.is_symlink():
                    link.unlink()
                    removed(f"{name} from {target}")

    # -- Hooks --

    def deploy_hooks(self, discoveries: list[dict]):
        claude_hooks = []
        cursor_hooks = []
        codex_hooks = []
        for pkg in discoveries:
            targets = package_targets(pkg, self.cfg.targets)
            if "claude" in targets and pkg.get("hooks_claude"):
                claude_hooks.append(Path(pkg["hooks_claude"]))
            if "cursor" in targets and pkg.get("hooks_cursor"):
                cursor_hooks.append(Path(pkg["hooks_cursor"]))
            if "codex" in targets and pkg.get("hooks_codex"):
                codex_hooks.append(pkg)

        if cursor_hooks:
            merged = self._merge_hooks(cursor_hooks)
            out_dir = self.cfg.repo_dir / ".cursor"
            out_dir.mkdir(parents=True, exist_ok=True)
            with open(out_dir / "hooks.json", "w") as f:
                json.dump(merged, f, indent=2)
                f.write("\n")
            total = sum(len(v) for v in merged.get("hooks", {}).values())
            ok(f"Cursor hooks: deduplicated ({total} unique entries)")

        if claude_hooks:
            out_dir = self.cfg.repo_dir / ".github" / "hooks"
            destinations = {}
            for source in claude_hooks:
                if source.name in destinations and source.read_bytes() != destinations[source.name].read_bytes():
                    raise NexusError(f"Claude hook filename collision: {source.name}")
                destinations[source.name] = source
            for name, source in destinations.items():
                destination = out_dir / name
                if destination.exists() and destination.read_bytes() != source.read_bytes():
                    raise NexusError(f"Refusing to overwrite unverified hook file: {destination}")
            out_dir.mkdir(parents=True, exist_ok=True)
            for name, source in destinations.items():
                shutil.copy2(source, out_dir / name)
            ok("Claude hooks: copied to .github/hooks/")

        if "codex" in self.cfg.targets:
            path = self.cfg.codex_hooks_path()
            existing = self._load_hook_config(path)
            merged = self._merge_codex_hooks(codex_hooks, path)
            if codex_hooks or merged != existing:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "w") as f:
                    json.dump(merged, f, indent=2)
                    f.write("\n")
                total = sum(len(v) for v in merged.get("hooks", {}).values())
                ok(f"Codex hooks: merged {total} entries into {path}")

    @staticmethod
    def _merge_hooks(hook_files: list[Path]) -> dict:
        merged: dict[str, list] = {}
        seen: dict[str, set] = {}
        for path in hook_files:
            try:
                with open(path) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            for event, entries in data.get("hooks", {}).items():
                if event not in merged:
                    merged[event] = []
                    seen[event] = set()
                for entry in entries:
                    clean = {k: v for k, v in entry.items() if not k.startswith("_")}
                    key = hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()
                    if key not in seen[event]:
                        seen[event].add(key)
                        merged[event].append(entry)
        return {"hooks": merged}

    @classmethod
    def _merge_codex_hooks(cls, packages: list[dict], hooks_path: Path) -> dict:
        existing = cls._load_hook_config(hooks_path)
        cls._strip_nexus_managed_hooks(existing)

        for pkg in packages:
            try:
                with open(pkg["hooks_codex"]) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            package_root = pkg["path"]
            for event, entries in data.get("hooks", {}).items():
                existing.setdefault("hooks", {}).setdefault(event, [])
                for entry in entries:
                    existing["hooks"][event].append(
                        cls._substitute_package_root(entry, package_root)
                    )

        cls._dedupe_hook_config(existing)
        return existing

    @staticmethod
    def _load_hook_config(path: Path) -> dict:
        if not path.exists():
            return {"hooks": {}}
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"hooks": {}}
        if not isinstance(data, dict):
            return {"hooks": {}}
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            data["hooks"] = {}
        return data

    @classmethod
    def _strip_nexus_managed_hooks(cls, config: dict):
        hooks = config.setdefault("hooks", {})
        for event in list(hooks):
            entries = hooks.get(event)
            if not isinstance(entries, list):
                del hooks[event]
                continue
            kept = []
            for entry in entries:
                stripped = cls._strip_managed_commands_from_entry(entry)
                if stripped is not None:
                    kept.append(stripped)
            if kept:
                hooks[event] = kept
            else:
                del hooks[event]

    @classmethod
    def _strip_managed_commands_from_entry(cls, entry):
        if not isinstance(entry, dict):
            return entry
        if cls._is_nexus_managed_command(entry):
            return None
        if isinstance(entry.get("hooks"), list):
            clean_hooks = [
                hook for hook in entry["hooks"]
                if not cls._is_nexus_managed_command(hook)
            ]
            if not clean_hooks:
                return None
            clean_entry = dict(entry)
            clean_entry["hooks"] = clean_hooks
            return clean_entry
        return entry

    @staticmethod
    def _is_nexus_managed_command(entry) -> bool:
        if not isinstance(entry, dict):
            return False
        command = entry.get("command")
        return isinstance(command, str) and "--nexus-package" in command

    @classmethod
    def _substitute_package_root(cls, value, package_root: str):
        if isinstance(value, dict):
            return {
                key: cls._substitute_package_root(item, package_root)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._substitute_package_root(item, package_root) for item in value]
        if isinstance(value, str):
            return value.replace("{{package_root}}", package_root)
        return value

    @staticmethod
    def _dedupe_hook_config(config: dict):
        hooks = config.setdefault("hooks", {})
        for event, entries in list(hooks.items()):
            if not isinstance(entries, list):
                del hooks[event]
                continue
            seen = set()
            deduped = []
            for entry in entries:
                key = hashlib.sha256(
                    json.dumps(entry, sort_keys=True).encode()
                ).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(entry)
            if deduped:
                hooks[event] = deduped
            else:
                del hooks[event]

    # -- MCPs --

    def sync_mcps(self, all_mcps: list[dict]):
        if not all_mcps:
            unchanged("No MCP servers selected; no MCP config files created")
            return
        for target in self.cfg.targets:
            target_mcps = [mcp for mcp in all_mcps if target in mcp_targets(mcp, self.cfg.targets)]
            if not target_mcps:
                unchanged(f"No MCP servers selected for {target}")
                continue
            mcp_path = self.cfg.mcp_path(target)
            if not mcp_path:
                continue
            info(f"Syncing MCPs to {mcp_path}...")
            if self.cfg.mcp_format(target) == "codex_toml":
                self._sync_mcps_for_codex(target_mcps, mcp_path)
            else:
                self._sync_mcps_for_target(target_mcps, mcp_path, target)

    def _sync_mcps_for_target(self, all_mcps: list[dict], mcp_path: Path, target: str):
        # Read existing config
        config = {}
        if mcp_path.exists():
            try:
                with open(mcp_path) as f:
                    config = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        else:
            mcp_path.parent.mkdir(parents=True, exist_ok=True)

        servers = config.setdefault("mcpServers", {})

        for mcp in all_mcps:
            name = mcp["name"]
            entry = self._build_mcp_entry(mcp, target=target)

            if name in servers:
                entry = self._merge_mcp_entry(servers[name], entry)
                if servers[name] == entry:
                    unchanged(f"{name} (unchanged)")
                    continue
                ok(f"{name} (updated)")
            else:
                ok(f"{name} (added)")
            servers[name] = entry

        with open(mcp_path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")

    def _sync_mcps_for_codex(self, all_mcps: list[dict], mcp_path: Path):
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        original = mcp_path.read_text() if mcp_path.exists() else ""
        existing_managed = self._parse_codex_managed_env(original)
        existing = self._strip_codex_managed_block(original).rstrip()

        lines = [
            "",
            "# BEGIN NEXUS MANAGED MCP SERVERS",
            f"# This block is generated by agent-nexus. Edit {self.cfg.yml_path.name} instead.",
        ]
        for mcp in all_mcps:
            name = mcp["name"]
            entry = self._build_mcp_entry(mcp)
            if name in existing_managed:
                entry = self._merge_mcp_entry(existing_managed[name], entry)
            lines.extend(self._codex_toml_for_mcp(name, entry))
            ok(f"{name} (synced)")
        lines.append("# END NEXUS MANAGED MCP SERVERS")

        content = existing + "\n" + "\n".join(lines) + "\n"
        mcp_path.write_text(content)

    @staticmethod
    def _strip_codex_managed_block(content: str) -> str:
        begin = "# BEGIN NEXUS MANAGED MCP SERVERS"
        end = "# END NEXUS MANAGED MCP SERVERS"
        start = content.find(begin)
        if start == -1:
            return content
        stop = content.find(end, start)
        if stop == -1:
            return content[:start]
        return content[:start] + content[stop + len(end):]

    @classmethod
    def _parse_codex_managed_env(cls, content: str) -> dict:
        begin = "# BEGIN NEXUS MANAGED MCP SERVERS"
        end = "# END NEXUS MANAGED MCP SERVERS"
        start = content.find(begin)
        if start == -1:
            return {}
        stop = content.find(end, start)
        if stop == -1:
            block = content[start:]
        else:
            block = content[start:stop]

        import re

        section_re = re.compile(r'^\[mcp_servers\.("(?:\\.|[^"])*"|[A-Za-z0-9_-]+)(\.env)?\]$')
        value_re = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$')
        managed: dict[str, dict] = {}
        current_name = None
        in_env = False

        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            section = section_re.match(line)
            if section:
                current_name = cls._parse_toml_key(section.group(1))
                in_env = bool(section.group(2))
                if current_name:
                    managed.setdefault(current_name, {})
                    if in_env:
                        managed[current_name].setdefault("env", {})
                continue
            if not current_name or not in_env:
                continue
            value = value_re.match(line)
            if value:
                managed[current_name].setdefault("env", {})[value.group(1)] = cls._parse_toml_scalar(value.group(2))
        return managed

    @staticmethod
    def _parse_toml_key(value: str) -> str:
        if value.startswith('"'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return ""
        return value

    @staticmethod
    def _parse_toml_scalar(value: str):
        value = value.strip().rstrip(",")
        if value.startswith('"'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value.strip('"')
        return value

    @staticmethod
    def _toml_string(value: str) -> str:
        return json.dumps(value)

    @classmethod
    def _toml_array(cls, values: list) -> str:
        return "[" + ", ".join(cls._toml_string(str(v)) for v in values) + "]"

    @classmethod
    def _codex_toml_for_mcp(cls, name: str, entry: dict) -> list[str]:
        quoted_name = cls._toml_string(name)
        lines = [
            "",
            f"[mcp_servers.{quoted_name}]",
        ]
        if entry.get("type") in ("http", "sse"):
            if entry.get("type") == "sse":
                lines.append('type = "sse"')
            lines.append(f"url = {cls._toml_string(entry['url'])}")
            if entry.get("oauth_resource"):
                lines.append(f"oauth_resource = {cls._toml_string(entry['oauth_resource'])}")
            headers = entry.get("headers") or {}
            if headers:
                lines.append("http_headers = { " + ", ".join(
                    f"{key} = {cls._toml_string(str(headers[key]))}"
                    for key in sorted(headers)
                ) + " }")
            return lines

        lines.append(f"command = {cls._toml_string(entry['command'])}")
        lines.append(f"args = {cls._toml_array(entry.get('args', []))}")

        env = entry.get("env") or {}
        if env:
            lines.append("")
            lines.append(f"[mcp_servers.{quoted_name}.env]")
            for key in sorted(env):
                lines.append(f"{key} = {cls._toml_string(str(env[key]))}")
        return lines

    def _build_mcp_entry(self, mcp: dict, target: str | None = None) -> dict:
        if mcp.get("transport") in ("http", "sse") or "url" in mcp:
            if target == "antigravity":
                entry = {"serverUrl": mcp["url"]}
                if mcp.get("headers"):
                    entry["headers"] = mcp["headers"]
                return entry
            entry = {
                "type": mcp.get("transport", "sse"),
                "url": mcp["url"],
            }
            if mcp.get("oauth_resource"):
                entry["oauth_resource"] = mcp["oauth_resource"]
            if mcp.get("headers"):
                entry["headers"] = mcp["headers"]
            return entry

        command = mcp.get("command", "npx")
        if command in ("npx", "node"):
            resolved = shutil.which(command)
            if resolved:
                command = resolved

        env = dict(mcp.get("env") or {})
        if "env" not in mcp and "PATH" not in env:
            env["PATH"] = STANDARD_PATH
        return {"type": "stdio", "command": command, "args": mcp.get("args", []), "env": env}

    @classmethod
    def _merge_mcp_entry(cls, existing, desired):
        """Merge a desired MCP entry without dropping local-only keys or secrets."""
        if not isinstance(existing, dict) or not isinstance(desired, dict):
            return desired

        merged = dict(existing)
        for key, value in desired.items():
            if key == "env" and value == {}:
                # An explicit empty manifest env is a complete shape, not an
                # invitation to retain stale PATH or secret-bearing local keys.
                merged[key] = {}
            elif key == "env" and isinstance(value, dict):
                merged[key] = cls._merge_mcp_env(existing.get(key), value)
            else:
                merged[key] = value
        return merged

    @staticmethod
    def _merge_mcp_env(existing, desired):
        if not isinstance(existing, dict):
            return dict(desired)
        merged = dict(existing)
        for key, value in desired.items():
            current = existing.get(key)
            if (
                isinstance(current, str)
                and isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                merged[key] = current
            else:
                merged[key] = value
        return merged

    def prune_mcps(self, current_mcps: list[dict], prev_lock: dict | None):
        """Remove previously managed MCPs that no longer target each host."""
        if not prev_lock:
            return
        previous = [
            entry
            for entry in prev_lock.get("mcps", {}).get("managed", [])
            if isinstance(entry, dict) and entry.get("name")
        ]

        for target in self.cfg.targets:
            previous_names = {
                entry["name"]
                for entry in previous
                if target in mcp_targets(entry, self.cfg.targets)
            }
            current_names = {
                mcp["name"]
                for mcp in current_mcps
                if target in mcp_targets(mcp, self.cfg.targets)
            }
            stale = previous_names - current_names
            if not stale:
                continue

            mcp_path = self.cfg.mcp_path(target)
            if not mcp_path or not mcp_path.exists():
                continue
            if self.cfg.mcp_format(target) == "codex_toml":
                self._prune_codex_mcps(mcp_path, stale)
                continue
            try:
                with open(mcp_path) as f:
                    config = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            servers = config.get("mcpServers", {})

            changed = False
            for name in stale:
                if name in servers:
                    del servers[name]
                    removed(f"{name} from {target} MCP config")
                    changed = True

            if changed:
                with open(mcp_path, "w") as f:
                    json.dump(config, f, indent=2)
                    f.write("\n")

    def _prune_codex_mcps(self, mcp_path: Path, stale: set[str]):
        original = mcp_path.read_text()
        existing_managed = self._parse_codex_managed_entries(original)
        kept = [
            (name, lines)
            for name, lines in existing_managed
            if name not in stale
        ]
        removed_names = {name for name, _lines in existing_managed if name in stale}
        if not removed_names:
            return

        existing = self._strip_codex_managed_block(original).rstrip()
        lines = [
            "",
            "# BEGIN NEXUS MANAGED MCP SERVERS",
            f"# This block is generated by agent-nexus. Edit {self.cfg.yml_path.name} instead.",
        ]
        for _name, entry_lines in kept:
            lines.extend(entry_lines)
        lines.append("# END NEXUS MANAGED MCP SERVERS")
        mcp_path.write_text(existing + "\n" + "\n".join(lines) + "\n")

        for name in sorted(removed_names):
            removed(f"{name} from codex MCP config")

    @classmethod
    def _parse_codex_managed_entries(cls, content: str) -> list[tuple[str, list[str]]]:
        begin = "# BEGIN NEXUS MANAGED MCP SERVERS"
        end = "# END NEXUS MANAGED MCP SERVERS"
        start = content.find(begin)
        if start == -1:
            return []
        stop = content.find(end, start)
        block = content[start:] if stop == -1 else content[start:stop]

        entries = []
        current_name = None
        current_lines = []
        for raw_line in block.splitlines():
            line = raw_line.strip()
            name = cls._codex_mcp_section_name(line)
            if name and not line.endswith(".env]"):
                if current_name:
                    entries.append((current_name, current_lines))
                current_name = name
                current_lines = ["", raw_line]
                continue
            if current_name:
                current_lines.append(raw_line)
        if current_name:
            entries.append((current_name, current_lines))
        return entries

    @staticmethod
    def _codex_mcp_section_name(line: str) -> str:
        import re

        match = re.match(r'^\[mcp_servers\.("(?:\\.|[^"])*"|[A-Za-z0-9_-]+)(?:\.env)?\]$', line)
        if not match:
            return ""
        return Deployer._parse_toml_key(match.group(1))


# ---------------------------------------------------------------------------
# Lockfile
# ---------------------------------------------------------------------------
def _resolved_commit_from_cache_path(path: str | None) -> str | None:
    if not path:
        return None
    name = Path(path).name
    if "-sparse-" in name:
        return name.split("-sparse-", 1)[0]
    return name if len(name) == 40 and all(ch in "0123456789abcdef" for ch in name.lower()) else None


def _floating_ref_warning(ref: str | None) -> str | None:
    if ref in {"main", "master", "HEAD"}:
        return f"floating ref '{ref}' can change between syncs; prefer a tag or commit SHA for reproducible installs"
    return None


def _hook_deployments(pkg: dict, targets: list[str]) -> list[str]:
    selected = set(package_targets(pkg, targets))
    result = []
    for target, key in [
        ("claude", "hooks_claude"),
        ("cursor", "hooks_cursor"),
        ("codex", "hooks_codex"),
    ]:
        if target in selected and pkg.get(key):
            result.append(target)
    return result


def generate_lockfile(
    discoveries: list[dict],
    manifest: dict,
    targets: list[str],
    repo_dir: Path | None = None,
    managed_mcps: list[dict] | None = None,
    manifest_path: Path | None = None,
) -> dict:
    repo_dir = repo_dir or Path.cwd()
    lock = {
        "lockfile_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "nexus_version": NEXUS_VERSION,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_revision": hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path and manifest_path.exists() else None,
        "packages": [],
        "mcps": {"managed": []},
        "hooks": {"managed_files": []},
    }
    for pkg in discoveries:
        source = pkg.get("source", {}) if isinstance(pkg.get("source"), dict) else {}
        entry = {
            "name": pkg["name"],
            "path": pkg["path"],
            "cache_path": pkg["path"],
            "source": source,
            "discovered": {
                "skills": [s["name"] for s in pkg.get("skills", [])],
                "hooks_claude": pkg.get("hooks_claude") is not None,
                "hooks_cursor": pkg.get("hooks_cursor") is not None,
                "hooks_codex": pkg.get("hooks_codex") is not None,
                "commands": pkg.get("commands", []),
                "agents": pkg.get("agents", []),
            },
            "deployed_to": package_targets(pkg, targets),
            "hook_deployments": _hook_deployments(pkg, targets),
        }
        warning = _floating_ref_warning(source.get("requested_ref"))
        if warning:
            entry["warnings"] = [warning]
        overlays = []
        for skill in pkg.get("skills", []):
            for overlay in skill_overlays(pkg, skill["name"], targets):
                overlay_path = (
                    repo_dir / ".nexus" / "generated" / overlay["target"] / "skills" / skill["name"]
                )
                overlays.append({**overlay, "path": str(overlay_path)})
        if overlays:
            entry["overlays"] = overlays
        lock["packages"].append(entry)
        if "claude" in entry["hook_deployments"] and pkg.get("hooks_claude"):
            source_path = Path(pkg["hooks_claude"])
            lock["hooks"]["managed_files"].append({
                "target": "claude",
                "path": str(repo_dir / ".github" / "hooks" / source_path.name),
                "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path.is_file() else None,
            })
        if "cursor" in entry["hook_deployments"] and pkg.get("hooks_cursor"):
            lock["hooks"]["managed_files"].append({"target": "cursor", "path": str(repo_dir / ".cursor" / "hooks.json")})
    if managed_mcps is None:
        managed_mcps = [mcp for mcp in manifest.get("mcps", []) if not mcp.get("optional")]

    for mcp in managed_mcps:
        entry = {
            "name": mcp["name"],
            "targets": mcp_targets(mcp, targets),
        }
        if mcp.get("optional"):
            entry["optional"] = True
        lock["mcps"]["managed"].append(entry)
    return lock


def write_lockfile(lock: dict, path: Path):
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(lock, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        with open(path, "w") as f:
            json.dump(lock, f, indent=2)
            f.write("\n")


# ---------------------------------------------------------------------------
# Security review
# ---------------------------------------------------------------------------
def show_review(all_mcps: list[dict], targets: list[str]):
    print(file=sys.stderr)
    info("Security review - MCP servers to be registered:")
    print(file=sys.stderr)
    for mcp in all_mcps:
        name = mcp["name"]
        if "url" in mcp:
            detail = f"{mcp.get('transport', 'sse')}: {mcp['url']}"
        else:
            cmd = mcp.get("command", "npx")
            args = " ".join(mcp.get("args", []))
            detail = f"stdio: {cmd} {args}"
        target_label = ",".join(mcp_targets(mcp, targets)) or "none"
        print(f"    {name:30s} {detail} -> {target_label}", file=sys.stderr)
    print(file=sys.stderr)


# ---------------------------------------------------------------------------
# Resolve which optional MCPs to include
# ---------------------------------------------------------------------------
def resolve_optionals(cfg: Config, include_all: bool = False, include_names: list[str] | None = None, no_optional: bool = False, prompt_allowed: bool = True) -> list[str]:
    include_names = include_names or []
    optional = [mcp for mcp in cfg.mcps if mcp.get("optional")] + list(cfg.optional_mcps)
    available = {mcp.get("name") for mcp in optional if mcp.get("name")}
    unknown = sorted(set(include_names) - available)
    if unknown:
        raise ManifestValidationError(f"Unknown optional MCP: {', '.join(unknown)}")
    accepted = []
    for mcp in optional:
        name = mcp["name"]
        selected = include_all or name in include_names
        if not selected and not no_optional and prompt_allowed:
            selected = confirm(f"Include optional MCP: {name} ({mcp.get('description', 'No description')})?")
        if selected:
            accepted.append(name)
            ok(f"{name} (included)")
        else:
            warn(f"{name} (skipped; use --include-optional {name})")
    return accepted

def collect_mcps(cfg: Config, accepted_optional: list[str]) -> list[dict]:
    """Build the full list of MCPs to deploy."""
    accepted_set = set(accepted_optional)
    result = []
    for mcp in cfg.mcps:
        if mcp.get("optional"):
            if mcp["name"] in accepted_set:
                result.append(mcp)
        else:
            result.append(mcp)
    for mcp in cfg.optional_mcps:
        if mcp["name"] in accepted_set:
            included = dict(mcp)
            included["optional"] = True
            result.append(included)
    return result


# ---------------------------------------------------------------------------
# Dashboard model, local UI, and management actions
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path_value(path: Path | None) -> str | None:
    return str(path) if path else None


def dashboard_path(path: str | Path | None, cfg: Config) -> str | None:
    if not path:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        return str(candidate)
    resolved = candidate.resolve(strict=False)
    repo = cfg.repo_dir.resolve(strict=False)
    home = Path.home().resolve(strict=False)
    if resolved == repo:
        return "."
    if repo in resolved.parents:
        return f"./{resolved.relative_to(repo)}"
    if resolved == home:
        return "~"
    if home in resolved.parents:
        return f"~/{resolved.relative_to(home)}"
    return f"[external]/{resolved.name}"


def sanitize_dashboard_paths(value, cfg: Config):
    if isinstance(value, dict):
        return {key: sanitize_dashboard_paths(item, cfg) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_dashboard_paths(item, cfg) for item in value]
    if isinstance(value, str) and Path(value).expanduser().is_absolute():
        return dashboard_path(value, cfg)
    return value


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def sanitize_mcp(mcp: dict) -> dict:
    clean = {}
    for key, value in mcp.items():
        if key == "env" and isinstance(value, dict):
            clean["env_keys"] = sorted(str(k) for k in value.keys())
        elif key == "headers" and isinstance(value, dict):
            clean["header_keys"] = sorted(str(k) for k in value.keys())
        elif key not in {"env", "headers"}:
            clean[key] = value
    return clean


def sanitize_manifest(data: dict) -> dict:
    sanitized = dict(data) if isinstance(data, dict) else {}
    sanitized["mcps"] = [sanitize_mcp(mcp) for mcp in sanitized.get("mcps", []) if isinstance(mcp, dict)]
    sanitized["optional_mcps"] = [
        sanitize_mcp(mcp) for mcp in sanitized.get("optional_mcps", []) if isinstance(mcp, dict)
    ]
    return sanitized


DASHBOARD_REDACTED_VALUE = "REDACTED_BY_NEXUS_DASHBOARD"


def load_manifest_text(cfg: Config) -> str:
    return cfg.yml_path.read_text(encoding="utf-8")


def redact_manifest_for_dashboard(data: dict) -> dict:
    def scrub(value):
        if isinstance(value, dict):
            return {
                key: ({secret_key: DASHBOARD_REDACTED_VALUE for secret_key in val.keys()}
                      if key in {"env", "headers"} and isinstance(val, dict)
                      else scrub(val))
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value
    return scrub(data)


def redact_manifest_text_for_dashboard(text: str) -> str:
    redacted = []
    secret_indent = None
    for line in text.splitlines():
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if secret_indent is not None and stripped and not stripped.startswith("#") and indent <= secret_indent:
            secret_indent = None
        if stripped.startswith(("env:", "headers:")):
            secret_indent = indent
            redacted.append(line)
            continue
        if secret_indent is not None and stripped and not stripped.startswith("#") and ":" in stripped:
            key = stripped.split(":", 1)[0]
            redacted.append(f"{' ' * indent}{key}: {DASHBOARD_REDACTED_VALUE}")
            continue
        redacted.append(line)
    return "\n".join(redacted) + ("\n" if text.endswith("\n") else "")


def load_redacted_manifest_text(cfg: Config) -> str:
    if cfg.yml_path.exists():
        return redact_manifest_text_for_dashboard(load_manifest_text(cfg))
    return starter_manifest_text(cfg.repo_dir)


def require_manifest_revision(cfg: Config, revision: str | None):
    current = cfg.manifest_revision()
    if revision != current:
        raise ManifestValidationError("Manifest changed since this view loaded. Refresh and review the latest file.")


def parse_manifest_text(text: str) -> dict:
    try:
        import yaml
    except ImportError:
        raise ValueError("PyYAML is required to parse the manifest")
    try:
        data = yaml.safe_load(text) or {}
    except Exception as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a YAML mapping")
    return data


def validate_dashboard_manifest(data: dict) -> list[dict]:
    errors = []
    if not isinstance(data, dict):
        return [{"field": "manifest", "message": "Manifest must be a YAML mapping"}]
    for key in ["packages", "mcps", "optional_mcps", "targets"]:
        if key in data and not isinstance(data[key], list):
            errors.append({"field": key, "message": f"{key} must be a list"})
    errors.extend(validate_target_values(data.get("targets"), "targets"))
    for section in ["mcps", "optional_mcps"]:
        for index, mcp in enumerate(data.get(section, []) or []):
            if not isinstance(mcp, dict):
                errors.append({"field": f"{section}[{index}]", "message": "MCP entry must be a mapping"})
                continue
            if not mcp.get("name"):
                errors.append({"field": f"{section}[{index}].name", "message": "MCP name is required"})
            if "url" not in mcp and not mcp.get("command"):
                errors.append({"field": f"{section}[{index}].command", "message": "MCP command or url is required"})
            errors.extend(validate_mcp_target_values(mcp.get("targets"), f"{section}[{index}].targets"))
    for index, pkg in enumerate(data.get("packages", []) or []):
        field = f"packages[{index}]"
        if not isinstance(pkg, dict):
            errors.append({"field": field, "message": "Package entry must be a mapping"})
            continue
        if not pkg.get("repo") and not pkg.get("path"):
            errors.append({"field": field, "message": "Package repo or path is required"})
        errors.extend(validate_target_values(pkg.get("targets"), f"{field}.targets"))
        errors.extend(validate_target_values(pkg.get("hooks"), f"{field}.hooks"))
        overrides = pkg.get("skill_overrides", {})
        if isinstance(overrides, dict):
            for skill_name, override in overrides.items():
                if isinstance(override, dict):
                    errors.extend(validate_target_values(
                        override.get("targets"), f"{field}.skill_overrides.{skill_name}.targets"
                    ))
    return errors


def _restore_redacted_values(proposed, original):
    if proposed == DASHBOARD_REDACTED_VALUE:
        return original
    if isinstance(proposed, dict):
        source = original if isinstance(original, dict) else {}
        return {key: _restore_redacted_values(value, source.get(key)) for key, value in proposed.items()}
    if isinstance(proposed, list):
        source = original if isinstance(original, list) else []
        return [
            _restore_redacted_values(value, source[index] if index < len(source) else None)
            for index, value in enumerate(proposed)
        ]
    return proposed


def write_manifest_atomically(cfg: Config, text: str):
    data = parse_manifest_text(text)
    errors = validate_dashboard_manifest(data)
    if errors:
        raise ValueError(errors[0]["message"])
    cfg.yml_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{cfg.yml_path.name}.", suffix=".tmp", dir=cfg.yml_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            if text and not text.endswith("\n"):
                f.write("\n")
        os.replace(tmp_name, cfg.yml_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def update_manifest_from_dashboard(cfg: Config, payload: dict) -> dict:
    if payload.get("revision") is not None:
        require_manifest_revision(cfg, payload.get("revision"))
    if "text" in payload:
        text = str(payload.get("text", ""))
        if DASHBOARD_REDACTED_VALUE in text:
            try:
                import yaml
            except ImportError:
                raise ValueError("PyYAML is required to write the manifest")
            original = parse_manifest_text(load_manifest_text(cfg)) if cfg.yml_path.exists() else {}
            restored = _restore_redacted_values(parse_manifest_text(text), original)
            text = yaml.dump(restored, default_flow_style=False, sort_keys=False)
    elif isinstance(payload.get("manifest"), dict):
        try:
            import yaml
        except ImportError:
            raise ValueError("PyYAML is required to write the manifest")
        original = cfg.data if DASHBOARD_REDACTED_VALUE in json.dumps(payload["manifest"]) else {}
        manifest = _restore_redacted_values(payload["manifest"], original)
        text = yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    else:
        raise ValueError("Expected manifest text or structured manifest data")
    write_manifest_atomically(cfg, text)
    return {"ok": True, "path": str(cfg.yml_path)}


def replace_manifest_targets_text(text: str, targets: list[str]) -> str:
    lines = text.splitlines()
    output = []
    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("targets:") and not line.startswith((" ", "\t")):
            replaced = True
            output.append("targets:")
            i += 1
            suffixes = {}
            if line.strip() == "targets:":
                while i < len(lines):
                    current = lines[i]
                    stripped = current.strip()
                    if current and not current.startswith((" ", "\t")):
                        break
                    if stripped.startswith("- "):
                        value = stripped[2:]
                        name = value.split("#", 1)[0].strip()
                        suffix = ""
                        if "#" in value:
                            suffix = "  #" + value.split("#", 1)[1]
                        suffixes[name] = suffix
                    i += 1
            for target in targets:
                output.append(f"  - {target}{suffixes.get(target, '')}")
            continue
        output.append(line)
        i += 1
    if not replaced:
        target_block = ["targets:", *[f"  - {target}" for target in targets], ""]
        output = target_block + output
    return "\n".join(output) + ("\n" if text.endswith("\n") else "")


def update_manifest_targets(cfg: Config, targets: list[str], revision: str | None = None) -> dict:
    if revision is not None:
        require_manifest_revision(cfg, revision)
    if not isinstance(targets, list) or not targets:
        raise ValueError("Select at least one target")
    if any(not isinstance(target, str) or not target.strip() for target in targets):
        raise ValueError("Targets must be non-empty strings")
    clean_targets = canonical_targets(targets)
    if not clean_targets:
        raise ValueError("Select at least one target")
    text = load_manifest_text(cfg) if cfg.yml_path.exists() else ""
    write_manifest_atomically(cfg, replace_manifest_targets_text(text, clean_targets))
    return {"ok": True, "targets": clean_targets, "path": str(cfg.yml_path)}


def _remove_path(mapping: dict, path: list[str]):
    if not path or not isinstance(mapping, dict):
        return
    key = path[0]
    if key not in mapping:
        return
    if len(path) == 1:
        mapping.pop(key, None)
        return
    child = mapping.get(key)
    if isinstance(child, dict):
        _remove_path(child, path[1:])
        if not child:
            mapping.pop(key, None)


def _ordered_skill_names(states: dict[str, dict], available_order: list[str]) -> list[str]:
    ordered = [name for name in available_order if name in states]
    ordered.extend(name for name in states if name not in ordered)
    return ordered


def _set_skill_manual_only(pkg: dict, skill_name: str, manual_only: bool):
    overrides = pkg.setdefault("skill_overrides", {})
    if not isinstance(overrides, dict):
        overrides = {}
        pkg["skill_overrides"] = overrides
    override = overrides.setdefault(skill_name, {})
    if not isinstance(override, dict):
        override = {}
        overrides[skill_name] = override
    if manual_only:
        override["skill_frontmatter"] = deep_merge(
            override.get("skill_frontmatter", {}) if isinstance(override.get("skill_frontmatter"), dict) else {},
            {"disable-model-invocation": True},
        )
        override["agents_openai"] = deep_merge(
            override.get("agents_openai", {}) if isinstance(override.get("agents_openai"), dict) else {},
            {"policy": {"allow_implicit_invocation": False}},
        )
        return
    _remove_path(override, ["skill_frontmatter", "disable-model-invocation"])
    _remove_path(override, ["agents_openai", "policy", "allow_implicit_invocation"])
    if not override:
        overrides.pop(skill_name, None)
    if not overrides:
        pkg.pop("skill_overrides", None)


def update_manifest_package_skill_policy(cfg: Config, payload: dict) -> dict:
    if payload.get("revision") is not None:
        require_manifest_revision(cfg, payload.get("revision"))
    try:
        import yaml
    except ImportError:
        raise ValueError("PyYAML is required to write the manifest")
    if not isinstance(payload, dict):
        raise ValueError("Expected structured skill policy data")
    package_index = payload.get("package_index")
    if not isinstance(package_index, int):
        raise ValueError("package_index must be an integer")
    skills_payload = payload.get("skills")
    if not isinstance(skills_payload, list):
        raise ValueError("skills must be a list")
    original_text = load_manifest_text(cfg)
    manifest = parse_manifest_text(original_text)
    packages = manifest.get("packages", [])
    if not isinstance(packages, list) or package_index < 0 or package_index >= len(packages):
        raise ValueError("Unknown package")
    pkg = packages[package_index]
    if not isinstance(pkg, dict):
        raise ValueError("Package entry must be a mapping")
    package_name = _manifest_package_name(pkg)
    if payload.get("package") != package_name:
        raise ValueError("Package name does not match package_index")

    lock = cfg.load_lockfile() or {}
    lock_packages = lock.get("packages", []) if isinstance(lock.get("packages", []), list) else []
    lock_by_name = {entry.get("name"): entry for entry in lock_packages if isinstance(entry, dict)}
    available = build_package_skill_inventory(cfg, pkg, lock_by_name.get(package_name, {}), package_index)
    available_order = [skill["name"] for skill in available["skill_inventory"]]
    known = set(available_order)
    states = {}
    for item in skills_payload:
        if not isinstance(item, dict):
            raise ValueError("Skill policy rows must be mappings")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Skill name is required")
        if name not in known:
            raise ValueError(f"Unknown skill: {name}")
        if not isinstance(item.get("enabled"), bool) or not isinstance(item.get("manual_only"), bool):
            raise ValueError("enabled and manual_only must be booleans")
        states[name] = {"enabled": item["enabled"], "manual_only": item["manual_only"]}
    if set(states) != known:
        missing = sorted(known - set(states))
        raise ValueError(f"Missing skill policy rows: {', '.join(missing)}")

    enabled = [name for name in _ordered_skill_names(states, available_order) if states[name]["enabled"]]
    if len(enabled) == len(available_order):
        pkg.pop("skills", None)
    else:
        pkg["skills"] = enabled
    for name in _ordered_skill_names(states, available_order):
        _set_skill_manual_only(pkg, name, states[name]["manual_only"])

    text = yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    write_manifest_atomically(cfg, text)
    return {
        "ok": True,
        "package": package_name,
        "enabled_skills": enabled,
        "manual_only_skills": [name for name in _ordered_skill_names(states, available_order) if states[name]["manual_only"]],
        "path": str(cfg.yml_path),
    }


def find_skill_markdown(pkg_path: Path, skill_name: str) -> Path | None:
    if not pkg_path.is_dir():
        return None
    try:
        candidates = list(pkg_path.rglob("SKILL.md"))
    except OSError:
        return None
    for candidate in candidates:
        if skill_name_from_file(candidate, candidate.parent.name) == skill_name:
            return candidate
    for candidate in candidates:
        if candidate.parent.name == skill_name:
            return candidate
    return None


def inspect_skill_links(cfg: Config, target: str) -> dict:
    skill_dir = cfg.skill_path(target)
    result = {
        "path": _path_value(skill_dir),
        "exists": bool(skill_dir and skill_dir.exists()),
        "symlinks": 0,
        "broken": 0,
        "status": "missing",
    }
    if not skill_dir or not skill_dir.exists():
        return result
    links = [p for p in skill_dir.iterdir() if p.is_symlink()]
    broken = [p for p in links if not p.resolve(strict=False).exists()]
    result.update({
        "symlinks": len(links),
        "broken": len(broken),
        "status": "warning" if broken else "healthy",
    })
    return result


def _read_mcp_servers(cfg: Config, target: str, mcp_path: Path) -> tuple[dict, str | None]:
    try:
        if cfg.mcp_format(target) == "codex_toml":
            import tomllib
            with open(mcp_path, "rb") as f:
                data = tomllib.load(f)
            return data.get("mcp_servers", {}) or {}, None
        with open(mcp_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mcpServers", {}) or {}, None
    except Exception as exc:
        return {}, str(exc)


def inspect_mcp_config(cfg: Config, target: str, managed_names: set[str]) -> dict:
    mcp_path = cfg.mcp_path(target)
    result = {
        "path": _path_value(mcp_path),
        "exists": bool(mcp_path and mcp_path.exists()),
        "format": cfg.mcp_format(target),
        "server_count": 0,
        "managed_present": [],
        "managed_missing": sorted(managed_names),
        "status": "missing",
        "error": None,
    }
    if not mcp_path:
        result["status"] = "unsupported"
        return result
    if not mcp_path.exists():
        return result
    servers, error = _read_mcp_servers(cfg, target, mcp_path)
    if error:
        result.update({"status": "invalid", "error": error})
        return result
    names = set(servers.keys())
    present = sorted(names & managed_names)
    missing = sorted(managed_names - names)
    result.update({
        "server_count": len(servers),
        "managed_present": present,
        "managed_missing": missing,
        "status": "warning" if missing else "healthy",
    })
    return result


def inspect_hook_status(cfg: Config) -> dict:
    status = {}
    cursor_hooks = cfg.repo_dir / ".cursor" / "hooks.json"
    status["cursor"] = _inspect_json_hooks(cursor_hooks)
    if "codex" in cfg.targets:
        status["codex"] = _inspect_json_hooks(cfg.codex_hooks_path())
    return status


def _inspect_json_hooks(path: Path) -> dict:
    result = {"path": str(path), "exists": path.exists(), "count": 0, "status": "missing", "error": None}
    if not path.exists():
        return result
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        count = sum(len(v) for v in data.get("hooks", {}).values())
        result.update({"count": count, "status": "warning" if count > 10 else "healthy"})
    except Exception as exc:
        result.update({"status": "invalid", "error": str(exc)})
    return result


def _safe_targets(cfg: Config) -> list[str]:
    if cfg.yml_path.exists():
        return cfg.targets
    return list(CORE_DEFAULT_TARGETS)


def _redact_home_path(path: str | None, redact_home: bool) -> str | None:
    if path is None:
        return None
    if not redact_home:
        return path
    home = str(Path.home())
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def _target_skill_path_for_audit(cfg: Config, target: str) -> Path | None:
    return cfg.skill_path(target)


def _target_mcp_path_for_audit(cfg: Config, target: str) -> Path | None:
    return cfg.mcp_path(target)


def _target_root_path(cfg: Config, target: str) -> Path | None:
    skill_dir = _target_skill_path_for_audit(cfg, target)
    if skill_dir:
        return skill_dir.parent
    mcp_path = _target_mcp_path_for_audit(cfg, target)
    if mcp_path:
        return mcp_path.parent
    return None


def _lock_managed_mcp_names(
    lock: dict | None,
    target: str | None = None,
    configured_targets: list[str] | None = None,
) -> set[str]:
    if not lock:
        return set()
    managed = lock.get("mcps", {}).get("managed", []) if isinstance(lock.get("mcps"), dict) else []
    if target is None:
        return {mcp.get("name") for mcp in managed if isinstance(mcp, dict) and mcp.get("name")}
    defaults = configured_targets or CORE_DEFAULT_TARGETS
    return {
        mcp.get("name")
        for mcp in managed
        if isinstance(mcp, dict)
        and mcp.get("name")
        and target in mcp_targets(mcp, defaults)
    }


def _mcp_transport(entry: dict) -> str:
    if "serverUrl" in entry:
        return "url"
    if "url" in entry:
        return entry.get("type", "sse")
    return entry.get("type", "stdio")


def _audit_mcp_entry(name: str, entry: dict, managed_names: set[str]) -> dict:
    result = {
        "name": name,
        "managed": name in managed_names,
        "transport": _mcp_transport(entry) if isinstance(entry, dict) else "unknown",
        "env_keys": [],
        "header_keys": [],
    }
    if not isinstance(entry, dict):
        return result
    if result["transport"] == "stdio" or "command" in entry:
        result["command"] = entry.get("command")
        result["args"] = entry.get("args", []) if isinstance(entry.get("args", []), list) else []
    if "url" in entry:
        result["url"] = entry.get("url")
    if "serverUrl" in entry:
        result["url"] = entry.get("serverUrl")
    env = entry.get("env")
    if isinstance(env, dict):
        result["env_keys"] = sorted(str(key) for key in env)
    headers = entry.get("headers", entry.get("http_headers"))
    if isinstance(headers, dict):
        result["header_keys"] = sorted(str(key) for key in headers)
    return result


def _audit_mcp_config(cfg: Config, target: str, lock_managed_names: set[str]) -> dict:
    mcp_path = _target_mcp_path_for_audit(cfg, target)
    result = {
        "path": str(mcp_path) if mcp_path else None,
        "exists": bool(cfg.yml_path.exists() and mcp_path and mcp_path.exists()),
        "format": cfg.mcp_format(target),
        "servers": [],
        "managed": [],
        "unmanaged": [],
        "error": None,
    }
    if not mcp_path:
        result["status"] = "unsupported"
        return result
    if not cfg.yml_path.exists() or not mcp_path.exists():
        return result

    managed_names = set(lock_managed_names)
    if cfg.mcp_format(target) == "codex_toml":
        try:
            content = mcp_path.read_text(encoding="utf-8")
        except OSError as exc:
            result["error"] = str(exc)
            return result
        managed_names |= {name for name, _lines in Deployer._parse_codex_managed_entries(content)}

    servers, error = _read_mcp_servers(cfg, target, mcp_path)
    if error:
        result["error"] = error
        return result
    result["servers"] = [
        _audit_mcp_entry(name, entry, managed_names)
        for name, entry in sorted(servers.items())
    ]
    result["managed"] = [server["name"] for server in result["servers"] if server["managed"]]
    result["unmanaged"] = [server["name"] for server in result["servers"] if not server["managed"]]
    return result


def _path_points_into(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _is_nexus_skill_link(cfg: Config, link: Path) -> bool:
    dest = link.resolve(strict=False)
    return (
        _path_points_into(dest, cfg.cache_dir)
        or _path_points_into(dest, cfg.nexus_dir / "generated")
    )


def _symlink_is_stale(link: Path) -> bool:
    try:
        link.resolve(strict=True)
        return False
    except OSError:
        return True


def _audit_skills(cfg: Config, target: str) -> dict:
    skill_dir = _target_skill_path_for_audit(cfg, target)
    result = {
        "path": str(skill_dir) if skill_dir else None,
        "exists": bool(cfg.yml_path.exists() and skill_dir and skill_dir.exists()),
        "nexus_symlinks": [],
        "unmanaged_dirs": [],
        "stale_symlinks": [],
    }
    if not cfg.yml_path.exists() or not skill_dir or not skill_dir.exists():
        return result
    for child in sorted(skill_dir.iterdir(), key=lambda p: p.name):
        if child.is_symlink():
            if _symlink_is_stale(child):
                result["stale_symlinks"].append(child.name)
            elif _is_nexus_skill_link(cfg, child):
                result["nexus_symlinks"].append(child.name)
        elif child.is_dir():
            result["unmanaged_dirs"].append(child.name)
    return result


def _hook_path_for_target(cfg: Config, target: str) -> Path | None:
    if target == "claude":
        return cfg.repo_dir / ".github" / "hooks"
    if target == "cursor":
        return cfg.repo_dir / ".cursor" / "hooks.json"
    if target == "codex":
        return cfg.codex_hooks_path()
    return None


def _walk_hook_commands(value) -> list[str]:
    commands = []
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            commands.append(command)
        for item in value.values():
            commands.extend(_walk_hook_commands(item))
    elif isinstance(value, list):
        for item in value:
            commands.extend(_walk_hook_commands(item))
    return commands


def _audit_hooks(cfg: Config, target: str) -> dict:
    hook_path = _hook_path_for_target(cfg, target)
    result = {
        "path": str(hook_path) if hook_path else None,
        "exists": bool(hook_path and hook_path.exists()),
        "managed": 0,
        "unmanaged": 0,
        "files": 0,
        "error": None,
    }
    if not hook_path or not hook_path.exists():
        return result
    if hook_path.is_dir():
        result["files"] = sum(1 for child in hook_path.iterdir() if child.is_file())
        result["unmanaged"] = result["files"]
        return result
    try:
        data = json.loads(hook_path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["error"] = str(exc)
        return result
    commands = _walk_hook_commands(data.get("hooks", {}))
    result["managed"] = sum(1 for command in commands if "--nexus-package" in command)
    result["unmanaged"] = len(commands) - result["managed"]
    return result


def build_audit_model(cfg: Config, targets: list[str] | None = None, redact_home: bool = False) -> dict:
    selected_targets = targets or _safe_targets(cfg)
    lock = cfg.load_lockfile()
    target_rows = []
    for target in selected_targets:
        managed_names = _lock_managed_mcp_names(lock, target, cfg.targets)
        root = _target_root_path(cfg, target)
        target_rows.append({
            "name": target,
            "root": {
                "path": _redact_home_path(str(root) if root else None, redact_home),
                "exists": bool(root and root.exists()),
            },
            "skills": _audit_skills(cfg, target),
            "mcp": _audit_mcp_config(cfg, target, managed_names),
            "hooks": _audit_hooks(cfg, target),
        })
    for row in target_rows:
        for section in ["skills", "mcp", "hooks"]:
            if row[section].get("path"):
                row[section]["path"] = _redact_home_path(row[section]["path"], redact_home)
    return {
        "meta": {
            "nexus_version": NEXUS_VERSION,
            "manifest_path": _redact_home_path(str(cfg.yml_path), redact_home),
            "manifest_exists": cfg.yml_path.exists(),
            "lockfile_path": _redact_home_path(str(cfg.lockfile_path), redact_home),
            "lockfile_exists": cfg.lockfile_path.exists(),
        },
        "targets": target_rows,
    }


def _print_audit_text(model: dict):
    info("nexus audit")
    print(file=sys.stderr)
    print("Targets:", file=sys.stderr)
    for target in model["targets"]:
        marker = "+" if target["root"]["exists"] else "-"
        print(f"  {marker} {target['name']}: {target['root']['path'] or 'not configured'}", file=sys.stderr)

    print(file=sys.stderr)
    print("MCP servers:", file=sys.stderr)
    for target in model["targets"]:
        mcp = target["mcp"]
        if mcp["error"]:
            print(f"  {target['name']}: invalid ({mcp['error']})", file=sys.stderr)
            continue
        managed = ", ".join(mcp["managed"]) or "none"
        unmanaged = ", ".join(mcp["unmanaged"]) or "none"
        print(f"  {target['name']}:", file=sys.stderr)
        print(f"    nexus-managed: {managed}", file=sys.stderr)
        print(f"    unmanaged: {unmanaged}", file=sys.stderr)

    print(file=sys.stderr)
    print("Skills:", file=sys.stderr)
    for target in model["targets"]:
        skills = target["skills"]
        if not skills["exists"]:
            print(f"  {target['name']}: not found", file=sys.stderr)
            continue
        print(
            f"  {target['name']}: {len(skills['nexus_symlinks'])} Nexus symlinks, "
            f"{len(skills['unmanaged_dirs'])} unmanaged dirs, "
            f"{len(skills['stale_symlinks'])} stale symlinks",
            file=sys.stderr,
        )

    print(file=sys.stderr)
    print("Hooks:", file=sys.stderr)
    for target in model["targets"]:
        hooks = target["hooks"]
        if not hooks["path"]:
            print(f"  {target['name']}: not supported", file=sys.stderr)
        elif not hooks["exists"]:
            print(f"  {target['name']}: not found ({hooks['path']})", file=sys.stderr)
        elif hooks["error"]:
            print(f"  {target['name']}: invalid ({hooks['error']})", file=sys.stderr)
        elif hooks["files"]:
            print(f"  {target['name']}: {hooks['files']} hook files ({hooks['path']})", file=sys.stderr)
        else:
            print(f"  {target['name']}: {hooks['managed']} managed commands, {hooks['unmanaged']} unmanaged commands", file=sys.stderr)


def cmd_audit(cfg: Config, args):
    targets = canonical_targets([args.target]) if getattr(args, "target", None) else None
    model = build_audit_model(cfg, targets, getattr(args, "redact_home", False))
    if getattr(args, "json", False):
        print(json.dumps(model, indent=2, sort_keys=False))
        return
    print()
    _print_audit_text(model)
    print()


def _manifest_package_name(pkg: dict) -> str:
    if pkg.get("name"):
        return pkg["name"]
    if pkg.get("repo"):
        return str(pkg["repo"]).split("/", 1)[-1]
    if pkg.get("path"):
        return Path(str(pkg["path"])).name
    return "unknown"


def _skill_override(manifest_packages: list[dict], pkg_name: str, skill_name: str) -> dict:
    for pkg in manifest_packages:
        if _manifest_package_name(pkg) != pkg_name:
            continue
        overrides = pkg.get("skill_overrides", {}) if isinstance(pkg.get("skill_overrides"), dict) else {}
        skill_override = overrides.get(skill_name, {}) if isinstance(overrides.get(skill_name, {}), dict) else {}
        return skill_override if isinstance(skill_override, dict) else {}
    return {}


def _package_cost_metadata(manifest_packages: list[dict], pkg_name: str, skill_name: str) -> dict:
    skill_override = _skill_override(manifest_packages, pkg_name, skill_name)
    return skill_override.get("cost", {}) if isinstance(skill_override.get("cost"), dict) else {}


def package_skill_manual_only(pkg: dict, skill_name: str) -> bool:
    override = skill_override(pkg, skill_name)
    frontmatter = override.get("skill_frontmatter") if isinstance(override, dict) else None
    if isinstance(frontmatter, dict) and frontmatter.get("disable-model-invocation") is True:
        return True
    agents_openai = override.get("agents_openai") if isinstance(override, dict) else None
    policy = agents_openai.get("policy") if isinstance(agents_openai, dict) else None
    return isinstance(policy, dict) and policy.get("allow_implicit_invocation") is False


def package_skill_enabled(pkg: dict, skill_name: str) -> bool:
    configured = pkg.get("skills")
    if configured is None:
        return True
    if not isinstance(configured, list):
        return False
    return skill_name in configured


def _skill_implicit_invocation_enabled(manifest_packages: list[dict], pkg_name: str, skill_name: str) -> bool:
    for pkg in manifest_packages:
        if _manifest_package_name(pkg) == pkg_name:
            return not package_skill_manual_only(pkg, skill_name)
    return True


def _lock_package_source_path(lock_entry: dict) -> str | None:
    source = lock_entry.get("source") if isinstance(lock_entry.get("source"), dict) else {}
    for key in ["cache_path", "path"]:
        value = source.get(key)
        if value:
            return str(value)
    value = lock_entry.get("path")
    return str(value) if value else None


def dashboard_package_source_path(cfg: Config, pkg_spec: dict | None, lock_entry: dict | None) -> Path | None:
    lock_entry = lock_entry or {}
    value = _lock_package_source_path(lock_entry)
    if value:
        candidate = Path(str(value)).expanduser()
        if candidate.exists():
            return candidate
    if isinstance(pkg_spec, dict) and pkg_spec.get("path"):
        candidate = Path(str(pkg_spec["path"])).expanduser()
        if not candidate.is_absolute():
            candidate = cfg.repo_dir / candidate
        if candidate.exists():
            return candidate
    return None


def _skill_names_from_fallbacks(pkg_spec: dict | None, lock_entry: dict | None) -> list[str]:
    names = []
    lock_entry = lock_entry or {}
    for name in lock_entry.get("discovered", {}).get("skills", []) or []:
        if isinstance(name, str) and name not in names:
            names.append(name)
    if isinstance(pkg_spec, dict):
        for name in pkg_spec.get("skills", []) or []:
            if isinstance(name, str) and name not in names:
                names.append(name)
        overrides = pkg_spec.get("skill_overrides", {}) if isinstance(pkg_spec.get("skill_overrides"), dict) else {}
        for name in overrides:
            if isinstance(name, str) and name not in names:
                names.append(name)
    return names


def discover_dashboard_package_skills(cfg: Config, pkg_spec: dict | None, lock_entry: dict | None) -> list[dict]:
    pkg_name = _manifest_package_name(pkg_spec or lock_entry or {})
    source_path = dashboard_package_source_path(cfg, pkg_spec, lock_entry)
    if source_path:
        discovered = PackageManager.discover(
            source_path,
            pkg_name,
            pkg_spec.get("sparse_paths") if isinstance(pkg_spec, dict) else None,
        )
        return [
            {"name": skill["name"], "path": skill.get("path"), "source": "local"}
            for skill in discovered.get("skills", [])
            if isinstance(skill.get("name"), str)
        ]
    return [{"name": name, "path": None, "source": "manifest/lockfile"} for name in _skill_names_from_fallbacks(pkg_spec, lock_entry)]


def build_package_skill_inventory(cfg: Config, pkg_spec: dict | None, lock_entry: dict | None, index: int | None) -> dict:
    pkg_spec = pkg_spec or {}
    lock_entry = lock_entry or {}
    deployed_skills = set(lock_entry.get("discovered", {}).get("skills", []) or [])
    deployed_to = lock_entry.get("deployed_to", []) or []
    skills = []
    for skill in discover_dashboard_package_skills(cfg, pkg_spec, lock_entry):
        name = skill["name"]
        skill_file = Path(skill["path"]) / "SKILL.md" if skill.get("path") else None
        static_tokens = 0
        token_source = "unknown"
        if skill_file and skill_file.is_file():
            try:
                static_tokens = estimate_tokens(skill_file.read_text(encoding="utf-8"))
                token_source = str(skill_file)
            except OSError:
                pass
        enabled = package_skill_enabled(pkg_spec, name) if pkg_spec else name in deployed_skills
        manual_only = package_skill_manual_only(pkg_spec, name) if pkg_spec else False
        skills.append({
            "name": name,
            "enabled": enabled,
            "manual_only": manual_only,
            "implicit_invocation": enabled and not manual_only,
            "deployed": name in deployed_skills,
            "deployed_to": deployed_to if name in deployed_skills else [],
            "static_tokens": static_tokens,
            "token_source": token_source,
            "source": skill.get("source", "unknown"),
        })
    enabled_count = sum(1 for skill in skills if skill["enabled"])
    manual_count = sum(1 for skill in skills if skill["manual_only"])
    mode = "all" if pkg_spec.get("skills") is None else "allowlist"
    return {
        "index": index,
        "skill_policy": {
            "mode": mode,
            "auto_enable_new_skills": mode == "all",
            "enabled_count": enabled_count,
            "available_count": len(skills),
            "disabled_count": len(skills) - enabled_count,
            "manual_only_count": manual_count,
            "editable": index is not None,
        },
        "skill_inventory": skills,
    }


def _cost_estimate(cost: dict) -> dict:
    tokens = cost.get("estimated_tokens_per_call", cost.get("estimated_tokens_per_invocation"))
    price = cost.get("estimated_usd_per_1k_tokens")
    estimated_usd = None
    if isinstance(tokens, (int, float)) and isinstance(price, (int, float)):
        estimated_usd = round((tokens / 1000) * price, 6)
    return {
        "metadata": cost,
        "estimated_tokens": tokens if isinstance(tokens, (int, float)) else None,
        "estimated_usd": estimated_usd,
    }


def build_dashboard_model(cfg: Config) -> dict:
    data = cfg.data_or_empty() if hasattr(cfg, "data_or_empty") else cfg.data
    lock = cfg.load_lockfile() or {}
    lock_packages = lock.get("packages", []) if isinstance(lock.get("packages", []), list) else []
    managed_mcps = lock.get("mcps", {}).get("managed", []) if isinstance(lock.get("mcps"), dict) else []
    managed_names = {
        mcp.get("name")
        for mcp in managed_mcps
        if isinstance(mcp, dict) and mcp.get("name")
    }
    hook_status = inspect_hook_status(cfg)
    target_rows = []
    warnings = []

    for target in cfg.targets:
        target_managed_names = {
            mcp.get("name")
            for mcp in managed_mcps
            if isinstance(mcp, dict)
            and mcp.get("name")
            and target in mcp_targets(mcp, cfg.targets)
        }
        skill_status = inspect_skill_links(cfg, target)
        mcp_status = inspect_mcp_config(cfg, target, target_managed_names)
        target_hook = hook_status.get(target)
        states = [state for state in [skill_status["status"], mcp_status["status"]] if state != "unsupported"]
        if target_hook and target_hook["status"] != "unsupported":
            states.append(target_hook["status"])
        if "invalid" in states:
            overall = "invalid"
        elif "warning" in states:
            overall = "warning"
        elif all(state == "healthy" for state in states):
            overall = "healthy"
        else:
            overall = "missing"
        if skill_status["broken"]:
            warnings.append(f"{target} has {skill_status['broken']} broken skill links")
        if mcp_status["status"] == "invalid":
            warnings.append(f"{target} MCP config is invalid")
        safe_skills = {**skill_status, "path": dashboard_path(skill_status.get("path"), cfg)}
        safe_mcp = {**mcp_status, "path": dashboard_path(mcp_status.get("path"), cfg)}
        safe_hooks = ({**target_hook, "path": dashboard_path(target_hook.get("path"), cfg)} if target_hook else None)
        target_rows.append({
            "id": target,
            "name": target,
            "display": TARGET_REGISTRY.get(target, {}).get("display", target),
            "skill_path": safe_skills["path"],
            "mcp_path": safe_mcp["path"],
            "skills": safe_skills,
            "mcp": safe_mcp,
            "hooks": safe_hooks,
            "support": TARGET_REGISTRY.get(target, {}).get("status", {}),
            "status": overall,
        })

    packages = []
    lock_by_name = {pkg.get("name"): pkg for pkg in lock_packages if isinstance(pkg, dict)}
    for index, pkg in enumerate(data.get("packages", []) or []):
        if not isinstance(pkg, dict):
            continue
        name = _manifest_package_name(pkg)
        lock_entry = lock_by_name.get(name, {})
        skill_inventory = build_package_skill_inventory(cfg, pkg, lock_entry, index)
        packages.append({
            "index": index,
            "name": name,
            "repo": pkg.get("repo"),
            "path": pkg.get("path"),
            "deploy_targets": pkg.get("targets", cfg.targets),
            "uses_global_targets": "targets" not in pkg,
            "skills": pkg.get("skills"),
            "hooks": pkg.get("hooks"),
            "sparse_paths": pkg.get("sparse_paths", []),
            "discovered": lock_entry.get("discovered", {}),
            "deployed_to": lock_entry.get("deployed_to", []),
            "overlays": lock_entry.get("overlays", []),
            **skill_inventory,
        })
    manifest_package_names = {p["name"] for p in packages}
    for pkg in lock_packages:
        if pkg.get("name") not in manifest_package_names:
            skill_inventory = build_package_skill_inventory(cfg, None, pkg, None)
            packages.append({
                "index": None,
                "name": pkg.get("name"),
                "repo": None,
                "path": pkg.get("path"),
                "deploy_targets": pkg.get("deployed_to", []),
                "uses_global_targets": False,
                "skills": None,
                "hooks": None,
                "sparse_paths": [],
                "discovered": pkg.get("discovered", {}),
                "deployed_to": pkg.get("deployed_to", []),
                "overlays": pkg.get("overlays", []),
                **skill_inventory,
            })
    available_package_skills = sum(pkg.get("skill_policy", {}).get("available_count", 0) for pkg in packages)
    disabled_package_skills = sum(pkg.get("skill_policy", {}).get("disabled_count", 0) for pkg in packages)
    manual_only_package_skills = sum(pkg.get("skill_policy", {}).get("manual_only_count", 0) for pkg in packages)

    skills = []
    total_skill_tokens = 0
    implicit_skill_tokens = 0
    implicit_skill_count = 0
    for pkg in lock_packages:
        pkg_name = pkg.get("name", "unknown")
        pkg_path = Path(pkg.get("path", ""))
        overlays = pkg.get("overlays", []) if isinstance(pkg.get("overlays", []), list) else []
        for skill_name in pkg.get("discovered", {}).get("skills", []) or []:
            skill_file = find_skill_markdown(pkg_path, skill_name)
            estimate_source = None
            token_estimate = None
            if skill_file:
                try:
                    token_estimate = estimate_tokens(skill_file.read_text(encoding="utf-8"))
                    estimate_source = str(skill_file)
                except OSError:
                    token_estimate = None
            if token_estimate is None:
                token_estimate = 0
                estimate_source = "unknown"
            total_skill_tokens += token_estimate
            implicit_enabled = _skill_implicit_invocation_enabled(
                data.get("packages", []) or [], pkg_name, skill_name
            )
            if implicit_enabled:
                implicit_skill_tokens += token_estimate
                implicit_skill_count += 1
            cost = _package_cost_metadata(data.get("packages", []) or [], pkg_name, skill_name)
            skills.append({
                "name": skill_name,
                "package": pkg_name,
                "deployed_to": pkg.get("deployed_to", []),
                "overlays": [o for o in overlays if o.get("skill") == skill_name],
                "implicit_invocation": implicit_enabled,
                "token_consumption": {
                    "static_tokens": token_estimate,
                    "source": estimate_source,
                },
                "static_tokens": token_estimate,
                "token_source": estimate_source,
                "cost": _cost_estimate(cost),
            })

    declared_mcps = []
    for mcp in data.get("mcps", []) or []:
        if isinstance(mcp, dict):
            declared_mcps.append((mcp, bool(mcp.get("optional"))))
    for mcp in data.get("optional_mcps", []) or []:
        if isinstance(mcp, dict):
            declared_mcps.append((mcp, True))

    mcps = []
    total_mcp_tokens = 0
    for mcp, optional in declared_mcps:
        clean = sanitize_mcp(mcp)
        footprint_text = json.dumps(clean, sort_keys=True)
        static_tokens = estimate_tokens(footprint_text)
        total_mcp_tokens += static_tokens
        name = clean.get("name")
        mcps.append({
            **clean,
            "optional": optional,
            "included_in_lockfile": name in managed_names,
            "token_consumption": {
                "static_tokens": static_tokens,
                "source": "sanitized MCP config",
            },
            "static_tokens": static_tokens,
            "cost": _cost_estimate(mcp.get("cost", {}) if isinstance(mcp.get("cost"), dict) else {}),
            "targets": {
                target["name"]: name in set(target["mcp"].get("managed_present", []))
                for target in target_rows
            },
        })

    manifest_exists = cfg.yml_path.exists()
    lockfile_exists = cfg.lockfile_path.exists()
    if not lockfile_exists:
        warnings.append(f"{cfg.lockfile_path.name} missing; preview and deploy to populate discovered assets")
    manifest_revision = cfg.manifest_revision() if hasattr(cfg, "manifest_revision") else None
    lock_current = bool(lockfile_exists and lock.get("manifest_revision") == manifest_revision)
    if not manifest_exists:
        stage, next_action = "uninitialized", "initialize"
    elif not lockfile_exists:
        stage, next_action = "configured", "preview"
    elif not lock_current:
        stage, next_action = "needs-preview", "preview"
    elif warnings:
        stage, next_action = "needs-attention", "inspect-health"
    else:
        stage, next_action = "healthy", "inspect-health"

    model = {
        "meta": {
            "nexus_version": NEXUS_VERSION,
            "manifest_path": str(cfg.yml_path),
            "lockfile_path": str(cfg.lockfile_path),
            "manifest_exists": manifest_exists,
            "manifest_revision": manifest_revision,
            "lockfile_exists": lockfile_exists,
            "lockfile_current": lock_current,
            "lockfile_generated_at": lock.get("generated_at"),
            "generated_at": _now_iso(),
        },
        "lifecycle": {
            "stage": stage,
            "manifest_ready": manifest_exists,
            "preview_ready": False,
            "deployed": lockfile_exists,
            "health_ready": lock_current and not warnings,
            "next_action": next_action,
        },
        "summary": {
            "targets": len(cfg.targets),
            "packages": len(packages),
            "skills": len(skills),
            "implicit_skills": implicit_skill_count,
            "managed_mcps": len(managed_names),
            "declared_mcps": len(mcps),
            "warnings": len(warnings),
            "skill_static_tokens": implicit_skill_tokens,
            "all_skill_static_tokens": total_skill_tokens,
            "mcp_static_tokens": total_mcp_tokens,
            "available_package_skills": available_package_skills,
            "disabled_package_skills": disabled_package_skills,
            "manual_only_package_skills": manual_only_package_skills,
        },
        "deployment": {
            "global_targets": cfg.targets,
            "available_targets": list(dict.fromkeys([*TARGET_REGISTRY.keys(), *cfg.targets])),
            "target_catalog": [
                {"id": target, "display": entry.get("display", target), "status": entry.get("status", {}), "core": bool(entry.get("default"))}
                for target, entry in TARGET_REGISTRY.items()
            ],
            "default_to_all": cfg.targets == skill_target_names(),
        },
        "manifest": sanitize_manifest(data),
        "packages": packages,
        "skills": skills,
        "mcps": mcps,
        "targets": target_rows,
        "actions": {
            "can_save_manifest": cfg.yml_path.exists(),
            "can_dry_run": cfg.yml_path.exists(),
            "can_deploy": cfg.yml_path.exists(),
        },
        "warnings": warnings,
    }
    return sanitize_dashboard_paths(model, cfg)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict):
    body = json.dumps(payload, indent=2, sort_keys=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _text_response(handler: BaseHTTPRequestHandler, status: int, text: str, content_type: str = "text/plain; charset=utf-8"):
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _capture_sync(cfg: Config, args: SimpleNamespace) -> dict:
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            cmd_sync(cfg, args)
        stderr_text = stderr.getvalue()
        plan_hash = None
        for line in stderr_text.splitlines():
            if "Plan:" in line:
                plan_hash = line.split("Plan:", 1)[1].strip().split()[0]
                break
        return {
            "ok": True,
            "stdout": stdout.getvalue(),
            "stderr": stderr_text,
            "plan_hash": plan_hash,
            "manifest_revision": cfg.manifest_revision() if hasattr(cfg, "manifest_revision") else None,
        }
    except SystemExit as exc:
        return {"ok": False, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "exit_code": exc.code}
    except Exception as exc:
        return {"ok": False, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(), "error": str(exc)}


def _dashboard_sync_args(payload: dict, dry_run: bool) -> SimpleNamespace:
    return SimpleNamespace(
        all=bool(payload.get("all", False)),
        include_optional=list(payload.get("include_optional", []) or []),
        no_optional=bool(payload.get("no_optional", True)),
        dry_run=dry_run,
        yes=not dry_run,
    )


def run_dashboard_sync_action(cfg: Config, action: str, payload: dict | None = None) -> dict:
    payload = payload or {}
    if action == "dry-run":
        return _capture_sync(cfg, _dashboard_sync_args(payload, True))
    if action == "deploy":
        if payload.get("confirm") != "deploy":
            return {"ok": False, "error": "Type deploy to confirm."}
        require_manifest_revision(cfg, payload.get("manifest_revision"))
        preview = _capture_sync(cfg, _dashboard_sync_args(payload, True))
        if not preview.get("ok") or not payload.get("plan_hash") or preview.get("plan_hash") != payload.get("plan_hash"):
            return {"ok": False, "error": "The reviewed plan is missing or stale. Run Preview again."}
        result = _capture_sync(cfg, _dashboard_sync_args(payload, False))
        result["reviewed_plan_hash"] = payload.get("plan_hash")
        return result
    return {"ok": False, "error": "Unknown dashboard action"}


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body or "{}")


def render_dashboard_html() -> str:
    return r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Local review console for Agent Nexus workspace packages, targets, health, and deployment plans.">
<title>Agent Nexus Dashboard</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23071018'/%3E%3Cpath d='M32 9 49 17v13c0 11-7 20-17 25-10-5-17-14-17-25V17l17-8Z' fill='none' stroke='%2331d0aa' stroke-width='4' stroke-linejoin='round'/%3E%3Cpath d='M22 33h20M32 23v20' stroke='%2365a7ff' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E">
<style>
:root {
  color-scheme: dark;
  --bg: #071018;
  --panel: #0b1520;
  --panel-soft: #101c29;
  --panel-subtle: #0e1924;
  --border: #223446;
  --border-soft: #172838;
  --text: #eef7ff;
  --text-soft: #c4d3e2;
  --text-muted: #94a7b8;
  --accent: #31d0aa;
  --accent-quiet: rgba(49, 208, 170, .12);
  --blue: #65a7ff;
  --good: #68e39b;
  --warn: #ffd166;
  --bad: #ff7a6f;
  --code: #e8f2ff;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100dvh;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: radial-gradient(circle at top left, rgba(49, 208, 170, .08), transparent 34rem), var(--bg);
  color: var(--text);
}
button, textarea, pre, input { font: inherit; }
.shell { width: min(1180px, calc(100vw - 32px)); margin: 0 auto; }
header { padding: 24px 0 12px; border-bottom: 1px solid var(--border-soft); }
.topbar { display:flex; justify-content:space-between; align-items:flex-start; gap: 24px; }
.brand { display:flex; align-items:flex-start; gap: 13px; min-width: 0; }
.mark { flex:0 0 auto; width: 36px; height: 36px; border-radius: 10px; display:grid; place-items:center; background: var(--accent-quiet); border:1px solid rgba(49,208,170,.28); color: var(--accent); }
.mark svg { width: 23px; height: 23px; }
h1 { margin: 0; font-size: 24px; line-height: 1.15; letter-spacing: -.025em; text-wrap: balance; }
.lede { max-width: 720px; margin: 6px 0 0; color: var(--text-soft); font-size: 14px; line-height: 1.55; text-wrap: pretty; }
.pathline { margin-top: 9px; color: var(--text-muted); font-size: 12px; word-break: break-word; }
.toolbar { display:flex; gap:8px; justify-content:flex-end; flex-wrap:wrap; }
button {
  border: 1px solid var(--border);
  background: var(--panel-soft);
  color: var(--text);
  border-radius: 10px;
  padding: 9px 12px;
  font-weight: 720;
  cursor: pointer;
  transition: background .16s ease, border-color .16s ease, transform .16s ease;
}
button:hover { background:#142232; border-color:#35506a; }
button:active { transform: translateY(1px); }
button.primary { background: var(--accent); border-color: transparent; color: #03100d; }
button.primary:hover { background:#48dec0; }
button.danger { border-color: rgba(255,122,111,.44); color:#ffd9d5; background: rgba(255,122,111,.10); }
button:focus-visible, textarea:focus-visible, input:focus-visible, summary:focus-visible { outline: 3px solid rgba(49, 208, 170, .42); outline-offset: 2px; }
.safety-row { display:flex; flex-wrap:wrap; gap: 14px; margin-top: 14px; color: var(--text-muted); font-size: 12px; }
.safety-chip { display:inline-flex; align-items:center; gap:7px; }
.safety-chip::before { content:""; width:6px; height:6px; border-radius:999px; background: var(--accent); }
main { padding: 18px 0 44px; }
.overview-grid { display:grid; grid-template-columns: minmax(280px, 1.7fr) repeat(3, minmax(140px, .75fr)); gap: 10px; }
.readiness-card, .stat-card, .package-card, .health-card { border:1px solid var(--border); border-radius: 16px; background: rgba(11, 21, 32, .92); box-shadow: 0 18px 44px rgba(0,0,0,.16); }
.readiness-card { padding: 18px; min-height: 142px; display:flex; flex-direction:column; justify-content:space-between; }
.readiness-label { color: var(--text-muted); font-size: 12px; font-weight: 780; text-transform: uppercase; letter-spacing: .08em; }
.readiness-title { margin-top: 7px; font-size: 26px; font-weight: 860; letter-spacing: -.035em; }
.readiness-detail { margin-top: 7px; color: var(--text-soft); font-size: 13px; line-height: 1.5; max-width: 52rem; }
.readiness-meta { display:flex; flex-wrap:wrap; gap: 8px; margin-top: 14px; }
.next-step { display:flex; align-items:center; justify-content:space-between; gap: 12px; margin-top: 14px; padding: 10px; border:1px solid var(--border-soft); border-radius: 12px; background: rgba(255,255,255,.025); }
.next-step strong { display:block; font-size: 13px; }
.next-step span { display:block; margin-top: 3px; color: var(--text-muted); font-size: 12px; }
.stat-card { padding: 14px; min-height: 142px; }
.stat-value { font-size: 26px; font-weight: 850; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.stat-label { margin-top: 5px; color: var(--text-soft); font-size: 13px; font-weight: 760; }
.stat-detail { margin-top: 8px; color: var(--text-muted); font-size: 12px; line-height: 1.45; }
.tone-good { color: var(--good); } .tone-warn { color: var(--warn); }
.tabs { display:flex; gap: 4px; margin: 16px 0 10px; border-bottom:1px solid var(--border-soft); }
.tab { border:0; border-bottom: 2px solid transparent; border-radius: 0; padding: 10px 12px; background: transparent; color: var(--text-muted); }
.tab strong { font-size: 14px; font-weight: 760; }
.tab.active { color: var(--text); border-bottom-color: var(--accent); background: transparent; }
section { display:none; padding-top: 12px; }
section.active { display:block; }
.section-head { display:flex; align-items:flex-end; justify-content:space-between; gap: 16px; margin: 0 0 14px; }
h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
h3 { margin: 22px 0 10px; font-size: 15px; }
.helper { color: var(--text-muted); font-size: 13px; line-height: 1.5; }
.panel { border:1px solid var(--border); border-radius: 14px; background: var(--panel); padding: 14px; }
.table-wrap { overflow:auto; border: 1px solid var(--border-soft); border-radius: 12px; background: #08121c; }
table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 680px; }
th, td { text-align:left; padding: 11px 10px; border-bottom: 1px solid rgba(255,255,255,.065); vertical-align: middle; }
th { color: var(--text-muted); font-size: 11px; font-weight: 780; }
tr:last-child td { border-bottom: 0; }
.name-cell { font-weight: 780; color: #f7fbff; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; }
.pill { display:inline-flex; align-items:center; gap:7px; border-radius:999px; padding:4px 8px; border:1px solid var(--border); font-size:12px; font-weight:760; white-space: nowrap; background: rgba(255,255,255,.03); }
.pill::before { content:""; width:6px; height:6px; border-radius:999px; background: currentColor; }
.healthy { color: var(--good); } .warning { color: var(--warn); } .invalid, .missing { color: var(--bad); } .unknown { color: var(--text-muted); }
.token-meter { display:inline-flex; align-items:center; gap:6px; color: var(--text-soft); }
.token-bar { display:none; }
.target-grid { display:flex; flex-wrap:wrap; gap: 8px; margin: 12px 0; }
.target-chip { display:inline-flex; align-items:center; gap:8px; padding:8px 10px; border:1px solid var(--border); border-radius:999px; background: var(--panel-subtle); color:var(--text); font-weight:720; }
.target-chip input, .skill-policy-table input { accent-color: var(--accent); }
details { border:1px solid var(--border); border-radius: 14px; background: var(--panel); }
details + details { margin-top: 10px; }
summary { cursor:pointer; list-style:none; padding: 13px 14px; display:flex; justify-content:space-between; align-items:center; gap:12px; }
summary::-webkit-details-marker { display:none; }
summary::after { content:"Open"; color: var(--text-muted); font-size:12px; }
details[open] > summary { border-bottom:1px solid var(--border-soft); }
details[open] > summary::after { content:"Close"; }
.disclosure-body { padding: 14px; }
.skill-control-panel { margin: 10px 0; }
.skill-control-title { display:flex; flex-direction:column; gap:3px; min-width:0; }
.skill-control-title h4 { margin:0; font-size:15px; }
.skill-policy-table table { min-width: 720px; }
.inline-check { display:inline-flex; align-items:center; gap:7px; font-weight:720; }
.source-badge { display:inline-flex; border:1px solid var(--border); border-radius:999px; padding:3px 7px; color:var(--text-muted); font-size:11px; font-weight:720; }
textarea { width:100%; min-height: 420px; resize: vertical; border:1px solid var(--border); border-radius:12px; padding:14px; background: #06111b; color: var(--code); font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre { overflow:auto; white-space:pre-wrap; background:#06111b; padding:12px; border-radius:10px; border:1px solid var(--border-soft); color: var(--code); font-size:12px; }
.notice { padding: 11px 13px; background: rgba(49, 208, 170, .08); border:1px solid rgba(49, 208, 170, .22); border-radius: 12px; margin-bottom: 12px; color:#dffbf5; font-size:13px; line-height:1.45; }
.sync-result { margin-top: 12px; }
.notice.warn { background: rgba(255, 209, 102, .09); border-color: rgba(255, 209, 102, .26); color: #fff1ca; }
.empty-state { padding: 14px; border:1px dashed var(--border); border-radius: 12px; color: var(--text-muted); background: rgba(255,255,255,.025); }
.row-actions { display:flex; flex-wrap:wrap; gap:10px; margin: 12px 0; }
.small { font-size: 12px; }
.workflow-list { display:grid; gap: 8px; grid-template-columns: repeat(5, minmax(120px, 1fr)); margin-top: 12px; }
.workflow-list div { padding:10px; border:1px solid var(--border-soft); border-radius:14px; background: rgba(255,255,255,.025); }
.workflow-list div.complete { border-color:rgba(104,227,155,.42); background:rgba(104,227,155,.08); }
.workflow-list div.current { border-color:rgba(49,208,170,.6); background:var(--accent-quiet); }
.workflow-list div.attention { border-color:rgba(255,209,102,.48); background:rgba(255,209,102,.08); }
.workflow-list strong { display:block; margin-bottom:4px; font-size: 12px; }
.package-grid, .health-grid { display:grid; gap: 10px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.skip-link { position:fixed; left:12px; top:-80px; z-index:20; background:var(--accent); color:#03100d; padding:10px 14px; border-radius:8px; }
.skip-link:focus { top:12px; }
.sr-status { min-height:1px; }
dialog { width:min(520px, calc(100vw - 32px)); border:1px solid var(--border); border-radius:16px; padding:20px; background:var(--panel); color:var(--text); }
dialog::backdrop { background:rgba(0,0,0,.72); }
dialog input { width:100%; margin-top:10px; border:1px solid var(--border); border-radius:10px; padding:10px; background:#06111b; color:var(--text); }
.package-card, .health-card { padding: 14px; }
.card-top { display:flex; align-items:flex-start; justify-content:space-between; gap: 12px; }
.card-title { margin:0; font-size: 15px; font-weight: 820; }
.card-subtitle { margin-top: 4px; color: var(--text-muted); font-size: 12px; word-break: break-word; }
.card-facts { display:grid; gap: 8px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 14px; }
.fact { border:1px solid var(--border-soft); border-radius: 10px; padding: 9px; background: rgba(255,255,255,.025); }
.fact strong { display:block; font-size: 13px; }
.fact span { display:block; margin-top: 3px; color: var(--text-muted); font-size: 11px; }
.asset-row { display:flex; flex-wrap:wrap; gap: 6px; margin-top: 12px; }
.asset-chip { display:inline-flex; align-items:center; gap: 5px; border:1px solid var(--border-soft); border-radius: 999px; padding: 4px 7px; color: var(--text-soft); background: rgba(255,255,255,.025); font-size: 11px; font-weight: 720; }
.target-group { margin-top: 12px; }
.target-group-title { color: var(--text-soft); font-size: 12px; font-weight: 780; text-transform: uppercase; letter-spacing: .07em; }
@media (max-width: 900px) { .topbar { flex-direction:column; } .toolbar { justify-content:flex-start; } .overview-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .readiness-card { grid-column: 1 / -1; } .workflow-list, .package-grid, .health-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 620px) { .shell { width: min(100% - 20px, 1180px); } header { padding-top: 16px; } .brand { flex-direction:column; } .overview-grid, .workflow-list, .package-grid, .health-grid, .card-facts { grid-template-columns: 1fr; } .tabs { overflow:auto; } .section-head { align-items:flex-start; flex-direction:column; } summary { align-items:flex-start; flex-direction:column; } table { min-width:0; } thead { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); } tbody, tr, td { display:block; width:100%; } tr { padding:8px; border-bottom:1px solid var(--border); } td { display:grid; grid-template-columns:minmax(110px, 38%) 1fr; gap:10px; border:0; padding:7px; } td::before { content:attr(data-label); color:var(--text-muted); font-size:11px; font-weight:780; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; scroll-behavior: auto !important; } }
</style>
</head>
<body>
<a class="skip-link" href="#mainContent">Skip to dashboard content</a>
<header>
  <div class="shell topbar">
    <div class="brand">
      <div class="mark" aria-hidden="true"><svg viewBox="0 0 64 64" fill="none"><path d="M32 9 49 17v13c0 11-7 20-17 25-10-5-17-14-17-25V17l17-8Z" stroke="currentColor" stroke-width="5" stroke-linejoin="round"/><path d="M22 33h20M32 23v20" stroke="#65a7ff" stroke-width="5" stroke-linecap="round"/></svg></div>
      <div>
        <h1>Review your agent workspace</h1>
        <p class="lede">Inspect packages, target health, and deploy readiness before Nexus writes native config.</p>
        <div class="pathline" id="paths">Loading local Nexus state...</div>
        <div class="safety-row" aria-label="Dashboard safety properties">
          <span class="safety-chip">localhost only</span>
          <span class="safety-chip">redacted secrets</span>
          <span class="safety-chip">confirmed deploys</span>
        </div>
      </div>
    </div>
    <div class="toolbar">
      <button type="button" id="refreshBtn">Refresh state</button>
      <button type="button" class="danger" id="deployBtn" data-endpoint="/api/sync/deploy" disabled>Deploy reviewed plan</button>
    </div>
  </div>
</header>
<main class="shell" id="mainContent" tabindex="-1">
  <div id="actionStatus" class="sr-status" role="status" aria-live="polite"></div>
  <div id="actionError" class="sr-status" role="alert"></div>
  <div class="overview-grid" id="summary"></div>
  <div class="workflow-list" id="workflow" aria-label="Agent Nexus workflow"></div>
  <details class="sync-result" id="syncResultPanel">
    <summary><span><strong>Latest dashboard action</strong><span class="helper"> dry-run and deploy output</span></span></summary>
    <div class="disclosure-body"><pre id="syncResult">No dashboard action has run yet.</pre></div>
  </details>
  <div class="tabs" role="tablist" aria-label="Dashboard views">
    <button type="button" id="tab-inventory" class="tab active" data-tab="inventory" role="tab" aria-controls="inventory" aria-selected="true" tabindex="0"><strong>Packages</strong></button>
    <button type="button" id="tab-manage" class="tab" data-tab="manage" role="tab" aria-controls="manage" aria-selected="false" tabindex="-1"><strong>Targets</strong></button>
    <button type="button" id="tab-status" class="tab" data-tab="status" role="tab" aria-controls="status" aria-selected="false" tabindex="-1"><strong>Health</strong></button>
    <button type="button" id="tab-manifest" class="tab" data-tab="manifest" role="tab" aria-controls="manifest" aria-selected="false" tabindex="-1"><strong>Manifest</strong></button>
  </div>
  <section id="inventory" class="active" role="tabpanel" aria-labelledby="tab-inventory"></section>
  <section id="manage" role="tabpanel" aria-labelledby="tab-manage" hidden></section>
  <section id="status" role="tabpanel" aria-labelledby="tab-status" hidden></section>
  <section id="manifest" role="tabpanel" aria-labelledby="tab-manifest" hidden></section>
</main>
<dialog id="deployDialog" aria-labelledby="deployDialogTitle">
  <h2 id="deployDialogTitle">Deploy the reviewed plan?</h2>
  <p class="helper">Nexus will rebuild the preview and deploy only if it still matches. Type <strong>deploy</strong> to continue.</p>
  <label for="deployConfirm">Confirmation</label><input id="deployConfirm" autocomplete="off">
  <div class="row-actions"><button type="button" id="cancelDeployBtn">Cancel</button><button type="button" class="danger" id="confirmDeployBtn" disabled>Deploy plan</button></div>
</dialog>
<script>
let state = null;
let reviewedPlan = null;
const esc = value => String(value ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const formatNumber = value => new Intl.NumberFormat().format(Number(value || 0));
const fileName = value => String(value || '').split(/[\\/]/).filter(Boolean).pop() || 'missing';
function statusMeta(status) {
  const normalized = status || 'unknown';
  const labels = {healthy:'healthy', warning:'warning', invalid:'invalid', missing:'missing', unknown:'unknown'};
  return {label: labels[normalized] || normalized, className: labels[normalized] ? normalized : 'unknown'};
}
function statusPill(status) {
  const meta = statusMeta(status);
  return `<span class="pill ${esc(meta.className)}">${esc(meta.label)}</span>`;
}
function tokenMeter(value, max, label='token estimate') {
  return `<span class="token-meter" aria-label="${esc(label)}: ${esc(value)} tokens"><span class="mono">${esc(formatNumber(value))}</span><span>tokens</span></span>`;
}
function statCard({label, value, detail}) {
  return `<div class="stat-card"><div class="stat-value">${esc(formatNumber(value))}</div><div class="stat-label">${esc(label)}</div><div class="stat-detail">${esc(detail || '')}</div></div>`;
}
function compactPill(label, tone='') {
  return `<span class="pill ${esc(tone)}">${esc(label)}</span>`;
}
function emptyRow(headersLength, message) {
  return `<tr><td colspan="${headersLength}"><div class="empty-state">${esc(message)}</div></td></tr>`;
}
function sectionIntro(title, subtitle) {
  return `<div class="section-head"><div><h2>${esc(title)}</h2><div class="helper">${esc(subtitle)}</div></div></div>`;
}
function table(headers, rows, emptyMessage='No rows yet.') {
  const labelled = rows.map(row => { let index = 0; return row.replace(/<td/g, () => `<td data-label="${esc(headers[index++] || '')}"`); });
  return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${labelled.join('') || emptyRow(headers.length, emptyMessage)}</tbody></table></div>`;
}
function cleanActionOutput(value) {
  return String(value || '').replace(/\x1b\[[0-9;]*m/g, '').replace(/\/Users\/[^\s\/"]+/g, '~').replace(/\/home\/[^\s\/"]+/g, '~');
}
async function api(path, options={}) {
  const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = {ok:false, error:text}; }
  if (!res.ok) throw new Error(data.error || data.message || res.statusText);
  return data;
}
async function refresh() {
  state = await api('/api/state');
  reviewedPlan = reviewedPlan && reviewedPlan.manifest_revision === state.meta.manifest_revision ? reviewedPlan : null;
  document.getElementById('paths').textContent = `Manifest: ${fileName(state.meta.manifest_path)} | Lockfile: ${fileName(state.meta.lockfile_path)}`;
  document.getElementById('deployBtn').disabled = !reviewedPlan || !state.actions.can_deploy;
  renderWorkflow(); renderSummary(); renderInventory(); renderManage(); renderStatus(); await renderManifest();
}
function renderWorkflow() {
  const stage = state.lifecycle.stage;
  const order = ['inspect','configure','preview','deploy','verify'];
  const current = {uninitialized:'configure', configured:'preview', 'needs-preview':'preview', previewed:'deploy', deployed:'verify', 'needs-attention':'verify', healthy:'verify'}[stage] || 'inspect';
  const currentIndex = order.indexOf(current);
  const labels = {inspect:['Inspect','Read local state.'], configure:['Configure','Create or edit the manifest.'], preview:['Preview','Review an exact plan.'], deploy:['Deploy','Apply the reviewed plan.'], verify:['Verify','Inspect health and lockfile.']};
  document.getElementById('workflow').innerHTML = order.map((step,index) => `<div class="${index < currentIndex ? 'complete' : index === currentIndex ? (stage === 'needs-attention' ? 'attention' : 'current') : ''}" data-testid="workflow-step-${step}"><strong>${labels[step][0]}</strong><span class="helper">${labels[step][1]}</span></div>`).join('');
}
function renderSummary() {
  const warningCount = state.summary.warnings || 0;
  const initialized = state.meta.manifest_exists;
  const ready = warningCount === 0 && initialized;
  const title = !initialized ? 'Start with a safe manifest' : ready ? 'Ready for review' : `${formatNumber(warningCount)} warning${warningCount === 1 ? '' : 's'} to review`;
  const detail = !initialized ? 'This page is read-only until you explicitly create a minimal starter manifest.' : ready ? 'Review the exact dry-run plan before deploying changes.' : 'Inspect warnings, then preview again before deployment.';
  const meta = [compactPill(initialized ? `Manifest ${fileName(state.meta.manifest_path)}` : 'No manifest', initialized ? '' : 'warning'), compactPill(`Stage ${state.lifecycle.stage}`), compactPill(state.meta.lockfile_current ? 'Lockfile current' : 'Lockfile pending', state.meta.lockfile_current ? 'healthy' : 'warning')];
  const action = !initialized ? `<button type="button" class="primary" id="initBtn">Create safe starter</button>` : `<button type="button" class="primary" data-sync-action="dry-run">Preview dry run</button>`;
  const nextStep = `<div class="next-step"><div><strong>Next safe step</strong><span>${!initialized ? 'Review and create a starter with no packages or MCPs.' : 'Build a non-persistent review plan.'}</span></div>${action}</div>`;
  const readiness = `<div class="readiness-card"><div><div class="readiness-label">Workspace readiness</div><div class="readiness-title ${ready ? 'tone-good' : 'tone-warn'}">${esc(title)}</div><div class="readiness-detail">${esc(detail)}</div></div><div><div class="readiness-meta">${meta.join('')}</div>${nextStep}</div></div>`;
  const rows = [
    {label:'Targets', value: state.summary.targets, detail:'selected destinations'},
    {label:'Packages', value: state.summary.packages, detail:'declared or lockfile-traced'},
    {label:'Skills', value: state.summary.available_package_skills || state.summary.skills, detail:`${formatNumber(state.summary.disabled_package_skills || 0)} disabled · ${formatNumber(state.summary.manual_only_package_skills || 0)} manual only`}
  ];
  document.getElementById('summary').innerHTML = readiness + rows.map(statCard).join('');
  const initBtn = document.getElementById('initBtn'); if (initBtn) initBtn.onclick = initializeWorkspace;
}
function renderInventory() {
  const packages = state.packages.map(p => `<tr><td class="name-cell">${esc(p.name)}</td><td>${esc(p.repo || p.path || '')}</td><td>${esc(p.uses_global_targets ? 'Global targets' : (p.deploy_targets || []).join(', '))}</td><td>${esc((p.skill_inventory || []).length)} available / ${esc(((p.discovered||{}).skills||[]).length)} deployed</td><td>${esc((p.deployed_to || []).join(', ') || 'not deployed')}</td></tr>`);
  const packageCards = (state.packages || []).map(p => {
    const policy = p.skill_policy || {};
    const source = p.repo || p.path || 'manifest package';
    const sourceType = p.repo ? 'GitHub package' : (p.path ? 'Local package' : 'Lockfile package');
    const targetPolicy = p.uses_global_targets ? 'Global targets' : ((p.deploy_targets || []).join(', ') || 'package filter');
    const discovered = p.discovered || {};
    const commandCount = (discovered.commands || []).length;
    const agentCount = (discovered.agents || []).length;
    const overlayCount = (p.overlays || []).length;
    const hookCount = (p.hooks || []).length;
    const assets = [
      `${(p.skill_inventory || []).length} skills`,
      `${commandCount} commands`,
      `${agentCount} agents`,
      `${hookCount} hook targets`,
      `${overlayCount} overlays`
    ].map(label => `<span class="asset-chip">${esc(label)}</span>`).join('');
    return `<article class="package-card"><div class="card-top"><div><h3 class="card-title">${esc(p.name)}</h3><div class="card-subtitle">${esc(source)}</div></div><div>${compactPill(sourceType)} ${compactPill(targetPolicy)}</div></div><div class="asset-row">${assets}</div><div class="card-facts"><div class="fact"><strong>${esc(policy.enabled_count || 0)}</strong><span>enabled</span></div><div class="fact"><strong>${esc(policy.disabled_count || 0)}</strong><span>disabled</span></div><div class="fact"><strong>${esc(policy.manual_only_count || 0)}</strong><span>manual only</span></div><div class="fact"><strong>${esc((p.deployed_to || []).length)}</strong><span>targets</span></div></div><div class="card-subtitle" style="margin-top:12px">Deployed to ${esc((p.deployed_to || []).join(', ') || 'no targets yet')}</div></article>`;
  }).join('') || '<div class="empty-state">No packages configured yet. Add a package to your Nexus manifest, then run sync.</div>';
  const skills = state.skills.map(s => `<tr><td class="name-cell">${esc(s.name)}</td><td>${esc(s.package)}</td><td>${esc(s.implicit_invocation ? 'Implicit' : 'Manual only')}</td><td>${esc((s.deployed_to || []).join(', ') || 'not deployed')}</td><td>${tokenMeter(s.static_tokens, 1, `${s.name} token estimate`)}</td></tr>`);
  const mcps = state.mcps.map(m => `<tr><td class="name-cell">${esc(m.name)}</td><td>${esc(m.optional ? 'Optional' : 'Required')}</td><td>${esc(m.transport || (m.url ? 'http/sse' : 'stdio'))}</td><td>${esc(m.command || m.url || '')}</td><td>${tokenMeter(m.static_tokens, 1, `${m.name} token estimate`)}</td></tr>`);
  const controls = (state.packages || []).map(renderPackageSkillControls).join('') || '<div class="empty-state">No package skills are available to edit yet. Run sync after adding a package.</div>';
  document.getElementById('inventory').innerHTML = `${sectionIntro('Packages', 'Start with package readiness. Expand controls only when you need to change skill policy.')}${warningsHtml()}<div class="package-grid">${packageCards}</div><details><summary><span><strong>Package table</strong><span class="helper"> source, targets, and deployment rows</span></span></summary><div class="disclosure-body">${table(['Name','Source','Target policy','Skills','Deployed to'], packages, 'No packages configured yet. Add a package to your Nexus manifest, then run sync.')}</div></details><h3>Package skill controls</h3><div class="notice">Saving skill controls updates the manifest only. Run Deploy after review or <span class="mono">nexus sync</span> to apply target filesystem changes.</div>${controls}<details><summary><span><strong>Currently deployed skills</strong><span class="helper"> ${esc(formatNumber(state.skills.length))} rows</span></span></summary><div class="disclosure-body">${table(['Skill','Package','Invocation','Deployed to','Tokens'], skills, 'No skills deployed yet. Run sync after adding a package with skills.')}</div></details><details><summary><span><strong>MCP servers</strong><span class="helper"> ${esc(formatNumber(state.mcps.length))} declared</span></span></summary><div class="disclosure-body">${table(['Name','Kind','Transport','Command or URL','Tokens'], mcps, 'No MCP servers declared yet. Add an MCP entry to your manifest to manage it across targets.')}</div></details>`;
}
function renderPackageSkillControls(pkg) {
  const policy = pkg.skill_policy || {};
  if (!policy.editable) return '';
  const rows = (pkg.skill_inventory || []).map(skill => `<tr data-skill-row data-skill-name="${esc(skill.name)}"><td class="name-cell">${esc(skill.name)}</td><td><label class="inline-check"><input type="checkbox" data-field="enabled" ${skill.enabled ? 'checked' : ''}>Enabled</label></td><td><label class="inline-check"><input type="checkbox" data-field="manual_only" ${skill.manual_only ? 'checked' : ''}>Manual only</label></td><td>${esc(skill.deployed ? (skill.deployed_to || []).join(', ') : 'not deployed')}</td><td>${tokenMeter(skill.static_tokens || 0, 1, `${skill.name} token estimate`)}</td><td><span class="source-badge">${esc(skill.source || 'unknown')}</span></td></tr>`);
  return `<details class="skill-control-panel" data-package-index="${esc(pkg.index)}" data-package-name="${esc(pkg.name)}"><summary><span class="skill-control-title"><h4>${esc(pkg.name)}</h4><span class="helper">${esc(policy.enabled_count || 0)} enabled · ${esc(policy.disabled_count || 0)} disabled · ${esc(policy.manual_only_count || 0)} manual only</span></span></summary><div class="disclosure-body"><div class="skill-policy-table">${table(['Skill','Enabled','Invocation','Deployed','Tokens','Source'], rows, 'No package skills discovered locally yet.')}</div><div class="row-actions"><button class="primary" data-save-package="${esc(pkg.index)}">Save skill policy</button></div><details><summary><span><strong>Save result</strong><span class="helper"> latest manifest update response</span></span></summary><div class="disclosure-body"><pre id="skillPolicyResult-${esc(pkg.index)}">No changes saved yet.</pre></div></details></div></details>`;
}
function collectPackageSkillState(packageIndex) {
  const panel = document.querySelector(`[data-package-index="${CSS.escape(String(packageIndex))}"]`);
  return [...panel.querySelectorAll('[data-skill-row]')].map(row => ({
    name: row.dataset.skillName,
    enabled: row.querySelector('[data-field="enabled"]').checked,
    manual_only: row.querySelector('[data-field="manual_only"]').checked
  }));
}
async function savePackageSkillPolicy(packageIndex) {
  const pkg = (state.packages || []).find(p => String(p.index) === String(packageIndex));
  const resultEl = document.getElementById(`skillPolicyResult-${packageIndex}`);
  const result = await api('/api/packages/skills/save', {method:'POST', body: JSON.stringify({package_index: pkg.index, package: pkg.name, skills: collectPackageSkillState(packageIndex), revision: state.meta.manifest_revision})}).catch(e => ({ok:false, error:e.message}));
  resultEl.textContent = JSON.stringify(result, null, 2);
  if (result.ok) { reviewedPlan = null; await refresh(); setStatus('Skill policy saved. Preview again before deploy.'); }
}
function warningsHtml() {
  return (state.warnings || []).length ? `<div class="notice warn"><strong>Review before deploy</strong><ul>${state.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></div>` : '<div class="notice"><strong>No dashboard warnings.</strong> Local state has no lockfile or platform warnings reported by Nexus.</div>';
}
function renderManage() {
  const selected = new Set(state.deployment.global_targets || []);
  const catalog = state.deployment.target_catalog || [];
  const available = catalog.length ? catalog : (state.deployment.available_targets || []).map(id => ({id, display:id, core:['claude','cursor','antigravity','codex'].includes(id)}));
  const chip = target => `<label class="target-chip"><input type="checkbox" data-target="${esc(target.id)}" ${selected.has(target.id) ? 'checked' : ''}>${esc(target.display)} <span class="helper mono">${esc(target.id)}</span></label>`;
  const coreChips = available.filter(target => target.core).map(chip).join('');
  const extraChips = available.filter(target => !target.core).map(chip).join('');
  const extras = extraChips ? `<details><summary><span><strong>Additional skill presets</strong><span class="helper"> optional skill-only targets</span></span></summary><div class="disclosure-body"><div class="target-grid">${extraChips}</div></div></details>` : '';
  document.getElementById('manage').innerHTML = `${sectionIntro('Targets', 'Choose default deploy targets. Package-level filters can narrow this per package.')}<div class="panel"><div class="notice">Saving updates only the manifest target policy; raw secrets stay out of the dashboard. Deploy remains gated: <strong>Type deploy</strong> when prompted to run sync.</div><div id="targetGrid"><div class="target-group"><div class="target-group-title">Core native targets</div><div class="target-grid">${coreChips || '<span class="helper">No core targets available.</span>'}</div></div>${extras}</div><div class="row-actions"><button class="primary" id="saveTargetsBtn">Save target policy</button></div><pre id="targetResult">Current targets: ${esc((state.deployment.global_targets || []).join(', ') || 'none selected')}</pre></div>`;
  document.getElementById('saveTargetsBtn').onclick = saveTargets;
}
async function saveTargets() {
  const targets = [...document.querySelectorAll('#targetGrid input:checked')].map(input => input.dataset.target);
  const result = await api('/api/targets/save', {method:'POST', body: JSON.stringify({targets, revision: state.meta.manifest_revision})}).catch(e => ({ok:false, error:e.message}));
  document.getElementById('targetResult').textContent = JSON.stringify(result, null, 2);
  if (result.ok) { reviewedPlan = null; await refresh(); setStatus('Target policy saved. Preview again before deploy.'); }
}
function renderStatus() {
  const rows = state.targets.map(t => `<tr><td class="name-cell">${esc(t.display || t.name)}</td><td>${statusPill(t.status)}</td><td>${esc(t.skill_path || '')}</td><td>${esc(t.skills.symlinks)} links / ${esc(t.skills.broken)} broken</td><td>${statusPill(t.mcp.status)} ${esc(t.mcp.server_count)} servers</td><td>${esc(t.hooks ? `${t.hooks.count} entries (${t.hooks.status})` : 'n/a')}</td></tr>`);
  const cards = state.targets.map(t => `<article class="health-card"><div class="card-top"><div><h3 class="card-title">${esc(t.display || t.name)}</h3><div class="card-subtitle">${esc(t.skill_path || 'skill path missing')}</div></div>${statusPill(t.status)}</div><div class="card-facts"><div class="fact"><strong>${esc(t.skills.symlinks)}</strong><span>skill links</span></div><div class="fact"><strong>${esc(t.mcp.server_count)}</strong><span>MCP servers</span></div><div class="fact"><strong>${esc(t.hooks ? t.hooks.count : 'n/a')}</strong><span>hooks</span></div></div><div class="card-subtitle" style="margin-top:12px">Skills: ${esc(t.skills.broken)} broken · MCP: ${esc(t.mcp.status)}${t.hooks ? ` · Hooks: ${esc(t.hooks.status)}` : ''}</div></article>`).join('') || '<div class="empty-state">No target checks are available yet.</div>';
  const counts = state.targets.reduce((acc, target) => { acc[target.status] = (acc[target.status] || 0) + 1; return acc; }, {});
  document.getElementById('status').innerHTML = `${sectionIntro('Health', 'Live local checks for skill links, MCP config, and hooks without making paths the focus.')}<div class="helper" style="margin-bottom:10px">${esc(formatNumber(counts.healthy || 0))} healthy · ${esc(formatNumber(counts.warning || 0))} warning · ${esc(formatNumber((counts.invalid || 0) + (counts.missing || 0)))} missing or invalid</div><div class="health-grid">${cards}</div><details><summary><span><strong>Detailed platform table</strong><span class="helper"> paths and raw status rows</span></span></summary><div class="disclosure-body">${table(['Target','Status','Skill path','Skills','MCP config','Hooks'], rows, 'No target checks are available yet.')}</div></details>`;
}
async function renderManifest() {
  const result = await api('/api/manifest').catch(e => ({ok:false, error:e.message}));
  if (!result.ok) { document.getElementById('manifest').innerHTML = `<div class="notice warn">${esc(result.error)}</div>`; return; }
  document.getElementById('manifest').innerHTML = `${sectionIntro('Manifest', 'Advanced redacted YAML editor. Structured controls remain the safer choice for common changes.')}<div class="notice">Secret values stay hidden and are restored only when their redaction placeholders remain in place.</div><textarea id="manifestEditor" data-testid="manifest-editor">${esc(result.text)}</textarea><div class="row-actions"><button type="button" id="validateManifestBtn">Validate</button><button type="button" class="primary" id="saveManifestBtn">Save manifest</button></div><pre id="manifestResult">Revision: ${esc(result.revision || 'not created')}</pre>`;
  document.getElementById('validateManifestBtn').onclick = () => { document.getElementById('manifestResult').textContent = 'Validation runs before every atomic save.'; };
  document.getElementById('saveManifestBtn').onclick = async () => {
    const saved = await api('/api/manifest/save', {method:'POST', body:JSON.stringify({text:document.getElementById('manifestEditor').value, revision:state.meta.manifest_revision})}).catch(e=>({ok:false,error:e.message}));
    document.getElementById('manifestResult').textContent = JSON.stringify(saved,null,2);
    if (saved.ok) { reviewedPlan = null; await refresh(); setStatus('Manifest saved. Preview again before deploy.'); }
  };
}
async function initializeWorkspace() {
  setStatus('Creating a safe starter manifest…');
  const result = await api('/api/init', {method:'POST', body:'{}'}).catch(e=>({ok:false,error:e.message}));
  if (!result.ok) return setError(result.error);
  setStatus('Safe starter created. Review the manifest before previewing.');
  await refresh();
  activateTab(document.getElementById('tab-manifest'));
}
function setStatus(message) { document.getElementById('actionError').textContent=''; document.getElementById('actionStatus').textContent=message || ''; }
function setError(message) { document.getElementById('actionError').textContent=message || 'Dashboard action failed.'; }
async function syncAction(action, confirmText='') {
  setStatus(action === 'dry-run' ? 'Building a non-persistent preview…' : 'Rebuilding and deploying the reviewed plan…');
  const body = {confirm:confirmText, plan_hash:reviewedPlan?.plan_hash, manifest_revision:state.meta.manifest_revision, no_optional:true};
  const result = await api(`/api/sync/${action}`, {method:'POST', body: JSON.stringify(body)}).catch(e => ({ok:false, error:e.message}));
  const output = [result.stderr, result.stdout, result.error].filter(Boolean).join('\n').trim() || JSON.stringify(result, null, 2);
  document.getElementById('syncResult').textContent = cleanActionOutput(output);
  document.getElementById('syncResultPanel').open = true;
  if (!result.ok) { setError(result.error); return; }
  if (action === 'dry-run') reviewedPlan = {plan_hash:result.plan_hash, manifest_revision:result.manifest_revision};
  setStatus(action === 'dry-run' ? 'Preview complete. Deploy is available while the manifest remains unchanged.' : 'Deployment complete. Inspect health next.');
  await refresh();
}
function activateTab(btn) {
  document.querySelectorAll('.tab').forEach(tab => { tab.classList.remove('active'); tab.setAttribute('aria-selected','false'); tab.tabIndex=-1; });
  document.querySelectorAll('[role="tabpanel"]').forEach(panel => { panel.hidden=true; panel.classList.remove('active'); });
  btn.classList.add('active'); btn.setAttribute('aria-selected','true'); btn.tabIndex=0;
  const panel = document.getElementById(btn.dataset.tab); panel.hidden=false; panel.classList.add('active');
}
const tabs = [...document.querySelectorAll('.tab')];
tabs.forEach((btn,index) => { btn.onclick=()=>activateTab(btn); btn.onkeydown=event=>{ let next=null; if(event.key==='ArrowRight') next=(index+1)%tabs.length; if(event.key==='ArrowLeft') next=(index-1+tabs.length)%tabs.length; if(event.key==='Home') next=0; if(event.key==='End') next=tabs.length-1; if(next!==null){event.preventDefault();activateTab(tabs[next]);tabs[next].focus();}}; });
document.addEventListener('click', event => {
  if (event.target.matches('[data-save-package]')) savePackageSkillPolicy(event.target.dataset.savePackage);
  if (event.target.matches('[data-sync-action]')) syncAction(event.target.dataset.syncAction);
});
const deployDialog=document.getElementById('deployDialog'); const deployConfirm=document.getElementById('deployConfirm'); const confirmDeployBtn=document.getElementById('confirmDeployBtn');
deployConfirm.oninput=()=>{confirmDeployBtn.disabled=deployConfirm.value!=='deploy';};
document.getElementById('cancelDeployBtn').onclick=()=>deployDialog.close();
confirmDeployBtn.onclick=()=>{const value=deployConfirm.value;deployDialog.close();syncAction('deploy',value);};
document.getElementById('refreshBtn').onclick=()=>{setStatus('Refreshing local state…');refresh().then(()=>setStatus('State refreshed.')).catch(e=>setError(e.message));};
document.getElementById('deployBtn').onclick=()=>{deployConfirm.value='';confirmDeployBtn.disabled=true;deployDialog.showModal();deployConfirm.focus();};
refresh().catch(e => setError(e.stack || e.message));
</script>
</body>
</html>'''


def make_dashboard_handler(repo_dir: Path):
    action_lock = threading.Lock()

    class DashboardHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            print(f"dashboard: {format % args}", file=sys.stderr)

        def _cfg(self) -> Config:
            return Config(repo_dir)

        def do_GET(self):
            try:
                cfg = self._cfg()
                if self.path == "/":
                    _text_response(self, 200, render_dashboard_html(), "text/html; charset=utf-8")
                elif self.path == "/api/state":
                    _json_response(self, 200, build_dashboard_model(cfg))
                elif self.path == "/api/manifest":
                    _json_response(self, 200, {
                        "ok": True,
                        "text": load_redacted_manifest_text(cfg),
                        "revision": cfg.manifest_revision(),
                        "file": cfg.yml_path.name,
                        "exists": cfg.yml_path.exists(),
                    })
                else:
                    _json_response(self, 404, {"ok": False, "error": "Not found"})
            except NexusError as exc:
                _json_response(self, 400, {"ok": False, "error": str(exc)})

        def do_POST(self):
            try:
                payload = _read_json_body(self)
                cfg = self._cfg()
                if self.path == "/api/init":
                    _json_response(self, 200, initialize_manifest(cfg, "safe", False))
                elif self.path == "/api/manifest/save":
                    _json_response(self, 200, update_manifest_from_dashboard(cfg, payload))
                elif self.path == "/api/targets/save":
                    _json_response(self, 200, update_manifest_targets(cfg, payload.get("targets", []), payload.get("revision")))
                elif self.path == "/api/packages/skills/save":
                    _json_response(self, 200, update_manifest_package_skill_policy(cfg, payload))
                elif self.path in {"/api/sync/dry-run", "/api/sync/deploy"}:
                    action = "dry-run" if self.path.endswith("dry-run") else "deploy"
                    if not action_lock.acquire(blocking=False):
                        _json_response(self, 409, {"ok": False, "error": "Another Nexus action is already running."})
                        return
                    try:
                        result = run_dashboard_sync_action(cfg, action, payload)
                    finally:
                        action_lock.release()
                    _json_response(self, 200 if result.get("ok") else 400, result)
                else:
                    _json_response(self, 404, {"ok": False, "error": "Not found"})
            except ManifestValidationError as exc:
                status = 409 if "changed since" in str(exc) else 400
                _json_response(self, status, {"ok": False, "error": str(exc)})
            except (NexusError, ValueError) as exc:
                _json_response(self, 400, {"ok": False, "error": str(exc)})
            except Exception as exc:
                _json_response(self, 500, {"ok": False, "error": str(exc)})

    return DashboardHandler


# ============================================================
# SUBCOMMANDS
# ============================================================

def _read_hook_commands(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return _walk_hook_commands(data.get("hooks", {}))


def collect_hook_review(discoveries: list[dict], targets: list[str]) -> list[dict]:
    rows = []
    for pkg in discoveries:
        selected = set(package_targets(pkg, targets))
        for target, key in [
            ("claude", "hooks_claude"),
            ("cursor", "hooks_cursor"),
            ("codex", "hooks_codex"),
        ]:
            hook_path = pkg.get(key)
            if target not in selected or not hook_path:
                continue
            commands = [
                Deployer._substitute_package_root(command, pkg["path"])
                for command in _read_hook_commands(Path(hook_path))
            ]
            rows.append({
                "package": pkg["name"],
                "target": target,
                "path": hook_path,
                "commands": commands,
            })
    return rows


def show_hook_review(discoveries: list[dict], targets: list[str]):
    rows = collect_hook_review(discoveries, targets)
    if not rows:
        return
    info("Hook review - executable hook commands to be installed:")
    print(file=sys.stderr)
    for row in rows:
        if row["commands"]:
            for command in row["commands"]:
                print(f"    {row['package']:30s} {row['target']:8s} {command}", file=sys.stderr)
        else:
            print(f"    {row['package']:30s} {row['target']:8s} {row['path']}", file=sys.stderr)
    print(file=sys.stderr)


def cmd_sync(cfg: Config, args):
    if not shutil.which("git"):
        raise NexusError("git is required")

    cfg.data  # Require and validate the manifest before network or filesystem work.
    prev_lock = cfg.load_lockfile()
    dry_run = bool(getattr(args, "dry_run", False))
    include_all = bool(getattr(args, "all", False))
    include_names = list(getattr(args, "include_optional", []) or [])
    no_optional = bool(getattr(args, "no_optional", False))

    info("Resolving optional MCPs...")
    accepted_optional = resolve_optionals(
        cfg,
        include_all=include_all,
        include_names=include_names,
        no_optional=no_optional or dry_run,
        prompt_allowed=not dry_run and not getattr(args, "yes", False) and sys.stdin.isatty(),
    )
    all_mcps = collect_mcps(cfg, accepted_optional)

    info("Fetching packages...")
    pm = PackageManager(cfg)
    discoveries = []
    temporary_checkout = tempfile.TemporaryDirectory(prefix="nexus-dry-run-") if dry_run else None
    ephemeral_root = Path(temporary_checkout.name) if temporary_checkout else None

    for pkg_spec in cfg.packages:
        repo = pkg_spec.get("repo")
        ref = pkg_spec.get("ref", "main")
        local_path = pkg_spec.get("path")
        if repo:
            pkg_name = repo.split("/", 1)[1]
            pkg_path = pm.fetch(repo, ref, pkg_spec.get("sparse_paths"), ephemeral_root=ephemeral_root)
            if not pkg_path:
                warn(f"Failed to fetch {repo}, skipping")
                continue
        elif local_path:
            pkg_path = cfg.repo_dir / local_path
            pkg_name = os.path.basename(local_path)
            if not pkg_path.is_dir():
                warn(f"Local path {local_path} does not exist, skipping")
                continue
            ok(f"{pkg_name} (local)")
        else:
            continue

        discovery = apply_package_filters(pm.discover(pkg_path, pkg_name, pkg_spec.get("sparse_paths")), pkg_spec)
        if repo:
            discovery["source"] = {
                "type": "github",
                "repo": repo,
                "source_url": f"https://github.com/{repo}",
                "requested_ref": ref,
                "resolved_commit": _resolved_commit_from_cache_path(str(pkg_path)),
                "cache_path": str(pkg_path),
                "sparse_paths": pkg_spec.get("sparse_paths", []),
            }
        else:
            discovery["source"] = {"type": "local", "path": local_path, "resolved_path": str(pkg_path)}
        discoveries.append(discovery)
        parts = [f"{len(discovery['skills'])} skills"]
        if discovery["commands"]:
            parts.append(f"{len(discovery['commands'])} commands")
        if discovery["agents"]:
            parts.append(f"{len(discovery['agents'])} agents")
        for key, label in [("hooks_claude", "hooks(claude)"), ("hooks_cursor", "hooks(cursor)"), ("hooks_codex", "hooks(codex)")]:
            if discovery[key]:
                parts.append(label)
        info(f"  {discovery['name']}: {', '.join(parts)}")

    manifest_revision = cfg.manifest_revision() if hasattr(cfg, "manifest_revision") else hashlib.sha256(json.dumps(cfg.data, sort_keys=True).encode()).hexdigest()
    plan_payload = {
        "manifest_revision": manifest_revision,
        "optional_mcps": accepted_optional,
        "mcps": [sanitize_mcp(mcp) for mcp in all_mcps],
        "packages": [{
            "name": pkg.get("name"),
            "source": pkg.get("source", {}),
            "skills": [skill.get("name") for skill in pkg.get("skills", [])],
            "targets": package_targets(pkg, cfg.targets),
            "hooks": _hook_deployments(pkg, cfg.targets),
        } for pkg in discoveries],
    }
    plan_hash = hashlib.sha256(json.dumps(plan_payload, sort_keys=True).encode()).hexdigest()
    info(f"Plan: {plan_hash[:12]} (manifest {str(manifest_revision or 'none')[:12]})")
    show_review(all_mcps, cfg.targets)
    show_hook_review(discoveries, cfg.targets)

    if not getattr(args, "yes", False) and not dry_run and not confirm("Apply this reviewed plan?"):
        print("Aborted.")
        return

    if dry_run:
        info("Dry run - no target configs or lockfiles written. No persistent cache or hooks written.")
        print(file=sys.stderr)
        info("Would deploy:")
        for mcp in all_mcps:
            target_label = ",".join(mcp_targets(mcp, cfg.targets)) or "none"
            print(f"  mcp: {mcp['name']} -> {target_label}", file=sys.stderr)
        for pkg in discoveries:
            targets = package_targets(pkg, cfg.targets)
            target_label = ",".join(targets) or "none"
            for skill in pkg["skills"]:
                overlays = skill_overlays(pkg, skill["name"], cfg.targets)
                inline_overlay = ""
                if len(overlays) == 1 and targets == [overlays[0]["target"]]:
                    inline_overlay = f" (overlay: {overlays[0]['type']})"
                print(f"  skill: {skill['name']} -> {target_label}{inline_overlay}", file=sys.stderr)
                if not inline_overlay:
                    for overlay in overlays:
                        print(f"    overlay: {overlay['target']} {overlay['type']}", file=sys.stderr)
            for target in _hook_deployments(pkg, cfg.targets):
                print(f"  hooks: {pkg['name']} -> {target}", file=sys.stderr)
        if temporary_checkout:
            temporary_checkout.cleanup()
        return

    deployer = Deployer(cfg)
    info("Pruning stale skills...")
    deployer.prune_skills(discoveries, prev_lock)
    info("Deploying skills...")
    total_skills = deployer.deploy_skills(discoveries)
    info("Deploying hooks...")
    deployer.deploy_hooks(discoveries)
    info("Pruning stale MCPs...")
    deployer.prune_mcps(all_mcps, prev_lock)
    info("Syncing MCP servers...")
    deployer.sync_mcps(all_mcps)
    info("Generating lockfile...")
    lock = generate_lockfile(discoveries, cfg.data, cfg.targets, cfg.repo_dir, all_mcps, cfg.yml_path)
    write_lockfile(lock, cfg.lockfile_path)
    ok(f"{cfg.lockfile_path.name} written")

    skill_counts = {target: 0 for target in cfg.targets}
    for pkg in discoveries:
        for target in package_targets(pkg, cfg.targets):
            skill_counts[target] = skill_counts.get(target, 0) + len(pkg.get("skills", []))
    skill_summary = ", ".join(f"{target}={count}" for target, count in skill_counts.items())
    mcp_paths = []
    for target in cfg.targets:
        if not any(target in mcp_targets(mcp, cfg.targets) for mcp in all_mcps):
            continue
        mcp_path = cfg.mcp_path(target)
        if mcp_path:
            mcp_paths.append(dashboard_path(mcp_path, cfg) or str(mcp_path))
    print(file=sys.stderr)
    info("Sync complete!")
    print(f"  {total_skills} skills processed; deployed counts: {skill_summary}", file=sys.stderr)
    print(f"  MCP servers synced to: {', '.join(mcp_paths) if mcp_paths else 'no MCP-capable targets selected'}", file=sys.stderr)
    if accepted_optional:
        print(f"  Optional MCPs included: {' '.join(accepted_optional)}", file=sys.stderr)
    print(file=sys.stderr)
    print("  Restart your AI IDEs to pick up changes.", file=sys.stderr)

def cmd_list(cfg: Config, _args):
    data = cfg.data_or_empty()
    if not cfg.manifest_exists:
        warn("No Nexus manifest yet. Run 'nexus init' to create a safe starter.")
    print()
    print("\033[1mPackages:\033[0m")
    packages = data.get("packages", []) or []
    for pkg in packages:
        repo = pkg.get("repo", pkg.get("path", "?"))
        ref = pkg.get("ref", "local")
        print(f"  {repo}  {ref}")
    if not packages:
        print("  none")

    prev_lock = cfg.load_lockfile()
    if prev_lock:
        print()
        print("\033[1mDiscovered Skills:\033[0m")
        for pkg in prev_lock.get("packages", []):
            name = pkg["name"]
            for skill in pkg.get("discovered", {}).get("skills", []):
                print(f"  {skill:40s} ({name})")

        print()
        print("\033[1mDiscovered Hooks:\033[0m")
        for pkg in prev_lock.get("packages", []):
            name = pkg["name"]
            discovered = pkg.get("discovered", {})
            for hook_name, key in [("claude", "hooks_claude"), ("cursor", "hooks_cursor"), ("codex", "hooks_codex")]:
                if discovered.get(key):
                    print(f"  {hook_name:40s} ({name})")

    print()
    print("\033[1mMCP Servers:\033[0m")
    mcps = [*(data.get("mcps", []) or []), *(data.get("optional_mcps", []) or [])]
    for mcp in mcps:
        optional = mcp in (data.get("optional_mcps", []) or []) or mcp.get("optional")
        suffix = " (optional)" if optional else ""
        if "url" in mcp:
            print(f"  {mcp['name']:30s} {mcp.get('transport', 'sse'):8s} {mcp['url']}{suffix}")
        else:
            args_str = " ".join(mcp.get("args", []))
            print(f"  {mcp['name']:30s} {'stdio':8s} {mcp.get('command', 'npx')} {args_str}{suffix}")
    if not mcps:
        print("  none")

    print()
    targets = canonical_targets(data.get("targets"), CORE_DEFAULT_TARGETS)
    print(f"\033[1mTargets:\033[0m {', '.join(targets)}")
    print()


def cmd_doctor(cfg: Config, _args):
    print()
    info(f"nexus doctor - v{NEXUS_VERSION}")
    print()

    # Manifest
    if cfg.yml_path.exists():
        ok(f"{cfg.yml_path.name} found")
        try:
            cfg.data  # trigger parse
            ok(f"{cfg.yml_path.name} is valid YAML")
        except NexusError as exc:
            warn(f"{cfg.yml_path.name} is invalid: {exc}")
    else:
        warn("nexus manifest not found")

    # Cache
    if cfg.cache_dir.exists():
        fetched = list(cfg.cache_dir.rglob("*.fetched"))
        ok(f"Package cache: {len(fetched)} packages cached")
    else:
        warn("Package cache: empty (run nexus sync)")

    # Lockfile
    lock = None
    if cfg.lockfile_path.exists():
        ok(f"{cfg.lockfile_path.name} exists")
        lock = cfg.load_lockfile()
    else:
        warn(f"{cfg.lockfile_path.name} missing (run nexus sync)")

    # Skill symlinks
    doctor_targets = cfg.safe_targets() if hasattr(cfg, "safe_targets") else cfg.targets
    for target in doctor_targets:
        skill_dir = cfg.skill_path(target)
        if not skill_dir or not skill_dir.exists():
            warn(f"{target} skills: directory missing")
            continue
        links = [p for p in skill_dir.iterdir() if p.is_symlink()]
        broken = [p for p in links if not p.resolve().exists()]
        if broken:
            warn(f"{target} skills: {len(links)} symlinks ({len(broken)} broken)")
        else:
            ok(f"{target} skills: {len(links)} symlinks")

    # Skill metadata overlays
    overlay_count = 0
    overlay_failures = 0
    if lock:
        for pkg in lock.get("packages", []):
            for overlay in pkg.get("overlays", []):
                overlay_count += 1
                skill_name = overlay.get("skill")
                target = overlay.get("target")
                overlay_type = overlay.get("type")
                path = Path(overlay.get("path", ""))
                if not path.is_dir():
                    warn(f"{target} overlay {skill_name}: generated directory missing ({path})")
                    overlay_failures += 1
                    continue

                skill_dir = cfg.skill_path(target)
                link = skill_dir / skill_name if skill_dir and skill_name else None
                if not link or not link.is_symlink():
                    warn(f"{target} overlay {skill_name}: skill link missing")
                    overlay_failures += 1
                elif link.resolve(strict=False) != path.resolve(strict=False):
                    warn(f"{target} overlay {skill_name}: skill link points to {link.resolve(strict=False)}")
                    overlay_failures += 1

                if not (path / "SKILL.md").is_file():
                    warn(f"{target} overlay {skill_name}: SKILL.md missing")
                    overlay_failures += 1

                if overlay_type == "agents_openai":
                    metadata_path = path / "agents" / "openai.yaml"
                    try:
                        import yaml

                        with open(metadata_path, encoding="utf-8") as f:
                            yaml.safe_load(f)
                    except Exception:
                        warn(f"{target} overlay {skill_name}: invalid agents/openai.yaml")
                        overlay_failures += 1
        if overlay_count and overlay_failures == 0:
            ok(f"Skill overlays: {overlay_count} generated")

    # MCP configs
    for target in doctor_targets:
        mcp_path = cfg.mcp_path(target)
        if not mcp_path:
            unchanged(f"{target} MCP config: unsupported")
            continue
        expected = _lock_managed_mcp_names(lock, target, cfg.targets)
        if not mcp_path.exists():
            if lock is not None and not expected:
                unchanged(f"{target} MCP config: not required, 0 Nexus-managed")
            else:
                warn(f"{target} MCP config: not found")
            continue
        try:
            if cfg.mcp_format(target) == "codex_toml":
                import tomllib
                with open(mcp_path, "rb") as f:
                    data = tomllib.load(f)
                names = set(data.get("mcp_servers", {}))
            else:
                with open(mcp_path) as f:
                    data = json.load(f)
                names = set(data.get("mcpServers", {}))
            missing = sorted(expected - names)
            if missing:
                warn(f"{target} MCP config: missing managed servers {', '.join(missing)} ({mcp_path})")
            else:
                ok(f"{target} MCP config: {len(names)} servers, {len(expected)} Nexus-managed ({mcp_path})")
        except (json.JSONDecodeError, OSError, ValueError):
            warn(f"{target} MCP config: invalid config ({mcp_path})")

    # Hook duplication
    cursor_hooks = cfg.repo_dir / ".cursor" / "hooks.json"
    if cursor_hooks.exists():
        try:
            with open(cursor_hooks) as f:
                data = json.load(f)
            count = sum(len(v) for v in data.get("hooks", {}).values())
            if count > 10:
                warn(f"Cursor hooks: {count} entries (possible duplication)")
            else:
                ok(f"Cursor hooks: {count} entries")
        except (json.JSONDecodeError, OSError):
            warn("Cursor hooks: invalid JSON")

    if "codex" in cfg.targets:
        codex_hooks = cfg.codex_hooks_path()
        if codex_hooks.exists():
            try:
                with open(codex_hooks) as f:
                    data = json.load(f)
                count = sum(len(v) for v in data.get("hooks", {}).values())
                ok(f"Codex hooks: {count} entries ({codex_hooks})")
            except (json.JSONDecodeError, OSError):
                warn(f"Codex hooks: invalid JSON ({codex_hooks})")
        else:
            warn(f"Codex hooks: not found ({codex_hooks})")

    # Legacy artifacts
    if (cfg.repo_dir / "apm.yml").exists():
        warn("Legacy apm.yml found — consider removing")
    if (cfg.repo_dir / "apm_modules").is_dir():
        warn("Legacy apm_modules/ found — consider removing")

    print()


def cmd_dashboard(cfg: Config, args):
    if getattr(args, "json", False):
        print(json.dumps(build_dashboard_model(cfg), indent=2, sort_keys=False))
        return

    host = getattr(args, "host", "127.0.0.1")
    port = getattr(args, "port", 8765)
    if host != "127.0.0.1" and not getattr(args, "allow_remote", False):
        print("Error: dashboard binds to 127.0.0.1 by default. Pass --allow-remote to use another host.", file=sys.stderr)
        sys.exit(1)

    handler = make_dashboard_handler(cfg.repo_dir)
    try:
        server = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        print(f"Error: could not start dashboard on {host}:{port}: {exc}", file=sys.stderr)
        sys.exit(1)

    url = f"http://{host}:{port}/"
    info(f"Agent Nexus dashboard running at {url}")
    print("  Press Ctrl-C to stop.", file=sys.stderr)
    if not getattr(args, "no_open", False):
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(file=sys.stderr)
        info("Dashboard stopped.")
    finally:
        server.server_close()


def build_clean_plan(cfg: Config) -> dict:
    items = []
    warnings = []
    roots = [cfg.cache_dir.resolve(strict=False), (cfg.nexus_dir / "generated").resolve(strict=False)]
    targets = cfg.safe_targets() if hasattr(cfg, "safe_targets") else cfg.targets
    for target in targets:
        skill_dir = cfg.skill_path(target)
        if not skill_dir or not skill_dir.exists():
            continue
        for link in skill_dir.iterdir():
            if not link.is_symlink():
                continue
            destination = link.resolve(strict=False)
            if any(destination == root or root in destination.parents for root in roots):
                items.append({"type": "symlink", "path": str(link), "label": f"{target} skill {link.name}"})
    for path, label in [(cfg.nexus_dir / "compiled", "compiled output"), (cfg.nexus_dir / "generated", "generated overlays"), (cfg.cache_dir, "package cache"), (cfg.lockfile_path, "lockfile")]:
        if path.exists():
            items.append({"type": "directory" if path.is_dir() else "file", "path": str(path), "label": label})
    lock = cfg.load_lockfile() or {}
    managed_files = lock.get("hooks", {}).get("managed_files", []) if isinstance(lock.get("hooks"), dict) else []
    for entry in managed_files:
        if not isinstance(entry, dict) or entry.get("target") != "claude":
            continue
        path = Path(entry.get("path", ""))
        expected = entry.get("source_sha256")
        if path.is_file() and expected and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            items.append({"type": "file", "path": str(path), "label": f"managed Claude hook {path.name}"})
        elif path.exists():
            warnings.append(f"Preserving modified or unverified hook file: {path}")
    warnings.append("Unowned repo hook files and directories are always preserved.")
    return {"items": items, "managed_mcp_count": len(lock.get("mcps", {}).get("managed", [])) if isinstance(lock.get("mcps"), dict) else 0, "warnings": warnings}


def render_clean_plan(plan: dict):
    info("Clean plan - Nexus-owned artifacts only:")
    if not plan["items"] and not plan["managed_mcp_count"]:
        unchanged("Nothing to remove")
    for item in plan["items"]:
        print(f"  - {item['label']}: {item['path']}", file=sys.stderr)
    if plan["managed_mcp_count"]:
        print(f"  - {plan['managed_mcp_count']} lockfile-managed MCP entries", file=sys.stderr)
    for message in plan["warnings"]:
        warn(message)


def apply_clean_plan(cfg: Config, plan: dict):
    lock = cfg.load_lockfile()
    if lock:
        deployer = Deployer(cfg)
        deployer.prune_mcps([], lock)
        targets = cfg.safe_targets() if hasattr(cfg, "safe_targets") else cfg.targets
        if "codex" in targets:
            path = cfg.codex_hooks_path()
            existing = deployer._load_hook_config(path)
            cleaned = json.loads(json.dumps(existing))
            deployer._strip_nexus_managed_hooks(cleaned)
            if cleaned != existing:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")
    for item in plan["items"]:
        path = Path(item["path"])
        if item["type"] == "directory" and path.is_dir():
            shutil.rmtree(path)
        elif path.is_symlink() or path.is_file():
            path.unlink()
        removed(item["label"])


def cmd_clean(cfg: Config, args):
    plan = build_clean_plan(cfg)
    render_clean_plan(plan)
    if getattr(args, "dry_run", False):
        info("Dry run - nothing removed.")
        return
    if not getattr(args, "yes", False) and not confirm("Apply this clean plan?"):
        print("Aborted.")
        return
    apply_clean_plan(cfg, plan)
    info("Clean complete. Run 'nexus sync' to rebuild.")


def starter_manifest_text(repo_dir: Path) -> str:
    name = repo_dir.name.strip() or "agent-workspace"
    safe_name = "-".join(name.lower().replace("_", " ").split())
    return SAFE_STARTER_TEMPLATE.format(name=safe_name)


def initialize_manifest(cfg: Config, template: str = "safe", force: bool = False) -> dict:
    target = cfg.repo_dir / "nexus.personal.yml"
    if target.exists() and not force:
        raise NexusError(f"{target.name} already exists. Use 'nexus init --force' to overwrite it.")
    if template == "example":
        source = cfg.repo_dir / "nexus.example.yml"
        if not source.is_file():
            raise NexusError(f"{source.name} not found in {cfg.repo_dir}")
        text = source.read_text(encoding="utf-8")
        source_label = source.name
    else:
        text = starter_manifest_text(cfg.repo_dir)
        source_label = "safe starter"
    init_cfg = Config(cfg.repo_dir)
    init_cfg.yml_path = target
    init_cfg.lockfile_path = cfg.repo_dir / "nexus.personal.lock.yml"
    write_manifest_atomically(init_cfg, text)
    return {"ok": True, "path": target.name, "template": template, "source": source_label}


def cmd_init(cfg: Config, args):
    result = initialize_manifest(
        cfg,
        template=getattr(args, "template", "safe"),
        force=getattr(args, "force", False),
    )
    ok(f"Created {result['path']} from {result['source']}")
    print("Review nexus.personal.yml, then run 'nexus sync --dry-run'.", file=sys.stderr)


# ============================================================
# MAIN
# ============================================================

def _find_manifest_parent(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "nexus.personal.yml").exists() or (candidate / "nexus.yml").exists():
            return candidate
    return None


def resolve_project_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_dir = os.environ.get("NEXUS_PROJECT_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    module_dir = Path(__file__).resolve().parent
    invoked = Path(sys.argv[0]).expanduser().resolve()
    if invoked == Path(__file__).resolve() and (module_dir / "nexus.example.yml").exists():
        return module_dir
    return _find_manifest_parent(Path.cwd().resolve()) or Path.cwd().resolve()


def resolve_repo_dir() -> Path:
    """Backward-compatible alias for older callers."""
    return resolve_project_dir()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="nexus",
        description=f"nexus v{NEXUS_VERSION} - Agent environment manager",
    )
    parser.add_argument("--project-dir", help="Workspace containing the Nexus manifest (default: nearest parent)")
    parser.add_argument("--version", action="version", version=f"nexus v{NEXUS_VERSION}")
    sub = parser.add_subparsers(dest="command")

    sp_sync = sub.add_parser("sync", help="Fetch packages, compile skills, merge MCPs, deploy to IDEs")
    sp_sync.add_argument("--all", action="store_true", help="Include all optional MCPs without prompting")
    sp_sync.add_argument("--include-optional", action="append", default=[], metavar="NAME", help="Include one optional MCP (repeatable)")
    sp_sync.add_argument("--no-optional", action="store_true", help="Skip every optional MCP without prompting")
    sp_sync.add_argument("--yes", "-y", action="store_true", help="Apply without confirmation after printing the review")
    sp_sync.add_argument("--dry-run", action="store_true", help="Show what would change without persistent writes")

    sub.add_parser("list", help="Show installed packages, skills, and MCP servers")
    sp_audit = sub.add_parser("audit", help="Read-only inventory of existing target config")
    sp_audit.add_argument("--json", action="store_true", help="Print machine-readable audit output")
    sp_audit.add_argument("--target", choices=sorted(set(TARGET_REGISTRY) | set(TARGET_ALIASES)), help="Audit one target")
    sp_audit.add_argument("--redact-home", action="store_true", help="Replace the home directory prefix with ~ in paths")
    sub.add_parser("doctor", help="Run diagnostics and health checks")
    sp_dashboard = sub.add_parser("dashboard", help="Open the local management dashboard")
    sp_dashboard.add_argument("--host", default="127.0.0.1", help="Dashboard bind host (default: 127.0.0.1)")
    sp_dashboard.add_argument("--port", type=int, default=8765, help="Dashboard port (default: 8765)")
    sp_dashboard.add_argument("--no-open", action="store_true", help="Do not open the dashboard in a browser")
    sp_dashboard.add_argument("--json", action="store_true", help="Print dashboard state as JSON and exit")
    sp_dashboard.add_argument("--allow-remote", action="store_true", help="Allow binding to a non-loopback host")
    sp_clean = sub.add_parser("clean", help="Preview and remove Nexus-owned artifacts")
    sp_clean.add_argument("--dry-run", action="store_true", help="Show what would be removed without writing")
    sp_clean.add_argument("--yes", "-y", action="store_true", help="Apply the clean plan without prompting")
    sp_init = sub.add_parser("init", help="Create a safe nexus.personal.yml starter")
    sp_init.add_argument("--force", action="store_true", help="Overwrite an existing nexus.personal.yml")
    sp_init.add_argument("--template", choices=["safe", "example"], default="safe", help="Starter template (default: safe)")
    sub.add_parser("version", help="Show version")

    args = parser.parse_args(argv)
    cfg = Config(resolve_project_dir(args.project_dir))
    dispatch = {
        "sync": cmd_sync,
        "list": cmd_list,
        "audit": cmd_audit,
        "doctor": cmd_doctor,
        "dashboard": cmd_dashboard,
        "clean": cmd_clean,
        "init": cmd_init,
        "version": lambda _c, _a: print(f"nexus v{NEXUS_VERSION}"),
    }
    if not args.command:
        parser.print_help()
        return 0
    handler = dispatch.get(args.command)
    if not handler:
        parser.print_help()
        return 1
    try:
        handler(cfg, args)
    except NexusError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
