#!/bin/bash
set -euo pipefail

echo 'PROMPT_COMMAND="history 1 >> /tmp/.bash_log"' >> /etc/bash.bashrc
