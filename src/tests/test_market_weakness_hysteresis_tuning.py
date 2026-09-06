from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from src.engine.risk.market_weakness_state import STATE_REPLAY_CONTRACT

from src.engine.automation.market_weakness_hysteresis_tuning import (
    build_outputs,
    write_outputs,
)
from src.engine.risk.market_weakness_threshold_policy import (
    THRESHOLD_REVIEW_METHOD,
    canonical_sha256,
    load_applied_policy,
    threshold_recommendation_review_hash,
    validate_applied_policy,
)

SOURCE_DATE = date(2026, 8, 28)
EFFECTIVE_DATE = date(2026, 8, 31)


def _write_source(
    source_dir: Path,
    *,
    current_activation: int = 3,
    current_release: int = 3,
    selected_activation: int | None = None,
    selected_release: int | None = None,
) -> Path:
    selected = None
    candidate_ready = selected_activation is not None and selected_release is not None
    if candidate_ready:
        stratum_guards = {
            stratum: {
                "sample_count": 25,
                "holdout_sample_count": 5,
                "holdout_incremental_vs_current_policy_avg_pct": 0.005,
                "full_incremental_vs_current_policy_avg_pct": 0.008,
                "candidate_misclassification_count": 2,
                "current_policy_misclassification_count": 3,
            }
            for stratum in (
                "owner:widget",
                "owner:episode",
                "market:KOSPI",
                "market:KOSDAQ",
            )
        }
        selected = {
            "activation_unique_observations": selected_activation,
            "release_unique_observations": selected_release,
            "changed_axis": (
                "activation_unique_observations"
                if selected_activation != current_activation
                else "release_unique_observations"
            ),
            "candidate_key": f"a{selected_activation}_r{selected_release}",
            "sample_count": 50,
            "calibration_sample_count": 35,
            "holdout_sample_count": 15,
            "calibration_incremental_vs_current_policy_avg_pct": 0.01,
            "holdout_incremental_vs_current_policy_avg_pct": 0.005,
            "full_incremental_vs_current_policy_avg_pct": 0.008,
            "full_incremental_vs_current_policy_p10_pct": -0.01,
            "misclassification_count": 4,
            "stratum_guards": stratum_guards,
            "review_status": "passed_out_of_sample_review",
            "state_replay_contract": STATE_REPLAY_CONTRACT,
            "misclassification_role": "diagnostic_only",
        }
    recommendation = {
        "window_start": "2026-06-05",
        "window_end": SOURCE_DATE.isoformat(),
        "calibration_dates": [
            "2026-08-14",
            "2026-08-13",
            "2026-08-18",
            "2026-08-19",
            "2026-08-20",
            "2026-08-21",
            "2026-08-24",
        ],
        "holdout_dates": ["2026-08-26", "2026-08-27", "2026-08-28"],
        "current_policy_observed_dates": [
            "2026-08-26",
            "2026-08-27",
            "2026-08-28",
        ],
        "sample_floor": {
            "trading_dates_met": candidate_ready,
            "counterfactual_entry_signals_met": candidate_ready,
            "holdout_trading_dates_met": candidate_ready,
            "current_policy_observed_trading_dates_met": candidate_ready,
            "per_listing_market_signals_met": candidate_ready,
            "per_owner_signals_met": candidate_ready,
        },
        "current_policy": {
            "activation_unique_observations": current_activation,
            "release_unique_observations": current_release,
            "misclassification_count": 5,
        },
        "selected_policy": selected,
        "policy_candidate_ready": candidate_ready,
        "review_method": THRESHOLD_REVIEW_METHOD,
        "counterfactual_entry_signal_count": 50 if candidate_ready else 0,
        "owner_signal_counts": (
            {"widget": 25, "episode": 25}
            if candidate_ready
            else {"widget": 0, "episode": 0}
        ),
        "listing_market_signal_counts": (
            {"KOSPI": 25, "KOSDAQ": 25}
            if candidate_ready
            else {"KOSPI": 0, "KOSDAQ": 0}
        ),
    }
    recommendation["review_hash"] = threshold_recommendation_review_hash(recommendation)
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": SOURCE_DATE.isoformat(),
        "market_weakness_entry_response": {
            "schema": "machine_market_weakness_response_v2",
            "target_date": SOURCE_DATE.isoformat(),
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "broker_order_forbidden": True,
            },
            "threshold_recommendation": recommendation,
        },
    }
    path = source_dir / f"machine_microstructure_attribution_{SOURCE_DATE}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_no_candidate_carries_current_policy_instead_of_resetting_baseline(tmp_path):
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    output_dir = tmp_path / "report"
    source_path = _write_source(source_dir, current_activation=3, current_release=3)

    report, applied = build_outputs(
        source_date=SOURCE_DATE,
        source_report_dir=source_dir,
    )
    write_outputs(
        report,
        applied,
        output_dir=output_dir,
        policy_dir=policy_dir,
    )
    loaded, reason = load_applied_policy(
        target_date=EFFECTIVE_DATE,
        policy_dir=policy_dir,
        source_report_dir=source_dir,
    )

    assert applied["activation_unique_observations"] == 3
    assert applied["release_unique_observations"] == 3
    assert applied["prior_activation_unique_observations"] == 3
    assert applied["review"]["status"] == (
        "current_policy_carry_forward_no_approved_candidate"
    )
    assert applied["source_report_canonical_sha256"] == canonical_sha256(
        json.loads(source_path.read_text(encoding="utf-8"))
    )
    assert reason == "ready"
    assert loaded == applied
    assert Path(applied["source_report"]).parent == policy_dir / "source_snapshots"
    assert Path(applied["source_report"]).exists()
    snapshot = json.loads(Path(applied["source_report"]).read_text(encoding="utf-8"))
    assert set(snapshot) == {
        "schema",
        "source_date",
        "source_origin_report",
        "source_origin_report_canonical_sha256",
        "market_weakness_entry_response",
    }


