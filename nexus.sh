#!/usr/bin/env bash
# nexus — Agent environment manager
# Manages skills, hooks, and MCP servers across multiple AI IDEs from nexus.yml.
set -euo pipefail

NEXUS_VERSION="0.1.0"
# Resolve symlinks to find the actual script location
_resolve_link() {
    local target="$1"
    while [ -L "$target" ]; do
        local dir="$(cd "$(dirname "$target")" && pwd)"
        target="$(readlink "$target")"
        # Handle relative symlinks
        [[ "$target" != /* ]] && target="$dir/$target"
    done
    echo "$(cd "$(dirname "$target")" && pwd)"
}
REPO_DIR="$(_resolve_link "$0")"
NEXUS_YML="$REPO_DIR/nexus.yml"
NEXUS_DIR="$REPO_DIR/.nexus"
CACHE_DIR="$NEXUS_DIR/cache"
COMPILED_DIR="$NEXUS_DIR/compiled"
LOCKFILE="$REPO_DIR/nexus.lock.yml"

# ---------- IDE target paths ----------
# Bash 3.2 compatible (no associative arrays)
skill_path_for() {
    case "$1" in
        claude)       echo "$HOME/.claude/skills" ;;
        cursor)       echo "$HOME/.cursor/skills" ;;
        antigravity)  echo "$HOME/.gemini/antigravity/skills" ;;
        *)            echo "" ;;
    esac
}
mcp_path_for() {
    case "$1" in
        claude)       echo "$HOME/.claude.json" ;;
        cursor)       echo "$HOME/.cursor/mcp.json" ;;
        antigravity)  echo "$HOME/.gemini/antigravity/mcp_config.json" ;;
        *)            echo "" ;;
    esac
}

# ---------- Output helpers (all to stderr so stdout stays clean for data) ----------
info()    { printf '\033[1;34m==>\033[0m %s\n' "$1" >&2; }
ok()      { printf '\033[1;32m  +\033[0m %s\n' "$1" >&2; }
warn()    { printf '\033[1;33m  !\033[0m %s\n' "$1" >&2; }
removed() { printf '\033[1;31m  -\033[0m %s\n' "$1" >&2; }
unchanged() { printf '\033[0;37m  =\033[0m %s\n' "$1" >&2; }

confirm() {
    if "${INCLUDE_ALL:-false}"; then return 0; fi
    local prompt="$1"
    printf '\033[1;33m  ?\033[0m %s [y/N] ' "$prompt"
    read -r reply
    case "$reply" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# ---------- Dependency checks ----------
check_deps() {
    local missing=()
    command -v git &>/dev/null || missing+=(git)
    command -v jq &>/dev/null || missing+=(jq)
    command -v python3 &>/dev/null || missing+=(python3)
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Error: missing required tools: ${missing[*]}"
        echo "Install them and try again."
        exit 1
    fi
}

# ---------- YAML parsing via Python ----------
# Reads nexus.yml and outputs JSON to stdout
parse_manifest() {
    python3 - "$NEXUS_YML" <<'PYEOF'
import sys, json
try:
    import yaml
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyyaml"], stdout=subprocess.DEVNULL)
    import yaml
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
PYEOF
}

# ---------- Package fetching ----------
fetch_package() {
    local repo="$1" ref="$2"
    local org repo_name
    org="$(echo "$repo" | cut -d/ -f1)"
    repo_name="$(echo "$repo" | cut -d/ -f2)"

    # Resolve ref to commit SHA
    local resolved_sha
    if [[ "$ref" =~ ^[0-9a-f]{40}$ ]]; then
        resolved_sha="$ref"
    else
        resolved_sha=$(git ls-remote "https://github.com/$repo" "$ref" 2>/dev/null | head -1 | cut -f1)
        if [ -z "$resolved_sha" ]; then
            # Try refs/tags/
            resolved_sha=$(git ls-remote "https://github.com/$repo" "refs/tags/$ref" 2>/dev/null | head -1 | cut -f1)
        fi
        if [ -z "$resolved_sha" ]; then
            warn "Could not resolve ref '$ref' for $repo"
            return 1
        fi
    fi

    local cache_path="$CACHE_DIR/github.com/$org/$repo_name/$resolved_sha"

    if [ -f "${cache_path}.fetched" ]; then
        unchanged "$repo@${resolved_sha:0:7} (cached)"
        echo "$cache_path"
        return 0
    fi

    info "Fetching $repo@$ref (${resolved_sha:0:7})..."
    mkdir -p "$(dirname "$cache_path")"
    rm -rf "${cache_path}.tmp"

    if git clone --depth=1 --branch "$ref" "https://github.com/$repo" "${cache_path}.tmp" 2>/dev/null; then
        rm -rf "${cache_path}.tmp/.git"
        mv "${cache_path}.tmp" "$cache_path"
    else
        # Branch clone failed, try full clone + checkout
        git clone --depth=1 "https://github.com/$repo" "${cache_path}.tmp" 2>/dev/null
        (cd "${cache_path}.tmp" && git fetch --depth=1 origin "$resolved_sha" 2>/dev/null && git checkout "$resolved_sha" 2>/dev/null) || true
        rm -rf "${cache_path}.tmp/.git"
        mv "${cache_path}.tmp" "$cache_path"
    fi

    # Marker goes alongside the dir, not inside it (to avoid polluting skill content)
    touch "${cache_path}.fetched"
    ok "$repo@${resolved_sha:0:7} (fetched)"
    echo "$cache_path"
}

# ---------- Asset discovery ----------
# Discovers skills, hooks, commands, agents in a package directory
# Outputs JSON: { skills: [...], hooks_claude: path|null, hooks_cursor: path|null, commands: [...], agents: [...] }
discover_package() {
    local pkg_path="$1" pkg_name="$2"

    python3 - "$pkg_path" "$pkg_name" <<'PYEOF'
import os, sys, json

pkg_path, pkg_name = sys.argv[1], sys.argv[2]
result = {
    "name": pkg_name,
    "path": pkg_path,
    "skills": [],
    "hooks_claude": None,
    "hooks_cursor": None,
    "commands": [],
    "agents": []
}

# Find all SKILL.md files recursively
for root, dirs, files in os.walk(pkg_path):
    # Skip hidden directories and test directories
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'tests', 'test')]
    if 'SKILL.md' in files:
        skill_name = os.path.basename(root)
        # If SKILL.md is at package root, use package name instead of directory hash
        if os.path.normpath(root) == os.path.normpath(pkg_path):
            skill_name = pkg_name
        result["skills"].append({
            "name": skill_name,
            "path": root
        })

# Find hooks
for hooks_file in ["hooks/hooks.json", "hooks.json"]:
    full = os.path.join(pkg_path, hooks_file)
    if os.path.isfile(full):
        result["hooks_claude"] = full
        break

for hooks_file in ["hooks/hooks-cursor.json", "hooks-cursor.json"]:
    full = os.path.join(pkg_path, hooks_file)
    if os.path.isfile(full):
        result["hooks_cursor"] = full
        break

# Find commands
commands_dir = os.path.join(pkg_path, "commands")
if os.path.isdir(commands_dir):
    for f in os.listdir(commands_dir):
        if f.endswith('.md'):
            result["commands"].append(f[:-3])

# Find agents
agents_dir = os.path.join(pkg_path, "agents")
if os.path.isdir(agents_dir):
    for f in os.listdir(agents_dir):
        if f.endswith('.md'):
            result["agents"].append(f[:-3])

print(json.dumps(result))
PYEOF
}

# ---------- Skill deployment ----------
deploy_skills() {
    local discoveries_json="$1"
    local targets_json="$2"

    local targets
    targets=$(echo "$targets_json" | jq -r '.[]')

    local total_skills=0

    # Iterate over each package's discovered skills
    echo "$discoveries_json" | jq -c '.[]' | while IFS= read -r pkg; do
        local pkg_name
        pkg_name=$(echo "$pkg" | jq -r '.name')
        local skills
        skills=$(echo "$pkg" | jq -c '.skills[]' 2>/dev/null) || continue

        echo "$skills" | while IFS= read -r skill; do
            local skill_name skill_path
            skill_name=$(echo "$skill" | jq -r '.name')
            skill_path=$(echo "$skill" | jq -r '.path')

            for target in $targets; do
                local target_dir="$(skill_path_for "$target")"
                [ -z "$target_dir" ] && continue
                mkdir -p "$target_dir"

                local link="$target_dir/$skill_name"
                if [ -L "$link" ] || [ ! -e "$link" ]; then
                    ln -snf "$skill_path" "$link"
                else
                    warn "$link exists and is not a symlink, skipping"
                fi
            done
            ok "$skill_name -> $(echo "$targets" | tr '\n' ',' | sed 's/,$//')"
            total_skills=$((total_skills + 1))
        done
    done
}

# ---------- Hook aggregation + deduplication ----------
deploy_hooks() {
    local discoveries_json="$1"

    # Collect all hook files per format
    local claude_hooks=()
    local cursor_hooks=()

    while IFS= read -r hooks_claude; do
        [ "$hooks_claude" != "null" ] && [ -n "$hooks_claude" ] && claude_hooks+=("$hooks_claude")
    done < <(echo "$discoveries_json" | jq -r '.[].hooks_claude')

    while IFS= read -r hooks_cursor; do
        [ "$hooks_cursor" != "null" ] && [ -n "$hooks_cursor" ] && cursor_hooks+=("$hooks_cursor")
    done < <(echo "$discoveries_json" | jq -r '.[].hooks_cursor')

    # Merge and deduplicate hooks using jq
    if [ ${#cursor_hooks[@]} -gt 0 ]; then
        local merged
        merged=$(python3 - "${cursor_hooks[@]}" <<'PYEOF'
import sys, json, hashlib

def dedup_key(entry):
    """Generate a hash key for dedup, stripping metadata fields."""
    clean = {k: v for k, v in entry.items() if not k.startswith('_')}
    return hashlib.sha256(json.dumps(clean, sort_keys=True).encode()).hexdigest()

merged = {}
for path in sys.argv[1:]:
    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue
    hooks = data.get("hooks", {})
    for event_name, entries in hooks.items():
        if event_name not in merged:
            merged[event_name] = {"entries": [], "seen": set()}
        for entry in entries:
            key = dedup_key(entry)
            if key not in merged[event_name]["seen"]:
                merged[event_name]["seen"].add(key)
                merged[event_name]["entries"].append(entry)

# Build output
output = {"hooks": {}}
total = 0
for event_name, data in merged.items():
    output["hooks"][event_name] = data["entries"]
    total += len(data["entries"])

print(json.dumps(output, indent=2))
PYEOF
)
        # Write cursor hooks
        mkdir -p "$REPO_DIR/.cursor"
        echo "$merged" > "$REPO_DIR/.cursor/hooks.json"
        ok "Cursor hooks: deduplicated ($(echo "$merged" | jq '[.hooks | to_entries[] | .value | length] | add // 0') unique entries)"
    fi

    if [ ${#claude_hooks[@]} -gt 0 ]; then
        mkdir -p "$REPO_DIR/.github/hooks"
        for f in "${claude_hooks[@]}"; do
            local basename
            basename=$(basename "$f")
            cp "$f" "$REPO_DIR/.github/hooks/$basename"
        done
        ok "Claude hooks: copied to .github/hooks/"
    fi
}

# ---------- MCP config merging ----------
sync_mcps() {
    local manifest_json="$1"
    local targets_json="$2"
    local accepted_optional="$3"  # comma-separated names

    local targets
    targets=$(echo "$targets_json" | jq -r '.[]')

    for target in $targets; do
        local mcp_path="$(mcp_path_for "$target")"
        [ -z "$mcp_path" ] && continue

        info "Syncing MCPs to $mcp_path..."

        python3 - "$manifest_json" "$mcp_path" "$accepted_optional" "$target" "$REPO_DIR" <<'PYEOF'
import sys, json, os, shutil

manifest = json.loads(sys.argv[1])
mcp_path = sys.argv[2]
accepted_csv = sys.argv[3]
target = sys.argv[4]
repo_dir = sys.argv[5]
accepted_optional = set(accepted_csv.split(",")) if accepted_csv else set()

# Collect MCPs: core (non-optional) + accepted optional from mcps + optional_mcps
all_mcps = []
for mcp in manifest.get("mcps", []):
    if mcp.get("optional", False):
        if mcp["name"] in accepted_optional:
            all_mcps.append(mcp)
    else:
        all_mcps.append(mcp)
for mcp in manifest.get("optional_mcps", []):
    if mcp["name"] in accepted_optional:
        all_mcps.append(mcp)

if not all_mcps:
    print("  No MCPs to sync")
    sys.exit(0)

# Read existing config
if os.path.exists(mcp_path):
    with open(mcp_path) as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
else:
    os.makedirs(os.path.dirname(mcp_path), exist_ok=True)
    config = {}

# Claude Code stores MCPs per-project inside ~/.claude.json
# Other targets use a flat mcpServers at the file root
if target == "claude":
    projects = config.setdefault("projects", {})
    project = projects.setdefault(repo_dir, {})
    servers = project.setdefault("mcpServers", {})
else:
    servers = config.setdefault("mcpServers", {})

# Standard PATH for restricted environments
path_env = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

added, updated, skipped = [], [], []
for mcp in all_mcps:
    name = mcp["name"]

    # SSE/HTTP transport
    if mcp.get("transport") == "sse" or "url" in mcp:
        entry = {"type": "sse", "url": mcp["url"]}
    else:
        # stdio transport
        command = mcp.get("command", "npx")
        if command in ("npx", "node"):
            resolved = shutil.which(command)
            if resolved:
                command = resolved

        entry = {"type": "stdio", "command": command, "args": mcp.get("args", [])}

        # Build env
        env = dict(mcp.get("env") or {})
        if "PATH" not in env:
            env["PATH"] = path_env
        entry["env"] = env

    if name in servers:
        if servers[name] == entry:
            skipped.append(name)
            continue
        updated.append(name)
    else:
        added.append(name)

    servers[name] = entry

# Write back
with open(mcp_path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")

for n in added:
    print(f"  \033[1;32m+\033[0m {n} (added)")
for n in updated:
    print(f"  \033[1;33m~\033[0m {n} (updated)")
for n in skipped:
    print(f"  \033[0;37m=\033[0m {n} (unchanged)")
PYEOF
    done
}

# ---------- Security review ----------
show_review() {
    local manifest_json="$1"
    local accepted_optional="$2"

    echo ""
    info "Security review — MCP servers to be registered:"
    echo ""

    python3 - "$manifest_json" "$accepted_optional" <<'PYEOF'
import sys, json

manifest = json.loads(sys.argv[1])
accepted_csv = sys.argv[2]
accepted_optional = set(accepted_csv.split(",")) if accepted_csv else set()

all_mcps = []
for mcp in manifest.get("mcps", []):
    if mcp.get("optional", False):
        if mcp["name"] in accepted_optional:
            all_mcps.append(mcp)
    else:
        all_mcps.append(mcp)
for mcp in manifest.get("optional_mcps", []):
    if mcp["name"] in accepted_optional:
        all_mcps.append(mcp)

for mcp in all_mcps:
    name = mcp["name"]
    if "url" in mcp:
        detail = f"sse: {mcp['url']}"
    else:
        cmd = mcp.get("command", "npx")
        args = " ".join(mcp.get("args", []))
        detail = f"stdio: {cmd} {args}"
    print(f"    {name:30s} {detail}")

print()
PYEOF
}

# ---------- Lockfile generation ----------
generate_lockfile() {
    local discoveries_json="$1"
    local manifest_json="$2"
    local targets_json="$3"

    python3 - "$discoveries_json" "$manifest_json" "$targets_json" "$NEXUS_VERSION" <<'PYEOF'
import sys, json, datetime

discoveries = json.loads(sys.argv[1])
manifest = json.loads(sys.argv[2])
targets = json.loads(sys.argv[3])
version = sys.argv[4]

lock = {
    "lockfile_version": 1,
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "nexus_version": version,
    "packages": [],
    "mcps": {"managed": []}
}

for pkg in discoveries:
    entry = {
        "name": pkg["name"],
        "path": pkg["path"],
        "discovered": {
            "skills": [s["name"] for s in pkg.get("skills", [])],
            "hooks_claude": pkg.get("hooks_claude") is not None,
            "hooks_cursor": pkg.get("hooks_cursor") is not None,
            "commands": pkg.get("commands", []),
            "agents": pkg.get("agents", [])
        },
        "deployed_to": targets
    }
    lock["packages"].append(entry)

for mcp in manifest.get("mcps", []):
    if not mcp.get("optional", False):
        lock["mcps"]["managed"].append({"name": mcp["name"]})

for mcp in manifest.get("optional_mcps", []):
    lock["mcps"]["managed"].append({"name": mcp["name"], "optional": True})

# Output as YAML-ish (valid YAML via JSON-compatible subset)
import yaml
try:
    import yaml
except ImportError:
    # Fallback: write as JSON
    print(json.dumps(lock, indent=2))
    sys.exit(0)

print(yaml.dump(lock, default_flow_style=False, sort_keys=False))
PYEOF
}


# ============================================================
# SUBCOMMANDS
# ============================================================

cmd_sync() {
    local INCLUDE_ALL=false
    local AUTO_YES=false
    local DRY_RUN=false

    for arg in "$@"; do
        case "$arg" in
            --all) INCLUDE_ALL=true ;;
            --yes|-y) AUTO_YES=true ;;
            --dry-run) DRY_RUN=true ;;
        esac
    done

    check_deps

    if [ ! -f "$NEXUS_YML" ]; then
        echo "Error: nexus.yml not found in $REPO_DIR"
        exit 1
    fi

    # Phase 1: Parse manifest
    info "Parsing nexus.yml..."
    local manifest_json
    manifest_json=$(parse_manifest)

    local targets_json
    targets_json=$(echo "$manifest_json" | jq -c '.targets // ["claude","cursor","antigravity"]')

    # Phase 2: Resolve optional MCPs
    info "Resolving optional MCPs..."
    local OPTIONAL_ACCEPTED=()

    # Inline optional MCPs (optional: true in mcps section)
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        local desc
        desc=$(echo "$manifest_json" | jq -r --arg n "$name" '.mcps[] | select(.name == $n) | .description // "No description"')
        if $INCLUDE_ALL || confirm "Include optional MCP: $name ($desc)?"; then
            OPTIONAL_ACCEPTED+=("$name")
            ok "$name (included)"
        else
            warn "$name (skipped)"
        fi
    done < <(echo "$manifest_json" | jq -r '.mcps[]? | select(.optional == true) | .name')

    # Separate optional_mcps section
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        local desc
        desc=$(echo "$manifest_json" | jq -r --arg n "$name" '.optional_mcps[] | select(.name == $n) | .description // "No description"')
        if $INCLUDE_ALL || confirm "Include optional MCP: $name ($desc)?"; then
            OPTIONAL_ACCEPTED+=("$name")
            ok "$name (included)"
        else
            warn "$name (skipped)"
        fi
    done < <(echo "$manifest_json" | jq -r '.optional_mcps[]? | .name')

    local optional_csv=""
    for n in "${OPTIONAL_ACCEPTED[@]+"${OPTIONAL_ACCEPTED[@]}"}"; do
        if [ -n "$optional_csv" ]; then optional_csv="$optional_csv,$n"; else optional_csv="$n"; fi
    done

    # Phase 3: Fetch packages
    info "Fetching packages..."
    local discoveries=()
    local all_discoveries_json="["

    while IFS= read -r pkg_line; do
        [ -z "$pkg_line" ] && continue
        local repo ref
        repo=$(echo "$pkg_line" | jq -r '.repo // empty')
        ref=$(echo "$pkg_line" | jq -r '.ref // "main"')
        local local_path
        local_path=$(echo "$pkg_line" | jq -r '.path // empty')

        local pkg_path=""
        local pkg_name=""

        if [ -n "$repo" ]; then
            pkg_name=$(echo "$repo" | cut -d/ -f2)
            pkg_path=$(fetch_package "$repo" "$ref")
            if [ -z "$pkg_path" ]; then
                warn "Failed to fetch $repo, skipping"
                continue
            fi
        elif [ -n "$local_path" ]; then
            pkg_path="$REPO_DIR/$local_path"
            pkg_name=$(basename "$local_path")
            if [ ! -d "$pkg_path" ]; then
                warn "Local path $local_path does not exist, skipping"
                continue
            fi
            ok "$pkg_name (local)"
        fi

        # Phase 4: Discover assets
        local discovery
        discovery=$(discover_package "$pkg_path" "$pkg_name")

        local skill_count cmd_count agent_count
        skill_count=$(echo "$discovery" | jq '.skills | length')
        cmd_count=$(echo "$discovery" | jq '.commands | length')
        agent_count=$(echo "$discovery" | jq '.agents | length')
        local has_hooks_claude has_hooks_cursor
        has_hooks_claude=$(echo "$discovery" | jq '.hooks_claude != null')
        has_hooks_cursor=$(echo "$discovery" | jq '.hooks_cursor != null')

        local summary="$skill_count skills"
        [ "$cmd_count" -gt 0 ] && summary="$summary, $cmd_count commands"
        [ "$agent_count" -gt 0 ] && summary="$summary, $agent_count agents"
        [ "$has_hooks_claude" = "true" ] && summary="$summary, hooks(claude)"
        [ "$has_hooks_cursor" = "true" ] && summary="$summary, hooks(cursor)"
        info "  $pkg_name: $summary"

        if [ "$all_discoveries_json" != "[" ]; then
            all_discoveries_json="$all_discoveries_json,"
        fi
        all_discoveries_json="$all_discoveries_json$discovery"
    done < <(echo "$manifest_json" | jq -c '.packages[]?')

    all_discoveries_json="$all_discoveries_json]"

    # Security review
    if ! $AUTO_YES && ! $DRY_RUN; then
        show_review "$manifest_json" "$optional_csv"
        if ! confirm "Apply these changes?"; then
            echo "Aborted."
            exit 0
        fi
    elif $DRY_RUN; then
        show_review "$manifest_json" "$optional_csv"
        info "Dry run — no changes written."
        echo ""
        info "Would deploy:"
        echo "$all_discoveries_json" | jq -r '.[].skills[].name' | while read -r s; do
            echo "  skill: $s"
        done
        exit 0
    fi

    # Phase 5: Deploy
    info "Deploying skills..."
    deploy_skills "$all_discoveries_json" "$targets_json"

    info "Deploying hooks..."
    deploy_hooks "$all_discoveries_json"

    info "Syncing MCP servers..."
    sync_mcps "$manifest_json" "$targets_json" "$optional_csv"

    # Phase 6: Lockfile
    info "Generating lockfile..."
    generate_lockfile "$all_discoveries_json" "$manifest_json" "$targets_json" > "$LOCKFILE"
    ok "nexus.lock.yml written"

    # Cleanup: remove workspace Cursor MCP if generated
    rm -f "$REPO_DIR/.cursor/mcp.json" 2>/dev/null || true
    rm -rf "$REPO_DIR/.vscode" 2>/dev/null || true

    echo ""
    info "Sync complete!"
    local total_skills
    total_skills=$(echo "$all_discoveries_json" | jq '[.[].skills | length] | add // 0')
    echo "  $total_skills skills deployed to: $(echo "$targets_json" | jq -r '. | join(", ")')"
    echo "  MCP servers synced to: $(echo "$targets_json" | jq -r '[.[] as $t | if $t == "claude" then "~/.claude.json" elif $t == "cursor" then "~/.cursor/mcp.json" elif $t == "antigravity" then "~/.gemini/antigravity/mcp_config.json" else $t end] | join(", ")')"
    if [ ${#OPTIONAL_ACCEPTED[@]} -gt 0 ]; then
        echo "  Optional MCPs included: ${OPTIONAL_ACCEPTED[*]}"
    fi
    echo ""
    echo "  Restart your AI IDEs to pick up changes."
}

cmd_list() {
    check_deps

    if [ ! -f "$NEXUS_YML" ]; then
        echo "Error: nexus.yml not found"
        exit 1
    fi

    local manifest_json
    manifest_json=$(parse_manifest)

    echo ""
    printf '\033[1mPackages:\033[0m\n'
    echo "$manifest_json" | jq -r '.packages[]? | "  \(.repo // .path)  \(.ref // "local")"'

    # If lockfile exists, show discovered assets
    if [ -f "$LOCKFILE" ]; then
        echo ""
        printf '\033[1mDiscovered Skills:\033[0m\n'
        python3 - "$LOCKFILE" <<'PYEOF'
import sys
try:
    import yaml
except ImportError:
    print("  (install PyYAML to read lockfile)")
    sys.exit(0)
with open(sys.argv[1]) as f:
    lock = yaml.safe_load(f)
for pkg in lock.get("packages", []):
    name = pkg["name"]
    skills = pkg.get("discovered", {}).get("skills", [])
    for s in skills:
        print(f"  {s:40s} ({name})")
PYEOF
    fi

    echo ""
    printf '\033[1mMCP Servers:\033[0m\n'
    echo "$manifest_json" | jq -r '
        (.mcps // [])[] |
        if .url then
          "  \(.name)\t\(.transport // "sse")\t\(.url)" + (if .optional then " (optional)" else "" end)
        else
          "  \(.name)\t\(.transport // "stdio")\t\(.command) \(.args | join(" "))" + (if .optional then " (optional)" else "" end)
        end
    ' | column -t -s$'\t'

    local opt_mcps
    opt_mcps=$(echo "$manifest_json" | jq -r '(.optional_mcps // [])[]? | "  \(.name)\tstdio\t\(.command) \(.args | join(" ")) (optional)"' | column -t -s$'\t')
    [ -n "$opt_mcps" ] && echo "$opt_mcps"

    echo ""
    printf '\033[1mTargets:\033[0m %s\n' "$(echo "$manifest_json" | jq -r '.targets | join(", ")')"
    echo ""
}

cmd_doctor() {
    check_deps
    echo ""
    info "nexus doctor — v$NEXUS_VERSION"
    echo ""

    # Check manifest
    if [ -f "$NEXUS_YML" ]; then
        ok "nexus.yml found"
        if python3 -c "import yaml; yaml.safe_load(open('$NEXUS_YML'))" 2>/dev/null; then
            ok "nexus.yml is valid YAML"
        else
            warn "nexus.yml has YAML syntax errors"
        fi
    else
        warn "nexus.yml not found"
    fi

    # Check cache
    if [ -d "$CACHE_DIR" ]; then
        local pkg_count
        pkg_count=$(find "$CACHE_DIR" -name "*.fetched" 2>/dev/null | wc -l | tr -d ' ')
        ok "Package cache: $pkg_count packages cached"
    else
        warn "Package cache: empty (run nexus sync)"
    fi

    # Check lockfile
    if [ -f "$LOCKFILE" ]; then
        ok "nexus.lock.yml exists"
    else
        warn "nexus.lock.yml missing (run nexus sync)"
    fi

    # Check skill symlinks
    local manifest_json
    manifest_json=$(parse_manifest 2>/dev/null) || manifest_json="{}"
    local targets
    targets=$(echo "$manifest_json" | jq -r '.targets[]? // empty' 2>/dev/null) || targets=""

    for target in $targets; do
        local skill_dir="$(skill_path_for "$target")"
        [ -z "$skill_dir" ] && continue
        if [ -d "$skill_dir" ]; then
            local count broken
            count=$(find "$skill_dir" -maxdepth 1 -type l 2>/dev/null | wc -l | tr -d ' ')
            broken=$(find "$skill_dir" -maxdepth 1 -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l | tr -d ' ')
            if [ "$broken" -gt 0 ]; then
                warn "$target skills: $count symlinks ($broken broken)"
            else
                ok "$target skills: $count symlinks"
            fi
        else
            warn "$target skills: directory missing"
        fi
    done

    # Check MCP configs
    for target in $targets; do
        local mcp_path="$(mcp_path_for "$target")"
        [ -z "$mcp_path" ] && continue
        if [ -f "$mcp_path" ]; then
            local server_count
            server_count=$(jq '.mcpServers | length' "$mcp_path" 2>/dev/null) || server_count="?"
            ok "$target MCP config: $server_count servers ($mcp_path)"
        else
            warn "$target MCP config: not found ($mcp_path)"
        fi
    done

    # Check for hook duplication
    local cursor_hooks="$REPO_DIR/.cursor/hooks.json"
    if [ -f "$cursor_hooks" ]; then
        local hook_count
        hook_count=$(jq '[.hooks | to_entries[] | .value | length] | add // 0' "$cursor_hooks" 2>/dev/null) || hook_count="?"
        if [ "$hook_count" -gt 10 ]; then
            warn "Cursor hooks: $hook_count entries (possible duplication — run nexus sync to fix)"
        else
            ok "Cursor hooks: $hook_count entries"
        fi
    fi

    # Check for legacy APM artifacts
    if [ -f "$REPO_DIR/apm.yml" ]; then
        warn "Legacy apm.yml found — consider removing"
    fi
    if [ -d "$REPO_DIR/apm_modules" ]; then
        warn "Legacy apm_modules/ found — consider removing"
    fi

    echo ""
}

cmd_clean() {
    info "Cleaning nexus artifacts..."

    local manifest_json
    manifest_json=$(parse_manifest 2>/dev/null) || manifest_json="{}"
    local targets
    targets=$(echo "$manifest_json" | jq -r '.targets[]? // empty' 2>/dev/null) || targets=""

    # Remove skill symlinks that point into our cache
    for target in $targets; do
        local skill_dir="$(skill_path_for "$target")"
        [ -z "$skill_dir" ] || [ ! -d "$skill_dir" ] && continue

        for link in "$skill_dir"/*/; do
            [ -L "${link%/}" ] || continue
            local dest
            dest=$(readlink "${link%/}")
            if [[ "$dest" == *".nexus/cache"* ]] || [[ "$dest" == *"$REPO_DIR"* ]]; then
                rm -f "${link%/}"
                removed "$(basename "${link%/}") from $target"
            fi
        done
    done

    # Remove compiled output
    rm -rf "$COMPILED_DIR"
    ok "Removed compiled output"

    # Remove cache
    if [ -d "$CACHE_DIR" ]; then
        rm -rf "$CACHE_DIR"
        ok "Removed package cache"
    fi

    # Remove lockfile
    if [ -f "$LOCKFILE" ]; then
        rm -f "$LOCKFILE"
        ok "Removed nexus.lock.yml"
    fi

    # Remove generated IDE files
    rm -rf "$REPO_DIR/.cursor" "$REPO_DIR/.github" "$REPO_DIR/.claude/skills" "$REPO_DIR/.agent"
    ok "Removed generated IDE directories"

    echo ""
    info "Clean complete. Run 'nexus sync' to rebuild."
}

# ============================================================
# MAIN
# ============================================================
cmd_help() {
    cat <<EOF
nexus v$NEXUS_VERSION — Agent environment manager

Usage: nexus <command> [options]

Commands:
  sync      Fetch packages, compile skills, merge MCPs, deploy to IDEs
  list      Show installed packages, skills, and MCP servers
  doctor    Run diagnostics and health checks
  clean     Remove all nexus-managed artifacts

Sync options:
  --all       Include all optional MCPs without prompting
  --yes, -y   Skip security review confirmation
  --dry-run   Show what would change without writing anything

Examples:
  nexus sync              # Interactive deployment
  nexus sync --all        # Include optional MCPs
  nexus sync --dry-run    # Preview changes
  nexus list              # Show current state
  nexus doctor            # Check health
  nexus clean             # Remove everything
EOF
}

main() {
    local cmd="${1:-help}"
    shift || true

    case "$cmd" in
        sync)    cmd_sync "$@" ;;
        list)    cmd_list "$@" ;;
        doctor)  cmd_doctor "$@" ;;
        clean)   cmd_clean "$@" ;;
        help|--help|-h) cmd_help ;;
        version|--version|-v) echo "nexus v$NEXUS_VERSION" ;;
        *)
            echo "Unknown command: $cmd"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
