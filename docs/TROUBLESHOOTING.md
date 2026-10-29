# Linux service troubleshooting runbook

Use the layers in order. Preserve timestamps and exact errors; avoid changing the
system before evidence is collected.

## 1. Define the symptom and blast radius

- Is failure local to one client, one process, one host, or every client?
- Record the target name, IP, port, protocol, first failure time, and recent change.
- Reproduce with a bounded timeout. A hanging command without a timeout is weak evidence.

## 2. Check resources and process state

```bash
uptime
free -h
df -hT
df -ih
ps -eo pid,ppid,user,stat,%cpu,%mem,etime,comm --sort=-%cpu
cat /proc/<pid>/status
```

Disk blocks and inodes are separate failure modes. Process state `D` suggests
uninterruptible I/O wait; `Z` is a zombie. Validate ownership and permissions
with `namei -l`, `stat`, `id`, and `getfacl` where available.

## 3. Separate name, path, transport, and application failures

```bash
getent hosts service-name
ip route get <destination-ip>
ss -lntp
curl --verbose --connect-timeout 2 --max-time 5 http://service:8080/health
```

- DNS failure: no address returned; inspect `/etc/resolv.conf` and resolver logs.
- TCP refusal: the host answered but nothing accepted that port, or a reject rule did.
- TCP timeout: packet loss, routing, firewall drop, overload, or an unresponsive peer.
- HTTP 5xx: TCP and HTTP succeeded; investigate application and dependencies.
- Slow HTTP with healthy TCP: inspect queues, saturation, downstream latency, and logs.

## 4. Inspect logs and service lifecycle on a full Linux host

```bash
systemctl status <unit> --no-pager
journalctl -u <unit> --since '-30 min' --no-pager
systemctl show <unit> -p ActiveState,SubState,Result,ExecMainStatus
```

Do not use these steps inside the UBI container as evidence of RHEL service
administration. UBI is an application userspace and this lab does not boot systemd.

## 5. Form and test one hypothesis

Prefer the least invasive test. Examples: query a loopback health endpoint, compare
DNS name with known IP, inspect one listener, or reproduce against a controlled
server. Document symptom, evidence, cause, remediation, and a prevention check.

## Scenario diagnosis table

| Scenario | Expected evidence | Cause | Remediation |
| --- | --- | --- | --- |
| Healthy server | TCP open, HTTP 200 | None | Establish as baseline |
| Server stopped | TCP refused or policy-dependent timeout | No listener or dropped traffic | Confirm route/policy; start service; inspect prior exit |
| Closed port | Refused, or timeout under silent-drop policy | Wrong port, no listener, or filtering | Verify configuration and `ss -lntp` |
| DNS failure | `getent`/resolver failure | Invalid/missing record or resolver path | Correct record/config; re-test authoritative path |
| Application error | TCP open, HTTP 503 | Application/dependency failure | Inspect logs, health dependencies, saturation |
| Controlled latency | TCP open, HTTP timeout | Handler delay exceeds client budget | Trace latency; tune cause before retry policy |
| Low volume space | `df` available blocks decrease | Bounded fixture consumes tmpfs | Remove fixture; set alert and retention policy |

Retries can hide incidents and amplify load. Use bounded attempts, deadlines,
backoff, and only retry operations that are safe to repeat.