def test_applied_policy_uses_immutable_snapshot_after_daily_source_is_regenerated(
    tmp_path,
):
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    source_path = _write_source(source_dir)
    report, applied = build_outputs(
        source_date=SOURCE_DATE,
        source_report_dir=source_dir,
    )
    write_outputs(
        report,
        applied,
        output_dir=tmp_path / "report",
        policy_dir=policy_dir,
    )
    regenerated = json.loads(source_path.read_text(encoding="utf-8"))
    regenerated["regenerated_after_policy_publish"] = True
    source_path.write_text(json.dumps(regenerated), encoding="utf-8")

    loaded, reason = load_applied_policy(
        target_date=EFFECTIVE_DATE,
        policy_dir=policy_dir,
        source_report_dir=source_dir,
    )

    assert reason == "ready"
    assert loaded == applied


def test_tampered_immutable_snapshot_fails_closed(tmp_path):
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    _write_source(source_dir)
    report, applied = build_outputs(
        source_date=SOURCE_DATE,
        source_report_dir=source_dir,
    )
    write_outputs(
        report,
        applied,
        output_dir=tmp_path / "report",
        policy_dir=policy_dir,
    )
    snapshot_path = Path(applied["source_report"])
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["tampered"] = True
    snapshot_path.chmod(0o640)
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    loaded, reason = load_applied_policy(
        target_date=EFFECTIVE_DATE,
        policy_dir=policy_dir,
        source_report_dir=source_dir,
    )

    assert loaded is None
    assert reason == "market_weakness_policy_source_report_contract_invalid"


def test_reviewed_one_axis_neighbor_is_applied_to_next_exact_session(tmp_path):
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    _write_source(
        source_dir,
        current_activation=3,
        current_release=3,
        selected_activation=3,
        selected_release=4,
    )

    report, applied = build_outputs(
        source_date=SOURCE_DATE,
        source_report_dir=source_dir,
    )
    write_outputs(
        report,
        applied,
        output_dir=tmp_path / "report",
        policy_dir=policy_dir,
    )
    loaded, reason = load_applied_policy(
        target_date=EFFECTIVE_DATE,
        policy_dir=policy_dir,
        source_report_dir=source_dir,
    )

    assert report["status"] == "reviewed_candidate_selected"
    assert applied["activation_unique_observations"] == 3
    assert applied["release_unique_observations"] == 4
    assert applied["review"]["status"] == "passed_out_of_sample_review"
    assert reason == "ready"
    assert loaded == applied


def test_two_axis_or_non_neighbor_selected_policy_fails_closed(tmp_path):
    source_dir = tmp_path / "source"
    _write_source(
        source_dir,
        current_activation=2,
        current_release=3,
        selected_activation=3,
        selected_release=4,
    )

    with pytest.raises(
        ValueError, match="market_weakness_policy_selected_policy_invalid"
    ):
        build_outputs(source_date=SOURCE_DATE, source_report_dir=source_dir)


