#!/bin/bash
set -euo pipefail

echo "ALL" > /etc/at.allow && rm -f /etc/at.deny
