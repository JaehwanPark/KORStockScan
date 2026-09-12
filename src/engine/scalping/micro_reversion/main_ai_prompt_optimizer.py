"""Build a continuous, source-only Main AI prompt optimization plan.

The existing micro-reversion R0-R3 artifacts retain their historical three-arm
identity.  This producer removes micro applicability as a global prompt-search
gate by planning a base prompt comparison for every exact prepared parent and
an optional 2x2 prompt/input factorial comparison where enriched market data is
available.  It has no provider, runtime, threshold, quantity, or order authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_action_outcome_calibration as calibration_source
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CLEAN_BASELINE_DATE = date(2026, 6, 5)
SCHEMA = "main_ai_prompt_optimizer_v1"
FACTORIAL_DESIGN_VERSION = "main_ai_prompt_input_factorial_v1"
REPORT_DIR = DATA_DIR / "report" / "main_ai_prompt_optimizer"
PREPARED_DIR = DATA_DIR / "report" / "main_ai_quality_r0_r3"
BRIDGE_DIR = DATA_DIR / "report" / "micro_reversion_ai_quality_bridge"
DETAILED_DIR = DATA_DIR / "report" / "ai_prompt_detailed_paired_replay"
ENTRY_BATCH_DIR = DATA_DIR / "report" / "ai_entry_setup_paired_replay_batch"
ACTION_OUTCOME_CALIBRATION_DIR = (
    DATA_DIR / "report" / "ai_decision_action_outcome_calibration"
)
ACTION_OUTCOME_CALIBRATION_SCHEMA = "ai_decision_action_outcome_calibration_v2"
ACTION_OUTCOME_OPTIMIZER_HANDOFF_SCHEMA = "ai_action_outcome_optimizer_handoff_v1"

ENTRY_CANDIDATE_ORDER = (
    "decision_quality_v2_14_setup_risk_adjudicator",
    "decision_quality_v2_15_bounded_recovery",
    "decision_quality_v2_16_sequential_recovery",
)
ENTRY_CANDIDATE_PROMPT_SHA256 = {
    ENTRY_CANDIDATE_ORDER[0]: (
        "eeb6c079eb6cdc41f53cf073a92451778370c282fbfa9f2c10ded7c68e6b0e10"
    ),
    ENTRY_CANDIDATE_ORDER[1]: (
        "203b6bfba260393a5901079967a026d65d06c89fd8bcf56f78950db252e3d8d7"
    ),
    ENTRY_CANDIDATE_ORDER[2]: (
        "f062daa8d000aadc79085b67d5f88cf1d2340655b1a7a3eda6e61f5e24597113"
    ),
}
ENTRY_REGISTERED_BOUNDED_LIVE_PROMPT_VERSIONS = ENTRY_CANDIDATE_ORDER[:2]

# The v1 keys remain the historical replay contract.  v2 adds the route to
# the identity for the integrated KRX/NXT aftermarket; it is deliberately an
# observation-only cohort and therefore never becomes a prompt-search cell.
ENTRY_COHORT_CONTRACT_SCHEMA = "entry_replay_cohort_contract_v1"
ENTRY_COHORT_CONTRACT_V1 = "v1"
ENTRY_COHORT_CONTRACT_V2 = "v2"
ENTRY_DUAL_AFTERMARKET_SESSION = "KRX_NXT_AFTERMARKET"
ENTRY_DUAL_AFTERMARKET_VENUE = "INTEGRATED"
ENTRY_EXPECTED_COHORTS_BY_CONTRACT_VERSION = {
    ENTRY_COHORT_CONTRACT_V1: (
        ("KRX", "KRX_REGULAR", "", ENTRY_COHORT_CONTRACT_V1, "LEGACY"),
        ("NXT", "NXT_AFTERMARKET", "", ENTRY_COHORT_CONTRACT_V1, "LEGACY"),
    ),
    ENTRY_COHORT_CONTRACT_V2: (
        ("KRX", "KRX_REGULAR", "", ENTRY_COHORT_CONTRACT_V1, "LEGACY"),
        ("NXT", "NXT_AFTERMARKET", "", ENTRY_COHORT_CONTRACT_V1, "LEGACY"),
    ),
}

SOURCE_ONLY_AUTHORITY = {
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _ascii_canonical_sha256(value: Any) -> str:
    """Match the micro-reversion producer's ASCII JSON digest contract."""

    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _expected_entry_prompt_sha256(candidate_prompt_version: str) -> str:
    return ENTRY_CANDIDATE_PROMPT_SHA256.get(candidate_prompt_version, "")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _embedded_content_sha256_valid(payload: Mapping[str, Any], field: str) -> bool:
    embedded = _bounded_string(payload.get(field))
    if not embedded:
        return False
    content = {key: value for key, value in payload.items() if key != field}
    return _canonical_sha256(content) == embedded


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _source_only_authority_valid(payload: Mapping[str, Any]) -> bool:
    return bool(
        payload.get("runtime_effect") is False
        and payload.get("runtime_authority") is False
        and payload.get("allowed_runtime_apply") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )


