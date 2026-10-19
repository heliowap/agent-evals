"""Helpers shared by the hidden tests. Copied next to them at grading time."""
import io
import wsgiref.headers
import wsgiref.util


def call(app, path, headers=None, method="GET"):
    """Run one request through a WSGI app; return (status, headers, body).
    headers is case-insensitive, as HTTP header names are."""
    environ = {"PATH_INFO": path, "REQUEST_METHOD": method, "wsgi.input": io.BytesIO(),
               "wsgi.errors": io.StringIO()}
    for name, value in (headers or {}).items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value
    wsgiref.util.setup_testing_defaults(environ)
    result = {}

    def start_response(status, headerlist, exc_info=None):
        result["status"] = status
        result["headers"] = wsgiref.headers.Headers(list(headerlist))

    body = b"".join(app(environ, start_response))
    return int(result["status"].split()[0]), result["headers"], body
