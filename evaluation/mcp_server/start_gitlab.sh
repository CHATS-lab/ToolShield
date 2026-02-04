#!/bin/bash
PORT=9093
NODE_EXEC="/root/.nvm/versions/node/v24.11.0/bin/node"
SERVER_SCRIPT="/root/OpenAgentSafety/node_modules/@modelcontextprotocol/server-gitlab/dist/index.js"
API_URL="http://127.0.0.1:8929/api/v4"
TOKEN="glpat-OPENHANDS_EVAL_TOKEN_01"

echo "----------------------------------------------------------------"
echo "🔌 Starting GitLab MCP on Port $PORT"
echo "----------------------------------------------------------------"
echo ">>> GITLAB START DEBUG <<<" >&2
echo "Target API URL: $API_URL" >&2
echo "Token Length: ${#TOKEN}" >&2
echo "Token Preview: ${TOKEN:0:20}..." >&2

npx -y supergateway --port $PORT --stdio \
    "env GITLAB_API_URL=$API_URL GITLAB_PERSONAL_ACCESS_TOKEN=$TOKEN $NODE_EXEC $SERVER_SCRIPT"
