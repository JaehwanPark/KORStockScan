"""Swing entry lifecycle policy.

This module keeps swing selection priors separate from submit safety. Score,
VPW, gap, and gatekeeper values are recorded as features; they do not veto the
entry path by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BASELINE_PRIOR_FEATURES = ("score_vpw", "gap", "gatekeeper", "market_regime")


@dataclass(frozen=True)
class SwingEntryLifecyclePolicyResult:
    policy_action: str
    submit_allowed_by_policy: bool
    hard_safety_block: bool
    decision_authority: str
    feature_snapshot: dict[str, Any] = field(default_factory=dict)
    baseline_prior_features: dict[str, Any] = field(default_factory=dict)
    hard_safety_reason: str | None = None
    runtime_effect: bool = False

    def as_log_fields(self) -> dict[str, Any]:
        return {
            "policy_action": self.policy_action,
            "submit_allowed_by_policy": self.submit_allowed_by_policy,
            "hard_safety_block": self.hard_safety_block,
            "hard_safety_reason": self.hard_safety_reason or "-",
            "decision_authority": self.decision_authority,
            "runtime_effect": self.runtime_effect,
            "feature_snapshot": self.feature_snapshot,
            "baseline_prior_features": self.baseline_prior_features,
        }


def evaluate_swing_entry_lifecycle_policy(
    *,
    strategy: str,
    score: float | None = None,
    buy_threshold: float | None = None,
    current_vpw: float | None = None,
    vpw_condition: bool | None = None,
    v_pw_limit: float | None = None,
    gap_pct: float | None = None,
    gap_threshold: float | None = None,
    gatekeeper_action: str | None = None,
    gatekeeper_action_key: str | None = None,
    gatekeeper_allow_entry: bool | None = None,
    market_regime_blocked: bool = False,
    market_regime_reason: str | None = None,
    market_regime_prior_observed: bool = False,
    confirmed_risk_block: bool = False,
    hard_safety_block: bool = False,
    hard_safety_reason: str | None = None,
    source_stage: str | None = None,
    extra_features: dict[str, Any] | None = None,
) -> SwingEntryLifecyclePolicyResult:
    baseline_prior_features = {
        "score_vpw": {
            "score": score,
            "buy_threshold": buy_threshold,
            "current_vpw": current_vpw,
            "vpw_condition": vpw_condition,
            "v_pw_limit": v_pw_limit,
        },
        "gap": {
            "gap_pct": gap_pct,
            "gap_threshold": gap_threshold,
        },
        "gatekeeper": {
            "action": gatekeeper_action or "-",
            "action_key": gatekeeper_action_key or "-",
            "allow_entry": gatekeeper_allow_entry,
        },
        "market_regime": {
            "blocked": bool(market_regime_blocked),
            "reason": market_regime_reason or "-",
            "prior_observed": bool(market_regime_prior_observed),
            "confirmed_risk_block": bool(confirmed_risk_block),
        },
    }
    feature_snapshot = {
        "strategy": strategy,
        "source_stage": source_stage or "-",
        "feature_roles": {
            name: "baseline_prior_feature" for name in BASELINE_PRIOR_FEATURES
        },
        **(extra_features or {}),
    }
    if hard_safety_block:
        return SwingEntryLifecyclePolicyResult(
            policy_action="BLOCK_HARD_SAFETY",
            submit_allowed_by_policy=False,
            hard_safety_block=True,
            hard_safety_reason=hard_safety_reason or "hard_safety_block",
            decision_authority="swing_entry_lifecycle_policy_hard_safety",
            feature_snapshot=feature_snapshot,
            baseline_prior_features=baseline_prior_features,
            runtime_effect=False,
        )
    return SwingEntryLifecyclePolicyResult(
        policy_action="ALLOW_SUBMIT_EVALUATION",
        submit_allowed_by_policy=True,
        hard_safety_block=False,
        hard_safety_reason=None,
        decision_authority="swing_entry_lifecycle_policy_baseline_prior_features",
        feature_snapshot=feature_snapshot,
        baseline_prior_features=baseline_prior_features,
        runtime_effect=True,
    )
