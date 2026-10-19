import re
import unittest

import bottle

from .hidden_support import call

HEX32 = re.compile(r"^[0-9a-f]{32}$")


def make_app(header="X-Request-ID"):
    app = bottle.Bottle(catchall=True)
    if header:
        app.config["request_id.header"] = header
    seen = {}

    @app.route("/ok")
    def ok():
        seen["first"] = bottle.request.request_id
        seen["second"] = bottle.request.request_id
        return "ok"

    @app.route("/boom")
    def boom():
        raise RuntimeError("boom")

    @app.route("/abort")
    def do_abort():
        bottle.abort(403, "no")

    @app.route("/redirect")
    def do_redirect():
        bottle.redirect("/ok")

    @app.route("/created")
    def created():
        raise bottle.HTTPResponse("made", status=201)

    return app, seen


class TestRequestID(unittest.TestCase):
    def test_incoming_id_is_used_and_echoed(self):
        app, seen = make_app()
        status, headers, _ = call(app, "/ok", {"X-Request-ID": "abc-123"})
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("X-Request-ID"), "abc-123")
        self.assertEqual(seen["first"], "abc-123")

    def test_generated_id_is_hex32_and_stable(self):
        app, seen = make_app()
        _, headers, _ = call(app, "/ok")
        self.assertRegex(seen["first"], HEX32)
        self.assertEqual(seen["first"], seen["second"])
        self.assertEqual(headers.get("X-Request-ID"), seen["first"])

    def test_generated_ids_differ_between_requests(self):
        app, _ = make_app()
        a = call(app, "/ok")[1].get("X-Request-ID")
        b = call(app, "/ok")[1].get("X-Request-ID")
        self.assertNotEqual(a, b)

    def test_every_response_path_carries_the_header(self):
        app, _ = make_app()
        # redirect() answers 302 to HTTP/1.0 clients and 303 to HTTP/1.1 clients.
        for path, expected in (("/missing", {404}), ("/boom", {500}), ("/abort", {403}),
                               ("/redirect", {302, 303}), ("/created", {201})):
            status, headers, _ = call(app, path, {"X-Request-ID": "rid-" + path})
            self.assertIn(status, expected, path)
            self.assertEqual(headers.get("X-Request-ID"), "rid-" + path, path)

    def test_custom_header_name(self):
        app, _ = make_app("X-Correlation-ID")
        _, headers, _ = call(app, "/ok", {"X-Correlation-ID": "corr"})
        self.assertEqual(headers.get("X-Correlation-ID"), "corr")
        self.assertNotIn("X-Request-ID", headers)

    def test_unset_sends_no_header(self):
        app, _ = make_app(header=None)
        app.route("/plain", callback=lambda: "plain")
        _, headers, _ = call(app, "/plain", {"X-Request-ID": "abc"})
        self.assertNotIn("X-Request-ID", headers)
