#!/usr/bin/env python3
"""nexus — Agent environment manager.

Manages skills, hooks, and MCP servers across multiple AI IDEs from a nexus manifest.
Single-file, single-dependency (PyYAML) replacement for nexus.sh.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

NEXUS_VERSION = "0.2.0"

# ---------------------------------------------------------------------------
# Target registry — data-driven, not hardcoded case/switch
# ---------------------------------------------------------------------------
TARGET_REGISTRY = {
    "claude": {
        "skills": Path.home() / ".claude" / "skills",
        "mcp": Path.home() / ".claude.json",
        "mcp_format": "claude_json",
    },
    "cursor": {
        "skills": Path.home() / ".cursor" / "skills",
        "mcp": Path.home() / ".cursor" / "mcp.json",
        "mcp_format": "mcp_servers_json",
    },
    "antigravity": {
        "skills": Path.home() / ".gemini" / "antigravity" / "skills",
        "mcp": Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
        "mcp_format": "mcp_servers_json",
    },
    "codex": {
        "skills": Path.home() / ".codex" / "skills",
        "mcp": Path.home() / ".codex" / "config.toml",
        "mcp_format": "codex_toml",
    },
}

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
    def data(self) -> dict:
        if self._data is None:
            self._data = self._load()
        return self._data

    def _load(self) -> dict:
        try:
            import yaml
        except ImportError:
            print("Error: PyYAML is required. Install it: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        if not self.yml_path.exists():
            print(f"Error: no nexus manifest found in {self.repo_dir}", file=sys.stderr)
            print("Create nexus.personal.yml for your machine, or copy nexus.example.yml to nexus.yml.", file=sys.stderr)
            sys.exit(1)
        with open(self.yml_path) as f:
            return yaml.safe_load(f) or {}

    @property
    def targets(self) -> list[str]:
        return self.data.get("targets", ["claude", "cursor", "antigravity"])

    @property
    def packages(self) -> list[dict]:
        return self.data.get("packages", [])

    @property
    def mcps(self) -> list[dict]:
        return self.data.get("mcps", [])

    @property
    def optional_mcps(self) -> list[dict]:
        return self.data.get("optional_mcps", [])

    def skill_path(self, target: str) -> Path | None:
        entry = TARGET_REGISTRY.get(target)
        return entry["skills"] if entry else None

    def mcp_path(self, target: str) -> Path | None:
        entry = TARGET_REGISTRY.get(target)
        return entry["mcp"] if entry else None

    def mcp_format(self, target: str) -> str:
        entry = TARGET_REGISTRY.get(target) or {}
        return entry.get("mcp_format", "mcp_servers_json")

    def codex_hooks_path(self) -> Path:
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home:
            return Path(codex_home) / "hooks.json"
        return Path.home() / ".codex" / "hooks.json"

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

    def fetch(self, repo: str, ref: str, sparse_paths: list[str] | None = None) -> Path | None:
        org, repo_name = repo.split("/", 1)
        sha = self._resolve_sha(repo, ref)
        if not sha:
            warn(f"Could not resolve ref '{ref}' for {repo}")
            return None

        cache_key = sha
        if sparse_paths:
            sparse_hash = hashlib.sha256(
                "\n".join(sorted(sparse_paths)).encode()
            ).hexdigest()[:12]
            cache_key = f"{sha}-sparse-{sparse_hash}"

        cache_path = self.cfg.cache_dir / "github.com" / org / repo_name / cache_key
        marker = cache_path.parent / f"{cache_key}.fetched"

        if marker.exists():
            suffix = ", sparse" if sparse_paths else ""
            unchanged(f"{repo}@{sha[:7]} (cached{suffix})")
            return cache_path

        suffix = f" ({len(sparse_paths)} sparse paths)" if sparse_paths else ""
        info(f"Fetching {repo}@{ref} ({sha[:7]}){suffix}...")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.parent / f"{cache_key}.tmp"
        if tmp.exists():
            shutil.rmtree(tmp)

        try:
            self._clone(repo, ref, tmp, sparse_paths)
        except subprocess.CalledProcessError:
            # Fallback: clone default branch, fetch specific sha
            try:
                self._clone(repo, None, tmp, sparse_paths)
                subprocess.run(
                    ["git", "fetch", "--depth=1", "origin", sha],
                    cwd=str(tmp), capture_output=True, check=True,
                )
                subprocess.run(
                    ["git", "checkout", sha],
                    cwd=str(tmp), capture_output=True, check=True,
                )
            except subprocess.CalledProcessError:
                warn(f"Failed to fetch {repo}@{ref}")
                if tmp.exists():
                    shutil.rmtree(tmp)
                return None

        # Remove .git to save space
        git_dir = tmp / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        if cache_path.exists():
            shutil.rmtree(cache_path)
        tmp.rename(cache_path)
        marker.touch()

        ok(f"{repo}@{sha[:7]} (fetched)")
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
    return discovery


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
                for target in self.cfg.targets:
                    target_dir = self.cfg.skill_path(target)
                    if not target_dir:
                        continue
                    target_dir.mkdir(parents=True, exist_ok=True)
                    link = target_dir / name
                    if link.is_symlink() or not link.exists():
                        link.unlink(missing_ok=True)
                        link.symlink_to(path)
                        deployed_to.append(target)
                    else:
                        warn(f"{link} exists and is not a symlink, skipping")
                ok(f"{name} -> {','.join(deployed_to)}")
                count += 1
        return count

    def prune_skills(self, discoveries: list[dict], prev_lock: dict | None):
        """Remove symlinks for packages no longer in the manifest."""
        if not prev_lock:
            return

        current_skills = set()
        for pkg in discoveries:
            for skill in pkg.get("skills", []):
                current_skills.add(skill["name"])

        prev_skills = set()
        for pkg in prev_lock.get("packages", []):
            for s in pkg.get("discovered", {}).get("skills", []):
                prev_skills.add(s)

        stale = prev_skills - current_skills
        if not stale:
            return

        for target in self.cfg.targets:
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
            if "claude" in self.cfg.targets and pkg.get("hooks_claude"):
                claude_hooks.append(Path(pkg["hooks_claude"]))
            if "cursor" in self.cfg.targets and pkg.get("hooks_cursor"):
                cursor_hooks.append(Path(pkg["hooks_cursor"]))
            if "codex" in self.cfg.targets and pkg.get("hooks_codex"):
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
            out_dir.mkdir(parents=True, exist_ok=True)
            for f in claude_hooks:
                shutil.copy2(f, out_dir / f.name)
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
        for target in self.cfg.targets:
            mcp_path = self.cfg.mcp_path(target)
            if not mcp_path:
                continue
            info(f"Syncing MCPs to {mcp_path}...")
            if self.cfg.mcp_format(target) == "codex_toml":
                self._sync_mcps_for_codex(all_mcps, mcp_path)
            else:
                self._sync_mcps_for_target(all_mcps, mcp_path, target)

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

        # Claude stores MCPs per-project; others use flat mcpServers
        if target == "claude":
            projects = config.setdefault("projects", {})
            project = projects.setdefault(str(self.cfg.repo_dir), {})
            servers = project.setdefault("mcpServers", {})
        else:
            servers = config.setdefault("mcpServers", {})

        for mcp in all_mcps:
            name = mcp["name"]
            entry = self._build_mcp_entry(mcp, target=target)

            if name in servers:
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
        existing = mcp_path.read_text() if mcp_path.exists() else ""
        existing = self._strip_codex_managed_block(existing).rstrip()

        lines = [
            "",
            "# BEGIN NEXUS MANAGED MCP SERVERS",
            f"# This block is generated by agent-nexus. Edit {self.cfg.yml_path.name} instead.",
        ]
        for mcp in all_mcps:
            name = mcp["name"]
            entry = self._build_mcp_entry(mcp)
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
            if mcp.get("headers"):
                entry["headers"] = mcp["headers"]
            return entry

        command = mcp.get("command", "npx")
        if command in ("npx", "node"):
            resolved = shutil.which(command)
            if resolved:
                command = resolved

        env = dict(mcp.get("env") or {})
        if "PATH" not in env:
            env["PATH"] = STANDARD_PATH
        return {"type": "stdio", "command": command, "args": mcp.get("args", []), "env": env}

    def prune_mcps(self, current_names: set[str], prev_lock: dict | None):
        """Remove MCP entries no longer in the manifest."""
        if not prev_lock:
            return
        prev_names = set()
        for entry in prev_lock.get("mcps", {}).get("managed", []):
            prev_names.add(entry["name"])

        stale = prev_names - current_names
        if not stale:
            return

        for target in self.cfg.targets:
            mcp_path = self.cfg.mcp_path(target)
            if not mcp_path or not mcp_path.exists():
                continue
            try:
                with open(mcp_path) as f:
                    config = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            if target == "claude":
                servers = (config.get("projects", {})
                           .get(str(self.cfg.repo_dir), {})
                           .get("mcpServers", {}))
            else:
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


# ---------------------------------------------------------------------------
# Lockfile
# ---------------------------------------------------------------------------
def generate_lockfile(discoveries: list[dict], manifest: dict, targets: list[str]) -> dict:
    lock = {
        "lockfile_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "nexus_version": NEXUS_VERSION,
        "packages": [],
        "mcps": {"managed": []},
    }
    for pkg in discoveries:
        lock["packages"].append({
            "name": pkg["name"],
            "path": pkg["path"],
            "discovered": {
                "skills": [s["name"] for s in pkg.get("skills", [])],
                "hooks_claude": pkg.get("hooks_claude") is not None,
                "hooks_cursor": pkg.get("hooks_cursor") is not None,
                "hooks_codex": pkg.get("hooks_codex") is not None,
                "commands": pkg.get("commands", []),
                "agents": pkg.get("agents", []),
            },
            "deployed_to": targets,
        })
    for mcp in manifest.get("mcps", []):
        entry = {"name": mcp["name"]}
        if mcp.get("optional"):
            entry["optional"] = True
        lock["mcps"]["managed"].append(entry)
    for mcp in manifest.get("optional_mcps", []):
        lock["mcps"]["managed"].append({"name": mcp["name"], "optional": True})
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
def show_review(all_mcps: list[dict]):
    print(file=sys.stderr)
    info("Security review — MCP servers to be registered:")
    print(file=sys.stderr)
    for mcp in all_mcps:
        name = mcp["name"]
        if "url" in mcp:
            detail = f"{mcp.get('transport', 'sse')}: {mcp['url']}"
        else:
            cmd = mcp.get("command", "npx")
            args = " ".join(mcp.get("args", []))
            detail = f"stdio: {cmd} {args}"
        print(f"    {name:30s} {detail}", file=sys.stderr)
    print(file=sys.stderr)


# ---------------------------------------------------------------------------
# Resolve which optional MCPs to include
# ---------------------------------------------------------------------------
def resolve_optionals(cfg: Config, include_all: bool) -> list[str]:
    accepted = []

    # optional: true in mcps section
    for mcp in cfg.mcps:
        if mcp.get("optional"):
            desc = mcp.get("description", "No description")
            if include_all or confirm(f"Include optional MCP: {mcp['name']} ({desc})?"):
                accepted.append(mcp["name"])
                ok(f"{mcp['name']} (included)")
            else:
                warn(f"{mcp['name']} (skipped)")

    # separate optional_mcps section
    for mcp in cfg.optional_mcps:
        desc = mcp.get("description", "No description")
        if include_all or confirm(f"Include optional MCP: {mcp['name']} ({desc})?"):
            accepted.append(mcp["name"])
            ok(f"{mcp['name']} (included)")
        else:
            warn(f"{mcp['name']} (skipped)")

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
            result.append(mcp)
    return result


# ============================================================
# SUBCOMMANDS
# ============================================================

def cmd_sync(cfg: Config, args):
    # Check deps
    if not shutil.which("git"):
        print("Error: git is required", file=sys.stderr)
        sys.exit(1)

    prev_lock = cfg.load_lockfile()

    # Phase 1: Resolve optional MCPs
    info("Resolving optional MCPs...")
    accepted_optional = resolve_optionals(cfg, args.all)
    all_mcps = collect_mcps(cfg, accepted_optional)

    # Phase 2: Fetch packages + discover
    info("Fetching packages...")
    pm = PackageManager(cfg)
    discoveries = []

    for pkg_spec in cfg.packages:
        repo = pkg_spec.get("repo")
        ref = pkg_spec.get("ref", "main")
        local_path = pkg_spec.get("path")

        if repo:
            pkg_name = repo.split("/", 1)[1]
            pkg_path = pm.fetch(repo, ref, pkg_spec.get("sparse_paths"))
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

        discovery = apply_package_filters(
            pm.discover(pkg_path, pkg_name, pkg_spec.get("sparse_paths")),
            pkg_spec,
        )
        discoveries.append(discovery)

        parts = [f"{len(discovery['skills'])} skills"]
        if discovery["commands"]:
            parts.append(f"{len(discovery['commands'])} commands")
        if discovery["agents"]:
            parts.append(f"{len(discovery['agents'])} agents")
        if discovery["hooks_claude"]:
            parts.append("hooks(claude)")
        if discovery["hooks_cursor"]:
            parts.append("hooks(cursor)")
        if discovery["hooks_codex"]:
            parts.append("hooks(codex)")
        info(f"  {discovery['name']}: {', '.join(parts)}")

    # Security review
    if not args.yes and not args.dry_run:
        show_review(all_mcps)
        if not confirm("Apply these changes?"):
            print("Aborted.")
            return
    elif args.dry_run:
        show_review(all_mcps)
        info("Dry run — no changes written.")
        print(file=sys.stderr)
        info("Would deploy:")
        for pkg in discoveries:
            for s in pkg["skills"]:
                print(f"  skill: {s['name']}", file=sys.stderr)
            if "claude" in cfg.targets and pkg.get("hooks_claude"):
                print(f"  hooks: {pkg['name']} -> claude", file=sys.stderr)
            if "cursor" in cfg.targets and pkg.get("hooks_cursor"):
                print(f"  hooks: {pkg['name']} -> cursor", file=sys.stderr)
            if "codex" in cfg.targets and pkg.get("hooks_codex"):
                print(f"  hooks: {pkg['name']} -> codex ({cfg.codex_hooks_path()})", file=sys.stderr)
        return

    # Phase 3: Deploy
    deployer = Deployer(cfg)

    info("Pruning stale skills...")
    deployer.prune_skills(discoveries, prev_lock)

    info("Deploying skills...")
    total_skills = deployer.deploy_skills(discoveries)

    info("Deploying hooks...")
    deployer.deploy_hooks(discoveries)

    info("Pruning stale MCPs...")
    current_mcp_names = {m["name"] for m in all_mcps}
    deployer.prune_mcps(current_mcp_names, prev_lock)

    info("Syncing MCP servers...")
    deployer.sync_mcps(all_mcps)

    # Phase 4: Lockfile
    info("Generating lockfile...")
    lock = generate_lockfile(discoveries, cfg.data, cfg.targets)
    write_lockfile(lock, cfg.lockfile_path)
    ok(f"{cfg.lockfile_path.name} written")

    # Cleanup workspace IDE artifacts
    for p in [cfg.repo_dir / ".cursor" / "mcp.json", cfg.repo_dir / ".vscode"]:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)

    # Summary
    target_names = ", ".join(cfg.targets)
    mcp_paths = []
    for t in cfg.targets:
        p = cfg.mcp_path(t)
        if p:
            mcp_paths.append(f"~/{p.relative_to(Path.home())}")

    print(file=sys.stderr)
    info("Sync complete!")
    print(f"  {total_skills} skills deployed to: {target_names}", file=sys.stderr)
    print(f"  MCP servers synced to: {', '.join(mcp_paths)}", file=sys.stderr)
    if accepted_optional:
        print(f"  Optional MCPs included: {' '.join(accepted_optional)}", file=sys.stderr)
    print(file=sys.stderr)
    print("  Restart your AI IDEs to pick up changes.", file=sys.stderr)


def cmd_list(cfg: Config, _args):
    print()
    print("\033[1mPackages:\033[0m")
    for pkg in cfg.packages:
        repo = pkg.get("repo", pkg.get("path", "?"))
        ref = pkg.get("ref", "local")
        print(f"  {repo}  {ref}")

    prev_lock = cfg.load_lockfile()
    if prev_lock:
        print()
        print("\033[1mDiscovered Skills:\033[0m")
        for pkg in prev_lock.get("packages", []):
            name = pkg["name"]
            for s in pkg.get("discovered", {}).get("skills", []):
                print(f"  {s:40s} ({name})")

        print()
        print("\033[1mDiscovered Hooks:\033[0m")
        for pkg in prev_lock.get("packages", []):
            name = pkg["name"]
            discovered = pkg.get("discovered", {})
            for hook_name, key in [
                ("claude", "hooks_claude"),
                ("cursor", "hooks_cursor"),
                ("codex", "hooks_codex"),
            ]:
                if discovered.get(key):
                    print(f"  {hook_name:40s} ({name})")

    print()
    print("\033[1mMCP Servers:\033[0m")
    for mcp in cfg.mcps:
        opt = " (optional)" if mcp.get("optional") else ""
        if "url" in mcp:
            print(f"  {mcp['name']:30s} {mcp.get('transport', 'sse'):8s} {mcp['url']}{opt}")
        else:
            args_str = " ".join(mcp.get("args", []))
            print(f"  {mcp['name']:30s} {'stdio':8s} {mcp.get('command', 'npx')} {args_str}{opt}")
    for mcp in cfg.optional_mcps:
        args_str = " ".join(mcp.get("args", []))
        if "url" in mcp:
            print(f"  {mcp['name']:30s} {mcp.get('transport', 'sse'):8s} {mcp['url']} (optional)")
        else:
            print(f"  {mcp['name']:30s} {'stdio':8s} {mcp.get('command', 'npx')} {args_str} (optional)")

    print()
    print(f"\033[1mTargets:\033[0m {', '.join(cfg.targets)}")
    print()


def cmd_doctor(cfg: Config, _args):
    print()
    info(f"nexus doctor — v{NEXUS_VERSION}")
    print()

    # Manifest
    if cfg.yml_path.exists():
        ok(f"{cfg.yml_path.name} found")
        try:
            cfg.data  # trigger parse
            ok(f"{cfg.yml_path.name} is valid YAML")
        except SystemExit:
            warn(f"{cfg.yml_path.name} has YAML syntax errors")
    else:
        warn("nexus manifest not found")

    # Cache
    if cfg.cache_dir.exists():
        fetched = list(cfg.cache_dir.rglob("*.fetched"))
        ok(f"Package cache: {len(fetched)} packages cached")
    else:
        warn("Package cache: empty (run nexus sync)")

    # Lockfile
    if cfg.lockfile_path.exists():
        ok(f"{cfg.lockfile_path.name} exists")
    else:
        warn(f"{cfg.lockfile_path.name} missing (run nexus sync)")

    # Skill symlinks
    for target in cfg.targets:
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

    # MCP configs
    for target in cfg.targets:
        mcp_path = cfg.mcp_path(target)
        if not mcp_path or not mcp_path.exists():
            warn(f"{target} MCP config: not found")
            continue
        try:
            if cfg.mcp_format(target) == "codex_toml":
                import tomllib
                with open(mcp_path, "rb") as f:
                    data = tomllib.load(f)
                count = len(data.get("mcp_servers", {}))
            else:
                with open(mcp_path) as f:
                    data = json.load(f)
                if target == "claude":
                    count = len((data.get("projects", {})
                                 .get(str(cfg.repo_dir), {})
                                 .get("mcpServers", {})))
                else:
                    count = len(data.get("mcpServers", {}))
            ok(f"{target} MCP config: {count} servers ({mcp_path})")
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


def cmd_clean(cfg: Config, _args):
    info("Cleaning nexus artifacts...")

    # Remove skill symlinks pointing into our cache
    for target in cfg.targets:
        skill_dir = cfg.skill_path(target)
        if not skill_dir or not skill_dir.exists():
            continue
        for link in skill_dir.iterdir():
            if not link.is_symlink():
                continue
            dest = str(os.readlink(link))
            if ".nexus/cache" in dest or str(cfg.repo_dir) in dest:
                link.unlink()
                removed(f"{link.name} from {target}")

    # Remove compiled output
    compiled = cfg.nexus_dir / "compiled"
    if compiled.exists():
        shutil.rmtree(compiled)
    ok("Removed compiled output")

    # Remove cache
    if cfg.cache_dir.exists():
        shutil.rmtree(cfg.cache_dir)
        ok("Removed package cache")

    # Remove lockfile
    if cfg.lockfile_path.exists():
        cfg.lockfile_path.unlink()
        ok(f"Removed {cfg.lockfile_path.name}")

    # Remove generated IDE directories
    for d in [".cursor", ".github", ".claude/skills", ".agent"]:
        p = cfg.repo_dir / d
        if p.exists():
            shutil.rmtree(p)
    ok("Removed generated IDE directories")

    print()
    info("Clean complete. Run 'nexus sync' to rebuild.")


# ============================================================
# MAIN
# ============================================================

def resolve_repo_dir() -> Path:
    """Find the repo root by following the symlink of the script itself."""
    script = Path(__file__).resolve()
    return script.parent


def main():
    parser = argparse.ArgumentParser(
        prog="nexus",
        description=f"nexus v{NEXUS_VERSION} — Agent environment manager",
    )
    sub = parser.add_subparsers(dest="command")

    sp_sync = sub.add_parser("sync", help="Fetch packages, compile skills, merge MCPs, deploy to IDEs")
    sp_sync.add_argument("--all", action="store_true", help="Include all optional MCPs without prompting")
    sp_sync.add_argument("--yes", "-y", action="store_true", help="Skip security review confirmation")
    sp_sync.add_argument("--dry-run", action="store_true", help="Show what would change without writing")

    sub.add_parser("list", help="Show installed packages, skills, and MCP servers")
    sub.add_parser("doctor", help="Run diagnostics and health checks")
    sub.add_parser("clean", help="Remove all nexus-managed artifacts")
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()
    cfg = Config(resolve_repo_dir())

    dispatch = {
        "sync": cmd_sync,
        "list": cmd_list,
        "doctor": cmd_doctor,
        "clean": cmd_clean,
        "version": lambda _c, _a: print(f"nexus v{NEXUS_VERSION}"),
    }

    if not args.command:
        parser.print_help()
        return

    handler = dispatch.get(args.command)
    if handler:
        handler(cfg, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
