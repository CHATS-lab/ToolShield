#!/bin/bash
# Starts the Notion MCP server behind supergateway (stdio -> SSE).
#
#   MCP_NOTION_PORT   supergateway port   (default: 9097)
#   NOTION_TOKEN      Notion API token    (required for the server to authenticate)

PORT="${MCP_NOTION_PORT:-9097}"

if [ -z "$NOTION_TOKEN" ]; then
    echo "⚠️  NOTION_TOKEN is not set; the Notion MCP server will fail to authenticate."
fi

echo "🔌 Starting Notion MCP Server on Port $PORT"
npx -y supergateway --port "$PORT" \
  --stdio "env NOTION_TOKEN=$NOTION_TOKEN npx -y @notionhq/notion-mcp-server"
