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
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CLEAN_BASELINE_DATE = date(2026, 6, 5)
SCHEMA = "main_ai_prompt_optimizer_v1"
FACTORIAL_DESIGN_VERSION = "main_ai_prompt_input_factorial_v1"
REPORT_DIR = DATA_DIR / "report" / "main_ai_prompt_optimizer"
PREPARED_DIR = DATA_DIR / "report" / "main_ai_quality_r0_r3"
BRIDGE_DIR = DATA_DIR / "report" / "micro_reversion_ai_quality_bridge"
DETAILED_DIR = DATA_DIR / "report" / "ai_prompt_detailed_paired_replay"

ENTRY_CANDIDATE_ORDER = (
    "decision_quality_v2_14_setup_risk_adjudicator",
    "decision_quality_v2_15_bounded_recovery",
    "decision_quality_v2_16_sequential_recovery",
)
ENTRY_CANDIDATE_PROMPT_SHA256 = {
    ENTRY_CANDIDATE_ORDER[0]: (
        "4d7d540cdf771d4a1cd168b5a3311dd4e208266aec98c0a5279035fa72389015"
    ),
    ENTRY_CANDIDATE_ORDER[1]: (
        "0129e6950da4c563b8727a990ad435c72c3d6b617d3c71808377fa166d4d819b"
    ),
    ENTRY_CANDIDATE_ORDER[2]: (
        "74bbdc46ede54e2b5b5c3075ef387863a262b9d3f0ca9be3339027f95b8e303a"
    ),
}
ENTRY_REGISTERED_BOUNDED_LIVE_PROMPT_VERSIONS = ENTRY_CANDIDATE_ORDER[:2]

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


def _source_only_authority_valid(payload: Mapping[str, Any]) -> bool:
    return bool(
        payload.get("runtime_effect") is False
        and payload.get("runtime_authority") is False
        and payload.get("allowed_runtime_apply") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )


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
            "promotion_quality_gate_pass": cumulative.get("promotion_quality_gate_pass")
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


def _select_entry_challenger(
    legacy_challenger: str,
    detailed: list[dict[str, Any]],
    *,
    effective_venue: str,
    session_bucket: str,
) -> dict[str, Any]:
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
        if not evaluations:
            return {
                "prompt_version": version,
                "action": "start_new_challenger_evaluation",
                "reason": "first_untested_supported_challenger",
            }
        if any(row.get("promotion_quality_gate_pass") is True for row in evaluations):
            return {
                "prompt_version": version,
                "action": "freeze_as_runtime_candidate_pending_r2_r3",
                "reason": "at_least_one_isolated_cohort_passed_quality_gate",
            }
        if any(
            not (row.get("promotion_evidence_floor") or {}).get("pass")
            for row in evaluations
        ):
            return {
                "prompt_version": version,
                "action": "continue_current_challenger_new_mature_parents_only",
                "reason": "promotion_sample_floor_not_complete",
            }
    return {
        "prompt_version": legacy_challenger,
        "action": "candidate_registry_exhausted_generate_new_prompt_patch",
        "reason": "all_supported_challengers_evaluated_without_promotion",
    }


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
        },
    }


def build_report(
    target_date: str,
    *,
    prepared_path: Path | None = None,
    bridge_path: Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    if target_day < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_baseline")
    prepared_path = prepared_path or _prepared_path(target_date)
    bridge_path = bridge_path or _bridge_path(target_date)
    prepared = _read_json(prepared_path)
    bridge = _read_json(bridge_path)
    prepared_rows = prepared.get("prepared_requests")
    bridge_rows = bridge.get("rows")
    blockers: list[str] = []
    input_warnings: list[str] = []
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
        input_warnings.append("optional_micro_bridge_artifact_missing_or_invalid")
        bridge_rows = []
    if bridge.get("target_date") != target_date:
        input_warnings.append("optional_micro_bridge_target_date_mismatch")
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
        input_warnings.append("optional_micro_bridge_content_hash_invalid")
    if bridge and not _source_only_authority_valid(bridge):
        input_warnings.append("optional_micro_bridge_authority_contract_invalid")
    if not isinstance(bridge_rows, list):
        input_warnings.append("optional_micro_bridge_rows_missing")
        bridge_rows = []
    if input_warnings:
        bridge = {}
    stages = _stage_prompt_contracts(
        row for row in prepared_rows if isinstance(row, Mapping)
    )
    enriched = _enriched_trace_ids_by_stage(bridge)
    detailed = _detailed_reports(target_date)
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
                )
                if stage == "entry"
                else {
                    "prompt_version": legacy_challenger,
                    "action": "start_stage_specific_challenger_evaluation",
                    "reason": "no_stage_specific_detailed_evaluator_result",
                }
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
                    "factorial_input_design": _factorial_design(
                        cohort_trace_ids, enriched.get(stage, set())
                    ),
                    "selection_scope": "stage_effective_venue_session_isolated",
                    "cross_cohort_selection_forbidden": True,
                }
            )
            cohort_item = cohort_optimizers[-1]
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
                "only_after_stage_and_cohort_isolated_5d_10d_20d_EV_net_profit_"
                "p10_tail_HELD_guards_and_post_apply_attribution"
            ),
        }

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
        },
        "blockers": blockers,
        "optional_input_warnings": input_warnings,
        "stage_optimizers": stages,
        "evaluated_challengers": detailed,
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
    args = parser.parse_args()
    report = build_report(args.target_date, write=args.write)
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
