"""Same-day authority gate for one selected lower-price two-leg profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.low_price_two_leg.profiles import (
    PROFILE_REVISION_20260819_EFFECTIVE_DATE,
    PROFILE_REVISION_20260821_EFFECTIVE_DATE,
    PROFILE_REVISION_20260824_EFFECTIVE_DATE,
    PROFILE_REVISION_20260825_EFFECTIVE_DATE,
    PROFILE_REVISION_20260827_EFFECTIVE_DATE,
    PROFILE_REVISION_20260828_EFFECTIVE_DATE,
    PROFILE_REVISION_20260831_EFFECTIVE_DATE,
    PROFILES,
    MachineProfile,
    get_profile,
)
from src.trading.low_price_two_leg.policy_runtime import (
    load_applied_profile_policy,
    operator_policy_transitions,
)
from src.trading.order.episode_quantity import (
    EPISODE_LEG_QUANTITY,
    EPISODE_TOTAL_QUANTITY,
)
from src.trading.order.regular_two_leg_machine import KST
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

AUTHORITY_SCHEMA = "low_price_two_leg_authority_v2"
RESEARCH_REPORT_PATH = (
    DATA_DIR
    / "report"
    / "low_price_two_leg_entry_spot_research"
    / "low_price_two_leg_entry_spot_research_2026-08-10.json"
)
RESEARCH_REPORT_SHA256 = (
    "cff37627ad294efce6dbbe6e5a95f763aa5fbf75fb21164818d4430fd1061105"
)
RESEARCH_EVIDENCE_TOTAL_QUANTITY = 2
EPISODE_RESEARCH_REPORT_PATH = (
    DATA_DIR
    / "report"
    / "low_price_two_leg_episode_policy_research"
    / "low_price_two_leg_episode_policy_research_2026-08-11.json"
)
EPISODE_RESEARCH_REPORT_SHA256 = (
    "1ee1626d4c5e9d0beabcec537aea4ec6714c6913ab29e5cfea7365d11529b469"
)
EPISODE_RESEARCH_PROFILE_IDS = frozenset(
    {
        "mirae_asset_morning",
        "jeju_semiconductor_morning",
        "doosan_enerbility_morning",
        "hanwha_ocean_late_morning",
    }
)
EXPANDED_RESEARCH_REPORT_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-12.json"
)
EXPANDED_RESEARCH_REPORT_SHA256 = (
    "80741f569d0949d042d94fb07022fe843fa931052ccc9073b9f26c7ed23fb2a1"
)
EXPANDED_SOURCE_REPORT_SHA256 = (
    "bec92085a26c70a0a488ecd447530db96fe0119f9b36e2763e13a46ac37bf7f3"
)
EXPANDED_RESEARCH_PROFILE_MAP = {
    "kakao_morning": "candidate_035720_morning",
    "kepco_afternoon": "candidate_015760_afternoon",
    "kakao_late_morning": "candidate_035720_late_morning",
    "sk_eternix_morning": "existing_475150_morning",
    "mirae_asset_midday": "existing_006800_midday",
    "sk_eternix_afternoon": "existing_475150_afternoon",
}
RECOMMENDATION_20260818_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-18.json"
)
RECOMMENDATION_20260818_EVIDENCE_SHA256 = (
    "3f829f002f5ce53615460c55f9fa71211d286c87443794e1bd506f622544d795"
)
RECOMMENDATION_20260818_SOURCE_SHA256 = (
    "cabcb039571d138d16dc3dafad93fb1b564e993856a6966dd858aaed7d214d41"
)
RECOMMENDATION_20260818_PROFILE_MAP = {
    "mirae_asset_midday": "logic_mirae_asset_midday",
    "sk_eternix_morning": "logic_sk_eternix_morning",
    "sk_eternix_midday": "logic_sk_eternix_midday",
    "doosan_enerbility_morning": "logic_doosan_enerbility_morning",
    "mirae_asset_morning": "logic_mirae_asset_morning",
    "kakao_morning": "logic_kakao_morning",
    "samsung_heavy_morning": "existing_010140_morning",
    "kakao_late_morning": "logic_kakao_late_morning",
    "doosan_enerbility_late_morning": "existing_034020_late_morning",
    "kakao_midday": "existing_035720_midday",
    "sk_telecom_afternoon": "candidate_017670_afternoon",
    "samsung_ea_late_morning": "candidate_028050_late_morning",
    "samsung_ea_afternoon": "candidate_028050_afternoon",
    "samsung_ea_morning": "candidate_028050_morning",
}
RECOMMENDATION_20260819_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-19.json"
)
RECOMMENDATION_20260819_EVIDENCE_SHA256 = (
    "3acf5125074eaf7e48eca0e73c22f037b5e6b1ec354bd5b203cf32f14dea2381"
)
RECOMMENDATION_20260819_SOURCE_SHA256 = (
    "cd578fd9c8f4b9cf3f648dd7fbc99f03061e69f1b9de32f78406096aecbfab49"
)
RECOMMENDATION_20260819_PROFILE_MAP = {
    "doosan_enerbility_late_morning": "logic_doosan_enerbility_late_morning",
    "samsung_heavy_morning": "logic_samsung_heavy_morning",
    "kakao_midday": "logic_kakao_midday",
    "kakao_late_morning": "logic_kakao_late_morning",
    "sk_telecom_afternoon": "logic_sk_telecom_afternoon",
    "samsung_ea_morning": "logic_samsung_ea_morning",
    "sk_eternix_afternoon": "logic_sk_eternix_afternoon",
    "samsung_ea_afternoon": "logic_samsung_ea_afternoon",
    "sk_telecom_late_morning": "existing_017670_late_morning",
    "hanse_afternoon": "candidate_105630_afternoon",
    "hanse_morning": "candidate_105630_morning",
}
RECOMMENDATION_20260820_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-20.json"
)
RECOMMENDATION_20260820_EVIDENCE_SHA256 = (
    "36010903a2536f0bd860165e3257eacf967548b68f407522b5fefa54670e86c1"
)
RECOMMENDATION_20260820_SOURCE_SHA256 = (
    "e7bc66d5a2c71bb314f3e6340ddde0ba2ab6902ce9dfc6e01d03f83460f30c53"
)
RECOMMENDATION_20260820_PROFILE_MAP = {
    "doosan_enerbility_late_morning": "logic_doosan_enerbility_late_morning",
    "samsung_heavy_morning": "logic_samsung_heavy_morning",
    "samsung_ea_morning": "logic_samsung_ea_morning",
    "kakao_late_morning": "logic_kakao_late_morning",
    "sk_telecom_afternoon": "logic_sk_telecom_afternoon",
    "cj_cgv_midday": "candidate_079160_midday",
    "cj_cgv_afternoon": "candidate_079160_afternoon",
    "tym_afternoon": "candidate_002900_afternoon",
    "tym_midday": "candidate_002900_midday",
}
RECOMMENDATION_20260821_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-21.json"
)
RECOMMENDATION_20260821_EVIDENCE_SHA256 = (
    "6e25675e9647289bb3313f35dcd8bda9004a17fc7a7c43958f091d3cf18aa0d8"
)
RECOMMENDATION_20260821_SOURCE_SHA256 = (
    "e4350c7e79f82a3bb5e0cc8583adc21f76d0c2e9f1f6a4e198170e070ec52109"
)
RECOMMENDATION_20260821_PROFILE_MAP = {
    "cj_cgv_afternoon": "logic_cj_cgv_afternoon",
    "kepco_afternoon": "logic_kepco_afternoon",
    "tym_midday": "logic_tym_midday",
    "hanse_morning": "logic_hanse_morning",
    "samsung_ea_late_morning": "logic_samsung_ea_late_morning",
    "hanse_afternoon": "logic_hanse_afternoon",
    "cj_cgv_late_morning": "existing_079160_late_morning",
    "kepco_late_morning": "existing_015760_late_morning",
    "kepco_midday": "existing_015760_midday",
    "nhn_afternoon": "candidate_181710_afternoon",
    "youngone_afternoon": "candidate_111770_afternoon",
    "youngone_morning": "candidate_111770_morning",
    "hanse_late_morning": "existing_105630_late_morning",
    "hanse_midday": "existing_105630_midday",
}
RECOMMENDATION_20260824_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-24.json"
)
# Updated only when the immutable evidence projection changes.
RECOMMENDATION_20260824_EVIDENCE_SHA256 = (
    "ce447fe0c6d55a5004f821fb450cbe5d6377fc9664f2bee9a5cd6a31ee12d82f"
)
RECOMMENDATION_20260824_SOURCE_SHA256 = (
    "3d72f239f5d26cad6ffde71ff2fbde622df69a7b8258243e910368e824fb7480"
)
RECOMMENDATION_20260824_PROFILE_MAP = {
    "cj_cgv_late_morning": "logic_cj_cgv_late_morning",
    "kepco_late_morning": "logic_kepco_late_morning",
    "nhn_afternoon": "logic_nhn_afternoon",
    "hanse_afternoon": "logic_hanse_afternoon",
    "youngone_afternoon": "logic_youngone_afternoon",
    "hanse_late_morning": "logic_hanse_late_morning",
    "hanse_midday": "logic_hanse_midday",
    "sk_eternix_late_morning": "existing_475150_late_morning",
    "mirae_asset_late_morning": "existing_006800_late_morning",
    "kepco_morning": "existing_015760_morning",
    "nhn_morning": "existing_181710_morning",
    "nhn_late_morning": "existing_181710_late_morning",
}
RECOMMENDATION_20260826_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-26.json"
)
RECOMMENDATION_20260826_EVIDENCE_SHA256 = (
    "0a7b39dcdf625ed2148bdf7716521e219f70a64f18a9c61892cc67dd42ba6455"
)
RECOMMENDATION_20260826_SOURCE_SHA256 = (
    "3a90bc189c87d6f4a6692c53b0f62d6ab3453286040d858f898a3d15f981350d"
)
RECOMMENDATION_20260826_PROFILE_MAP = {
    "sk_eternix_late_morning": "logic_sk_eternix_late_morning",
    "cj_cgv_late_morning": "logic_cj_cgv_late_morning",
    "mirae_asset_late_morning": "logic_mirae_asset_late_morning",
    "kepco_morning": "logic_kepco_morning",
    "nhn_late_morning": "logic_nhn_late_morning",
    "sk_telecom_late_morning": "logic_sk_telecom_late_morning",
    "hanse_late_morning": "logic_hanse_late_morning",
    "sd_biosensor_morning": "candidate_137310_morning",
    "sd_biosensor_late_morning": "candidate_137310_late_morning",
    "sd_biosensor_midday": "candidate_137310_midday",
    "doosan_enerbility_afternoon": "existing_034020_afternoon",
    "samsung_ea_midday": "existing_028050_midday",
}
RECOMMENDATION_20260827_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-27.json"
)
RECOMMENDATION_20260827_EVIDENCE_SHA256 = (
    "12f750f9d719c8d4042574586ac85823f42a4afb429c239c710302d90847be56"
)
RECOMMENDATION_20260827_SOURCE_SHA256 = (
    "110b09ab2e48907175854dc4720a3532613cfbf37ecf786bcc6eeb58ac408dce"
)
RECOMMENDATION_20260827_PROFILE_MAP = {
    "kepco_late_morning": "logic_kepco_late_morning",
    "cj_cgv_midday": "logic_cj_cgv_midday",
    "mirae_asset_late_morning": "logic_mirae_asset_late_morning",
    "sd_biosensor_late_morning": "logic_sd_biosensor_late_morning",
    "sd_biosensor_morning": "logic_sd_biosensor_morning",
    "hanse_late_morning": "logic_hanse_late_morning",
    "samsung_ea_midday": "logic_samsung_ea_midday",
    "samsung_ea_afternoon": "logic_samsung_ea_afternoon",
    "sk_telecom_morning": "existing_017670_morning",
}
RECOMMENDATION_20260828_EVIDENCE_PATH = (
    DATA_DIR / "config" / "low_price_two_leg_expanded_profile_evidence_2026-08-28.json"
)
RECOMMENDATION_20260828_EVIDENCE_SHA256 = (
    "d5f6e6cb6f80e2fa70c1807f39dc18955060f74d14cdf2111821f1a6b9d1e944"
)
RECOMMENDATION_20260828_SOURCE_SHA256 = (
    "fdd5555eb5dc0a2901153eee5e674293d83359676a1850f84f2fb9abff578c34"
)
RECOMMENDATION_20260828_PROFILE_MAP = {
    "cj_cgv_midday": "logic_cj_cgv_midday",
    "mirae_asset_late_morning": "logic_mirae_asset_late_morning",
    "nhn_morning": "logic_nhn_morning",
    "tym_midday": "logic_tym_midday",
    "sk_telecom_morning": "logic_sk_telecom_morning",
    "fan_ocean_morning": "candidate_028670_morning",
    "fan_ocean_late_morning": "candidate_028670_late_morning",
}


def _research_evidence_contract(
    profile: MachineProfile, *, target_date: date | None = None
) -> dict:
    recommendation_20260828_profile_id = (
        RECOMMENDATION_20260828_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260831_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260828_profile_id:
        return {
            "path": RECOMMENDATION_20260828_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260828_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v6",
            "start_date": "2026-06-05",
            "end_date": "2026-08-28",
            "trading_date_count": 59,
            "window": "2026-06-05_through_2026-08-28_59_trading_days",
            "report_profile_id": recommendation_20260828_profile_id,
            "source_report_sha256": RECOMMENDATION_20260828_SOURCE_SHA256,
        }
    recommendation_20260827_profile_id = (
        RECOMMENDATION_20260827_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260828_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260827_profile_id:
        return {
            "path": RECOMMENDATION_20260827_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260827_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v6",
            "start_date": "2026-06-05",
            "end_date": "2026-08-27",
            "trading_date_count": 58,
            "window": "2026-06-05_through_2026-08-27_58_trading_days",
            "report_profile_id": recommendation_20260827_profile_id,
            "source_report_sha256": RECOMMENDATION_20260827_SOURCE_SHA256,
        }
    recommendation_20260826_profile_id = (
        RECOMMENDATION_20260826_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260827_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260826_profile_id:
        return {
            "path": RECOMMENDATION_20260826_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260826_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v6",
            "start_date": "2026-06-05",
            "end_date": "2026-08-26",
            "trading_date_count": 57,
            "window": "2026-06-05_through_2026-08-26_57_trading_days",
            "report_profile_id": recommendation_20260826_profile_id,
            "source_report_sha256": RECOMMENDATION_20260826_SOURCE_SHA256,
        }
    recommendation_20260824_profile_id = (
        RECOMMENDATION_20260824_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260825_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260824_profile_id:
        return {
            "path": RECOMMENDATION_20260824_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260824_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v6",
            "start_date": "2026-06-05",
            "end_date": "2026-08-24",
            "trading_date_count": 55,
            "window": "2026-06-05_through_2026-08-24_55_trading_days",
            "report_profile_id": recommendation_20260824_profile_id,
            "source_report_sha256": RECOMMENDATION_20260824_SOURCE_SHA256,
        }
    recommendation_20260821_profile_id = (
        RECOMMENDATION_20260821_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260824_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260821_profile_id:
        return {
            "path": RECOMMENDATION_20260821_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260821_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v5",
            "start_date": "2026-06-05",
            "end_date": "2026-08-21",
            "trading_date_count": 54,
            "window": "2026-06-05_through_2026-08-21_54_trading_days",
            "report_profile_id": recommendation_20260821_profile_id,
            "source_report_sha256": RECOMMENDATION_20260821_SOURCE_SHA256,
        }
    recommendation_20260820_profile_id = (
        RECOMMENDATION_20260820_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260821_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260820_profile_id:
        return {
            "path": RECOMMENDATION_20260820_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260820_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v4",
            "start_date": "2026-06-05",
            "end_date": "2026-08-20",
            "trading_date_count": 53,
            "window": "2026-06-05_through_2026-08-20_53_trading_days",
            "report_profile_id": recommendation_20260820_profile_id,
            "source_report_sha256": RECOMMENDATION_20260820_SOURCE_SHA256,
        }
    recommendation_20260819_profile_id = (
        RECOMMENDATION_20260819_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260821_EFFECTIVE_DATE
        else None
    )
    if recommendation_20260819_profile_id:
        return {
            "path": RECOMMENDATION_20260819_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260819_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v3",
            "start_date": "2026-06-05",
            "end_date": "2026-08-19",
            "trading_date_count": 52,
            "window": "2026-06-05_through_2026-08-19_52_trading_days",
            "report_profile_id": recommendation_20260819_profile_id,
            "source_report_sha256": RECOMMENDATION_20260819_SOURCE_SHA256,
        }
    recommendation_profile_id = (
        RECOMMENDATION_20260818_PROFILE_MAP.get(profile.profile_id)
        if target_date is None
        or target_date >= PROFILE_REVISION_20260819_EFFECTIVE_DATE
        else None
    )
    if recommendation_profile_id:
        return {
            "path": RECOMMENDATION_20260818_EVIDENCE_PATH,
            "sha256": RECOMMENDATION_20260818_EVIDENCE_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v2",
            "start_date": "2026-06-05",
            "end_date": "2026-08-18",
            "trading_date_count": 51,
            "window": "2026-06-05_through_2026-08-18_51_trading_days",
            "report_profile_id": recommendation_profile_id,
            "source_report_sha256": RECOMMENDATION_20260818_SOURCE_SHA256,
        }
    expanded_profile_id = EXPANDED_RESEARCH_PROFILE_MAP.get(profile.profile_id)
    if expanded_profile_id:
        return {
            "path": EXPANDED_RESEARCH_REPORT_PATH,
            "sha256": EXPANDED_RESEARCH_REPORT_SHA256,
            "schema": "low_price_two_leg_user_approved_profile_evidence_v1",
            "start_date": "2026-06-05",
            "end_date": "2026-08-12",
            "trading_date_count": 48,
            "window": "2026-06-05_through_2026-08-12_48_trading_days",
            "report_profile_id": expanded_profile_id,
            "source_report_sha256": EXPANDED_SOURCE_REPORT_SHA256,
        }
    if profile.profile_id in EPISODE_RESEARCH_PROFILE_IDS:
        return {
            "path": EPISODE_RESEARCH_REPORT_PATH,
            "sha256": EPISODE_RESEARCH_REPORT_SHA256,
            "schema": "low_price_two_leg_episode_policy_research_v1",
            "start_date": "2026-06-05",
            "end_date": "2026-08-11",
            "trading_date_count": 47,
            "window": "2026-06-05_through_2026-08-11_47_trading_days",
            "report_profile_id": profile.profile_id,
        }
    return {
        "path": RESEARCH_REPORT_PATH,
        "sha256": RESEARCH_REPORT_SHA256,
        "schema": "low_price_two_leg_entry_spot_research_v1",
        "start_date": "2026-06-05",
        "end_date": "2026-08-10",
        "trading_date_count": 46,
        "window": "2026-06-05_through_2026-08-10_46_trading_days",
        "report_profile_id": profile.profile_id,
    }


def default_authority_path(profile: MachineProfile) -> Path:
    return (
        DATA_DIR
        / "runtime"
        / "low_price_two_leg"
        / f"{profile.profile_id}_authority.json"
    )


@dataclass(frozen=True)
class PreflightDecision:
    ready: bool
    target_date: str
    profile_id: str
    symbol: str
    session: str
    main_bot_active: bool
    shared_token_available: bool
    operator_exclusion_source: str
    research_evidence_ready: bool
    applied_policy_ready: bool
    applied_policy_hash: str
    independent_order_ledger_required: bool
    blockers: tuple[str, ...]


def validate_research_evidence(
    profile: MachineProfile,
    path: Path | None = None,
    *,
    expected_sha256: str | None = None,
    target_date: date | None = None,
) -> tuple[bool, str]:
    contract = _research_evidence_contract(profile, target_date=target_date)
    try:
        evidence_profile = (
            profile
            if target_date is None
            else get_profile(profile.profile_id, target_date=target_date)
        )
    except ValueError:
        return False, "research_profile_not_effective_for_target_date"
    report_path = Path(path or contract["path"])
    expected_digest = str(expected_sha256 or contract["sha256"])
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"research_report_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict):
        return False, "research_report_contract_invalid"
    canonical_sha256 = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    if (
        payload.get("start_date") != contract["start_date"]
        or payload.get("end_date") != contract["end_date"]
        or canonical_sha256 != expected_digest
        or payload.get("runtime_effect") is not False
        or payload.get("allowed_runtime_apply") is not False
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
    ):
        return False, "research_report_provenance_invalid"
    schema = str(payload.get("schema") or "")
    if schema not in {
        "low_price_two_leg_entry_spot_research_v1",
        "low_price_two_leg_episode_policy_research_v1",
        "low_price_two_leg_user_approved_profile_evidence_v1",
        "low_price_two_leg_user_approved_profile_evidence_v2",
        "low_price_two_leg_user_approved_profile_evidence_v3",
        "low_price_two_leg_user_approved_profile_evidence_v4",
        "low_price_two_leg_user_approved_profile_evidence_v5",
        "low_price_two_leg_user_approved_profile_evidence_v6",
    }:
        return False, "research_report_schema_invalid"
    source = (payload.get("source_meta") or {}).get(evidence_profile.symbol)
    report_profile_id = str(contract["report_profile_id"])
    result = (payload.get("profiles") or {}).get(report_profile_id)
    if not isinstance(source, dict):
        return False, "research_profile_result_missing"
    policy = evidence_profile.policy
    expected_spot = {
        "scan_start": policy.scan_start.strftime("%H:%M"),
        "scan_end": policy.scan_last_bar.strftime("%H:%M"),
        "lookback_bars": policy.lookback_bars,
        "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
        "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
    }
    if schema == "low_price_two_leg_user_approved_profile_evidence_v6":
        source_report = payload.get("source_report")
        if (
            not isinstance(source_report, dict)
            or source_report.get("schema")
            != "low_price_two_leg_expanded_candidate_research_v5"
            or source_report.get("canonical_sha256")
            != contract.get("source_report_sha256")
        ):
            return False, "research_source_report_provenance_invalid"
        recommendations = {
            str(row.get("profile_id") or ""): row
            for row in payload.get("recommendations") or []
            if isinstance(row, dict)
        }
        recommendation = recommendations.get(report_profile_id)
        expected_policy = {
            **expected_spot,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        if not isinstance(recommendation, dict):
            return False, "research_profile_result_missing"
        calibration = recommendation.get("calibration")
        full = recommendation.get("full")
        holdout = recommendation.get("holdout")
        result_policy_matches = (
            recommendation.get("recommended_spot") == expected_policy
        )
        decision_ready = bool(
            recommendation.get("symbol") == evidence_profile.symbol
            and recommendation.get("session") == evidence_profile.session
            and recommendation.get("implementation_status")
            == "source_only_requires_review_and_user_approval"
            and recommendation.get("runtime_effect") is False
            and float(recommendation.get("calibration_first_half_ev_pct", 0.0) or 0.0)
            > 0.0
            and float(recommendation.get("calibration_second_half_ev_pct", 0.0) or 0.0)
            > 0.0
            and isinstance(calibration, dict)
            and int(calibration.get("signal_episodes", 0) or 0) >= 6
            and int(calibration.get("completed_legs", 0) or 0) >= 8
            and float(calibration.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(full, dict)
            and int(full.get("completed_legs", 0) or 0) >= 10
            and float(full.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(holdout, dict)
            and int(holdout.get("signal_episodes", 0) or 0) >= 3
            and int(holdout.get("completed_legs", 0) or 0) >= 4
            and float(holdout.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
        )
    elif schema == "low_price_two_leg_entry_spot_research_v1":
        if not isinstance(result, dict):
            return False, "research_profile_result_missing"
        holdout = (result.get("selected") or {}).get("holdout")
        result_policy_matches = result.get("recommended_spot") == expected_spot
        decision_ready = result.get("decision") in {
            "holdout_pass_source_only_early_candidate",
            "holdout_positive_not_better_keep_baseline",
        }
    elif schema == "low_price_two_leg_episode_policy_research_v1":
        if not isinstance(result, dict):
            return False, "research_profile_result_missing"
        expected_policy = {
            **expected_spot,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
            # Historical clean-baseline replay was generated at two shares.
            # The user-directed runtime size does not rewrite source evidence.
            "quantity": RESEARCH_EVIDENCE_TOTAL_QUANTITY,
            "route": policy.route,
        }
        result_policy = dict(result.get("policy") or {})
        holdout = result.get("holdout")
        calibration = result.get("calibration")
        full = result.get("full")
        half_ev = result.get("calibration_half_ev_pct")
        third_ev = result.get("calibration_third_ev_pct")
        result_policy_matches = result_policy == expected_policy
        decision_ready = bool(
            result.get("decision") == "holdout_pass_user_approved_live_profile"
            and isinstance(calibration, dict)
            and int(calibration.get("signal_episodes", 0) or 0) >= 6
            and int(calibration.get("completed_legs", 0) or 0) >= 8
            and int(calibration.get("held_legs", 0) or 0) == 0
            and float(calibration.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(full, dict)
            and int(full.get("completed_legs", 0) or 0) >= 10
            and int(full.get("held_legs", 0) or 0) == 0
            and isinstance(half_ev, list)
            and len(half_ev) == 2
            and all(float(value) > 0.0 for value in half_ev)
            and isinstance(third_ev, list)
            and len(third_ev) == 3
            and all(float(value) > 0.0 for value in third_ev)
        )
    else:
        if not isinstance(result, dict):
            return False, "research_profile_result_missing"
        source_report = payload.get("source_report")
        if (
            not isinstance(source_report, dict)
            or source_report.get("schema")
            != "low_price_two_leg_expanded_candidate_research_v5"
            or source_report.get("canonical_sha256")
            != contract.get("source_report_sha256")
        ):
            return False, "research_source_report_provenance_invalid"
        expected_policy = {
            **expected_spot,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "entry_valid_completed_bars": policy.entry_valid_completed_bars,
            "target_ticks": policy.target_ticks,
        }
        holdout = (result.get("selected") or {}).get("holdout")
        calibration = (result.get("selected") or {}).get("calibration")
        full = (result.get("selected") or {}).get("full")
        recommendations = {
            str(row.get("profile_id") or ""): row
            for row in payload.get("recommendations") or []
            if isinstance(row, dict)
        }
        recommendation = recommendations.get(report_profile_id)
        first_half = (result.get("selected") or {}).get("calibration_first_half")
        second_half = (result.get("selected") or {}).get("calibration_second_half")
        result_policy_matches = result.get("recommended_spot") == expected_policy
        decision_ready = bool(
            result.get("decision") == "holdout_pass_source_only_early_candidate"
            and isinstance(recommendation, dict)
            and recommendation.get("symbol") == evidence_profile.symbol
            and recommendation.get("session") == evidence_profile.session
            and recommendation.get("recommended_spot") == expected_policy
            and recommendation.get("implementation_status")
            == "source_only_requires_review_and_user_approval"
            and recommendation.get("runtime_effect") is False
            and isinstance(first_half, dict)
            and float(first_half.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(second_half, dict)
            and float(second_half.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(calibration, dict)
            and int(calibration.get("signal_episodes", 0) or 0) >= 6
            and int(calibration.get("completed_legs", 0) or 0) >= 8
            and float(calibration.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
            and isinstance(full, dict)
            and int(full.get("completed_legs", 0) or 0) >= 10
            and float(full.get("notional_weighted_ev_pct", 0.0) or 0.0) > 0.0
        )
        if isinstance(holdout, dict):
            held_rate = float(holdout.get("held_leg_rate_per_filled_leg", 0.0) or 0.0)
            held_mark = holdout.get("active_unrealized_notional_weighted_pct")
            decision_ready = bool(
                decision_ready
                and 0.0 <= held_rate <= 0.25
                and (held_mark is None or float(held_mark) >= -3.0)
                and isinstance(recommendation, dict)
                and int(recommendation.get("holdout_held_legs", -1) or 0)
                == int(holdout.get("held_legs", -2) or 0)
                and float(
                    recommendation.get("holdout_held_leg_rate_per_filled_leg", -1.0)
                    or 0.0
                )
                == held_rate
            )
    if (
        source.get("source_quality_status") != "PASS"
        or int(source.get("trading_date_count", 0) or 0)
        != int(contract["trading_date_count"])
        or int(source.get("invalid_row_count", 0) or 0) != 0
        or int(source.get("duplicate_row_count", 0) or 0) != 0
        or not result_policy_matches
        or not decision_ready
        or not isinstance(holdout, dict)
        or int(holdout.get("signal_episodes", 0) or 0) < 3
        or int(holdout.get("completed_legs", 0) or 0) < 4
        or (
            schema
            not in {
                "low_price_two_leg_user_approved_profile_evidence_v1",
                "low_price_two_leg_user_approved_profile_evidence_v2",
                "low_price_two_leg_user_approved_profile_evidence_v3",
                "low_price_two_leg_user_approved_profile_evidence_v4",
                "low_price_two_leg_user_approved_profile_evidence_v5",
                "low_price_two_leg_user_approved_profile_evidence_v6",
            }
            and int(holdout.get("held_legs", 0) or 0) != 0
        )
        or float(holdout.get("notional_weighted_ev_pct", 0.0) or 0.0) <= 0.0
    ):
        return False, "research_profile_result_not_eligible"
    return True, "ready"


def evaluate_preflight(
    *,
    target_date: date,
    profile: MachineProfile,
    main_bot_active: bool,
    shared_token_available: bool,
    operator_exclusion_source: str,
    research_evidence_ready: bool,
    applied_policy_ready: bool,
    applied_policy_hash: str,
) -> PreflightDecision:
    blockers: list[str] = []
    if not main_bot_active:
        blockers.append("main_bot_inactive")
    if not shared_token_available:
        blockers.append("shared_token_unavailable")
    if not operator_exclusion_source:
        blockers.append("manual_operator_exclusion_missing")
    if not research_evidence_ready:
        blockers.append("research_evidence_invalid")
    if not applied_policy_ready or not applied_policy_hash:
        blockers.append("exact_date_applied_policy_invalid")
    return PreflightDecision(
        not blockers,
        target_date.isoformat(),
        profile.profile_id,
        profile.symbol,
        profile.session,
        bool(main_bot_active),
        bool(shared_token_available),
        str(operator_exclusion_source or ""),
        bool(research_evidence_ready),
        bool(applied_policy_ready),
        str(applied_policy_hash or ""),
        True,
        tuple(blockers),
    )


def _policy_contract(
    profile: MachineProfile,
    applied_policy: dict,
    applied_policy_hash: str,
    *,
    target_date: date,
) -> dict:
    effective_profile = get_profile(profile.profile_id, target_date=target_date)
    policy = effective_profile.policy
    contract = {
        "profile_id": profile.profile_id,
        "symbol": effective_profile.symbol,
        "name": effective_profile.name,
        "session": effective_profile.session,
        "quantity": EPISODE_TOTAL_QUANTITY,
        "allocation": {
            "leg_quantity": EPISODE_LEG_QUANTITY,
            "entry_offsets_ticks": list(policy.entry_offsets_ticks),
            "leg_ids": list(policy.entry_leg_ids),
        },
        "market": "SOR_regular_integrated",
        "scan_start": policy.scan_start.isoformat(),
        "scan_last_bar": policy.scan_last_bar.isoformat(),
        "lookback_bars": int(applied_policy["lookback_bars"]),
        "rolling_high_drawdown_pct": float(applied_policy["rolling_high_drawdown_pct"]),
        "rolling_low_proximity_pct": float(applied_policy["rolling_low_proximity_pct"]),
        "entry_valid_completed_bars": int(applied_policy["entry_valid_completed_bars"]),
        "target_ticks": int(applied_policy["target_ticks"]),
        "applied_policy_hash": applied_policy_hash,
        "stop_loss": "none",
        "unfilled_target": "hold_position_without_forced_exit",
        "relationship": "parallel_independent_strategy_and_order_ledger",
    }
    transitions = [
        transition
        for transition in operator_policy_transitions(target_date)
        if transition["profile_id"] == profile.profile_id
    ]
    if transitions:
        contract["target_ticks_authority"] = transitions[0]["decision_authority"]
        contract["target_ticks_baseline"] = policy.target_ticks
        contract["target_ticks_transition"] = transitions[0]
    return contract


def build_authority_artifact(
    decision: PreflightDecision,
    *,
    profile: MachineProfile,
    applied_policy: dict,
    applied_policy_hash: str,
    observed_at: datetime,
) -> dict:
    if not decision.ready:
        raise ValueError("preflight_not_ready")
    observed_at = observed_at.astimezone(KST)
    target_date = date.fromisoformat(decision.target_date)
    research = _research_evidence_contract(profile, target_date=target_date)
    return {
        "schema": AUTHORITY_SCHEMA,
        "status": "ready",
        "target_date": decision.target_date,
        "observed_at_kst": observed_at.isoformat(),
        "valid_until_kst": datetime.combine(
            date.fromisoformat(decision.target_date), time(23, 59, 59), tzinfo=KST
        ).isoformat(),
        "decision": asdict(decision),
        "policy": _policy_contract(
            profile,
            applied_policy,
            applied_policy_hash,
            target_date=target_date,
        ),
        "evidence": {
            "path": str(research["path"]),
            "report_sha256": str(research["sha256"]),
            "schema": str(research["schema"]),
            "window": str(research["window"]),
            "cost_pct": 0.20,
        },
        "metric_role": "operator_runtime_authority_gate",
        "decision_authority": "explicit_user_directed_low_price_two_leg_live_implementation",
        "window_policy": "target_date_profile_once_then_terminal_or_held",
        "sample_floor": (
            "explicit_user_selected_"
            f"{research['trading_date_count']}_trading_day_clean_baseline_source_replay"
        ),
        "primary_decision_metric": "runtime_contract_and_profile_evidence_ready",
        "source_quality_gate": "PASS",
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": False,
        "rollback": {
            "trigger": "ambiguous broker write, unresolved owned order or position, source contract failure, or two-leg contract breach",
            "action": f"fail_closed_and_disable_only_{profile.profile_id}",
            "other_machine_effect": "none",
        },
        "forbidden_uses": [
            "quantity_above_twenty_or_leg_quantity_above_ten",
            "non_sor_regular_route",
            "hard_safety_or_global_buy_pause_bypass",
            "use_other_machine_orders_or_positions_as_this_profile_ledger",
            "cancel_or_sell_other_machine_owned_orders_or_quantity",
            "target_timeout_cancel",
            "forced_exit_or_stop_loss",
            "symbol_or_session_not_in_immutable_profile_allowlist",
        ],
    }


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o640)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def validate_authority(
    *,
    profile: MachineProfile,
    path: Path | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    now = (now or datetime.now(tz=KST)).astimezone(KST)
    authority_path = Path(path or default_authority_path(profile))
    try:
        payload = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"authority_unreadable:{type(exc).__name__}"
    if not isinstance(payload, dict) or payload.get("schema") != AUTHORITY_SCHEMA:
        return False, "authority_schema_invalid"
    if (
        payload.get("status") != "ready"
        or payload.get("target_date") != now.date().isoformat()
    ):
        return False, "authority_not_ready_or_target_date_mismatch"
    try:
        valid_until = datetime.fromisoformat(str(payload.get("valid_until_kst") or ""))
    except ValueError:
        return False, "authority_expiry_invalid"
    if valid_until.tzinfo is None or now > valid_until.astimezone(KST):
        return False, "authority_expired"
    decision = payload.get("decision")
    if (
        not isinstance(decision, dict)
        or decision.get("ready") is not True
        or decision.get("profile_id") != profile.profile_id
        or decision.get("symbol") != profile.symbol
        or decision.get("session") != profile.session
        or decision.get("independent_order_ledger_required") is not True
        or decision.get("research_evidence_ready") is not True
        or decision.get("applied_policy_ready") is not True
        or not decision.get("applied_policy_hash")
        or not decision.get("operator_exclusion_source")
    ):
        return False, "authority_decision_contract_invalid"
    applied_policy, applied_hash, applied_reason = load_applied_profile_policy(
        profile.profile_id, target_date=now.date()
    )
    if applied_policy is None:
        return False, f"authority_applied_policy_{applied_reason}"
    if payload.get("policy") != _policy_contract(
        profile, applied_policy, applied_hash, target_date=now.date()
    ):
        return False, "authority_policy_mismatch"
    evidence = payload.get("evidence")
    research = _research_evidence_contract(profile, target_date=now.date())
    if (
        not isinstance(evidence, dict)
        or evidence.get("path") != str(research["path"])
        or evidence.get("report_sha256") != research["sha256"]
        or evidence.get("schema") != research["schema"]
        or evidence.get("window") != research["window"]
    ):
        return False, "authority_evidence_mismatch"
    if any(
        key in payload.get("policy", {})
        for key in ("max_hold_minutes", "target_timeout", "stop_price")
    ):
        return False, "authority_forced_exit_policy_forbidden"
    evidence_ready, evidence_reason = validate_research_evidence(
        profile, target_date=now.date()
    )
    if not evidence_ready:
        return False, f"authority_research_evidence_{evidence_reason}"
    return True, "ready"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--target-date", default=None)
    parser.add_argument("--authority-path", type=Path, default=None)
    parser.add_argument("--main-bot-active", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    observed_at = datetime.now(tz=KST)
    target_date = (
        date.fromisoformat(args.target_date) if args.target_date else observed_at.date()
    )
    try:
        profile = get_profile(args.profile, target_date=target_date)
    except ValueError:
        print(
            json.dumps(
                {
                    "decision": {
                        "ready": False,
                        "target_date": target_date.isoformat(),
                        "profile_id": args.profile,
                        "blockers": ["profile_not_effective_for_target_date"],
                    }
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    evidence_ready, evidence_reason = validate_research_evidence(
        profile, target_date=target_date
    )
    applied_policy, applied_hash, applied_reason = load_applied_profile_policy(
        profile.profile_id, target_date=target_date
    )
    decision = evaluate_preflight(
        target_date=target_date,
        profile=profile,
        main_bot_active=args.main_bot_active,
        shared_token_available=bool(kiwoom_utils.get_cached_kiwoom_token()),
        operator_exclusion_source=manual_control_operator_exclusion_source(
            profile.symbol
        ),
        research_evidence_ready=evidence_ready,
        applied_policy_ready=applied_policy is not None,
        applied_policy_hash=applied_hash,
    )
    authority_path = args.authority_path or default_authority_path(profile)
    output = {
        "decision": asdict(decision),
        "evidence_reason": evidence_reason,
        "applied_policy_reason": applied_reason,
        "authority_path": str(authority_path),
    }
    if decision.ready and args.write:
        if applied_policy is None:
            raise RuntimeError("ready_preflight_missing_applied_policy")
        output["artifact"] = build_authority_artifact(
            decision,
            profile=profile,
            applied_policy=applied_policy,
            applied_policy_hash=applied_hash,
            observed_at=observed_at,
        )
        _atomic_write(authority_path, output["artifact"])
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
