"""Publish and consume immutable initial-entry quantity policies."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES

SCHEMA = "initial_entry_quantity_runtime_baseline_v1"
RUNTIME_V2_SCHEMA = "initial_entry_quantity_runtime_v2"
RUNTIME_REFRESH_SCHEMA = "initial_entry_quantity_runtime_refresh_v1"
ENV_FILE = "KORSTOCKSCAN_INITIAL_QUANTITY_POLICY_FILE"
ENV_SHA = "KORSTOCKSCAN_INITIAL_QUANTITY_POLICY_SHA256"
CURRENT_SCHEMA = "initial_entry_quantity_current_v1"
CURRENT_V2_SCHEMA = "initial_entry_quantity_current_v2"
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
_RUNTIME_V2_KEYS = frozenset({
    "schema_version", "policy_owner", "generation_kind", "source_date",
    "effective_from", "parent_policy_content_sha256",
    "parent_current_content_sha256", "candidate_policy_content_sha256",
    "candidate_policy_file_sha256", "candidate_stage_receipt_content_sha256",
    "report_content_sha256", "following_bar_source_content_sha256",
    "input_manifest_sha256", "all_completed_initial_trades",
    "quantity_type_classifier_version", "p1_price_policy_sha256",
    "type_policies", "runtime_apply_allowed", "action_authority",
    "price_authority", "scale_in_authority", "quantity_cap_relaxation",
    "policy_version", "policy_content_sha256",
})
_RUNTIME_REFRESH_KEYS = _RUNTIME_V2_KEYS | {
    "evaluation_content_sha256", "timeout_research_content_sha256",
}


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
                   or row.get("timeout_mode") != "existing_runtime_profile"
                   or row.get("selected_total_wait_sec") is not None
                   for row in types.values())):
        raise ValueError("initial_candidate_ratio_or_timeout_invalid")
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


def build_initial_quantity_runtime_v2(
    stage: dict[str, Any], parent_policy: dict[str, Any],
    parent_current_content_sha256: str,
) -> dict[str, Any]:
    """Bind one initial candidate to the selected first-policy lineage.

    This builder does not select current or grant broker authority. The order
    dispatcher and current CAS are separate gates.
    """
    from src.engine.scalping.entry_execution_sizing_plan import (
        ENTRY_PRICE_POLICY_SHA256,
    )
    from src.engine.scalping.initial_quantity_policy import (
        initial_quantity_stage_terminal_valid,
    )

    if (not initial_quantity_stage_terminal_valid(stage)
            or not baseline_policy_valid(parent_policy)
            or not isinstance(parent_current_content_sha256, str)
            or len(parent_current_content_sha256) != 64):
        raise ValueError("initial_runtime_v2_source_invalid")
    candidate = json.loads(Path(stage["candidate_policy_path"]).read_text())
    if (candidate["source_date"] != parent_policy["source_date"]
            or candidate["effective_from"] != parent_policy["effective_from"]
            or candidate["policy_content_sha256"] !=
            parent_policy["candidate_policy_content_sha256"]):
        raise ValueError("initial_runtime_v2_parent_candidate_mismatch")
    rows = candidate["type_policies"]
    types = {
        name: {
            "ratio_mode": row["ratio_mode"],
            "selected_shape": row["selected_shape"],
            "timeout_mode": row["timeout_mode"],
            "selected_total_wait_sec": row["selected_total_wait_sec"],
        }
        for name, row in sorted(rows.items())
    }
    body = {
        "schema_version": RUNTIME_V2_SCHEMA,
        "policy_owner": "entry_execution_sizing_owner",
        "generation_kind": "initial_completed_trade_seed",
        "source_date": candidate["source_date"],
        "effective_from": candidate["effective_from"],
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "parent_current_content_sha256": parent_current_content_sha256,
        "candidate_policy_content_sha256": candidate["policy_content_sha256"],
        "candidate_policy_file_sha256": stage["candidate_policy_file_sha256"],
        "candidate_stage_receipt_content_sha256": stage["receipt_content_sha256"],
        "report_content_sha256": candidate["report_content_sha256"],
        "following_bar_source_content_sha256": candidate[
            "following_bar_source_content_sha256"],
        "input_manifest_sha256": candidate["input_manifest_sha256"],
        "all_completed_initial_trades": candidate["all_completed_initial_trades"],
        "quantity_type_classifier_version": candidate["classifier_version"],
        "p1_price_policy_sha256": ENTRY_PRICE_POLICY_SHA256,
        "type_policies": types,
        "runtime_apply_allowed": True,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_cap_relaxation": False,
    }
    core = {**body, "policy_version": (
        "initial-quantity-runtime-v2-" + _digest(body)[:12])}
    policy = {**core, "policy_content_sha256": _digest(core)}
    if not runtime_v2_policy_valid(policy):
        raise ValueError("initial_runtime_v2_invalid")
    return policy


def runtime_v2_policy_valid(policy: Any) -> bool:
    if not isinstance(policy, dict):
        return False
    try:
        from src.engine.scalping.entry_execution_sizing_plan import (
            ENTRY_PRICE_POLICY_SHA256,
        )
        from src.engine.scalping.initial_quantity_policy import _SHAPES

        core = {key: value for key, value in policy.items()
                if key != "policy_content_sha256"}
        body = {key: value for key, value in core.items()
                if key != "policy_version"}
        source = date.fromisoformat(policy["source_date"])
        effective = date.fromisoformat(policy["effective_from"])
        types = policy["type_policies"]
        return bool(
            set(policy) == _RUNTIME_V2_KEYS
            and policy["schema_version"] == RUNTIME_V2_SCHEMA
            and policy["policy_owner"] == "entry_execution_sizing_owner"
            and policy["generation_kind"] == "initial_completed_trade_seed"
            and source >= date(2026, 6, 5) and effective > source
            and type(policy["all_completed_initial_trades"]) is int
            and policy["all_completed_initial_trades"] > 0
            and all(isinstance(policy[key], str)
                    and len(policy[key]) == 64
                    and all(char in "0123456789abcdef" for char in policy[key])
                    for key in (
                        "parent_policy_content_sha256",
                        "parent_current_content_sha256",
                        "candidate_policy_content_sha256",
                        "candidate_policy_file_sha256",
                        "candidate_stage_receipt_content_sha256",
                        "report_content_sha256",
                        "following_bar_source_content_sha256",
                        "input_manifest_sha256",
                    ))
            and policy["p1_price_policy_sha256"] == ENTRY_PRICE_POLICY_SHA256
            and policy["quantity_type_classifier_version"] ==
            "initial_quantity_type_v1"
            and isinstance(types, dict) and set(types) == set(QUANTITY_TYPES)
            and all(isinstance(row, dict) and set(row) == {
                "ratio_mode", "selected_shape", "timeout_mode",
                "selected_total_wait_sec",
            } and row["ratio_mode"] in {
                "parent_5stage", "cap_10pct", "cap_15pct", "cap_20pct"}
                    and (name != "SAFE_UNKNOWN"
                         or row["ratio_mode"] == "parent_5stage")
                    and row["selected_shape"] in _SHAPES
                    and (name != "SAFE_UNKNOWN"
                         or row["selected_shape"] == "parent")
                    and row["timeout_mode"] == "existing_runtime_profile"
                    and row["selected_total_wait_sec"] is None
                    for name, row in types.items())
            and policy["runtime_apply_allowed"] is True
            and all(policy[key] is False for key in (
                "action_authority", "price_authority", "scale_in_authority",
                "quantity_cap_relaxation"))
            and policy["policy_version"] == (
                "initial-quantity-runtime-v2-" + _digest(body)[:12])
            and policy["policy_content_sha256"] == _digest(core)
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def build_initial_quantity_refresh_runtime_policy(
    stage: dict[str, Any], parent_policy: dict[str, Any],
    parent_current_content_sha256: str,
) -> dict[str, Any]:
    """Turn a terminal eligible refresh into a parent-bound runtime artifact."""
    from src.engine.scalping.entry_execution_sizing_plan import (
        ENTRY_PRICE_POLICY_SHA256,
    )
    from src.engine.scalping.initial_quantity_policy import (
        refresh_quantity_stage_terminal_valid,
    )

    if (not refresh_quantity_stage_terminal_valid(stage)
            or stage.get("decision") != "eligible_source_only"
            or not refresh_parent_policy_valid(parent_policy)
            or stage.get("parent_policy_content_sha256") !=
            parent_policy["policy_content_sha256"]
            or not isinstance(parent_current_content_sha256, str)
            or len(parent_current_content_sha256) != 64
            or date.fromisoformat(stage["source_date"]) <
            date.fromisoformat(parent_policy["effective_from"])):
        raise ValueError("initial_refresh_runtime_source_invalid")
    candidate = json.loads(Path(stage["candidate_path"]).read_text())
    report = json.loads(Path(stage["report_path"]).read_text())
    if (stage.get("following_bar_source_status") not in {
            "source_bound", "no_winners"}
            or candidate.get("parent_policy_content_sha256") !=
            parent_policy["policy_content_sha256"]
            or candidate.get("source_date") != stage["source_date"]
            or (report.get("census") or {}).get("input_manifest_sha256") is None):
        raise ValueError("initial_refresh_runtime_candidate_invalid")
    types = {
        name: {
            "ratio_mode": row["ratio_mode"],
            "selected_shape": row["selected_shape"],
            "timeout_mode": row["timeout_mode"],
            "selected_total_wait_sec": row["selected_total_wait_sec"],
        }
        for name, row in sorted(candidate["type_policies"].items())
    }
    body = {
        "schema_version": RUNTIME_REFRESH_SCHEMA,
        "policy_owner": "entry_execution_sizing_owner",
        "generation_kind": "refresh",
        "source_date": candidate["source_date"],
        "effective_from": candidate["effective_from"],
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "parent_current_content_sha256": parent_current_content_sha256,
        "candidate_policy_content_sha256": candidate["policy_content_sha256"],
        "candidate_policy_file_sha256": stage["candidate_file_sha256"],
        "candidate_stage_receipt_content_sha256": stage["receipt_content_sha256"],
        "report_content_sha256": stage["report_content_sha256"],
        "evaluation_content_sha256": stage["evaluation_content_sha256"],
        "timeout_research_content_sha256":
            stage["timeout_research_content_sha256"],
        "following_bar_source_content_sha256":
            stage.get("following_bar_source_content_sha256"),
        "input_manifest_sha256": report["census"]["input_manifest_sha256"],
        "all_completed_initial_trades": stage["all_completed_initial_trades"],
        "quantity_type_classifier_version":
            parent_policy["quantity_type_classifier_version"],
        "p1_price_policy_sha256": ENTRY_PRICE_POLICY_SHA256,
        "type_policies": types,
        "runtime_apply_allowed": True,
        "action_authority": False,
        "price_authority": False,
        "scale_in_authority": False,
        "quantity_cap_relaxation": False,
    }
    core = {**body, "policy_version": (
        "initial-quantity-refresh-" + _digest(body)[:12])}
    policy = {**core, "policy_content_sha256": _digest(core)}
    if not runtime_refresh_policy_valid(policy):
        raise ValueError("initial_refresh_runtime_invalid")
    return policy


def runtime_refresh_policy_valid(policy: Any) -> bool:
    if not isinstance(policy, dict):
        return False
    try:
        from src.engine.scalping.entry_execution_sizing_plan import (
            ENTRY_PRICE_POLICY_SHA256,
        )
        from src.engine.scalping.initial_quantity_policy import _SHAPES

        core = {key: value for key, value in policy.items()
                if key != "policy_content_sha256"}
        body = {key: value for key, value in core.items()
                if key != "policy_version"}
        types = policy["type_policies"]
        return bool(
            set(policy) == _RUNTIME_REFRESH_KEYS
            and policy["schema_version"] == RUNTIME_REFRESH_SCHEMA
            and policy["generation_kind"] == "refresh"
            and policy["policy_owner"] == "entry_execution_sizing_owner"
            and date.fromisoformat(policy["source_date"]) >= date(2026, 6, 5)
            and date.fromisoformat(policy["effective_from"]) >
                date.fromisoformat(policy["source_date"])
            and type(policy["all_completed_initial_trades"]) is int
            and policy["all_completed_initial_trades"] > 0
            and all(isinstance(policy[key], str)
                    and len(policy[key]) == 64
                    and all(char in "0123456789abcdef" for char in policy[key])
                    for key in (
                        "parent_policy_content_sha256",
                        "parent_current_content_sha256",
                        "candidate_policy_content_sha256",
                        "candidate_policy_file_sha256",
                        "candidate_stage_receipt_content_sha256",
                        "report_content_sha256",
                        "evaluation_content_sha256",
                        "timeout_research_content_sha256",
                        "input_manifest_sha256"))
            and (policy["following_bar_source_content_sha256"] is None
                 or (isinstance(policy["following_bar_source_content_sha256"], str)
                     and len(policy["following_bar_source_content_sha256"]) == 64
                     and all(char in "0123456789abcdef" for char in
                             policy["following_bar_source_content_sha256"])))
            and policy["p1_price_policy_sha256"] == ENTRY_PRICE_POLICY_SHA256
            and policy["quantity_type_classifier_version"] ==
                "initial_quantity_type_v1"
            and isinstance(types, dict) and set(types) == set(QUANTITY_TYPES)
            and all(isinstance(row, dict) and set(row) == {
                "ratio_mode", "selected_shape", "timeout_mode",
                "selected_total_wait_sec",
            } and row["ratio_mode"] in {
                "parent_5stage", "cap_10pct", "cap_15pct", "cap_20pct"}
                    and (name != "SAFE_UNKNOWN"
                         or row["ratio_mode"] == "parent_5stage")
                    and row["selected_shape"] in _SHAPES
                    and (name != "SAFE_UNKNOWN"
                         or row["selected_shape"] == "parent")
                    and ((row["timeout_mode"] == "existing_runtime_profile"
                          and row["selected_total_wait_sec"] is None)
                         or (row["timeout_mode"] == "selected_total_wait_sec"
                             and row["selected_shape"] != "parent"
                             and type(row["selected_total_wait_sec"]) is int
                             and (row["selected_total_wait_sec"] >=
                                  6 * (3 if row["selected_shape"].startswith(
                                      "three_leg") else 2))
                             and row["selected_total_wait_sec"] <= 1200))
                    for name, row in types.items())
            and policy["runtime_apply_allowed"] is True
            and all(policy[key] is False for key in (
                "action_authority", "price_authority", "scale_in_authority",
                "quantity_cap_relaxation"))
            and policy["policy_version"] == (
                "initial-quantity-refresh-" + _digest(body)[:12])
            and policy["policy_content_sha256"] == _digest(core)
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return False


def refresh_parent_policy_valid(policy: Any) -> bool:
    """Accept the exact selected v1/v2 generation as refresh parent."""
    return (baseline_policy_valid(policy) or runtime_v2_policy_valid(policy)
            or runtime_refresh_policy_valid(policy))


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


def load_pinned_initial_quantity_policy(
    path: Path, expected_sha256: str, runtime_date: date,
) -> tuple[dict[str, Any] | None, str]:
    """Consume an immutable first or successor policy after its lower bound."""
    try:
        raw = Path(path).read_bytes()
        policy = json.loads(raw)
    except (OSError, ValueError, UnicodeError):
        return None, "initial_policy_unreadable"
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        return None, "initial_policy_file_hash_invalid"
    if baseline_policy_valid(policy):
        status = "initial_policy_loaded"
    elif runtime_v2_policy_valid(policy):
        status = "initial_policy_v2_loaded"
    elif runtime_refresh_policy_valid(policy):
        status = "initial_policy_refresh_loaded"
    else:
        return None, "initial_policy_invalid"
    if date.fromisoformat(policy["effective_from"]) > runtime_date:
        return None, "initial_policy_not_yet_effective"
    return policy, status


def publish_initial_quantity_runtime_v2(
    stage_path: Path, parent_current_path: Path, output_dir: Path,
) -> Path:
    """Stage one immutable policy without changing the active pointer."""
    stage_path = Path(stage_path).resolve()
    parent_current_path = Path(parent_current_path).resolve()
    stage = json.loads(stage_path.read_text())
    parent_current = json.loads(parent_current_path.read_text())
    selected_initial_quantity_env(
        parent_current_path, parent_current["effective_from"])
    if parent_current.get("schema_version") not in {
            CURRENT_SCHEMA, CURRENT_V2_SCHEMA}:
        raise ValueError("initial_runtime_v2_parent_current_invalid")
    if (stage.get("schema_version") !=
            "initial_entry_quantity_refresh_stage_v1"
            and parent_current.get("schema_version") != CURRENT_SCHEMA):
        raise ValueError("initial_runtime_v2_parent_current_invalid")
    parent_policy = json.loads(Path(parent_current["policy_file"]).read_text())
    if stage.get("schema_version") == "initial_entry_quantity_refresh_stage_v1":
        policy = build_initial_quantity_refresh_runtime_policy(
            stage, parent_policy, parent_current["current_content_sha256"])
    else:
        policy = build_initial_quantity_runtime_v2(
            stage, parent_policy, parent_current["current_content_sha256"])
    output_dir = Path(output_dir)
    path = output_dir / f"{policy['policy_version']}.json"
    encoded = (json.dumps(policy, ensure_ascii=False, indent=2) + "\n").encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix=".policy-v2.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise ValueError("immutable_initial_runtime_v2_conflict")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if _file_sha256(path) != hashlib.sha256(encoded).hexdigest():
        raise ValueError("initial_runtime_v2_publish_hash_mismatch")
    return path


def _replace_current_bytes(path: Path, encoded: bytes) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".current-v2.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _archive_parent_current(path: Path, encoded: bytes) -> None:
    """Keep exact pre-CAS pointer bytes for later PREOPEN lineage checks."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".parent-current.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise ValueError("initial_runtime_v2_parent_archive_conflict")
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def select_initial_quantity_runtime_v2(
    stage_path: Path, current_path: Path,
) -> dict[str, Any]:
    """CAS a reviewed v2 policy over exactly its selected first parent."""
    stage_path = Path(stage_path).resolve()
    current_path = Path(current_path).resolve()
    policy_path = publish_initial_quantity_runtime_v2(
        stage_path, current_path, current_path.parent)
    policy = json.loads(policy_path.read_text())
    stage = json.loads(stage_path.read_text())
    with current_path.with_suffix(".lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        old_bytes = current_path.read_bytes()
        parent = json.loads(old_bytes)
        if (parent.get("schema_version") not in {
                CURRENT_SCHEMA, CURRENT_V2_SCHEMA}
                or parent.get("current_content_sha256") !=
                policy["parent_current_content_sha256"]):
            raise ValueError("initial_runtime_v2_parent_cas_conflict")
        selected_initial_quantity_env(current_path, policy["effective_from"])
        parent_archive_path = current_path.parent / (
            "parent-current-" + parent["current_content_sha256"][:16] + ".json")
        _archive_parent_current(parent_archive_path, old_bytes)
        body = {
            "schema_version": CURRENT_V2_SCHEMA,
            "source_date": policy["source_date"],
            "effective_from": policy["effective_from"],
            "policy_file": str(policy_path.resolve()),
            "policy_file_sha256": _file_sha256(policy_path),
            "policy_content_sha256": policy["policy_content_sha256"],
            "stage_file": str(stage_path),
            "stage_file_sha256": _file_sha256(stage_path),
            "stage_receipt_content_sha256": stage["receipt_content_sha256"],
            "parent_policy_file": parent["policy_file"],
            "parent_policy_file_sha256": parent["policy_file_sha256"],
            "parent_policy_content_sha256":
                parent["policy_content_sha256"],
            "parent_current_sha256": parent["current_content_sha256"],
            "parent_current_file": str(parent_archive_path),
            "parent_current_file_sha256": hashlib.sha256(old_bytes).hexdigest(),
        }
        current = {**body, "current_content_sha256": _digest(body)}
        encoded = (json.dumps(current, ensure_ascii=False, indent=2) + "\n").encode()
        _replace_current_bytes(current_path, encoded)
        try:
            selected_initial_quantity_env(current_path, policy["effective_from"])
        except (OSError, ValueError, KeyError, TypeError):
            _replace_current_bytes(current_path, old_bytes)
            raise
        return current


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
    if current.get("schema_version") == CURRENT_V2_SCHEMA:
        return _selected_initial_quantity_v2_env(current, target)
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


def _selected_initial_quantity_v2_env(
    current: dict[str, Any], target: date,
) -> dict[str, str]:
    from src.engine.scalping.initial_quantity_policy import (
        initial_quantity_stage_terminal_valid,
    )

    expected_keys = {
        "schema_version", "source_date", "effective_from", "policy_file",
        "policy_file_sha256", "policy_content_sha256", "stage_file",
        "stage_file_sha256", "stage_receipt_content_sha256",
        "parent_policy_file", "parent_policy_file_sha256",
        "parent_policy_content_sha256", "parent_current_sha256",
        "parent_current_file", "parent_current_file_sha256",
        "current_content_sha256",
    }
    body = {key: value for key, value in current.items()
            if key != "current_content_sha256"}
    if (set(current) != expected_keys
            or current["current_content_sha256"] != _digest(body)
            or target < date.fromisoformat(current["effective_from"])):
        raise ValueError("initial_runtime_v2_current_invalid")
    paths = {key: Path(current[key]) for key in (
        "policy_file", "stage_file", "parent_policy_file",
        "parent_current_file")}
    if (any(not path.is_absolute() for path in paths.values())
            or any(_file_sha256(paths[key]) != current[key + "_sha256"]
                   for key in paths)):
        raise ValueError("initial_runtime_v2_current_file_invalid")
    stage = json.loads(paths["stage_file"].read_text())
    parent = json.loads(paths["parent_policy_file"].read_text())
    parent_current = json.loads(paths["parent_current_file"].read_text())
    if stage.get("schema_version") == "initial_entry_quantity_refresh_stage_v1":
        from src.engine.scalping.initial_quantity_policy import (
            refresh_quantity_stage_terminal_valid,
        )

        if (not refresh_quantity_stage_terminal_valid(stage)
                or not refresh_parent_policy_valid(parent)
                or parent_current.get("schema_version") not in {
                    CURRENT_SCHEMA, CURRENT_V2_SCHEMA}
                or parent_current.get("current_content_sha256") !=
                current["parent_current_sha256"]
                or date.fromisoformat(parent_current["effective_from"]) >=
                date.fromisoformat(current["effective_from"])
                or parent_current.get("policy_file") !=
                current["parent_policy_file"]
                or parent_current.get("policy_file_sha256") !=
                current["parent_policy_file_sha256"]
                or stage["receipt_content_sha256"] !=
                current["stage_receipt_content_sha256"]
                or parent["policy_content_sha256"] !=
                current["parent_policy_content_sha256"]):
            raise ValueError("initial_refresh_runtime_source_invalid")
        parent_env = selected_initial_quantity_env(
            paths["parent_current_file"], target.isoformat())
        if (parent_env.get(ENV_FILE) != str(paths["parent_policy_file"])
                or parent_env.get(ENV_SHA) !=
                current["parent_policy_file_sha256"]):
            raise ValueError("initial_refresh_runtime_parent_binding_invalid")
        expected = build_initial_quantity_refresh_runtime_policy(
            stage, parent, current["parent_current_sha256"])
        policy, status = load_pinned_initial_quantity_policy(
            paths["policy_file"], current["policy_file_sha256"], target)
        if (status != "initial_policy_refresh_loaded" or policy != expected
                or policy["policy_content_sha256"] !=
                current["policy_content_sha256"]
                or policy["source_date"] != current["source_date"]
                or policy["effective_from"] != current["effective_from"]):
            raise ValueError("initial_refresh_runtime_current_binding_invalid")
        return {ENV_FILE: str(paths["policy_file"]),
                ENV_SHA: current["policy_file_sha256"]}
    if (not initial_quantity_stage_terminal_valid(stage)
            or not baseline_policy_valid(parent)
            or parent_current.get("schema_version") != CURRENT_SCHEMA
            or parent_current.get("current_content_sha256") !=
            current["parent_current_sha256"]
            or parent_current.get("current_content_sha256") != _digest({
                key: value for key, value in parent_current.items()
                if key != "current_content_sha256"})
            or parent_current.get("policy_file") !=
            current["parent_policy_file"]
            or parent_current.get("policy_file_sha256") !=
            current["parent_policy_file_sha256"]
            or stage["receipt_content_sha256"] !=
            current["stage_receipt_content_sha256"]
            or parent["policy_content_sha256"] !=
            current["parent_policy_content_sha256"]):
        raise ValueError("initial_runtime_v2_source_invalid")
    expected = build_initial_quantity_runtime_v2(
        stage, parent, current["parent_current_sha256"])
    policy, status = load_pinned_initial_quantity_policy(
        paths["policy_file"], current["policy_file_sha256"], target)
    if (status != "initial_policy_v2_loaded" or policy != expected
            or policy["policy_content_sha256"] != current["policy_content_sha256"]
            or policy["source_date"] != current["source_date"]
            or policy["effective_from"] != current["effective_from"]):
        raise ValueError("initial_runtime_v2_current_binding_invalid")
    return {ENV_FILE: str(paths["policy_file"]),
            ENV_SHA: current["policy_file_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--parent-current", type=Path)
    parser.add_argument("--select-current", action="store_true")
    parser.add_argument("--require-selected-release", action="store_true")
    args = parser.parse_args(argv)
    if args.parent_current is not None:
        current_path = args.parent_current.resolve()
        if args.require_selected_release:
            if not args.select_current:
                raise ValueError("initial_runtime_release_guard_requires_selection")
            selection = json.loads((current_path.parent.parent /
                                    "runtime_release_selection.json").read_text())
            release_root = Path(__file__).resolve().parents[3]
            if (selection.get("schema") != "runtime_release_selection_v1"
                    or Path(selection.get("release_root") or "").resolve()
                    != release_root):
                raise ValueError("initial_runtime_selected_release_mismatch")
        if (args.select_current
                and args.output_dir.resolve() != current_path.parent):
            raise ValueError("initial_runtime_current_output_dir_mismatch")
        path = publish_initial_quantity_runtime_v2(
            args.stage, current_path, args.output_dir)
        if args.select_current:
            select_initial_quantity_runtime_v2(args.stage, current_path)
    else:
        path = publish_initial_quantity_baseline(args.stage, args.output_dir)
        if args.select_current:
            select_initial_quantity_baseline(args.stage, args.output_dir)
    print(json.dumps({"policy_file": str(path.resolve()),
                      "policy_file_sha256": _file_sha256(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
