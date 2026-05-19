from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TextIO


def existing_or_gzip_path(path: Path) -> Path:
    """Return path if present, otherwise the sibling .gz path when present."""
    if path.exists():
        return path
    gz_path = path.with_name(path.name + ".gz")
    return gz_path if gz_path.exists() else path


def open_text_auto(path: Path, *, errors: str = "replace") -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors=errors)
    return path.open("r", encoding="utf-8", errors=errors)


def iter_jsonl(path: Path, *, errors: str = "replace") -> Iterator[dict[str, Any]]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    with open_text_auto(actual_path, errors=errors) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def read_jsonl(path: Path, *, errors: str = "replace") -> list[dict[str, Any]]:
    return list(iter_jsonl(path, errors=errors))
