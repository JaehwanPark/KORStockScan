import json

from src.engine.scalping.rising_missed_selection_prior import (
    clear_selection_prior_cache,
    rising_missed_selection_prior_fields,
)


def _write_catalog(tmp_path, *, lanes=None, seeds=None, overrides=None, runtime_effect=False):
    path = tmp_path / "scalp_sim_policy_catalog.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "scalp_sim_policy_catalog_v1",
                "runtime_effect": runtime_effect,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
                "decision_authority": "scalp_sim_auto_policy_source_only",
                "active_sim_priority_seeds": seeds or [],
                "rising_missed_prior_observation_lanes": lanes or [],
                "rising_missed_prior_active_seed_status_overrides": overrides or [],
            }
        ),
        encoding="utf-8",
    )
    clear_selection_prior_cache()
    return path


def test_positive_prior_exact_match_creates_score_delta(tmp_path):
    policy = _write_catalog(
        tmp_path,
        seeds=[
            {
                "active_seed_id": "seed_positive",
                "status": "active",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
                "rising_missed_prior_recommendation": "positive_prior",
                "rising_missed_prior_confidence": "high",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ],
    )

    fields = rising_missed_selection_prior_fields(
        {
            "entry_score_parent": "score_mid_recovery",
            "scanner_promotion_reason": "wait6579_recovery",
        },
        policy_file=policy,
    )

    assert fields["rising_missed_selection_prior_key"] == "seed_positive"
    assert fields["rising_missed_selection_recommendation"] == "positive_prior"
    assert fields["rising_missed_selection_score_delta"] > 0
    assert fields["rising_missed_selection_runtime_effect"] is False


def test_recheck_prior_has_lower_delta_than_positive_prior(tmp_path):
    positive_policy = _write_catalog(
        tmp_path,
        lanes=[
            {
                "prior_key": "positive",
                "recommendation": "positive_prior",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
            }
        ],
    )
    positive = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=positive_policy,
    )
    recheck_policy = _write_catalog(
        tmp_path,
        lanes=[
            {
                "prior_key": "recheck",
                "recommendation": "recheck_prior",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
            }
        ],
    )
    recheck = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=recheck_policy,
    )

    assert positive["rising_missed_selection_score_delta"] > recheck["rising_missed_selection_score_delta"] > 0


def test_risk_prior_returns_negative_delta(tmp_path):
    policy = _write_catalog(
        tmp_path,
        overrides=[
            {
                "prior_key": "blocked",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
                "reason": "rising_missed_prior_source_quality_blocked",
                "forced_status": "cooldown",
            }
        ],
    )

    fields = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=policy,
    )

    assert fields["rising_missed_selection_recommendation"] == "source_quality_blocked"
    assert fields["rising_missed_selection_score_delta"] < 0
    assert fields["rising_missed_selection_rank_reason"] == "rising_missed_prior_source_quality_blocked"


def test_risk_override_recovers_recommendation_from_reason(tmp_path):
    policy = _write_catalog(
        tmp_path,
        overrides=[
            {
                "prior_key": "loss_override",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
                "reason": "rising_missed_prior_loss_filter",
                "forced_status": "cooldown",
            }
        ],
    )

    fields = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=policy,
    )

    assert fields["rising_missed_selection_recommendation"] == "loss_filter"
    assert fields["rising_missed_selection_score_delta"] == -20.0


def test_missing_or_invalid_catalog_returns_empty_result(tmp_path):
    missing = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=tmp_path / "missing.json",
    )
    invalid_policy = _write_catalog(tmp_path, runtime_effect=True)
    invalid = rising_missed_selection_prior_fields(
        {"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"},
        policy_file=invalid_policy,
    )

    assert missing["rising_missed_selection_recommendation"] == "unavailable"
    assert missing["rising_missed_selection_score_delta"] == 0.0
    assert invalid["rising_missed_selection_recommendation"] == "unavailable"
    assert invalid["rising_missed_selection_score_delta"] == 0.0


def test_source_signature_and_promotion_reason_fallback_match(tmp_path):
    policy = _write_catalog(
        tmp_path,
        lanes=[
            {
                "prior_key": "signature_prior",
                "recommendation": "recheck_prior",
                "source_signature": "sig_a",
                "observable_prefix": {"source_signature": "sig_a"},
            },
            {
                "prior_key": "promotion_prior",
                "recommendation": "quality_risk",
                "observable_prefix": {"source_signature": "wait6579_gap"},
            },
        ],
    )

    by_signature = rising_missed_selection_prior_fields({"source_signature": "sig_a"}, policy_file=policy)
    by_promotion = rising_missed_selection_prior_fields(
        {"scanner_promotion_reason": "wait6579_gap"},
        policy_file=policy,
    )

    assert by_signature["rising_missed_selection_prior_key"] == "signature_prior"
    assert by_signature["rising_missed_selection_match_type"] == "source_signature"
    assert by_promotion["rising_missed_selection_prior_key"] == "promotion_prior"
    assert by_promotion["rising_missed_selection_match_type"] == "scanner_promotion_reason"


def test_exact_prefix_requires_matching_source_signature_when_present(tmp_path):
    policy = _write_catalog(
        tmp_path,
        lanes=[
            {
                "prior_key": "strict_signature_prior",
                "recommendation": "positive_prior",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                    "source_signature": "sig_required",
                },
            }
        ],
    )

    mismatch = rising_missed_selection_prior_fields(
        {
            "entry_score_parent": "score_mid_recovery",
            "entry_source_parent": "entry_source_wait6579",
            "source_signature": "sig_other",
        },
        policy_file=policy,
    )
    matched = rising_missed_selection_prior_fields(
        {
            "entry_score_parent": "score_mid_recovery",
            "entry_source_parent": "entry_source_wait6579",
            "source_signature": "sig_required",
        },
        policy_file=policy,
    )

    assert mismatch["rising_missed_selection_recommendation"] == "unavailable"
    assert matched["rising_missed_selection_prior_key"] == "strict_signature_prior"
