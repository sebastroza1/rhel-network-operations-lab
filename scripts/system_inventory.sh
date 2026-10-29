#!/usr/bin/env bash
set -euo pipefail

echo "== identity =="
id
umask
echo "== operating system =="
cat /etc/os-release
uname -a
echo "== memory =="
free -h
echo "== filesystems =="
df -hT
echo "== processes (top by memory) =="
ps -eo pid,ppid,user,stat,%cpu,%mem,comm --sort=-%mem | head -n 12
echo "== routes and listeners =="
ip route
ss -lntup
echo "== resolver =="
cat /etc/resolv.conf
getent hosts localhost
echo "== selected environment =="
env | sort | grep -E '^(HOME|HOSTNAME|LANG|PATH|SHELL|USER)=' || true

