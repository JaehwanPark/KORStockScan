"""Publish and consume a behavior-equivalent first quantity policy.

The completed-trade candidate is research evidence.  This separate immutable
artifact grants only the already active five-stage quantity and parent order
shape.  Changed shapes or timeouts need a later execution contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES

SCHEMA = "initial_entry_quantity_runtime_baseline_v1"
ENV_FILE = "KORSTOCKSCAN_INITIAL_QUANTITY_POLICY_FILE"
ENV_SHA = "KORSTOCKSCAN_INITIAL_QUANTITY_POLICY_SHA256"
CURRENT_SCHEMA = "initial_entry_quantity_current_v1"
_BASELINE_KEYS = frozenset({
    "schema_version", "policy_owner", "generation_kind", "source_date",
    "effective_from", "candidate_policy_content_sha256",
    "candidate_policy_file_sha256", "candidate_stage_receipt_content_sha256",
    "report_content_sha256", "following_bar_source_content_sha256",
    "input_manifest_sha256", "all_completed_initial_trades",
    "quantity_type_classifier_version", "type_policies",
    "runtime_apply_allowed", "action_authority", "price_authority",
    "scale_in_authority", "quantity_cap_relaxation",
    "order_shape_change_allowed", "timeout_change_allowed",
    "policy_version", "policy_content_sha256",
})


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":")).encode()).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _activation_body(stage: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    types = candidate["type_policies"]
    if (not isinstance(candidate.get("following_bar_source_content_sha256"), str)
            or "following_bar_source_path" not in stage):
        raise ValueError("initial_winner_following_source_required")
    if (set(types) != set(QUANTITY_TYPES)
            or any(row.get("ratio_mode") != "parent_5stage"
                   or row.get("selected_shape") != "parent"
                   or row.get("timeout_mode") != "existing_runtime_profile"
                   or row.get("selected_total_wait_sec") is not None
                   for row in types.values())):
        raise ValueError("changed_order_or_quantity_requires_live_execution_contract")
    return {
        "schema_version": SCHEMA,
        "policy_owner": "entry_execution_sizing_owner",
        "generation_kind": "initial_completed_trade_seed",
        "source_date": candidate["source_date"],
        "effective_from": candidate["effective_from"],
        "candidate_policy_content_sha256": candidate["policy_content_sha256"],
        "candidate_policy_file_sha256": stage["candidate_policy_file_sha256"],
        "candidate_stage_receipt_content_sha256": stage["receipt_content_sha256"],
        "report_content_sha256": candidate["report_content_sha256"],
        "following_bar_source_content_sha256": candidate.get(
            "following_bar_source_content_sha256"),
        "input_manifest_sha256": candidate["input_manifest_sha256"],
        "all_completed_initial_trades": candidate["all_completed_initial_trades"],
        "quantity_type_classifier_version": candidate["classifier_version"],
        "type_policies": {
            name: {"ratio_mode": "parent_5stage", "selected_shape": "parent",
                   "timeout_mode": "existing_runtime_profile"}
            for name in sorted(types)
        },
        "runtime_apply_allowed": True,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_cap_relaxation": False,
        "order_shape_change_allowed": False,
        "timeout_change_allowed": False,
    }


def build_initial_quantity_baseline(stage: dict[str, Any]) -> dict[str, Any]:
    """Create a deployable first baseline without a successor uplift hurdle."""
    from src.engine.scalping.initial_quantity_policy import (
        initial_quantity_stage_terminal_valid,
    )
    if not initial_quantity_stage_terminal_valid(stage):
        raise ValueError("initial_quantity_stage_invalid")
    candidate = json.loads(Path(stage["candidate_policy_path"]).read_text())
    body = _activation_body(stage, candidate)
    policy_version = "initial-quantity-baseline-" + body[
        "candidate_policy_content_sha256"][:12]
    core = {**body, "policy_version": policy_version}
    return {**core, "policy_content_sha256": _digest(core)}


def baseline_policy_valid(policy: Any) -> bool:
    """Validate the narrow runtime contract without scanning research on BUY."""
    if not isinstance(policy, dict):
        return False
    try:
        core = {key: value for key, value in policy.items()
                if key != "policy_content_sha256"}
        source = date.fromisoformat(policy["source_date"])
        effective = date.fromisoformat(policy["effective_from"])
        types = policy["type_policies"]
        return bool(
            set(policy) == _BASELINE_KEYS
            and isinstance(types, dict)
            and policy.get("schema_version") == SCHEMA
            and policy.get("generation_kind") == "initial_completed_trade_seed"
            and policy.get("policy_owner") == "entry_execution_sizing_owner"
            and effective > source
            and source >= date(2026, 6, 5)
            and type(policy.get("all_completed_initial_trades")) is int
            and policy["all_completed_initial_trades"] > 0
            and all(isinstance(policy.get(key), str)
                    and len(policy[key]) == 64
                    and all(char in "0123456789abcdef" for char in policy[key])
                    for key in ("candidate_policy_content_sha256",
                                "candidate_policy_file_sha256",
                                "candidate_stage_receipt_content_sha256",
                                "report_content_sha256", "input_manifest_sha256",
                                "following_bar_source_content_sha256"))
            and policy.get("policy_version") == (
                "initial-quantity-baseline-"
                + policy["candidate_policy_content_sha256"][:12])
            and policy.get("policy_content_sha256") == _digest(core)
            and set(types) == set(QUANTITY_TYPES)
            and all(isinstance(row, dict) and row == {
                "ratio_mode": "parent_5stage", "selected_shape": "parent",
                "timeout_mode": "existing_runtime_profile"}
                for row in types.values())
            and policy.get("quantity_type_classifier_version")
            == "initial_quantity_type_v1"
            and policy.get("runtime_apply_allowed") is True
            and all(policy.get(key) is False for key in (
                "action_authority", "price_authority", "scale_in_authority",
                "quantity_cap_relaxation", "order_shape_change_allowed",
                "timeout_change_allowed"))
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def load_pinned_baseline(path: Path, expected_sha256: str,
                         runtime_date: date) -> tuple[dict[str, Any] | None, str]:
    try:
        raw = path.read_bytes()
        policy = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        return None, "initial_policy_unreadable"
    if (hashlib.sha256(raw).hexdigest() != expected_sha256
            or not baseline_policy_valid(policy)):
        return None, "initial_policy_invalid"
    if date.fromisoformat(policy["effective_from"]) > runtime_date:
        return None, "initial_policy_not_yet_effective"
    return policy, "initial_policy_loaded"


def publish_initial_quantity_baseline(stage_path: Path, output_dir: Path) -> Path:
    stage = json.loads(stage_path.read_text())
    policy = build_initial_quantity_baseline(stage)
    path = output_dir / f"{policy['policy_version']}.json"
    encoded = (json.dumps(policy, ensure_ascii=False, indent=2) + "\n").encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix=f".{path.name}.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise ValueError("immutable_initial_policy_conflict")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if _file_sha256(path) != hashlib.sha256(encoded).hexdigest():
        raise ValueError("initial_policy_publish_hash_mismatch")
    return path


def select_initial_quantity_baseline(stage_path: Path, output_dir: Path) -> dict[str, Any]:
    """Set the first current policy once; a different parent needs explicit CAS."""
    policy_path = publish_initial_quantity_baseline(stage_path, output_dir)
    policy = json.loads(policy_path.read_text())
    stage = json.loads(stage_path.read_text())
    body = {
        "schema_version": CURRENT_SCHEMA,
        "source_date": policy["source_date"],
        "effective_from": policy["effective_from"],
        "policy_file": str(policy_path.resolve()),
        "policy_file_sha256": _file_sha256(policy_path),
        "policy_content_sha256": policy["policy_content_sha256"],
        "stage_file": str(stage_path.resolve()),
        "stage_file_sha256": _file_sha256(stage_path),
        "stage_receipt_content_sha256": stage["receipt_content_sha256"],
        "parent_current_sha256": None,
    }
    current = {**body, "current_content_sha256": _digest(body)}
    current_path = output_dir / "current.json"
    encoded = (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode()
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix=".current.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, current_path)
        except FileExistsError:
            if current_path.read_bytes() != encoded:
                raise ValueError("initial_policy_current_already_selected")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return current


def selected_initial_quantity_env(current_path: Path, target_date: str) -> dict[str, str]:
    """Revalidate current, stage, and immutable policy for PREOPEN handoff."""
    from src.engine.scalping.initial_quantity_policy import (
        initial_quantity_stage_terminal_valid,
    )
    target = date.fromisoformat(target_date)
    current = json.loads(current_path.read_text())
    body = {key: value for key, value in current.items()
            if key != "current_content_sha256"}
    if (current.get("schema_version") != CURRENT_SCHEMA
            or current.get("current_content_sha256") != _digest(body)
            or current.get("parent_current_sha256") is not None):
        raise ValueError("initial_policy_current_invalid")
    stage_path = Path(current["stage_file"])
    policy_path = Path(current["policy_file"])
    if (not stage_path.is_absolute() or not policy_path.is_absolute()
            or _file_sha256(stage_path) != current["stage_file_sha256"]
            or _file_sha256(policy_path) != current["policy_file_sha256"]):
        raise ValueError("initial_policy_current_file_hash_invalid")
    stage = json.loads(stage_path.read_text())
    if (not initial_quantity_stage_terminal_valid(stage)
            or stage["receipt_content_sha256"] != current["stage_receipt_content_sha256"]):
        raise ValueError("initial_policy_current_stage_invalid")
    expected = build_initial_quantity_baseline(stage)
    policy, status = load_pinned_baseline(
        policy_path, current["policy_file_sha256"], target)
    if (status != "initial_policy_loaded" or policy != expected
            or policy["policy_content_sha256"] != current["policy_content_sha256"]
            or policy["source_date"] != current["source_date"]
            or policy["effective_from"] != current["effective_from"]):
        raise ValueError("initial_policy_current_binding_invalid")
    return {ENV_FILE: str(policy_path), ENV_SHA: current["policy_file_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--select-current", action="store_true")
    args = parser.parse_args(argv)
    path = publish_initial_quantity_baseline(args.stage, args.output_dir)
    if args.select_current:
        select_initial_quantity_baseline(args.stage, args.output_dir)
    print(json.dumps({"policy_file": str(path.resolve()),
                      "policy_file_sha256": _file_sha256(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
