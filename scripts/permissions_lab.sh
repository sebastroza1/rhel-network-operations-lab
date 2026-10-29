#!/usr/bin/env bash
set -euo pipefail

lab_dir="$(mktemp -d)"
trap 'rm -rf -- "$lab_dir"' EXIT
chmod 755 "$lab_dir"
printf 'private data\n' > "$lab_dir/private.txt"
chmod 600 "$lab_dir/private.txt"

actual="$(stat -c '%a' "$lab_dir/private.txt")"
actual_owner="$(stat -c '%u:%g' "$lab_dir/private.txt")"
expected_owner="$(id -u):$(id -g)"
test "$actual" = "600"
test "$actual_owner" = "$expected_owner"

cross_user_status="SKIPPED"
if [ "$(id -u)" -eq 0 ]; then
    if command -v setpriv >/dev/null 2>&1; then
        if setpriv --reuid=65534 --regid=65534 --clear-groups true 2>/dev/null; then
            if setpriv --reuid=65534 --regid=65534 --clear-groups \
                test ! -r "$lab_dir/private.txt"; then
                cross_user_status="VERIFIED"
            else
                echo "cross-user access check failed: unprivileged user could read mode-600 file" >&2
                exit 1
            fi
        else
            cross_user_status="NOT_VERIFIED"
            echo "cross-user access check NOT VERIFIED: setpriv transition unavailable" >&2
        fi
    else
        echo "cross-user access check SKIPPED: setpriv is not installed" >&2
    fi
else
    echo "cross-user access check SKIPPED: requires a root-capable setpriv environment" >&2
fi

printf 'permission scenario: mode=%s owner=%s cross_user=%s\n' \
    "$actual" "$(stat -c '%U:%G' "$lab_dir/private.txt")" "$cross_user_status"

