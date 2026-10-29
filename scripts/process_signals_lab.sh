#!/usr/bin/env bash
set -euo pipefail

sleep 30 &
child=$!
trap 'kill "$child" 2>/dev/null || true' EXIT
test -d "/proc/$child"
kill -TERM "$child"
if wait "$child"; then
    echo "expected SIGTERM exit" >&2
    exit 1
else
    status=$?
fi
test ! -d "/proc/$child"
trap - EXIT
echo "signal scenario passed: pid=$child wait_status=$status"

