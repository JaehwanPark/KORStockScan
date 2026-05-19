"""Lightweight offline bundle exporter for same-day live canary judgments.

The exporter intentionally performs only file copy and pipeline JSONL cutoff
filtering. Heavy report builders must stay out of intraday export paths.
"""

from __future__ import annotations

import argparse
import gzip
import json
import shutil
from datetime import datetime, time
from pathlib import Path
from typing import Iterable

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto


DEFAULT_OUTPUT_ROOT = Path("tmp/offline_live_canary_exports")
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"
SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
GATEKEEPER_DIR = DATA_DIR / "gatekeeper"


def _parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M:%S").time()


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _bundle_rel(src: Path) -> Path:
    return Path("data") / src.relative_to(DATA_DIR)


def _copy_file(
    src: Path,
    dest_root: Path,
    copied: list[dict[str, object]],
    *,
    compress_jsonl: bool = False,
) -> None:
    rel = _bundle_rel(src)
    if compress_jsonl and src.suffix == ".jsonl":
        rel = rel.with_suffix(rel.suffix + ".gz")
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if compress_jsonl and src.suffix == ".jsonl":
        with src.open("rb") as src_handle, gzip.open(dest, "wb", compresslevel=6) as dst_handle:
            shutil.copyfileobj(src_handle, dst_handle)
    else:
        shutil.copy2(src, dest)
    copied.append(
        {
            "source": _relative(src),
            "bundle_path": str(rel),
            "bytes": dest.stat().st_size,
            "compressed": bool(compress_jsonl and src.suffix == ".jsonl"),
        }
    )


def _copy_optional_file(
    src: Path,
    dest_root: Path,
    copied: list[dict[str, object]],
    missing: list[str],
    *,
    compress_jsonl: bool = False,
) -> None:
    if src.exists():
        _copy_file(src, dest_root, copied, compress_jsonl=compress_jsonl)
    else:
        missing.append(_relative(src))


def _copy_glob(
    base_dir: Path,
    pattern: str,
    dest_root: Path,
    copied: list[dict[str, object]],
    missing: list[str],
    *,
    compress_jsonl: bool = False,
) -> None:
    matches = sorted(base_dir.glob(pattern)) if base_dir.exists() else []
    if not matches:
        missing.append(_relative(base_dir / pattern))
        return
    for src in matches:
        if src.is_file():
            _copy_file(src, dest_root, copied, compress_jsonl=compress_jsonl)


def _filter_pipeline_events(
    source_path: Path,
    output_path: Path,
    *,
    target_date: str,
    evidence_cutoff: str,
) -> dict[str, object]:
    cutoff_time = _parse_time(evidence_cutoff)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    kept_rows = 0
    malformed_rows = 0
    source_path = existing_or_gzip_path(source_path)
    with open_text_auto(source_path) as src, gzip.open(output_path, "wt", encoding="utf-8") as dst:
        for line in src:
            total_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed_rows += 1
                continue
            emitted_date = str(row.get("emitted_date") or "")[:10]
            emitted_at = _parse_dt(row.get("emitted_at"))
            if emitted_date and emitted_date != target_date:
                continue
            if emitted_at is None:
                malformed_rows += 1
                continue
            if emitted_at.time() > cutoff_time:
                continue
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            kept_rows += 1
    return {
        "source": _relative(source_path),
        "bundle_path": str(Path("data") / source_path.relative_to(DATA_DIR)),
        "compressed_bundle_path": str(Path("data") / source_path.relative_to(DATA_DIR)) + ".gz",
        "total_rows": total_rows,
        "kept_rows": kept_rows,
        "malformed_rows": malformed_rows,
        "evidence_cutoff": evidence_cutoff,
        "compressed": True,
    }


