# RHEL Network Operations Lab

A safe, reproducible operations portfolio project covering Linux inspection,
permissions, processes and signals, bounded disk-pressure exercises, and layered
DNS/TCP/HTTP troubleshooting. The Python scenarios execute entirely on loopback;
the Bash exercises use temporary files and processes; no host firewall, DNS,
routing table, or global network configuration is changed.

## What is actually demonstrated

- Distinguishing DNS, TCP refusal, HTTP 5xx, and application latency failures.
- Explicit timeouts, bounded retries, incremental backoff, and elapsed-time evidence.
- Linux inventory using `ip`, `ss`, `/proc`, `ps`, `free`, `df`, identity, and resolver tools.
- File permissions and an optional unprivileged-user read check.
- Process creation, SIGTERM handling, wait status, and cleanup.
- A capped 1–32 MiB disk-pressure fixture that is always removed by a trap.
- An isolated Compose network and hardened, read-only UBI application containers.
- Automated Python tests and Linux CI exercises.

## Run locally

Python 3.10+ is sufficient and the runtime has no third-party dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
python -m opslab.scenarios
```

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --no-deps -e .
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python -m opslab.scenarios
```

The scenario runner creates an ephemeral loopback server and records eight cases:
healthy HTTP, open TCP, HTTP 503, latency-induced timeout, delayed success, stopped
server, closed TCP port, and the reserved `.invalid` DNS failure.

## UBI container exercise

```bash
docker compose build
docker compose up --wait server
docker compose run --rm client
docker compose down
```

The image uses Red Hat's UBI 9 Python 3.12 stream (`ubi9/python-312:1`). The
stream tag is explicit but mutable; production supply-chain policy should resolve
and pin an approved digest after registry inspection. The Compose network is
`internal`, host ports are not published, root filesystems
are read-only, and `/tmp` is a 16 MiB tmpfs. The image adds common diagnostic tools
to Red Hat UBI 9 and runs the application as UID 1001.

## Important scope boundary

Red Hat Universal Base Image is a redistributable container userspace derived
from RHEL packages. It is **not a complete RHEL installation** and does not prove
production RHEL administration. This project does not claim systemd, SELinux,
firewalld, kernel, boot, package-repository subscription, or VM lifecycle practice.
Those exercises require a proper RHEL-compatible VM or host. Container runtime
validation is recorded separately in [reports/RESULTS.md](reports/RESULTS.md).

## Troubleshooting method

Start with scope and timestamps; then check resource pressure and process state;
then test name resolution, routing, listening sockets, TCP, HTTP, and application
logs in that order. The detailed decision guide and command set are in
[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Limitations

- Loopback behavior does not reproduce packet loss, multi-host routing, MTU, NAT,
  TLS, or a production resolver hierarchy.
- Python's HTTP server is an experiment fixture, not a production service.
- A port reserved and then released can theoretically be claimed by another process.
- Docker-dependent evidence requires a working daemon; static configuration parsing
  alone is not runtime validation.
- `ping` and raw packet tools may need capabilities intentionally absent here.

## License

MIT
