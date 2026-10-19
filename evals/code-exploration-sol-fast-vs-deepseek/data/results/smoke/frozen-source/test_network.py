from contextlib import contextmanager
from dataclasses import replace
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import unittest
from urllib.parse import urlsplit

import runtime


@contextmanager
def upstream(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class ObserverNetwork(unittest.TestCase):
    def setUp(self):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler)
            server.server_close()
        except PermissionError:
            self.skipTest("Loopback bind forbidden by sandbox; run on terminal")

    def test_rate_limit_delay_is_forwarded_without_headers_in_evidence(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "7")
                self.end_headers()
                self.wfile.write(b'{"error":"limited"}')

        recorded = []
        with upstream(Handler) as endpoint:
            candidate = replace(runtime.CANDIDATES[0], upstream=endpoint)
            with runtime.observer(candidate, recorded, 5) as observed:
                url = urlsplit(observed)
                connection = http.client.HTTPConnection(url.hostname, url.port, timeout=5)
                connection.request("POST", "/v1/chat/completions", json.dumps({"model": "gpt-6.1-sol",
                                   "reasoning_effort": "low", "service_tier": "priority"}),
                                   {"Authorization": "Bearer private-key"})
                response = connection.getresponse()
                self.assertEqual((response.status, response.getheader("Retry-After")), (429, "7"))
                self.assertEqual(response.read(), b'{"error":"limited"}')
                connection.close()
        self.assertEqual(recorded[0]["status"], 429)
        self.assertNotIn("private-key", json.dumps(recorded))

    def test_stalled_stream_is_cancelled_before_observer_returns(self):
        active = threading.Event()
        release = threading.Event()

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                self.wfile.write(b'data: {"model":"gpt-6.1-sol","service_tier":"priority"}\n\n')
                self.wfile.flush()
                active.set()
                release.wait(timeout=5)

        recorded = []
        try:
            with upstream(Handler) as endpoint:
                candidate = replace(runtime.CANDIDATES[0], upstream=endpoint)
                with runtime.observer(candidate, recorded, 5) as observed:
                    url = urlsplit(observed)
                    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=5)
                    connection.request("POST", "/v1/chat/completions", json.dumps({"model": "gpt-6.1-sol",
                                       "reasoning_effort": "low", "service_tier": "priority"}))
                    response = connection.getresponse()
                    self.assertTrue(active.wait(timeout=2))
                    self.assertTrue(response.readline().startswith(b"data:"))
                    started = time.monotonic()
                self.assertLess(time.monotonic() - started, 2)
                saved = json.dumps(recorded, sort_keys=True)
                time.sleep(0.1)
                self.assertEqual(json.dumps(recorded, sort_keys=True), saved)
                self.assertIn("wall_s", recorded[0])
                connection.close()
                release.set()
        finally:
            release.set()


if __name__ == "__main__":
    unittest.main()
