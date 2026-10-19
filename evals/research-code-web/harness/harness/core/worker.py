"""Trusted core worker. Input is public spec plus ephemeral credentials, never gold."""

import json
import sys

from .runner import _run_reserved


def main():
    envelope = json.load(sys.stdin)
    result = _run_reserved(envelope["spec"], envelope["credentials"], envelope["record"])
    print(json.dumps({"trial_id": result["trial_id"], "status": result["status"]}))


if __name__ == "__main__":
    main()
