#!/usr/bin/env bash
set -euo pipefail

target="${1:-/tmp}"
size_mib="${2:-8}"
case "$size_mib" in
    ''|*[!0-9]*) echo "size must be an integer MiB" >&2; exit 2 ;;
esac
if (( size_mib < 1 || size_mib > 32 )); then
    echo "size must be between 1 and 32 MiB" >&2
    exit 2
fi
test -d "$target"
file="$target/opslab-disk-pressure-$$.bin"
trap 'rm -f -- "$file"' EXIT
before="$(df -Pk "$target" | awk 'NR==2 {print $4}')"
dd if=/dev/zero of="$file" bs=1M count="$size_mib" status=none
after="$(df -Pk "$target" | awk 'NR==2 {print $4}')"
echo "bounded disk-pressure scenario: available_kib_before=$before available_kib_after=$after"

