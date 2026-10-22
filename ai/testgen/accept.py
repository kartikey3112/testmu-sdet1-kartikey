"""Promotes a reviewed raw response to generated/<module>.json and records where it came from.

The accepted file holds the model's JSON exactly as returned, only re-indented for reading.
generated/accepted.json records, per module, which raw run and prompt version were accepted,
so anyone can trace an accepted case back to the prompt that produced it.
"""

import json
from pathlib import Path
from typing import Any

from ai.testgen.runner import ROOT

GENERATED_DIR = ROOT / "generated"
MANIFEST = GENERATED_DIR / "accepted.json"


def accept(raw_path: Path, note: str = "") -> Path:
    record = json.loads(raw_path.read_text(encoding="utf-8"))
    meta = record["metadata"]
    data = json.loads(record["content"])  # raises if the response was not JSON

    out = GENERATED_DIR / f"{meta['module']}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                   newline="\n")

    manifest: dict[str, Any] = (
        json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    )
    manifest[meta["module"]] = {
        "prompt_version": meta["prompt_version"],
        "prompt_file": meta["prompt_file"],
        "prompt_sha256": meta["prompt_sha256"],
        "raw_response": raw_path.resolve().relative_to(ROOT).as_posix(),
        "model": meta["model_reported"],
        "timestamp_utc": meta["timestamp_utc"],
        "case_count": len(data.get("cases", [])),
        "note": note,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
                        newline="\n")
    return out
