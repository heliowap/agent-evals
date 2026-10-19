import unittest
import uuid

import bottle

from .hidden_support import call

U = uuid.UUID("12345678-9abc-4def-8123-456789abcdef")


def make_app():
    app = bottle.Bottle()

    @app.route("/item/<id:uuid>", name="item")
    def item(id):
        return f"{type(id).__name__}:{id}"

    return app


class TestUUIDFilter(unittest.TestCase):
    def test_lowercase_match_passes_uuid_object(self):
        status, _, body = call(make_app(), f"/item/{U}")
        self.assertEqual((status, body), (200, f"UUID:{U}".encode()))

    def test_uppercase_match(self):
        status, _, body = call(make_app(), f"/item/{str(U).upper()}")
        self.assertEqual((status, body), (200, f"UUID:{U}".encode()))

    def test_non_uuid_is_404(self):
        app = make_app()
        for path in ("/item/not-a-uuid", "/item/1234", "/item/" + str(U)[:-1],
                     "/item/" + str(U) + "0", "/item/" + str(U).replace("a", "g")):
            self.assertEqual(call(app, path)[0], 404, path)

    def test_get_url_accepts_uuid(self):
        self.assertEqual(make_app().get_url("item", id=U), f"/item/{U}")

    def test_other_filters_unchanged(self):
        app = bottle.Bottle()

        @app.route("/n/<n:int>")
        def n(n):
            return str(n + 1)

        self.assertEqual(call(app, "/n/41")[2], b"42")
