#!/bin/bash
# Starts the Postgres MCP server behind supergateway (stdio -> SSE).
#
# Machine-specific values are overridable via environment variables
# (issue #5); defaults preserve the original behavior.
#
#   MCP_POSTGRES_PORT   supergateway port      (default: 9091)
#   POSTGRES_DB_URL     database connection    (default: postgresql://postgres:password@localhost:5432/postgres)
#   POSTGRES_MCP_EXEC   postgres-mcp binary    (default: legacy conda path when present,
#                       else `postgres-mcp` found on PATH)

PORT="${MCP_POSTGRES_PORT:-9091}"
# Connection to the standard 'postgres' db where we create our tables
DB_URL="${POSTGRES_DB_URL:-postgresql://postgres:password@localhost:5432/postgres}"

# Original hard-coded conda install; used only when it exists.
LEGACY_EXEC="/root/miniforge3/envs/mcp_mark/bin/postgres-mcp"

if [ -z "$POSTGRES_MCP_EXEC" ]; then
    if [ -x "$LEGACY_EXEC" ]; then
        POSTGRES_MCP_EXEC="$LEGACY_EXEC"
    elif command -v postgres-mcp >/dev/null 2>&1; then
        POSTGRES_MCP_EXEC="$(command -v postgres-mcp)"
    else
        echo "❌ postgres-mcp not found."
        echo "   Install it (e.g. \`pip install postgres-mcp\`) or set POSTGRES_MCP_EXEC."
        exit 1
    fi
fi

echo "----------------------------------------------------------------"
echo "🔌 Starting Postgres MCP Server on Port $PORT"
echo "----------------------------------------------------------------"
echo "   Target DB: $DB_URL"
echo "   Mode:      Stdio -> SSE (Supergateway)"

# Just run the server.
# The data reset is now handled by Python (evaluation/db_setup.py)
npx -y supergateway --port "$PORT" --stdio "$POSTGRES_MCP_EXEC $DB_URL"
