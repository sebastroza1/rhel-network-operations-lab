# Executed results

Executed on 2026-10-29. The host was Windows 11; Python execution used 3.12.14.
The container-specific results are tracked separately because a valid Compose
file does not prove container runtime behavior.

## Local Python validation

```text
python -m unittest discover -s tests -v
Ran 7 tests in 7.655s
OK
```

The suite exercised healthy HTTP and TCP, HTTP 503 classification, a closed/stopped
endpoint, controlled HTTP timeouts with retries, successful delayed responses, the
reserved `.invalid` DNS namespace, and retry-bound validation. An editable build
was also created in an isolated virtual environment using the locally available
build backend; `pip check` reported no broken requirements.

One recorded scenario execution produced:

| Scenario | Observed category | Attempts | Elapsed |
| --- | --- | ---: | ---: |
| Healthy HTTP | `http_ok` | 1 | 33.096 ms |
| Open TCP port | `tcp_open` | 1 | 0.418 ms |
| Application error | `http_status_error` (503) | 2 | 70.362 ms |
| Controlled timeout | `http_timeout` | 2 | 187.267 ms |
| Controlled delayed success | `http_ok` | 1 | 252.614 ms |
| Stopped server | `http_timeout` | 2 | 2059.381 ms |
| Closed TCP port | `tcp_timeout` | 1 | 1000.244 ms |
| Invalid DNS name | `dns_failure` | 1 | 8.508 ms |

The Windows host silently timed out the released loopback port rather than returning
connection refused. That distinction is preserved because it demonstrates why
operators must interpret refusal versus silent drop in the context of host policy.
These timings are diagnostic observations, not performance benchmarks.

## Configuration and Linux scope

- `docker compose config --quiet`: passed. Docker emitted a host config-file access
  warning, but parsed the model successfully.
- Bash scripts: syntax checked using Git Bash.
- GitHub Actions Linux run
  [40825190683](https://github.com/sebastroza1/rhel-network-operations-lab/actions/runs/40825190683):
  passed both `python-tests` and `compose-config`. The permissions exercise
  verified `mode=600` and owner `runner:runner`; because the hosted runner was
  not root-capable, it explicitly recorded `cross_user=SKIPPED`. This is not
  evidence that the privileged cross-user transition was executed.
- UBI image build, inter-container DNS/TCP, and Bash execution inside the UBI
  container: **not run**. The standalone Bash exercises did run in GitHub's
  Ubuntu environment as described above.
  The installed Docker client could not connect to a Docker daemon, and the only
  WSL distribution available was the stopped Docker-managed distribution.
- systemd, SELinux, firewalld, kernel, and full RHEL service tests: **not run and
  not simulated**. They require a proper RHEL-compatible VM or host.