def export_bundle(
    *,
    target_date: str,
    slot_label: str,
    evidence_cutoff: str,
    output_root: Path | None = None,
) -> Path:
    root = (output_root or DEFAULT_OUTPUT_ROOT) / target_date / slot_label
    root.mkdir(parents=True, exist_ok=True)

    copied_files: list[dict[str, object]] = []
    missing_files: list[str] = []
    filtered_files: list[dict[str, object]] = []

    source_pipeline_plain = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    source_pipeline = existing_or_gzip_path(source_pipeline_plain)
    bundle_pipeline = root / _bundle_rel(source_pipeline_plain)
    bundle_pipeline = bundle_pipeline.with_suffix(bundle_pipeline.suffix + ".gz")
    if source_pipeline.exists():
        filtered_files.append(
            _filter_pipeline_events(
                source_pipeline,
                bundle_pipeline,
                target_date=target_date,
                evidence_cutoff=evidence_cutoff,
            )
        )
    else:
        missing_files.append(_relative(source_pipeline))

    _copy_glob(
        POST_SELL_DIR,
        "post_sell_candidates_*.jsonl",
        root,
        copied_files,
        missing_files,
        compress_jsonl=True,
    )
    _copy_glob(
        POST_SELL_DIR,
        "post_sell_evaluations_*.jsonl",
        root,
        copied_files,
        missing_files,
        compress_jsonl=True,
    )

    for stem in ("performance_tuning", "trade_review"):
        src = SNAPSHOT_DIR / f"{stem}_{target_date}.json"
        gz_src = SNAPSHOT_DIR / f"{stem}_{target_date}.json.gz"
        if src.exists():
            _copy_file(src, root, copied_files)
        elif gz_src.exists():
            _copy_file(gz_src, root, copied_files)
        else:
            missing_files.append(_relative(src))

    _copy_glob(SNAPSHOT_DIR, "holding_exit_observation_*.json", root, copied_files, missing_files)
    _copy_glob(SNAPSHOT_DIR, "holding_exit_observation_*.json.gz", root, copied_files, missing_files)
    _copy_glob(SNAPSHOT_DIR / "manifests", f"*{target_date}*.json", root, copied_files, missing_files)

    _copy_optional_file(
        GATEKEEPER_DIR / f"gatekeeper_snapshots_{target_date}.jsonl",
        root,
        copied_files,
        missing_files,
        compress_jsonl=True,
    )
    _copy_optional_file(DATA_DIR / "analytics" / "shadow_diff_summary.json", root, copied_files, missing_files)

    manifest = {
        "schema_version": 1,
        "bundle_type": "offline_live_canary_bundle",
        "target_date": target_date,
        "slot_label": slot_label,
        "evidence_cutoff": evidence_cutoff,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "bundle_root": str(root),
        "filtered_files": filtered_files,
        "copied_files": copied_files,
        "missing_files": missing_files,
        "diagnostic_sections": [
            "entry_quote_fresh_composite",
            "soft_stop_micro_grace",
            "legacy_gatekeeper_fast_reuse",
            "entry_latency_offline",
        ],
        "runtime_policy": "standby_diagnostic_report_only",
        "local_command_template": (
            "analysis\\offline_live_canary_bundle\\run_local_canary_bundle_analysis.bat "
            f"--bundle-dir \"<download_root>\\offline_live_canary_exports\\{target_date}\\{slot_label}\" "
            "--since HH:MM:SS --until HH:MM:SS "
            f"--label {slot_label}"
        ),
    }
    manifest_path = root / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return root


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline live canary bundle utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export", help="Export a lightweight server bundle")
    export.add_argument("--target-date", required=True, help="YYYY-MM-DD")
    export.add_argument("--slot-label", required=True, help="Label such as h1000")
    export.add_argument("--evidence-cutoff", required=True, help="HH:MM:SS")
    export.add_argument("--output-root", type=Path, default=None)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "export":
        root = export_bundle(
            target_date=args.target_date,
            slot_label=args.slot_label,
            evidence_cutoff=args.evidence_cutoff,
            output_root=args.output_root,
        )
        print(f"exported offline live canary bundle: {root}")
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
