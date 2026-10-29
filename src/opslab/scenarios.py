from __future__ import annotations

import argparse
import contextlib
import dataclasses
import http.server
import json
import socket
import threading
import time
from collections.abc import Iterator

from .diagnostics import ProbeResult, probe_http, probe_tcp, resolve_name


class ScenarioHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - HTTP handler API
        if self.path == "/slow":
            time.sleep(0.25)
            self._reply(200, b"delayed\n")
        elif self.path == "/error":
            self._reply(503, b"controlled failure\n")
        elif self.path == "/health":
            self._reply(200, b"ok\n")
        else:
            self._reply(404, b"not found\n")

    def _reply(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, format: str, *args: object) -> None:
        return


class ThreadedServer(http.server.ThreadingHTTPServer):
    daemon_threads = True


@contextlib.contextmanager
def local_server() -> Iterator[ThreadedServer]:
    server = ThreadedServer(("127.0.0.1", 0), ScenarioHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def reserve_closed_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_all() -> list[dict[str, object]]:
    results: list[tuple[str, ProbeResult]] = []
    with local_server() as server:
        port = int(server.server_address[1])
        base = f"http://127.0.0.1:{port}"
        results.append(("healthy_http", probe_http(f"{base}/health")))
        results.append(("open_tcp_port", probe_tcp("127.0.0.1", port)))
        results.append(("application_error", probe_http(f"{base}/error", retries=1)))
        results.append(("controlled_latency_timeout", probe_http(f"{base}/slow", timeout=0.05, retries=1)))
        results.append(("controlled_latency_success", probe_http(f"{base}/slow", timeout=1.0)))
    closed_port = reserve_closed_port()
    results.append(("stopped_server", probe_http(f"http://127.0.0.1:{closed_port}/health", retries=1)))
    results.append(("closed_tcp_port", probe_tcp("127.0.0.1", closed_port)))
    results.append(("dns_failure", resolve_name("does-not-exist.invalid")))
    return [{"scenario": name, **dataclasses.asdict(result)} for name, result in results]


def serve(port: int) -> None:
    server = ThreadedServer(("0.0.0.0", port), ScenarioHandler)
    print(f"opslab server listening on {port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe loopback networking scenarios")
    parser.add_argument("--serve", type=int, metavar="PORT")
    args = parser.parse_args()
    if args.serve is not None:
        serve(args.serve)
        return 0
    print(json.dumps(run_all(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

