#!/bin/bash
# Starts the Playwright MCP server behind supergateway (stdio -> SSE).
#
# Machine-specific values are overridable via environment variables
# (issue #5); defaults preserve the original behavior.
#
#   MCP_PLAYWRIGHT_PORT       supergateway port         (default: 9092)
#   PLAYWRIGHT_MCP_CMD        command running the MCP   (default: legacy node install when
#                             present, else `npx -y @playwright/mcp`)
#   PLAYWRIGHT_BROWSERS_PATH  browser binaries location (default: /root/.cache/ms-playwright
#                             when present, else Playwright's per-user default)

PORT="${MCP_PLAYWRIGHT_PORT:-9092}"

# Original hard-coded install locations; used only when they actually exist.
LEGACY_NODE="/root/.nvm/versions/node/v24.11.0/bin/node"
LEGACY_SERVER="/mnt/data/OpenAgentSafety/node_modules/@playwright/mcp/cli.js"

if [ -z "$PLAYWRIGHT_MCP_CMD" ]; then
    if [ -x "$LEGACY_NODE" ] && [ -f "$LEGACY_SERVER" ]; then
        PLAYWRIGHT_MCP_CMD="$LEGACY_NODE $LEGACY_SERVER"
    else
        PLAYWRIGHT_MCP_CMD="npx -y @playwright/mcp"
    fi
fi

echo "----------------------------------------------------------------"
echo "🔌 Starting Playwright MCP (Ephemeral Session)"
echo "----------------------------------------------------------------"

# 1. Create a unique temp directory for THIS session (locks & profile) and clean it up on exit
TEMP_HOME=$(mktemp -d -t playwright_session_XXXXXX)
trap 'rm -rf "$TEMP_HOME"' EXIT
mkdir -p "$TEMP_HOME/.cache"

# 2. Browser binaries: point to the original benchmark-host location when it
# exists and nothing was set explicitly; otherwise leave whatever the caller
# exported (or Playwright's per-user default) in place rather than exporting
# a path that doesn't exist on this machine.
DEFAULT_BROWSERS_PATH="/root/.cache/ms-playwright"
if [ -z "$PLAYWRIGHT_BROWSERS_PATH" ] && [ -d "$DEFAULT_BROWSERS_PATH" ]; then
    PLAYWRIGHT_BROWSERS_PATH="$DEFAULT_BROWSERS_PATH"
fi

# Point HOME to the TEMP location to avoid "SingletonLock" errors
export HOME="$TEMP_HOME"
export XDG_CACHE_HOME="$TEMP_HOME/.cache"

BROWSERS_ENV=""
if [ -n "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    export PLAYWRIGHT_BROWSERS_PATH
    BROWSERS_ENV="PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
fi

echo "📂 User Data (Locks): $TEMP_HOME"
echo "📂 Browser Binaries:  ${PLAYWRIGHT_BROWSERS_PATH:-<playwright default>}"

# 3. Run Supergateway with isolated, no-sandbox browser contexts to avoid Playwright lock errors
npx -y supergateway --port "$PORT" --stdio \
    "env HOME=$TEMP_HOME XDG_CACHE_HOME=$XDG_CACHE_HOME $BROWSERS_ENV PLAYWRIGHT_MCP_ISOLATED=1 PLAYWRIGHT_MCP_SANDBOX=0 $PLAYWRIGHT_MCP_CMD --isolated --no-sandbox"
