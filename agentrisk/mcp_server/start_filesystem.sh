#!/bin/bash
# Starts the Filesystem MCP server behind supergateway (stdio -> SSE).
#
# Every machine-specific value is overridable via environment variables
# (issue #5); the defaults reproduce the original benchmark-host behavior
# exactly, and degrade gracefully when a default is unavailable (non-root
# user, or install paths from a different machine).
#
#   MCP_FILESYSTEM_PORT      supergateway port              (default: 9090)
#   SHARED_WORKSPACE_DIR     shared workspace directory     (default: /mnt/shared_workspace)
#   AGENT_WORKSPACE_DIR      agent-visible workspace path   (default: /workspace)
#   FILESYSTEM_MCP_CMD       command running the MCP server (default: legacy node install
#                            when present, else `npx -y @modelcontextprotocol/server-filesystem`)
#   FILESYSTEM_ALLOWED_DIRS  space-separated allowed dirs   (default: original list)

PORT="${MCP_FILESYSTEM_PORT:-9090}"
SHARED_DIR="${SHARED_WORKSPACE_DIR:-/mnt/shared_workspace}"
MOUNT_POINT="${AGENT_WORKSPACE_DIR:-/workspace}"

# Original hard-coded install locations. Used only when they actually exist,
# so hosts with that layout keep identical behavior; everyone else resolves
# the server through npx instead of hitting ENOENT.
LEGACY_NODE="/root/.nvm/versions/node/v24.11.0/bin/node"
LEGACY_SERVER="/mnt/data/OpenAgentSafety/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js"

if [ -z "$FILESYSTEM_MCP_CMD" ]; then
    if [ -x "$LEGACY_NODE" ] && [ -f "$LEGACY_SERVER" ]; then
        FILESYSTEM_MCP_CMD="$LEGACY_NODE $LEGACY_SERVER"
    else
        FILESYSTEM_MCP_CMD="npx -y @modelcontextprotocol/server-filesystem"
    fi
fi

# Shared workspace: keep the original location when writable; otherwise fall
# back to a user-writable directory instead of dying with 'Permission denied'.
# (For root both checks always pass, so the original host is unaffected.)
if ! mkdir -p "$SHARED_DIR" 2>/dev/null || [ ! -w "$SHARED_DIR" ]; then
    # Per-uid suffix so two unprivileged users don't collide on a shared
    # /tmp directory owned by whoever ran first.
    FALLBACK_SHARED="${TMPDIR:-/tmp}/toolshield_shared_workspace_$(id -u)"
    echo "⚠️  Cannot create or write $SHARED_DIR (permission denied); using $FALLBACK_SHARED."
    echo "    Set SHARED_WORKSPACE_DIR to override."
    SHARED_DIR="$FALLBACK_SHARED"
    mkdir -p "$SHARED_DIR"
fi

# Agent workspace view. Root: identical to the original script (remove stale
# entry, mkdir, bind mount). Non-root: bind mounts are unavailable, so a
# symlink provides the same view; if even that is impossible, serve the
# shared directory directly.
WORKSPACE_DIR=""
if [ "$(id -u)" -eq 0 ]; then
    rm -f "$MOUNT_POINT" 2>/dev/null
    mkdir -p "$MOUNT_POINT"
    mount --bind "$SHARED_DIR" "$MOUNT_POINT"
    WORKSPACE_DIR="$MOUNT_POINT"
else
    if [ -d "$MOUNT_POINT" ] && [ ! -L "$MOUNT_POINT" ]; then
        # Existing real directory (e.g. /workspace in a devcontainer):
        # use it as-is. ln -sfn into it would drop a stray symlink INSIDE
        # the directory instead of replacing it.
        WORKSPACE_DIR="$MOUNT_POINT"
    elif ln -sfn "$SHARED_DIR" "$MOUNT_POINT" 2>/dev/null; then
        WORKSPACE_DIR="$MOUNT_POINT"
    else
        echo "⚠️  Cannot create $MOUNT_POINT (permission denied); serving $SHARED_DIR directly."
        echo "    Set AGENT_WORKSPACE_DIR to a writable location to override."
    fi
fi

ls -ld "$SHARED_DIR"

ALLOWED_DIRS="${FILESYSTEM_ALLOWED_DIRS:-/root $SHARED_DIR $WORKSPACE_DIR /tmp /var /etc}"

npx -y supergateway --port "$PORT" --stdio "$FILESYSTEM_MCP_CMD $ALLOWED_DIRS"
