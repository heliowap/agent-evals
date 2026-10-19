"""Archive verifiable session fields while omitting private reasoning text."""

import hashlib
import json

from benchmark import ROOT, atomic_new, digest, frozen_manifest, pending_cells, validate_export
from import_preflight import export_session


def sanitize_export(export):
    info = export["info"]
    messages = []
    for message in export["messages"]:
        kind = message["type"]
        fields = {"type": kind}
        if kind == "user":
            fields["text"] = message["text"]
        elif kind == "assistant":
            fields.update({key: message[key] for key in ("agent", "model", "finish")})
            fields["content"] = [{"type": part["type"], **({"text": part["text"]} if part["type"] == "text" else {})}
                                 for part in message["content"]]
        elif kind == "agent-switched":
            fields["agent"] = message["agent"]
        messages.append(fields)
    return {"info": {key: info[key] for key in ("id", "agent", "model", "outcome", "cost", "tokens")},
            "messages": messages}


def archive_valid_results(results, export_session_fn=export_session):
    records = {}
    for result in results:
        transcript = export_session_fn(result["session"])
        verified = validate_export(transcript, result["prompt"], result["model"])
        if any(result.get(key) != verified[key] for key in ("session", "answer", "used_model", "tokens", "cost_usd")):
            raise ValueError(f"result differs from exported answer: {result['cell_id']}")
        safe = sanitize_export(transcript)
        if validate_export(safe, result["prompt"], result["model"]) != verified:
            raise ValueError(f"sanitized export differs from validated result: {result['cell_id']}")
        if result["cell_id"] in records:
            raise ValueError(f"duplicate cell: {result['cell_id']}")
        records[result["cell_id"]] = {
            "source_export_sha256": digest(json.dumps(transcript, sort_keys=True, ensure_ascii=False).encode()),
            "transcript": safe}
    return records


def main():
    root = ROOT
    _, manifest = frozen_manifest(root)
    if pending_cells(manifest, root):
        raise ValueError("cannot archive partial benchmark")
    results = [json.loads(path.read_text()) for path in sorted((root / "results").glob("*.json"))]
    if len(results) != len(manifest["cells"]):
        raise ValueError("result count differs from frozen manifest")
    records = archive_valid_results(results)
    if set(records) != {cell["id"] for cell in manifest["cells"]}:
        raise ValueError("archived cells differ from manifest")
    atomic_new(root / "session-evidence.json", {
        "kind": "sanitized session export; reasoning text and CLI event stream not archived",
        "manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
        "records": records})
    print(f"Saved {len(records)} sanitized, revalidated exports")


if __name__ == "__main__":
    main()
