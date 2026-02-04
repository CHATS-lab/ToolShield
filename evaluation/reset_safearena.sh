#!/bin/bash

export DOMAIN_NAME="chats-lab-gui-agent.uk"
export SUFFIX="aa-0"
export WA_FULL_RESET="https://sa-reset-${SUFFIX}.${DOMAIN_NAME}"

# Initiate reset
echo "Initiating reset..."
curl ${WA_FULL_RESET}/reset
echo ""

# Wait for reset to complete
echo "Waiting for reset to complete..."
while true; do
    STATUS=$(curl -s ${WA_FULL_RESET}/status)
    echo "Status: $STATUS"
    
    if echo "$STATUS" | grep -q "Ready for duty"; then
        echo "Reset complete!"
        break
    elif echo "$STATUS" | grep -q "Error executing reset script"; then
        echo "Reset failed! Check logs:"
        curl ${WA_FULL_RESET}/logs
        exit 1
    fi
    
    sleep 10  # Wait 10 seconds before checking again
done

# Now run your evaluation
echo "Starting evaluation..."
# poetry run python run_eval.py --agent-llm-config agent --agent-llm-config-file /root/OpenAgentSafety/evaluation/agent_config/config.toml --env-llm-config env --env-llm-config-file /root/OpenAgentSafety/evaluation/agent_config/config.toml --outputs-path ./test_output --server-hostname 64.176.198.19 --task-path /root/OpenAgentSafety/workspaces/mcp-tasks/playwright/reddit/single_turn_tasks/safety-baltimore-arms-forum
