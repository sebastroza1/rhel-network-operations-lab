#!/usr/bin/env bash
set -euo pipefail

lab_dir="$(mktemp -d)"
trap 'rm -rf -- "$lab_dir"' EXIT
printf 'private data\n' > "$lab_dir/private.txt"
chmod 600 "$lab_dir/private.txt"
actual="$(stat -c '%a' "$lab_dir/private.txt")"
test "$actual" = "600"
if command -v setpriv >/dev/null 2>&1; then
    setpriv --reuid=65534 --regid=65534 --clear-groups test ! -r "$lab_dir/private.txt"
fi
echo "permission scenario passed: mode=$actual owner=$(stat -c '%U:%G' "$lab_dir/private.txt")"

