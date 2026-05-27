#!/usr/bin/env bash
set -euo pipefail

# Simple TCP health check for SecureChat endpoint.
# Usage:
#   ./deploy/scripts/healthcheck-tcp.sh chat.example.com 65432

HOST="${1:-}"
PORT="${2:-65432}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-5}"

if [[ -z "${HOST}" ]]; then
  echo "Usage: $0 <host> [port]"
  exit 2
fi

if timeout "${TIMEOUT_SECONDS}" bash -c "cat < /dev/null > /dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
  echo "OK: ${HOST}:${PORT} reachable"
  exit 0
fi

echo "ERROR: ${HOST}:${PORT} unreachable"
exit 1
