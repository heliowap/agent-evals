import base64
import unittest

import bottle

from .hidden_support import call


def basic(user, password):
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def auth_of(header):
    return bottle.BaseRequest({"HTTP_AUTHORIZATION": header}).auth


class TestBasicAuthColon(unittest.TestCase):
    def test_password_with_one_colon(self):
        self.assertEqual(auth_of(basic("alice", "pa:ss")), ("alice", "pa:ss"))

    def test_password_with_several_colons(self):
        self.assertEqual(auth_of(basic("bob", ":a::b:")), ("bob", ":a::b:"))

    def test_plain_password_still_works(self):
        self.assertEqual(auth_of(basic("carol", "secret")), ("carol", "secret"))

    def test_empty_password(self):
        self.assertEqual(auth_of(basic("dave", "")), ("dave", ""))

    def test_malformed_headers_return_none(self):
        no_colon = "Basic " + base64.b64encode(b"nocolon").decode()
        for header in (no_colon, "Basic", "Bearer abc"):
            self.assertIsNone(auth_of(header), header)

    def test_auth_basic_decorator_accepts_colon_password(self):
        app = bottle.Bottle()

        @app.route("/")
        @bottle.auth_basic(lambda user, pw: (user, pw) == ("alice", "pa:ss"))
        def index():
            return "ok"

        status, _, body = call(app, "/", {"Authorization": basic("alice", "pa:ss")})
        self.assertEqual((status, body), (200, b"ok"))
        status, _, _ = call(app, "/", {"Authorization": basic("alice", "wrong")})
        self.assertEqual(status, 401)
