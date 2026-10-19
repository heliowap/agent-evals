import unittest

import bottle

from .hidden_support import call


def make_app(prefix, fail=False):
    seen = {}

    def child(environ, start_response):
        seen["child"] = (environ["SCRIPT_NAME"], environ["PATH_INFO"])
        if fail:
            raise RuntimeError("child failed")
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"child"]

    app = bottle.Bottle(catchall=True)
    app.mount(prefix, child)

    @app.hook("after_request")
    def log():
        seen["hook"] = (bottle.request.script_name, bottle.request.path, bottle.request.url)

    return app, seen


class TestMountMultiSegment(unittest.TestCase):
    def check(self, prefix):
        app, seen = make_app(prefix)
        status, _, body = call(app, prefix + "/x/y")
        self.assertEqual((status, body), (200, b"child"))
        self.assertEqual(seen["child"], (prefix, "/x/y"))
        self.assertEqual(seen["hook"], ("/", prefix + "/x/y", "http://127.0.0.1" + prefix + "/x/y"))

    def test_single_segment(self):
        self.check("/api")

    def test_two_segments(self):
        self.check("/api/v1")

    def test_three_segments(self):
        self.check("/api/v1/legacy")

    def test_exception_in_sub_app_restores_path(self):
        app, seen = make_app("/api/v1", fail=True)
        status, _, _ = call(app, "/api/v1/x")
        self.assertEqual(status, 500)
        self.assertEqual(seen["hook"][:2], ("/", "/api/v1/x"))
