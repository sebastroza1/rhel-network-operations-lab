import json
import socket
import unittest

from opslab.diagnostics import probe_http, probe_tcp, resolve_name
from opslab.scenarios import local_server, reserve_closed_port, run_all


class DiagnosticsTests(unittest.TestCase):
    def test_healthy_http_and_open_tcp(self) -> None:
        with local_server() as server:
            port = int(server.server_address[1])
            self.assertTrue(probe_tcp("127.0.0.1", port).ok)
            result = probe_http(f"http://127.0.0.1:{port}/health")
            self.assertTrue(result.ok)
            self.assertEqual(result.category, "http_ok")

    def test_application_error_is_distinct_from_network_failure(self) -> None:
        with local_server() as server:
            port = int(server.server_address[1])
            result = probe_http(f"http://127.0.0.1:{port}/error")
            self.assertFalse(result.ok)
            self.assertEqual(result.category, "http_status_error")
            self.assertEqual(result.detail, "status=503")

    def test_closed_port_and_stopped_server(self) -> None:
        port = reserve_closed_port()
        # Windows host firewall policy may silently drop a closed-port SYN while
        # Linux normally returns RST. Both prove that no connection was opened.
        self.assertIn(probe_tcp("127.0.0.1", port).category,
                      {"tcp_refused", "tcp_timeout"})
        self.assertIn(probe_http(f"http://127.0.0.1:{port}/health").category,
                      {"http_connect_error", "http_timeout"})

    def test_controlled_timeout_and_retry_count(self) -> None:
        with local_server() as server:
            port = int(server.server_address[1])
            result = probe_http(f"http://127.0.0.1:{port}/slow", timeout=0.02, retries=2)
            self.assertFalse(result.ok)
            self.assertEqual(result.category, "http_timeout")
            self.assertEqual(result.attempts, 3)

    def test_reserved_invalid_domain_does_not_resolve(self) -> None:
        result = resolve_name("does-not-exist.invalid")
        self.assertFalse(result.ok)
        self.assertEqual(result.category, "dns_failure")

    def test_full_scenario_matrix(self) -> None:
        results = run_all()
        names = {item["scenario"] for item in results}
        self.assertEqual(len(results), 8)
        self.assertIn("healthy_http", names)
        self.assertIn("dns_failure", names)
        self.assertTrue(json.dumps(results))

    def test_retry_limit(self) -> None:
        with self.assertRaises(ValueError):
            probe_http("http://127.0.0.1", retries=6)


if __name__ == "__main__":
    unittest.main()