def _calibration_cohort_identity(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Normalize legacy calibration rows while preserving v2 route identity."""
    version = _bounded_string(row.get("cohort_key_version")) or ENTRY_COHORT_CONTRACT_V1
    route = _bounded_string(row.get("market_data_route")).upper()
    authority = _bounded_string(row.get("authority_state")) or "LEGACY"
    return tuple(
        _bounded_string(row.get(field))
        for field in (
            "candidate_prompt_version",
            "candidate_prompt_sha256",
            "candidate_contract_sha256",
            "stage",
            "effective_venue",
            "session_bucket",
        )
    ) + (route, version, authority)


def _entry_cohort_contract(calibration: Mapping[str, Any]) -> dict[str, Any]:
    """Publish the exact replay census without granting v2 search authority."""
    dual_rows = sorted(
        {
            _bounded_string(row.get("market_data_route")).upper()
            for row in calibration.get("candidate_summaries") or []
            if isinstance(row, Mapping)
            and _bounded_string(row.get("stage")).lower() == "entry"
            and _bounded_string(row.get("effective_venue")).upper()
            == ENTRY_DUAL_AFTERMARKET_VENUE
            and _bounded_string(row.get("session_bucket")).upper()
            == ENTRY_DUAL_AFTERMARKET_SESSION
            and _bounded_string(row.get("cohort_key_version"))
            == ENTRY_COHORT_CONTRACT_V2
            and _bounded_string(row.get("authority_state")) == "OBSERVE_ONLY"
            and _bounded_string(row.get("market_data_route"))
        }
    )
    version = ENTRY_COHORT_CONTRACT_V2 if dual_rows else ENTRY_COHORT_CONTRACT_V1
    expected = [
        {
            "effective_venue": venue,
            "session_bucket": session,
            "market_data_route": route or None,
            "cohort_key_version": cohort_key_version,
            "authority_state": authority,
        }
        for venue, session, route, cohort_key_version, authority in (
            ENTRY_EXPECTED_COHORTS_BY_CONTRACT_VERSION[version]
        )
    ]
    expected.extend(
        {
            "effective_venue": ENTRY_DUAL_AFTERMARKET_VENUE,
            "session_bucket": ENTRY_DUAL_AFTERMARKET_SESSION,
            "market_data_route": route,
            "cohort_key_version": ENTRY_COHORT_CONTRACT_V2,
            "authority_state": "OBSERVE_ONLY",
        }
        for route in dual_rows
    )
    body = {
        "schema": ENTRY_COHORT_CONTRACT_SCHEMA,
        "version": version,
        "expected_cohorts": expected,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "dual_aftermarket_provider_forbidden": True,
    }
    return {**body, "contract_content_sha256": _canonical_sha256(body)}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                dict(payload),
                stream,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"main_ai_prompt_optimizer_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _prepared_path(target_date: str) -> Path:
    return PREPARED_DIR / f"main_ai_quality_micro_prepared_requests_{target_date}.json"


def _bridge_path(target_date: str) -> Path:
    return BRIDGE_DIR / f"micro_reversion_ai_quality_bridge_{target_date}.json"


def _latest_action_outcome_calibration(
    target_date: str,
) -> tuple[dict[str, Any], Path | None, list[str]]:
    warnings: list[str] = []
    path = (
        ACTION_OUTCOME_CALIBRATION_DIR
        / f"ai_decision_action_outcome_calibration_{target_date}.json"
    )
    payload = _read_json(path)
    if not payload:
        return {}, path, ["action_outcome_calibration_not_available_for_target_date"]
    handoff = payload.get("optimizer_handoff")
    handoff = handoff if isinstance(handoff, Mapping) else {}
    handoff_hash = _bounded_string(handoff.get("handoff_content_sha256"))
    handoff_body = {
        key: value for key, value in handoff.items() if key != "handoff_content_sha256"
    }
    source_contract = payload.get("source_contract_summary")
    source_contract = source_contract if isinstance(source_contract, Mapping) else {}
    candidate_summaries = payload.get("candidate_summaries")
    candidate_summaries = (
        candidate_summaries if isinstance(candidate_summaries, list) else []
    )
    if payload.get("schema") != ACTION_OUTCOME_CALIBRATION_SCHEMA:
        warnings.append("action_outcome_calibration_schema_invalid")
    if payload.get("policy_version") != calibration_source.POLICY_VERSION:
        warnings.append("action_outcome_calibration_policy_version_invalid")
    if payload.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE.isoformat():
        warnings.append("action_outcome_calibration_clean_baseline_invalid")
    if payload.get("target_date") != target_date or handoff.get("target_date") != (
        target_date
    ):
        warnings.append("action_outcome_calibration_target_date_mismatch")
    if not calibration_source._artifact_content_sha256_valid(payload):
        warnings.append("action_outcome_calibration_content_hash_invalid")
    for source in payload.get("source_reports") or []:
        if (
            not isinstance(source, Mapping)
            or source.get("artifact_content_sha256_verified") is not True
        ):
            continue
        source_path = Path(str(source.get("path") or ""))
        if source_path.parent.resolve() != DETAILED_DIR.resolve():
            warnings.append("action_outcome_calibration_source_path_invalid")
            break
        current_source = _read_json(source_path)
        if not calibration_source._artifact_content_sha256_valid(
            current_source
        ) or current_source.get("artifact_content_sha256") != source.get(
            "artifact_content_sha256"
        ):
            warnings.append("action_outcome_calibration_source_generation_changed")
            break
    if (
        not _source_only_authority_valid(payload)
        or payload.get("order_authority") is not False
        or payload.get("provider_authority") is not False
    ):
        warnings.append("action_outcome_calibration_authority_contract_invalid")
    if (
        handoff.get("schema") != ACTION_OUTCOME_OPTIMIZER_HANDOFF_SCHEMA
        or not handoff_hash
        or calibration_source._canonical_sha256(handoff_body) != handoff_hash
        or handoff.get("source_contract_pass") is not True
    ):
        warnings.append("action_outcome_calibration_handoff_invalid")
    if (
        source_contract.get("cross_cohort_aggregation_forbidden") is not True
        or source_contract.get("invalid_sources_excluded_before_calibration")
        is not True
        or source_contract.get("candidate_selection_requires_verified_source_hash")
        is not True
        or source_contract.get("conflicting_duplicate_traces_excluded") is not True
        or source_contract.get("cross_cohort_outcome_conflicts_excluded") is not True
    ):
        warnings.append("action_outcome_calibration_source_contract_invalid")
    candidate_identities: set[tuple[str, ...]] = set()
    candidate_contract_valid = isinstance(
        payload.get("candidate_summaries"), list
    ) and _native_nonnegative_int(payload.get("candidate_count")) == len(
        candidate_summaries
    )
    for row in candidate_summaries:
        if not isinstance(row, Mapping):
            candidate_contract_valid = False
            continue
        identity = _calibration_cohort_identity(row)
        route, cohort_version, authority = identity[-3:]
        is_dual = cohort_version == ENTRY_COHORT_CONTRACT_V2
        if (
            not all(identity[:6])
            or not _is_sha256(identity[1])
            or not _is_sha256(identity[2])
            or row.get("cohort_isolated") is not True
            or row.get("runtime_apply_authority") is not False
            or identity in candidate_identities
            or (is_dual and (
                identity[4].upper() != ENTRY_DUAL_AFTERMARKET_VENUE
                or identity[5].upper() != ENTRY_DUAL_AFTERMARKET_SESSION
                or not route
                or authority != "OBSERVE_ONLY"
                or row.get("review_classification") != "dual_aftermarket_observe_only"
                or row.get("review_ready_for_prompt_candidate") is not False
            ))
            or (not is_dual and (route or cohort_version != ENTRY_COHORT_CONTRACT_V1))
        ):
            candidate_contract_valid = False
        candidate_identities.add(identity)
    if not candidate_contract_valid:
        warnings.append("action_outcome_calibration_candidate_contract_invalid")
    report_ready_references = payload.get("review_ready_candidates")
    report_thin_references = payload.get("thin_positive_review_candidates")
    if (
        not isinstance(report_ready_references, list)
        or not isinstance(report_thin_references, list)
        or _native_nonnegative_int(payload.get("review_candidate_count"))
        != len(report_ready_references)
        or _native_nonnegative_int(payload.get("thin_positive_review_candidate_count"))
        != len(report_thin_references)
        or handoff.get("selected_review_candidate")
        != payload.get("selected_review_candidate")
        or handoff.get("review_ready_candidates") != report_ready_references
        or handoff.get("thin_positive_review_candidates") != report_thin_references
    ):
        warnings.append("action_outcome_calibration_handoff_candidate_invalid")
    candidates_by_identity = {
        _calibration_cohort_identity(row): row
        for row in candidate_summaries
        if isinstance(row, Mapping)
    }
    handoff_references: list[tuple[str, Mapping[str, Any]]] = []
    selected_reference = handoff.get("selected_review_candidate")
    if isinstance(selected_reference, Mapping):
        handoff_references.append(("review_ready", selected_reference))
    elif selected_reference is not None:
        warnings.append("action_outcome_calibration_handoff_candidate_invalid")
    ready_references = handoff.get("review_ready_candidates")
    if not isinstance(ready_references, list):
        warnings.append("action_outcome_calibration_handoff_candidate_invalid")
        ready_references = []
    for reference in ready_references:
        if isinstance(reference, Mapping):
            handoff_references.append(("review_ready", reference))
        else:
            warnings.append("action_outcome_calibration_handoff_candidate_invalid")
    thin_references = handoff.get("thin_positive_review_candidates")
    if not isinstance(thin_references, list):
        warnings.append("action_outcome_calibration_handoff_candidate_invalid")
        thin_references = []
    for reference in thin_references:
        if isinstance(reference, Mapping):
            handoff_references.append(("thin_positive_review", reference))
        else:
            warnings.append("action_outcome_calibration_handoff_candidate_invalid")
    for expected_classification, reference in handoff_references:
        identity = _calibration_cohort_identity(reference)
        matched = candidates_by_identity.get(identity)
        if (
            matched is None
            or matched.get("review_classification") != expected_classification
            or reference.get("runtime_apply_authority") is not False
        ):
            warnings.append("action_outcome_calibration_handoff_candidate_invalid")
            break
    if warnings:
        return {}, path, warnings
    return payload, path, []


def _action_outcome_advisory(
    calibration: Mapping[str, Any],
    *,
    stage: str,
    effective_venue: str,
    session_bucket: str,
    candidate_prompt_version: str,
    market_data_route: str = "",
    cohort_key_version: str = ENTRY_COHORT_CONTRACT_V1,
) -> dict[str, Any] | None:
    matches = [
        row
        for row in calibration.get("candidate_summaries") or []
        if isinstance(row, Mapping)
        and (
            _bounded_string(row.get("stage")).lower() == stage
            and _bounded_string(row.get("effective_venue")).upper() == effective_venue
            and _bounded_string(row.get("session_bucket")).upper() == session_bucket
            and _bounded_string(row.get("candidate_prompt_version"))
            == candidate_prompt_version
            and _bounded_string(row.get("market_data_route")).upper()
            == market_data_route.upper()
            and (_bounded_string(row.get("cohort_key_version")) or ENTRY_COHORT_CONTRACT_V1)
            == cohort_key_version
        )
    ]
    if len(matches) != 1:
        return None
    row = matches[0]
    return {
        "candidate_prompt_sha256": row.get("candidate_prompt_sha256"),
        "candidate_contract_sha256": row.get("candidate_contract_sha256"),
        "review_classification": row.get("review_classification"),
        "source_integrity_complete": row.get("source_integrity_complete"),
        "entry_research_progress": row.get("entry_research_progress"),
        "cost_aware_opportunity_diagnostic": row.get(
            "cost_aware_opportunity_diagnostic"
        ),
        "candidate_primary_decision_ev_delta_pct": row.get(
            "candidate_primary_decision_ev_delta_pct"
        ),
        "candidate_probe_cost_adjusted_ev_pct": row.get(
            "candidate_probe_cost_adjusted_ev_pct"
        ),
        "r3_handoff_evidence_pass": (
            (row.get("r3_handoff_evidence") or {}).get("pass")
            if isinstance(row.get("r3_handoff_evidence"), Mapping)
            else False
        ),
        "runtime_review_route": calibration_source.runtime_review_route(
            candidate_prompt_version, stage, effective_venue, session_bucket
        ),
        "selection_authority": False,
        "runtime_apply_authority": False,
    }


def _bounded_string(value: Any) -> str:
    return str(value or "").strip()


def _native_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _stage_prompt_contracts(
    prepared_rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_stage: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in prepared_rows:
        stage = _bounded_string(row.get("stage")).lower()
        if stage in {"entry", "holding", "exit"}:
            by_stage[stage].append(row)
    result: dict[str, dict[str, Any]] = {}
    for stage, rows in sorted(by_stage.items()):
        champion_pairs = Counter(
            (
                _bounded_string((row.get("control") or {}).get("prompt_version")),
                _bounded_string((row.get("control") or {}).get("prompt_sha256")),
            )
            for row in rows
            if isinstance(row.get("control"), Mapping)
        )
        challenger_pairs = Counter(
            (
                _bounded_string((row.get("candidate") or {}).get("prompt_version")),
                _bounded_string(
                    (row.get("candidate") or {}).get("system_prompt_sha256")
                ),
                _bounded_string((row.get("candidate") or {}).get("contract_sha256")),
            )
            for row in rows
            if isinstance(row.get("candidate"), Mapping)
        )
        champion = champion_pairs.most_common(1)[0][0] if champion_pairs else ("", "")
        challenger = (
            challenger_pairs.most_common(1)[0][0] if challenger_pairs else ("", "", "")
        )
        symbols = {
            _bounded_string(row.get("stock_code"))
            for row in rows
            if _bounded_string(row.get("stock_code"))
        }
        sessions = sorted(
            {
                (
                    _bounded_string(row.get("effective_venue")).upper(),
                    _bounded_string(row.get("session_bucket")).upper(),
                )
                for row in rows
            }
        )
        result[stage] = {
            "base_exact_parent_count": len(rows),
            "base_exact_unique_symbol_count": len(symbols),
            "base_exact_trace_ids_sha256": _canonical_sha256(
                sorted(_bounded_string(row.get("decision_trace_id")) for row in rows)
            ),
            "cohorts": [
                {"effective_venue": venue, "session_bucket": session}
                for venue, session in sessions
            ],
            "champion": {
                "prompt_version": champion[0],
                "prompt_sha256": champion[1],
                "observed_parent_count": champion_pairs.get(champion, 0),
                "dynamic_from_exact_runtime_trace": True,
            },
            "legacy_r0_challenger": {
                "prompt_version": challenger[0],
                "prompt_sha256": challenger[1],
                "contract_sha256": challenger[2],
                "observed_parent_count": challenger_pairs.get(challenger, 0),
                "selection_authority": False,
            },
            "contract_drift": {
                "champion_variant_count": len(champion_pairs),
                "challenger_variant_count": len(challenger_pairs),
                "pass": len(champion_pairs) == 1 and len(challenger_pairs) == 1,
            },
        }
    return result


def _enriched_trace_ids_by_stage(bridge: Mapping[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in bridge.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        if row.get("ask_depletion_sidecar_status") != (
            "eligible_source_only_feature_ablation"
        ):
            continue
        trace_id = _bounded_string(row.get("decision_trace_id"))
        raw_stage = _bounded_string(row.get("decision_stage")).lower()
        stage = "entry" if raw_stage.startswith("entry") else raw_stage.split("_", 1)[0]
        if trace_id and stage in {"entry", "holding", "exit"}:
            result[stage].add(trace_id)
    return result


def _detailed_reports(target_date: str) -> list[dict[str, Any]]:
    from src.engine.scalping.entry_setup_evidence import ENTRY_SETUP_EVIDENCE_VERSION
    from src.engine.scalping.entry_setup_live_policy import _full_cost_economics_pass

    latest: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    requested_date = date.fromisoformat(target_date)
    for path in sorted(DETAILED_DIR.glob("*.json")):
        payload = _read_json(path)
        try:
            source_date = date.fromisoformat(str(payload.get("target_date") or ""))
        except ValueError:
            continue
        cohort = payload.get("promotion_cohort_scope")
        cumulative = payload.get("cumulative_learning")
        if (
            payload.get("schema") != "ai_prompt_detailed_paired_replay_v1"
            or not CLEAN_BASELINE_DATE <= source_date <= requested_date
            or not isinstance(cohort, Mapping)
            or cohort.get("isolated") is not True
            or not isinstance(cumulative, Mapping)
            or cumulative.get("as_of_date") != source_date.isoformat()
            or cumulative.get("clean_tuning_baseline_date")
            != CLEAN_BASELINE_DATE.isoformat()
            or payload.get("promotion_report_integrity_pass") is not True
            or _native_nonnegative_int(payload.get("provider_failed_count")) != 0
            or _native_nonnegative_int(payload.get("candidate_provider_none_count"))
            != 0
        ):
            continue
        stages = cohort.get("stages") or []
        venues = cohort.get("effective_venues") or []
        sessions = cohort.get("session_buckets") or []
        stage = _bounded_string(stages[0]).lower() if len(stages) == 1 else ""
        if (
            stage not in {"entry", "holding", "exit"}
            or len(venues) != 1
            or len(sessions) != 1
            or cohort.get("candidate_contract_isolated") is not True
            or cohort.get("cross_cohort_promotion_forbidden") is not True
        ):
            continue
        candidate_prompt_version = _bounded_string(
            cumulative.get("candidate_prompt_version")
        )
        if not candidate_prompt_version:
            continue
        candidate_requests = [
            row.get("candidate")
            for row in payload.get("requests") or []
            if isinstance(row, Mapping) and isinstance(row.get("candidate"), Mapping)
        ]
        candidate_request_versions = {
            _bounded_string(candidate.get("prompt_version"))
            for candidate in candidate_requests
        }
        candidate_prompt_hashes = {
            _bounded_string(candidate.get("system_prompt_sha256"))
            for candidate in candidate_requests
        }
        candidate_contract_hashes = {
            _bounded_string(candidate.get("contract_sha256"))
            for candidate in candidate_requests
        }
        declared_candidate_contract_sha256 = _bounded_string(
            payload.get("candidate_contract_sha256")
        )
        expected_prompt_sha256 = (
            _expected_entry_prompt_sha256(candidate_prompt_version)
            if stage == "entry"
            else ""
        )
        if stage == "entry" and (
            candidate_prompt_version not in ENTRY_CANDIDATE_ORDER
            or candidate_request_versions != {f"{candidate_prompt_version}_entry"}
            or candidate_prompt_hashes != {expected_prompt_sha256}
            or not declared_candidate_contract_sha256
            or candidate_contract_hashes != {declared_candidate_contract_sha256}
            or _bounded_string(cohort.get("candidate_contract_sha256"))
            != declared_candidate_contract_sha256
            or _bounded_string(cumulative.get("candidate_contract_sha256"))
            != declared_candidate_contract_sha256
        ):
            continue
        net_economic_review_pass = bool(
            stage == "entry"
            and payload.get("runtime_effect") is False
            and payload.get("allowed_runtime_apply") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and payload.get("entry_setup_evidence_version")
            == ENTRY_SETUP_EVIDENCE_VERSION
            and _full_cost_economics_pass(cumulative.get("full_cost_economics"))
            and isinstance(cumulative.get("candidate_probe_risk_budget"), Mapping)
            and cumulative["candidate_probe_risk_budget"].get("pass") is True
            and isinstance(cumulative.get("promotion_evidence_floor"), Mapping)
            and cumulative["promotion_evidence_floor"].get("pass") is True
        )
        report = {
            "path": str(path),
            "source_date": source_date.isoformat(),
            "stage": stage,
            "candidate_prompt_version": candidate_prompt_version,
            "candidate_prompt_sha256": expected_prompt_sha256,
            "candidate_contract_sha256": declared_candidate_contract_sha256,
            "effective_venue": _bounded_string(venues[0]).upper(),
            "session_bucket": _bounded_string(sessions[0]).upper(),
            "decision_count": _native_nonnegative_int(cumulative.get("decision_count"))
            or 0,
            "unique_symbol_count": _native_nonnegative_int(
                cumulative.get("unique_symbol_count")
            )
            or 0,
            "candidate_exposure_decision_count": _native_nonnegative_int(
                cumulative.get("candidate_exposure_decision_count")
            )
            or 0,
            "candidate_exposure_unique_symbol_count": _native_nonnegative_int(
                cumulative.get("candidate_exposure_unique_symbol_count")
            )
            or 0,
            "candidate_primary_decision_ev_pct": cumulative.get(
                "candidate_primary_decision_ev_pct"
            ),
            "source_quality_adjusted_ev_delta_pct": cumulative.get(
                "source_quality_adjusted_ev_delta_pct"
            ),
            "candidate_exposure_probe_cost_adjusted_ev_pct": cumulative.get(
                "candidate_exposure_probe_cost_adjusted_ev_pct"
            ),
            "promotion_evidence_floor": cumulative.get("promotion_evidence_floor"),
            "promotion_quality_gate_pass": (
                net_economic_review_pass
                if stage == "entry" and "full_cost_economics" in cumulative
                else cumulative.get("promotion_quality_gate_pass") is True
            ),
            "net_economic_review_pass": net_economic_review_pass,
            "legacy_quality_diagnostic_pass": cumulative.get(
                "promotion_quality_gate_pass"
            )
            is True,
            "error_taxonomy_counts": cumulative.get("candidate_error_taxonomy_counts")
            or {},
            "provider_attempt_count": _native_nonnegative_int(
                payload.get("candidate_provider_attempt_count")
            )
            or 0,
            "provider_failed_count": _native_nonnegative_int(
                payload.get("provider_failed_count")
            )
            or 0,
            "evaluation_coverage_pct": (
                (payload.get("candidate_execution_selection") or {}).get(
                    "evaluation_coverage_pct"
                )
            ),
            "net_profit_status": payload.get("net_profit_status"),
        }
        identity = (
            report["stage"],
            report["effective_venue"],
            report["session_bucket"],
            report["candidate_prompt_version"],
        )
        prior = latest.get(identity)
        if prior is None or report["source_date"] > prior["source_date"]:
            latest[identity] = report
    return sorted(
        latest.values(),
        key=lambda row: (
            row["stage"],
            row["effective_venue"],
            row["session_bucket"],
            row["candidate_prompt_version"],
        ),
    )


def _research_rotation_due(evidence: Mapping[str, Any]) -> bool:
    progress = evidence.get("entry_research_progress")
    if not isinstance(progress, Mapping):
        return False
    parents = progress.get("exact_parent_ids")
    dates = progress.get("source_dates")
    cases = progress.get("small_opportunity_case_ids")
    if not all(isinstance(value, list) for value in (parents, dates, cases)):
        return False
    if not all(isinstance(x, str) and x for x in parents + dates + cases):
        return False
    evidence_dates = evidence.get("source_dates")
    if not isinstance(evidence_dates, list) or not all(
        isinstance(day, str) and day for day in evidence_dates
    ):
        return False
    return bool(
        progress.get("schema") == "entry_prompt_research_progress_v1"
        and progress.get("offline_rotation_due") is True
        and progress.get("allowed_runtime_apply") is False
        and progress.get("runtime_effect") is False
        and progress.get("research_window_pass") is True
        and type(progress.get("candidate_exposure_count")) is int
        and progress["candidate_exposure_count"] == 0
        and progress.get("window_policy")
        == "last_five_valid_source_dates_within_exact_candidate_cohort"
        and progress.get("cohort_exact_parent_count")
        == evidence.get("exact_trace_count")
        and len(parents) == len(set(parents)) == progress.get("exact_parent_count")
        and len(parents)
        <= (_native_nonnegative_int(evidence.get("exact_trace_count")) or 0)
        and len(set(parents)) >= 5
        and len(dates) == len(set(dates))
        and dates == sorted(set(evidence_dates))[-5:]
        and len(set(dates)) >= 5
        and (_native_nonnegative_int(progress.get("unique_symbol_count")) or 0) >= 3
        and progress.get("unique_symbol_count")
        <= (_native_nonnegative_int(evidence.get("unique_symbol_count")) or 0)
        and cases
        and set(cases) <= set(parents)
    )


def _prompt_revision_proposals(calibration, *, effective_venue, session_bucket):
    """Emit concrete offline patch drafts from verified isolated error cases."""
    proposals = []
    for evidence in calibration.get("candidate_summaries") or []:
        if not isinstance(evidence, Mapping):
            continue
        version = evidence.get("candidate_prompt_version")
        progress = evidence.get("entry_research_progress") or {}
        if not isinstance(progress, Mapping):
            continue
        cases = progress.get("small_opportunity_case_ids")
        parents = progress.get("exact_parent_ids")
        if not (
            evidence.get("stage") == "entry"
            and evidence.get("effective_venue") == effective_venue
            and evidence.get("session_bucket") == session_bucket
            and evidence.get("source_integrity_complete") is True
            and version in ENTRY_CANDIDATE_ORDER
            and evidence.get("candidate_prompt_sha256")
            == _expected_entry_prompt_sha256(version)
            and isinstance(cases, list)
            and cases
            and isinstance(parents, list)
            and all(isinstance(case, str) and case for case in cases + parents)
            and set(cases) <= set(parents)
            and progress.get("schema") == "entry_prompt_research_progress_v1"
            and progress.get("runtime_effect") is False
            and progress.get("allowed_runtime_apply") is False
        ):
            continue
        body = {
            "schema": "entry_prompt_revision_proposal_v1",
            "recommendation_id": "entry-prompt-revision-"
            + _canonical_sha256(
                [
                    version,
                    evidence["candidate_prompt_sha256"],
                    evidence.get("candidate_contract_sha256"),
                    effective_venue,
                    session_bucket,
                    sorted(set(cases)),
                ]
            )[:24],
            "owner": "AIDecisionActionOutcomeNaturalEvidence0908",
            "decision": "objective_followup_required",
            "parent_prompt_version": version,
            "parent_prompt_hash": evidence["candidate_prompt_sha256"],
            "candidate_contract_sha256": evidence.get("candidate_contract_sha256"),
            "effective_venue": effective_venue,
            "session_bucket": session_bucket,
            "case_ids": sorted(set(cases)),
            "cost_evidence_by_case": progress.get("small_opportunity_cost_cases") or [],
            "evidence_basis": "small_target_execution_proxy_not_verified_net_profit",
            "failure_hypothesis": "small_target_soft_risk_may_be_treated_as_hard_rejection",
            "patch_type": "review_only_appendix_for_new_version",
            "evaluation_population": "same_exact_parent_payload_and_action_neutral_outcome",
            "actuator_contract": calibration_source.runtime_review_route(
                version, "entry", effective_venue, session_bucket
            ),
            "candidate_registration_status": "new_version_and_hash_review_required",
            "proposed_appendix": (
                "Evaluate the declared target against verified roundtrip fees, tax, "
                "executable prices and fill feasibility. Do not require a large gross "
                "move when a smaller positive net opportunity meets the existing "
                "risk contract. Separate hard negatives from recheckable soft risk. "
                "Ask depletion alone is not confirmation: distinguish trade-backed "
                "consumption from cancellation, refill and collapsing bid support. "
                "Missing cost or source evidence is unknown, not zero or permission "
                "to buy. Preserve every existing output schema and execution guard."
            ),
            "counterexamples": [
                "gross_positive_but_negative_after_cost",
                "ask_cancellation_followed_by_refill_or_bid_collapse",
                "stale_or_cross_epoch_quote",
                "armed_recheck_without_valid_followup",
            ],
            "next_action": "review_versioned_patch_then_existing_bounded_offline_batch",
            "implementation_status": "pending_versioned_prompt_contract_review",
            "files_likely_touched": [
                "src/engine/ai_prompt_contracts.py",
                "src/engine/scalping/ai_decision_quality.py",
                "src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py",
            ],
            "required_downstream": [
                "code_improvement_workorder",
                "main_ai_prompt_consumer",
                "existing_bounded_offline_paired_replay",
            ],
            "acceptance_tests": [
                "pytest -q src/tests/test_main_ai_prompt_optimizer.py src/tests/test_main_ai_prompt_consumer.py src/tests/test_ai_decision_quality.py",
                "Parent prompt stays immutable; reviewed new version/hash and schema are explicit.",
                "Same exact parents, verified cost outcomes and counterexamples reach bounded offline evaluation.",
                "No provider budget increase, same-day selection mutation or inherited live authority.",
            ],
            "runtime_registry_mutation_allowed": False,
            "provider_budget_increase_allowed": False,
            "rollback_prompt_hash": evidence["candidate_prompt_sha256"],
            **SOURCE_ONLY_AUTHORITY,
        }
        proposals.append({**body, "proposal_content_sha256": _canonical_sha256(body)})
    return proposals


def _select_entry_challenger(
    legacy_challenger: str,
    detailed: list[dict[str, Any]],
    *,
    effective_venue: str,
    session_bucket: str,
    calibration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    screened_out: list[str] = []
    research_rotated: list[str] = []
    by_version: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in detailed:
        if (
            row.get("stage") == "entry"
            and row.get("effective_venue") == effective_venue
            and row.get("session_bucket") == session_bucket
            and row.get("candidate_prompt_version")
        ):
            by_version[str(row["candidate_prompt_version"])].append(row)
    for version in ENTRY_CANDIDATE_ORDER:
        evaluations = by_version.get(version) or []
        if any(row.get("net_economic_review_pass") is True for row in evaluations):
            # Keep learning on new exact parents. A gross/proxy calibration
            # screen must not discard a full-cost-positive challenger. This is
            # offline scheduling only; PREOPEN independently verifies authority.
            return {
                "prompt_version": version,
                "action": "continue_current_challenger_new_mature_parents_only",
                "reason": "verified_full_cost_net_positive_continue_exact_validation",
                "calibration_screened_out_versions": list(screened_out),
                "calibration_research_rotated_versions": list(research_rotated),
                **SOURCE_ONLY_AUTHORITY,
            }
        matches = [
            row
            for row in (calibration or {}).get("candidate_summaries") or []
            if row.get("stage") == "entry"
            and row.get("effective_venue") == effective_venue
            and row.get("session_bucket") == session_bucket
            and row.get("candidate_prompt_version") == version
            and row.get("candidate_prompt_sha256")
            == _expected_entry_prompt_sha256(version)
        ]
        if len(matches) == 1:
            evidence = matches[0]
            contract_matches = not evaluations or all(
                row.get("candidate_contract_sha256")
                == evidence.get("candidate_contract_sha256")
                for row in evaluations
            )
            checks = (evidence.get("prompt_review_gate") or {}).get("checks") or {}
            sufficient = all(
                checks.get(name) is True
                for name in (
                    "exact_trace_floor",
                    "unique_symbol_floor",
                    "independent_source_date_floor",
                    "candidate_exposure_floor",
                )
            )
            if contract_matches and evidence.get("source_integrity_complete") is True:
                # Rotation is research scheduling, not a promotion or economic
                # rejection. Do not require BUYs to explore a nonparticipating
                # challenger, and never select an unregistered live actuator.
                if _research_rotation_due(evidence):
                    research_rotated.append(version)
                    continue
                if evidence.get("review_classification") in {
                    "review_ready",
                    "thin_positive_review",
                }:
                    return {
                        "prompt_version": version,
                        "action": "continue_current_challenger_new_mature_parents_only",
                        "reason": "calibration_positive_validate_on_new_exact_parents",
                        "calibration_used_for_offline_selection": True,
                        "calibration_screened_out_versions": list(screened_out),
                        "calibration_research_rotated_versions": list(research_rotated),
                    }
                if (
                    sufficient
                    and evidence.get("probe_cost_contract_complete") is True
                    and checks.get("paired_economic_values_complete") is True
                    and (
                        checks.get("positive_probe_cost_adjusted_ev") is False
                        or checks.get("positive_ev_delta") is False
                        or (
                            checks.get("bounded_probe_risk_budget") is False
                            and type(evidence.get("candidate_probe_risk_missing_count"))
                            is int
                            and evidence["candidate_probe_risk_missing_count"] == 0
                        )
                    )
                ):
                    # Advance only within the existing offline registry. The
                    # live owner must independently review its exact evidence.
                    screened_out.append(version)
                    continue
        if not evaluations:
            return {
                "prompt_version": version,
                "action": "start_new_challenger_evaluation",
                "reason": "first_untested_supported_challenger",
                "calibration_screened_out_versions": list(screened_out),
                "calibration_research_rotated_versions": list(research_rotated),
            }
        if any(row.get("promotion_quality_gate_pass") is True for row in evaluations):
            return {
                "prompt_version": version,
                "action": "freeze_as_runtime_candidate_pending_r2_r3",
                "reason": "at_least_one_isolated_cohort_passed_quality_gate",
                "calibration_screened_out_versions": list(screened_out),
                "calibration_research_rotated_versions": list(research_rotated),
            }
        if any(
            not (row.get("promotion_evidence_floor") or {}).get("pass")
            for row in evaluations
        ):
            return {
                "prompt_version": version,
                "action": "continue_current_challenger_new_mature_parents_only",
                "reason": "promotion_sample_floor_not_complete",
                "calibration_screened_out_versions": list(screened_out),
                "calibration_research_rotated_versions": list(research_rotated),
            }
    return {
        "prompt_version": legacy_challenger,
        "action": "candidate_registry_exhausted_generate_new_prompt_patch",
        "reason": "all_supported_challengers_evaluated_without_promotion",
        "calibration_screened_out_versions": list(screened_out),
        "calibration_research_rotated_versions": list(research_rotated),
    }


def _frozen_entry_batch_selection(
    target_date: str,
) -> dict[tuple[str, str], dict[str, str]]:
    """Keep a terminal day's executed versions fixed during report refresh."""
    batch = _read_json(
        ENTRY_BATCH_DIR / f"ai_entry_setup_paired_replay_batch_{target_date}.json"
    )
    if not (
        batch.get("schema") == "ai_entry_setup_paired_replay_batch_v1"
        and batch.get("target_date") == target_date
        and batch.get("status") == "completed_offline_only"
        and batch.get("runtime_effect") is False
        and batch.get("allowed_runtime_apply") is False
        and batch.get("actual_order_submitted") is False
        and batch.get("broker_order_forbidden") is True
    ):
        raise ValueError("terminal_entry_batch_required_for_selection_preservation")
    result: dict[tuple[str, str], dict[str, str]] = {}
    for cohort in batch.get("cohorts") or []:
        if not isinstance(cohort, Mapping):
            raise ValueError("entry_batch_cohort_not_terminal")
        if cohort.get("status") == "completed_observe_only":
            if (
                cohort.get("effective_venue") != ENTRY_DUAL_AFTERMARKET_VENUE
                or cohort.get("session_bucket") != ENTRY_DUAL_AFTERMARKET_SESSION
                or cohort.get("cohort_key_version") != ENTRY_COHORT_CONTRACT_V2
                or cohort.get("authority_state") != "OBSERVE_ONLY"
                or not cohort.get("market_data_route")
            ):
                raise ValueError("entry_batch_dual_observe_only_contract_invalid")
            continue
        if cohort.get("status") not in {
            "completed_offline_only",
            "hold_no_mature_exact_request",
            "hold_no_exact_entry_control",
            "hold_candidate_registry_exhausted",
        }:
            raise ValueError("entry_batch_cohort_not_terminal")
        key = (cohort.get("effective_venue"), cohort.get("session_bucket"))
        version = cohort.get("candidate_prompt_version")
        if key in result or version not in ENTRY_CANDIDATE_ORDER:
            raise ValueError("entry_batch_selection_invalid_or_duplicate")
        result[key] = {
            "prompt_version": version,
            "action": (
                "candidate_registry_exhausted_generate_new_prompt_patch"
                if cohort.get("status") == "hold_candidate_registry_exhausted"
                else "continue_current_challenger_new_mature_parents_only"
            ),
            "reason": "terminal_day_selection_frozen_no_provider_reexecution",
        }
    if set(result) != {("KRX", "KRX_REGULAR"), ("NXT", "NXT_AFTERMARKET")}:
        raise ValueError("entry_batch_selection_cohort_set_invalid")
    return result


def _prompt_pair_contract(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    materialized = list(rows)
    champion_pairs = Counter(
        (
            _bounded_string((row.get("control") or {}).get("prompt_version")),
            _bounded_string((row.get("control") or {}).get("prompt_sha256")),
        )
        for row in materialized
        if isinstance(row.get("control"), Mapping)
    )
    challenger_pairs = Counter(
        (
            _bounded_string((row.get("candidate") or {}).get("prompt_version")),
            _bounded_string((row.get("candidate") or {}).get("system_prompt_sha256")),
            _bounded_string((row.get("candidate") or {}).get("contract_sha256")),
        )
        for row in materialized
        if isinstance(row.get("candidate"), Mapping)
    )
    champion = champion_pairs.most_common(1)[0][0] if champion_pairs else ("", "")
    challenger = (
        challenger_pairs.most_common(1)[0][0] if challenger_pairs else ("", "", "")
    )
    return {
        "champion": {
            "prompt_version": champion[0],
            "prompt_sha256": champion[1],
            "observed_parent_count": champion_pairs.get(champion, 0),
            "dynamic_from_exact_runtime_trace": True,
        },
        "legacy_r0_challenger": {
            "prompt_version": challenger[0],
            "prompt_sha256": challenger[1],
            "contract_sha256": challenger[2],
            "observed_parent_count": challenger_pairs.get(challenger, 0),
            "selection_authority": False,
        },
        "contract_drift": {
            "champion_variant_count": len(champion_pairs),
            "challenger_variant_count": len(challenger_pairs),
            "pass": len(champion_pairs) == 1 and len(challenger_pairs) == 1,
        },
    }


def _factorial_design(
    prepared_trace_ids: set[str], enriched_trace_ids: set[str]
) -> dict[str, Any]:
    enriched_common = enriched_trace_ids & prepared_trace_ids
    return {
        "design_version": FACTORIAL_DESIGN_VERSION,
        "arms": [
            "P0D0_champion_base_input",
            "P1D0_challenger_base_input",
            "P0D1_champion_enriched_micro_input",
            "P1D1_challenger_enriched_micro_input",
        ],
        "base_prompt_comparison_parent_count": len(prepared_trace_ids),
        "full_factorial_common_parent_count": len(enriched_common),
        "enriched_parent_trace_ids_sha256": _canonical_sha256(sorted(enriched_common)),
        "no_shock_or_micro_not_applicable_kept_in_base": True,
        "micro_or_ask_depletion_is_global_eligibility_gate": False,
        "estimands": {
            "prompt_main_effect": "P1D0-P0D0 on all exact base parents",
            "input_main_effect": "P0D1-P0D0 on enriched common parents",
            "prompt_input_interaction": "(P1D1-P1D0)-(P0D1-P0D0)",
        },
        "prompt_main_effect_estimable": bool(prepared_trace_ids),
        "input_and_interaction_estimable": bool(enriched_common),
    }


def _error_taxonomy(detailed: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    for report in detailed:
        counts.update(
            {
                str(key): int(value or 0)
                for key, value in (report.get("error_taxonomy_counts") or {}).items()
            }
        )
    dominant = [
        {"error": key, "count": count}
        for key, count in counts.most_common(8)
        if count > 0
    ]
    return {
        "counts": dict(sorted(counts.items())),
        "dominant": dominant,
        "candidate_patch_objectives": {
            "opportunity_capture": sum(
                count
                for key, count in counts.items()
                if key in {"false_wait", "false_drop", "false_drop_direct_profit"}
            ),
            "downside_avoidance": sum(
                count
                for key, count in counts.items()
                if key.startswith("false_buy") or "adverse" in key
            ),
            "recovery_discrimination": sum(
                count for key, count in counts.items() if "recovery" in key
            ),
            "small_profit_opportunity_diagnostic": sum(
                count
                for key, count in counts.items()
                if key
                in {
                    "false_drop_small_profit_execution_proxy",
                    "false_wait_small_profit_execution_proxy",
                }
            ),
        },
    }


def build_report(
    target_date: str,
    *,
    prepared_path: Path | None = None,
    bridge_path: Path | None = None,
    write: bool = False,
    preserve_entry_batch_selection: bool = False,
    require_action_outcome_calibration: bool = False,
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    if target_day < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_baseline")
    prepared_path = prepared_path or _prepared_path(target_date)
    bridge_path = bridge_path or _bridge_path(target_date)
    prepared = _read_json(prepared_path)
    bridge = _read_json(bridge_path)
    (
        action_outcome_calibration,
        action_outcome_calibration_path,
        action_outcome_warnings,
    ) = _latest_action_outcome_calibration(target_date)
    prepared_rows = prepared.get("prepared_requests")
    bridge_rows = bridge.get("rows")
    blockers: list[str] = []
    input_warnings: list[str] = list(action_outcome_warnings)
    bridge_warnings: list[str] = []
    if prepared.get("schema") != "main_ai_quality_micro_prepared_requests_v1":
        blockers.append("prepared_request_artifact_missing_or_invalid")
        prepared_rows = []
    if prepared.get("target_date") != target_date:
        blockers.append("prepared_request_target_date_mismatch")
    if prepared and not _embedded_content_sha256_valid(
        prepared, "artifact_content_sha256"
    ):
        blockers.append("prepared_request_content_hash_invalid")
    if prepared and not _source_only_authority_valid(prepared):
        blockers.append("prepared_request_authority_contract_invalid")
    if not isinstance(prepared_rows, list):
        blockers.append("prepared_request_rows_missing")
        prepared_rows = []
    if bridge.get("schema") != "micro_reversion_ai_quality_bridge_v1":
        bridge_warnings.append("optional_micro_bridge_artifact_missing_or_invalid")
        bridge_rows = []
    if bridge.get("target_date") != target_date:
        bridge_warnings.append("optional_micro_bridge_target_date_mismatch")
    bridge_content_hash = _bounded_string(bridge.get("report_content_sha256"))
    if bridge and (
        not bridge_content_hash
        or _ascii_canonical_sha256(
            {
                key: value
                for key, value in bridge.items()
                if key != "report_content_sha256"
            }
        )
        != bridge_content_hash
    ):
        bridge_warnings.append("optional_micro_bridge_content_hash_invalid")
    if bridge and not _source_only_authority_valid(bridge):
        bridge_warnings.append("optional_micro_bridge_authority_contract_invalid")
    if not isinstance(bridge_rows, list):
        bridge_warnings.append("optional_micro_bridge_rows_missing")
        bridge_rows = []
    input_warnings.extend(bridge_warnings)
    if bridge_warnings:
        bridge = {}
    stages = _stage_prompt_contracts(
        row for row in prepared_rows if isinstance(row, Mapping)
    )
    enriched = _enriched_trace_ids_by_stage(bridge)
    detailed = _detailed_reports(target_date)
    frozen_selection = (
        _frozen_entry_batch_selection(target_date)
        if preserve_entry_batch_selection
        else {}
    )
    entry_cohort_contract = _entry_cohort_contract(action_outcome_calibration)
    for stage, summary in stages.items():
        stage_rows = [
            row
            for row in prepared_rows
            if isinstance(row, Mapping)
            and _bounded_string(row.get("stage")).lower() == stage
        ]
        prepared_trace_ids = {
            _bounded_string(row.get("decision_trace_id"))
            for row in stage_rows
            if _bounded_string(row.get("decision_trace_id"))
        }
        summary["factorial_input_design"] = _factorial_design(
            prepared_trace_ids, enriched.get(stage, set())
        )
        cohort_optimizers: list[dict[str, Any]] = []
        for cohort in summary.get("cohorts") or []:
            venue = _bounded_string(cohort.get("effective_venue")).upper()
            session = _bounded_string(cohort.get("session_bucket")).upper()
            cohort_rows = [
                row
                for row in stage_rows
                if _bounded_string(row.get("effective_venue")).upper() == venue
                and _bounded_string(row.get("session_bucket")).upper() == session
            ]
            cohort_prompt_contract = _prompt_pair_contract(cohort_rows)
            legacy_challenger = cohort_prompt_contract["legacy_r0_challenger"][
                "prompt_version"
            ]
            selected_challenger = (
                _select_entry_challenger(
                    legacy_challenger,
                    detailed,
                    effective_venue=venue,
                    session_bucket=session,
                    calibration=action_outcome_calibration,
                )
                if stage == "entry"
                else {
                    "prompt_version": legacy_challenger,
                    "action": "start_stage_specific_challenger_evaluation",
                    "reason": "no_stage_specific_detailed_evaluator_result",
                }
            )
            next_session_selection = dict(selected_challenger)
            if stage == "entry" and (venue, session) in frozen_selection:
                selected_challenger = dict(frozen_selection[(venue, session)])
            action_outcome_advisory = _action_outcome_advisory(
                action_outcome_calibration,
                stage=stage,
                effective_venue=venue,
                session_bucket=session,
                candidate_prompt_version=_bounded_string(
                    selected_challenger.get("prompt_version")
                ),
            )
            if action_outcome_advisory is not None:
                selected_challenger["action_outcome_calibration"] = (
                    action_outcome_advisory
                )
            cohort_trace_ids = {
                _bounded_string(row.get("decision_trace_id"))
                for row in cohort_rows
                if _bounded_string(row.get("decision_trace_id"))
            }
            cohort_optimizers.append(
                {
                    "effective_venue": venue,
                    "session_bucket": session,
                    "base_exact_parent_count": len(cohort_rows),
                    "base_exact_unique_symbol_count": len(
                        {
                            _bounded_string(row.get("stock_code"))
                            for row in cohort_rows
                            if _bounded_string(row.get("stock_code"))
                        }
                    ),
                    **cohort_prompt_contract,
                    "selected_challenger": selected_challenger,
                    "next_session_evaluation_recommendation": next_session_selection,
                    "factorial_input_design": _factorial_design(
                        cohort_trace_ids, enriched.get(stage, set())
                    ),
                    "selection_scope": "stage_effective_venue_session_isolated",
                    "cross_cohort_selection_forbidden": True,
                }
            )
            cohort_item = cohort_optimizers[-1]
            if stage == "entry":
                cohort_item["prompt_revision_proposals"] = _prompt_revision_proposals(
                    action_outcome_calibration,
                    effective_venue=venue,
                    session_bucket=session,
                )
            cohort_contract = cohort_item.get("contract_drift") or {}
            champion = cohort_item.get("champion") or {}
            legacy = cohort_item.get("legacy_r0_challenger") or {}
            cohort_blockers = []
            if cohort_contract.get("pass") is not True:
                cohort_blockers.append("prompt_contract_drift")
            if not _bounded_string(
                champion.get("prompt_version")
            ) or not _bounded_string(champion.get("prompt_sha256")):
                cohort_blockers.append("champion_prompt_identity_missing")
            if not _bounded_string(legacy.get("prompt_version")):
                cohort_blockers.append("legacy_challenger_identity_missing")
            if len(cohort_trace_ids) != len(cohort_rows):
                cohort_blockers.append(
                    "exact_parent_trace_identity_missing_or_duplicate"
                )
            cohort_item["cohort_blockers"] = cohort_blockers
            cohort_item["prompt_search_ready"] = not cohort_blockers
        summary["cohort_optimizers"] = cohort_optimizers
        selected_versions = {
            _bounded_string(
                (item.get("selected_challenger") or {}).get("prompt_version")
            )
            for item in cohort_optimizers
        }
        selected_actions = {
            _bounded_string((item.get("selected_challenger") or {}).get("action"))
            for item in cohort_optimizers
        }
        summary["selected_challenger"] = (
            dict(cohort_optimizers[0]["selected_challenger"])
            if len(selected_versions) == 1
            and len(selected_actions) == 1
            and cohort_optimizers
            else {
                "prompt_version": "",
                "action": "use_isolated_cohort_selections",
                "reason": "stage_cohorts_have_different_candidate_states",
            }
        )
        summary["selection_scope"] = "cohort_optimizers_only"
        summary["continuous_execution_policy"] = {
            "run_when": [
                "new_mature_exact_parent_available",
                "selected_challenger_prompt_sha_changed",
                "input_bundle_version_changed",
            ],
            "reuse_when": "same_parent_same_prompt_sha_same_input_bundle_hash",
            "provider_budget_scope": "new_or_changed_cells_only",
            "champion_rollover": (
                "registered_runtime_owner_exact_stage_cohort_cost_evidence_"
                "and_preopen_guards_only_no_global_parallel_floor"
            ),
        }

    # A v2 integrated aftermarket route is a terminal source observation.  Do
    # not turn its calibration presence into an offline provider replay or a
    # candidate prompt selection merely because it is part of the same day.
    entry_summary = stages.get("entry")
    if (
        isinstance(entry_summary, dict)
        and entry_cohort_contract["version"] == ENTRY_COHORT_CONTRACT_V2
    ):
        cohort_optimizers = entry_summary.get("cohort_optimizers") or []
        for expected in entry_cohort_contract["expected_cohorts"]:
            if expected["cohort_key_version"] != ENTRY_COHORT_CONTRACT_V2:
                continue
            route = expected["market_data_route"]
            if any(
                _bounded_string(item.get("effective_venue")).upper()
                == expected["effective_venue"]
                and _bounded_string(item.get("session_bucket")).upper()
                == expected["session_bucket"]
                and _bounded_string(item.get("market_data_route")).upper() == route
                for item in cohort_optimizers
                if isinstance(item, Mapping)
            ):
                continue
            cohort_optimizers.append(
                {
                    **expected,
                    "base_exact_parent_count": 0,
                    "base_exact_unique_symbol_count": 0,
                    "selected_challenger": {
                        "prompt_version": "",
                        "action": "dual_aftermarket_observe_only_no_provider_replay",
                        "reason": "v2_route_isolated_source_only_contract",
                    },
                    "next_session_evaluation_recommendation": {
                        "action": "retain_route_isolated_source_observation"
                    },
                    "selection_scope": "route_isolated_source_only",
                    "cross_cohort_selection_forbidden": True,
                    "cohort_blockers": ["dual_aftermarket_observe_only"],
                    "prompt_search_ready": False,
                }
            )
        entry_summary["cohort_optimizers"] = cohort_optimizers

    active_candidate_cohorts = {
        (
            stage,
            _bounded_string(cohort.get("effective_venue")).upper(),
            _bounded_string(cohort.get("session_bucket")).upper(),
            _bounded_string(
                (cohort.get("selected_challenger") or {}).get("prompt_version")
            ),
        )
        for stage, summary in stages.items()
        for cohort in summary.get("cohort_optimizers") or []
        if cohort.get("prompt_search_ready") is True
    }
    evaluated_profit_candidate = any(
        row.get("promotion_quality_gate_pass") is True
        and (
            row.get("stage"),
            row.get("effective_venue"),
            row.get("session_bucket"),
            row.get("candidate_prompt_version"),
        )
        in active_candidate_cohorts
        for row in detailed
    )
    base_parent_count = sum(
        int(summary.get("base_exact_parent_count") or 0) for summary in stages.values()
    )
    challenger_ready = any(
        _bounded_string((cohort.get("selected_challenger") or {}).get("prompt_version"))
        for summary in stages.values()
        for cohort in summary.get("cohort_optimizers") or []
        if cohort.get("prompt_search_ready") is True
    )
    if not active_candidate_cohorts or not challenger_ready:
        blockers.append("no_stage_cohort_prompt_search_ready")
    candidate_generation_feasible = bool(
        base_parent_count > 0 and challenger_ready and not blockers
    )
    selected_entry_versions = {
        _bounded_string((cohort.get("selected_challenger") or {}).get("prompt_version"))
        for cohort in (stages.get("entry") or {}).get("cohort_optimizers") or []
        if cohort.get("prompt_search_ready") is True
    }
    entry_krx_bridge_registered = any(
        cohort.get("effective_venue") == "KRX"
        and cohort.get("session_bucket") == "KRX_REGULAR"
        and (cohort.get("selected_challenger") or {}).get("prompt_version")
        in ENTRY_REGISTERED_BOUNDED_LIVE_PROMPT_VERSIONS
        for cohort in (stages.get("entry") or {}).get("cohort_optimizers") or []
        if cohort.get("prompt_search_ready") is True
    )
    runtime_bridge_gaps = [
        "entry_v2_16_sequential_recovery_requires_later_snapshot_runtime_actuator",
        "holding_stage_base_provider_and_runtime_candidate_consumer_not_registered",
        "optional_enriched_2x2_provider_and_R2_R3_consumer_not_yet_connected",
    ]
    evidence_assessment = (
        "profit_improving_candidate_demonstrated"
        if evaluated_profit_candidate
        else (
            "future_candidate_generation_plausible_but_profit_improvement_unproven"
            if candidate_generation_feasible
            else "candidate_generation_blocked"
        )
    )
    if require_action_outcome_calibration and not action_outcome_calibration:
        blockers.append("required_action_outcome_calibration_invalid_or_unavailable")
        candidate_generation_feasible = False
        evidence_assessment = "candidate_generation_blocked"
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "ready_source_only_continuous_search",
        "decision": evidence_assessment,
        "objective": (
            "Continuously search stage-specific prompt and injected-input bundles "
            "for higher source-quality-adjusted EV and net profit."
        ),
        "source_bindings": {
            "prepared_request_path": str(prepared_path),
            "prepared_request_sha256": (
                _canonical_sha256(prepared) if prepared else None
            ),
            "micro_bridge_path": str(bridge_path),
            "micro_bridge_sha256": _canonical_sha256(bridge) if bridge else None,
            "detailed_report_paths": [row["path"] for row in detailed],
            "action_outcome_calibration_path": (
                str(action_outcome_calibration_path)
                if action_outcome_calibration_path is not None
                else None
            ),
            "action_outcome_calibration_artifact_content_sha256": (
                action_outcome_calibration.get("artifact_content_sha256")
                if action_outcome_calibration
                else None
            ),
        },
        "entry_cohort_contract": entry_cohort_contract,
        "blockers": blockers,
        "optional_input_warnings": input_warnings,
        "stage_optimizers": stages,
        "evaluated_challengers": detailed,
        "action_outcome_calibration_input": {
            "status": (
                "connected_validated_source_only"
                if action_outcome_calibration
                else "not_connected_invalid_or_unavailable"
            ),
            "source_target_date": (
                action_outcome_calibration.get("target_date")
                if action_outcome_calibration
                else None
            ),
            "optimizer_handoff": (
                action_outcome_calibration.get("optimizer_handoff")
                if action_outcome_calibration
                else None
            ),
            "selection_authority": False,
            "offline_evaluation_selection_enabled": True,
            "same_day_executed_selection_preserved": preserve_entry_batch_selection,
            "runtime_apply_authority": False,
        },
        "error_taxonomy": _error_taxonomy(detailed),
        "result_feasibility": {
            "candidate_generation_feasible": candidate_generation_feasible,
            "profit_improving_candidate_currently_demonstrated": (
                evaluated_profit_candidate
            ),
            "future_profit_improving_runtime_output_likelihood": (
                "partial_entry_krx_path_only_profit_improvement_unproven"
                if candidate_generation_feasible
                and entry_krx_bridge_registered
                and not evaluated_profit_candidate
                else (
                    "evidence_supported"
                    if evaluated_profit_candidate
                    else (
                        "blocked_pending_registered_runtime_bridge"
                        if candidate_generation_feasible
                        else "blocked"
                    )
                )
            ),
            "runtime_bridge_ready": False,
            "runtime_bridge_status": {
                "legacy_r3_family_runtime_enabled": False,
                "registered_entry_runtime_owner": "entry_setup_live_policy",
                "entry_krx_selected_candidate_registered": (
                    entry_krx_bridge_registered
                ),
                "entry_selected_prompt_versions": sorted(selected_entry_versions),
                "entry_v2_15_bounded_recovery_registered": True,
                "entry_v2_16_sequential_recovery_registered": False,
                "entry_nxt_registered": False,
                "holding_registered": False,
                "optional_enriched_factorial_registered": False,
                "all_requested_paths_ready": False,
            },
            "runtime_bridge_gaps": runtime_bridge_gaps,
            "future_result_generation_paths": {
                "entry_challenger_base_input": (
                    "connected_to_21_05_cohort_isolated_offline_batch"
                ),
                "holding_challenger_base_input": (
                    "connected_to_source_only_exact_hash_manifest_provider_"
                    "execution_budget_checkpoint_gated"
                ),
                "optional_enriched_factorial_cells": (
                    "connected_to_source_only_cell_router_existing_r0_r3_"
                    "duplicates_not_requeued"
                ),
            },
            "interpretation": (
                "The producer can now keep searching without requiring a micro shock, "
                "but no current candidate may be described as profit-improving until "
                "stage/cohort rolling EV, net-profit, tail, and post-apply guards pass."
            ),
        },
        "metric_contract": {
            "metric_role": "continuous_prompt_and_input_bundle_optimization_plan",
            "decision_authority": "postclose_source_only_ai_quality_research",
            "window_policy": "daily_plan_plus_stage_cohort_5d_10d_20d_validation",
            "sample_floor": (
                "existing stage-specific detailed replay and R2/R3 promotion floors"
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": (
                "clean_baseline_exact_payload_mature_outcome_and_stage_cohort_isolation"
            ),
            "forbidden_uses": [
                "cross_stage_or_cross_cohort_pooling_for_runtime_authority",
                "micro_or_ask_depletion_as_global_prompt_search_gate",
                "provider_model_threshold_quantity_order_or_bot_change",
                "runtime_promotion_from_plan_or_daily_count_only",
            ],
        },
        **SOURCE_ONLY_AUTHORITY,
    }
    report = {**body, "artifact_content_sha256": _canonical_sha256(body)}
    if write:
        json_path, markdown_path = report_paths(target_date)
        _atomic_write_json(json_path, report)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _render_markdown(report: Mapping[str, Any]) -> str:
    feasibility = report.get("result_feasibility") or {}
    lines = [
        f"# Main AI Prompt Optimizer - {report.get('target_date')}",
        "",
        "## Decision",
        f"- status: `{report.get('status')}`",
        f"- decision: `{report.get('decision')}`",
        f"- candidate_generation_feasible: `{feasibility.get('candidate_generation_feasible')}`",
        f"- profit_improving_candidate_currently_demonstrated: `{feasibility.get('profit_improving_candidate_currently_demonstrated')}`",
        f"- future_profit_improving_runtime_output_likelihood: `{feasibility.get('future_profit_improving_runtime_output_likelihood')}`",
        f"- runtime_bridge_ready: `{feasibility.get('runtime_bridge_ready')}`",
        "",
        "## Stage Optimizers",
    ]
    for stage, summary in (report.get("stage_optimizers") or {}).items():
        design = summary.get("factorial_input_design") or {}
        lines.append(
            f"- `{stage}` aggregate base/full-factorial parents="
            f"`{design.get('base_prompt_comparison_parent_count')}/"
            f"{design.get('full_factorial_common_parent_count')}`; selection is cohort-only"
        )
        for cohort in summary.get("cohort_optimizers") or []:
            cohort_design = cohort.get("factorial_input_design") or {}
            challenger = cohort.get("selected_challenger") or {}
            lines.append(
                f"  - `{cohort.get('effective_venue')}/{cohort.get('session_bucket')}` "
                f"champion=`{(cohort.get('champion') or {}).get('prompt_version')}` "
                f"challenger=`{challenger.get('prompt_version')}` "
                f"action=`{challenger.get('action')}` base/full-factorial parents="
                f"`{cohort_design.get('base_prompt_comparison_parent_count')}/"
                f"{cohort_design.get('full_factorial_common_parent_count')}`"
            )
    lines.extend(["", "## Runtime Bridge Gaps"])
    lines.extend(f"- `{gap}`" for gap in feasibility.get("runtime_bridge_gaps") or [])
    return "\n".join(lines) + "\n"


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--preserve-entry-batch-selection", action="store_true")
    parser.add_argument("--require-action-outcome-calibration", action="store_true")
    args = parser.parse_args()
    report = build_report(
        args.target_date,
        write=args.write,
        preserve_entry_batch_selection=args.preserve_entry_batch_selection,
        require_action_outcome_calibration=args.require_action_outcome_calibration,
    )
    if args.print_summary:
        feasibility = report["result_feasibility"]
        print(
            json.dumps(
                {
                    "target_date": report["target_date"],
                    "status": report["status"],
                    "decision": report["decision"],
                    "candidate_generation_feasible": feasibility[
                        "candidate_generation_feasible"
                    ],
                    "runtime_bridge_ready": feasibility["runtime_bridge_ready"],
                },
                ensure_ascii=False,
            )
        )
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
