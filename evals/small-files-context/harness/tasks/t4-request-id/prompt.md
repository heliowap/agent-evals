Please add an opt-in request ID feature. When `app.config['request_id.header']` is set to a header name (for example `X-Request-ID`):

- `request.request_id` returns the value of that header from the incoming request, or, if the request doesn't have it, a newly generated ID made of 32 lowercase hex characters. It must return the same value every time it is read during one request.
- Every response from that app carries that header with the request ID: normal responses, 404s, 500s caused by uncaught exceptions, `abort()`, `redirect()`, and a raised `HTTPResponse`.

When `request_id.header` is not set, nothing changes: no extra header is sent.
