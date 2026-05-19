from __future__ import annotations

import gzip
import json

from src.utils.jsonl_io import existing_or_gzip_path, read_jsonl


def test_read_jsonl_falls_back_to_gzip_sibling(tmp_path):
    plain_path = tmp_path / "events.jsonl"
    gzip_path = tmp_path / "events.jsonl.gz"
    rows = [{"event_type": "pipeline_event", "stage": "sample"}]

    with gzip.open(gzip_path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    assert existing_or_gzip_path(plain_path) == gzip_path
    assert read_jsonl(plain_path) == rows
