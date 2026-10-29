from __future__ import annotations

import dataclasses
import socket
import time
import urllib.error
import urllib.request


@dataclasses.dataclass(frozen=True)
class ProbeResult:
    target: str
    ok: bool
    category: str
    attempts: int
    elapsed_ms: float
    detail: str


def resolve_name(host: str, port: int = 80) -> ProbeResult:
    started = time.perf_counter()
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        detail = ", ".join(sorted({item[4][0] for item in addresses}))
        return ProbeResult(host, True, "dns_ok", 1, _elapsed(started), detail)
    except socket.gaierror as error:
        return ProbeResult(host, False, "dns_failure", 1, _elapsed(started), str(error))


def probe_tcp(host: str, port: int, timeout: float = 1.0) -> ProbeResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ProbeResult(f"{host}:{port}", True, "tcp_open", 1, _elapsed(started), "connected")
    except socket.timeout as error:
        return ProbeResult(f"{host}:{port}", False, "tcp_timeout", 1, _elapsed(started), str(error))
    except ConnectionRefusedError as error:
        return ProbeResult(f"{host}:{port}", False, "tcp_refused", 1, _elapsed(started), str(error))
    except OSError as error:
        return ProbeResult(f"{host}:{port}", False, "tcp_error", 1, _elapsed(started), str(error))


def probe_http(url: str, timeout: float = 1.0, retries: int = 0, backoff: float = 0.05) -> ProbeResult:
    if retries < 0 or retries > 5:
        raise ValueError("retries must be between 0 and 5")
    started = time.perf_counter()
    last_category = "http_error"
    last_detail = "no attempt"
    for attempt in range(1, retries + 2):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = response.status
                response.read(1024)
                return ProbeResult(url, 200 <= status < 400, "http_ok", attempt,
                                   _elapsed(started), f"status={status}")
        except urllib.error.HTTPError as error:
            last_category = "http_status_error"
            last_detail = f"status={error.code}"
        except urllib.error.URLError as error:
            reason = error.reason
            last_category = "http_timeout" if isinstance(reason, socket.timeout) else "http_connect_error"
            last_detail = str(reason)
        except (TimeoutError, socket.timeout) as error:
            last_category = "http_timeout"
            last_detail = str(error)
        if attempt <= retries:
            time.sleep(backoff * attempt)
    return ProbeResult(url, False, last_category, retries + 1, _elapsed(started), last_detail)


def _elapsed(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)

