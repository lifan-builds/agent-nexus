#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bin_dir="${NEXUS_BIN_DIR:-$HOME/.local/bin}"
link_path="$bin_dir/nexus"
target_path="$repo_dir/nexus.py"
force=0
uninstall=0

usage() {
  cat <<EOF
Usage: scripts/install-local.sh [--force] [--uninstall]

Options:
  --force      Replace an existing nexus file or symlink at $link_path
  --uninstall  Remove the Agent Nexus symlink installed by this checkout
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=1
      ;;
    --uninstall)
      uninstall=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [[ "$uninstall" -eq 1 ]]; then
  if [[ -L "$link_path" ]]; then
    existing_target="$(readlink "$link_path")"
    if [[ "$existing_target" == "$target_path" || "$force" -eq 1 ]]; then
      rm "$link_path"
      echo "Removed $link_path"
      exit 0
    fi
    echo "Refusing to remove $link_path because it points to $existing_target" >&2
    echo "Pass --force to remove it anyway." >&2
    exit 1
  fi

  if [[ -e "$link_path" ]]; then
    echo "Refusing to remove $link_path because it is not a symlink." >&2
    echo "Remove it manually if you own it." >&2
    exit 1
  fi

  echo "Agent Nexus is not installed at $link_path"
  exit 0
fi

mkdir -p "$bin_dir"

if [[ -e "$link_path" || -L "$link_path" ]]; then
  if [[ -L "$link_path" ]]; then
    existing_target="$(readlink "$link_path")"
    if [[ "$existing_target" != "$target_path" && "$force" -ne 1 ]]; then
      echo "Refusing to replace existing symlink: $link_path -> $existing_target" >&2
      echo "Pass --force if you want this checkout to own that command." >&2
      exit 1
    fi
  elif [[ "$force" -ne 1 ]]; then
    echo "Refusing to replace existing non-symlink file: $link_path" >&2
    echo "Move it aside or pass --force if you want Agent Nexus to replace it." >&2
    exit 1
  fi
  rm -f "$link_path"
fi

ln -s "$target_path" "$link_path"

cat <<EOF
Agent Nexus local install complete.

Installed:
  $link_path -> $target_path

Next steps:
  1. Ensure this directory is on PATH:
     $bin_dir
  2. Run:
     nexus audit
     nexus init
     nexus sync --dry-run

Uninstall:
  scripts/install-local.sh --uninstall
EOF
