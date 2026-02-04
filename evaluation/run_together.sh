#!/usr/bin/env bash
set -euo pipefail

retry_eval() {
    local desc="$1"; shift
    local max_attempts=5
    local attempt=1
    while true; do
        echo "Attempt $attempt for $desc"
        if "$@"; then
            echo "$desc succeeded"
            return 0
        fi
        if [ $attempt -ge $max_attempts ]; then
            echo "❌ $desc failed after $max_attempts attempts. Skipping..."
            return 1
        fi
        echo "Attempt $attempt for $desc failed. Retrying in 5 seconds..."
        sleep 5
        attempt=$((attempt + 1))
    done
}

cleanup() {
    echo "🧹 Cleaning up OpenHands runtime containers and volumes..."
    
    # 1. Kill container processes first (fixes permission denied)
    docker ps -q --filter 'name=openhands-runtime' | \
        xargs -r docker inspect --format '{{.State.Pid}}' 2>/dev/null | \
        xargs -r sudo kill -9 2>/dev/null || true
    
    # 2. Wait for processes to exit
    sleep 2
    
    # 3. Remove containers
    docker ps -a --filter 'name=openhands-runtime' -q | xargs -r docker rm -f 2>/dev/null || true
    
    # 4. Prune volumes
    docker volume prune -f
    
    echo "✅ Cleanup completed"
}


# --- SAFEARENA CHECKS ---
needs_safearena_reset() {
    local path="$1"
    if [[ "$path" == *"/reddit/"* ]] || [[ "$path" == *"/shopping/"* ]] || [[ "$path" == *"/shopping_admin/"* ]]; then
        return 0  # true
    fi
    return 1  # false
}

# --- PLAYWRIGHT CHECKS ---
needs_playwright_cleanup() {
    local path="$1"
    if [[ "$path" == *"/playwright/"* ]]; then
        return 0  # true
    fi
    return 1  # false
}

cleanup_playwright() {
    echo "🧹 Cleaning up Playwright browser processes..."
    pkill -f "playwright_chromiumdev_profile" || true
    echo "✅ Playwright cleanup completed"
}

needs_gitlab_reset() {
    local path="$1"
    if [[ "$path" == *"/gitlab/"* ]] || [[ "$path" == *"_gitlab"* ]]; then
        return 0  # true
    fi
    return 1  # false
}

reset_gitlab() {
    echo "🦊 Resetting GitLab..."
    curl -X POST "http://the-agent-company.com:2999/api/reset-gitlab"
    
    echo "⏳ Waiting for GitLab to be ready..."
    while true; do
        status=$(curl -s -o /dev/null -w "%{http_code}" -I "http://the-agent-company.com:2999/api/healthcheck/gitlab")
        echo "GitLab status: $status"
        if [ "$status" = "200" ]; then
            echo "✅ GitLab ready!"
            break
        fi
        sleep 5
    done
}

# --- POSTGRES CHECKS & RESET (NEW) ---
needs_postgres_reset() {
    local path="$1"
    if [[ "$path" == *"postgres"* ]]; then
        return 0
    fi
    return 1
}

reset_postgres() {
    echo "🐘 Resetting Postgres Container (Batch Maintenance)..."
    
    # 1. Get container PID and kill it directly
    PID=$(docker inspect --format '{{.State.Pid}}' mcpmark-postgres 2>/dev/null)
    if [ -n "$PID" ] && [ "$PID" != "0" ]; then
        echo "🔪 Killing process with PID: $PID"
        sudo kill -9 $PID 2>/dev/null || true
        sleep 2
    fi
    
    # 2. Force remove the container
    docker rm -f mcpmark-postgres 2>/dev/null || true
    
    # 3. CRITICAL: Prune volumes to wipe old data/passwords
    docker volume prune -f
    
    # 4. Restart fresh
    docker run --name mcpmark-postgres \
        -e POSTGRES_PASSWORD=password \
        -e POSTGRES_HOST_AUTH_METHOD=trust \
        -p 5432:5432 \
        -d postgres
    
    echo "⏳ Waiting 5s for Postgres to initialize..."
    sleep 5
    
    echo "✅ Postgres container reset complete"
}

# ---- claude tasks ----
AGENT_CFG="agent"
ENV_CFG="env"
AGENT_CFG_FILE="agent_config/config.toml"
ENV_CFG_FILE="agent_config/config.toml"
SERVER_HOST="localhost"
REMOTE_HOST="64.176.198.19"

EXPERIENCE_PATH="/mnt/data/MT-AgentRisk_ToolShield/self_exploration/experience_list_claude_playwright.json"

BASE_DIRS=(
    "/mnt/data/MT-AgentRisk_ToolShield/workspace/batch2"
)
OUTPUT_DIRS=(
    "/mnt/data/MT-AgentRisk_ToolShield/evaluation/test_output"
)
 
for i in "${!BASE_DIRS[@]}"; do
    BASE_DIR="${BASE_DIRS[$i]}"
    OUTPUT_DIR="${OUTPUT_DIRS[$i]}"
    
    task_count=0          # For SafeArena (Every 10)
    postgres_batch_count=0 # For Postgres (Every 30)
    gitlab_batch_count=0

    for task_dir in "$BASE_DIR"/*; do
        if [[ -d "$task_dir" ]]; then
            
            # --- SAFEARENA RESET (Existing) ---
            if [ $task_count -eq 500 ]; then
                if needs_safearena_reset "$BASE_DIR"; then
                    echo "🔄 Resetting SafeArena for $BASE_DIR..."
                    bash /mnt/data/MT-AgentRisk_ToolShield/evaluation/reset_safearena.sh
                fi
                task_count=0
            fi
            task_count=$((task_count + 1))
            
            # --- GITLAB RESET ---
            if needs_gitlab_reset "$BASE_DIR"; then
                if [ $gitlab_batch_count -ge 10 ]; then
                    reset_gitlab
                    gitlab_batch_count=0
                fi
                gitlab_batch_count=$((gitlab_batch_count + 1))
            fi

            # --- POSTGRES RESET (New) ---
            if needs_postgres_reset "$BASE_DIR"; then
                if [ $postgres_batch_count -ge 1 ]; then
                    reset_postgres
                    postgres_batch_count=0
                fi
                postgres_batch_count=$((postgres_batch_count + 1))
            fi

            echo "Running task: $task_dir"
            if ! retry_eval "task $task_dir" \
                poetry run python run_eval.py \
                    --agent-llm-config "$AGENT_CFG" \
                    --agent-llm-config-file "$AGENT_CFG_FILE" \
                    --env-llm-config "$ENV_CFG" \
                    --env-llm-config-file "$ENV_CFG_FILE" \
                    --outputs-path "$OUTPUT_DIR" \
                    --server-hostname "$REMOTE_HOST" \
                    --task-path "$task_dir"; then
                echo "⚠️  Skipping to next task due to failure..."
            fi

            cleanup
            if needs_playwright_cleanup "$BASE_DIR"; then
                cleanup_playwright
            fi
            docker images --format '{{.Repository}}:{{.Tag}}' | grep 'ghcr.io/all-hands-ai/runtime' | xargs -r docker rmi -f
            docker images | grep ghcr.io/all-hands-ai/runtime || true
            echo "Task processed: $task_dir"
            echo "----------------------------------------"
        fi
    done
done

docker system prune -f
docker builder prune -f

# Final cleanup
echo "🎉 All tasks completed! Running final cleanup..."
cleanup
cleanup_playwright
docker system prune -f
docker builder prune -f
echo "✅ All done!"