def test_applied_policy_validator_binds_change_to_declared_prior(tmp_path):
    source_dir = tmp_path / "source"
    _write_source(
        source_dir,
        current_activation=3,
        current_release=3,
        selected_activation=3,
        selected_release=4,
    )
    _report, applied = build_outputs(
        source_date=SOURCE_DATE,
        source_report_dir=source_dir,
    )
    invalid = {
        **applied,
        "prior_activation_unique_observations": 2,
    }

    valid, reason = validate_applied_policy(invalid, target_date=EFFECTIVE_DATE)

    assert valid is False
    assert reason == "market_weakness_policy_multiple_axis_change_forbidden"


def test_tampered_recommendation_review_hash_fails_closed(tmp_path):
    source_dir = tmp_path / "source"
    source_path = _write_source(
        source_dir,
        selected_activation=3,
        selected_release=4,
    )
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    payload["market_weakness_entry_response"]["threshold_recommendation"][
        "holdout_dates"
    ] = ["2026-08-28", "2026-08-27", "2026-08-26"]
    source_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="market_weakness_policy_review_hash_invalid"):
        build_outputs(source_date=SOURCE_DATE, source_report_dir=source_dir)


def test_owner_stratum_economic_degradation_fails_closed_even_with_rehashed_review(
    tmp_path,
):
    source_dir = tmp_path / "source"
    source_path = _write_source(
        source_dir,
        selected_activation=3,
        selected_release=4,
    )
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    recommendation = payload["market_weakness_entry_response"][
        "threshold_recommendation"
    ]
    recommendation["selected_policy"]["stratum_guards"]["owner:episode"][
        "full_incremental_vs_current_policy_avg_pct"
    ] = -0.01
    recommendation["review_hash"] = threshold_recommendation_review_hash(recommendation)
    source_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValueError, match="market_weakness_policy_economic_review_invalid"
    ):
        build_outputs(source_date=SOURCE_DATE, source_report_dir=source_dir)


def test_positive_ev_is_not_vetoed_by_diagnostic_misclassification_count(tmp_path):
    source_dir = tmp_path / "source"
    source_path = _write_source(source_dir, selected_activation=3, selected_release=4)
    payload = json.loads(source_path.read_text())
    recommendation = payload["market_weakness_entry_response"][
        "threshold_recommendation"
    ]
    selected = recommendation["selected_policy"]
    selected["misclassification_count"] = (
        recommendation["current_policy"]["misclassification_count"] + 1
    )
    for guard in selected["stratum_guards"].values():
        guard["candidate_misclassification_count"] = (
            guard["current_policy_misclassification_count"] + 1
        )
    recommendation["review_hash"] = threshold_recommendation_review_hash(recommendation)
    source_path.write_text(json.dumps(payload))
    _report, applied = build_outputs(
        source_date=SOURCE_DATE, source_report_dir=source_dir
    )
    assert applied["release_unique_observations"] == 4
    # A cached pre-repair matrix cannot be relabelled as a reviewed candidate.
    del selected["state_replay_contract"]
    recommendation["review_hash"] = threshold_recommendation_review_hash(recommendation)
    source_path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="selected_policy_invalid"):
        build_outputs(source_date=SOURCE_DATE, source_report_dir=source_dir)


def test_nonfinite_snapshot_fails_closed_without_loader_exception(tmp_path):
    source_dir = tmp_path / "source"
    policy_dir = tmp_path / "policy"
    _write_source(source_dir)
    report, applied = build_outputs(
        source_date=SOURCE_DATE, source_report_dir=source_dir
    )
    write_outputs(
        report, applied, output_dir=tmp_path / "report", policy_dir=policy_dir
    )
    snapshot = Path(applied["source_report"])
    payload = json.loads(snapshot.read_text())
    payload["invalid_float"] = float("nan")
    snapshot.chmod(0o640)
    snapshot.write_text(json.dumps(payload))
    loaded, reason = load_applied_policy(
        target_date=date.fromisoformat(applied["target_date"]),
        policy_dir=policy_dir,
        source_report_dir=source_dir,
    )
    assert loaded is None
    assert reason == "market_weakness_policy_source_report_contract_invalid"
