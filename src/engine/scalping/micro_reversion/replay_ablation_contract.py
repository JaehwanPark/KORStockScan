"""Versioned source-only contracts for micro-reversion replay ablations.

This module owns experiment identity only.  It has no provider client, runtime
consumer, policy selector, broker integration, or order authority.  Legacy
artifacts may omit a design version only when their exact three-arm census
matches the historical design; every current ask-depletion parent must declare
the current design explicitly.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

REPLAY_ABLATION_CONTRACT_SCHEMA = "micro_reversion_replay_ablation_contract_v1"
DESIGN_VERSION_FIELD = "ablation_design_version"

LEGACY_DESIGN_VERSION = "exact_no_micro_vs_micro_prompt_v1"
CURRENT_DESIGN_VERSION = "current_micro_vs_ask_depletion_prompt_v1"
CURRENT_DESIGN_ACTIVATION_DATE = "2026-08-25"

LEGACY_PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA = (
    "micro_reversion_provider_ablation_sample_floor_v1"
)
PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA = (
    "micro_reversion_provider_ablation_sample_floor_v2"
)
# The current three-arm design started on 2026-08-25, but the exact probe and
# residual submitted-quantity lineage required by the Provider sample floor was
# fixed in bridge v1.5 on 2026-08-26.  Earlier current-design materializations
# remain immutable audit evidence and must neither count toward nor poison the
# stricter floor.
PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE = "2026-08-26"
PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS = 30
PROVIDER_ABLATION_FLOOR_REQUIRED_TRADING_DAYS = 5
PROVIDER_ABLATION_FLOOR_REQUIRED_COMMON_PARENTS = 20
PROVIDER_ABLATION_FLOOR_REQUIRED_UNIQUE_SYMBOLS = 10

LEGACY_ARMS = (
    "replay_control_exact_no_micro",
    "replay_control_exact_plus_micro",
    "replay_candidate_exact_plus_micro",
)
CURRENT_ARMS = (
    "replay_control_exact_plus_micro",
    "replay_control_exact_plus_micro_ask_depletion",
    "replay_candidate_exact_plus_micro_ask_depletion",
)

CURRENT_BASE_CONTROL_ARM = CURRENT_ARMS[0]
CURRENT_ASK_CONTROL_ARM = CURRENT_ARMS[1]
CURRENT_ASK_CANDIDATE_ARM = CURRENT_ARMS[2]

# This is deliberately an exact seven-field authority surface.  Metric-role
# metadata belongs to the feature/report contract and must not be confused with
# the absence of runtime, provider, or broker authority recorded here.
SOURCE_ONLY_AUTHORITY_CONTRACT: Mapping[str, bool] = MappingProxyType(
    {
        "runtime_effect": False,
        "runtime_authority": False,
        "order_authority": False,
        "provider_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
)

SOURCE_ONLY_FALSE_AUTHORITY_ALIASES = (
    "selection_authority",
    "sim_effect",
    "trading_runtime_effect",
    "trading_decision_effect",
    "provider_effect",
    "threshold_effect",
    "quantity_effect",
    "provider_or_order_authority",
    "promotion_authority",
    "runtime_candidate_eligible",
    "auto_apply_eligible",
    "provider_route_change_allowed",
)

_MAX_IDENTIFIER_LENGTH = 256
_DESIGN_MARKER = ":ablation:"
_CURRENT_REQUEST_SUFFIX_BY_ARM: Mapping[str, str] = MappingProxyType(
    {
        CURRENT_BASE_CONTROL_ARM: "current-micro-control",
        CURRENT_ASK_CONTROL_ARM: "ask-depletion-control",
        CURRENT_ASK_CANDIDATE_ARM: "ask-depletion-candidate",
    }
)


class ReplayAblationContractError(ValueError):
    """Raised when an ablation identity or authority contract is ambiguous."""


def _bounded_identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ReplayAblationContractError(f"{field}_must_be_bounded_printable")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > _MAX_IDENTIFIER_LENGTH
        or not normalized.isprintable()
    ):
        raise ReplayAblationContractError(f"{field}_must_be_bounded_printable")
    return normalized


def _normalize_arm_census(arms: Iterable[object]) -> tuple[str, str, str]:
    if isinstance(arms, (str, bytes, Mapping)):
        raise ReplayAblationContractError("replay_ablation_arm_census_invalid")
    normalized = tuple(
        _bounded_identifier(value, field="micro_reversion_replay_arm") for value in arms
    )
    if len(normalized) != 3 or len(set(normalized)) != 3:
        raise ReplayAblationContractError("replay_ablation_arm_census_invalid")
    first, second, third = normalized
    return first, second, third


@dataclass(frozen=True, slots=True)
class ComparisonRoleMetadata:
    """One causal comparison inside a frozen three-arm replay design."""

    comparison_role: str
    left_arm: str
    right_arm: str
    changed_axis: str
    source_candidate_role: str

    def __post_init__(self) -> None:
        for field in (
            "comparison_role",
            "left_arm",
            "right_arm",
            "changed_axis",
            "source_candidate_role",
        ):
            _bounded_identifier(getattr(self, field), field=field)
        if self.left_arm == self.right_arm:
            raise ReplayAblationContractError(
                "replay_ablation_comparison_arms_must_differ"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "comparison_role": self.comparison_role,
            "left_arm": self.left_arm,
            "right_arm": self.right_arm,
            "changed_axis": self.changed_axis,
            "source_candidate_role": self.source_candidate_role,
            **SOURCE_ONLY_AUTHORITY_CONTRACT,
        }


@dataclass(frozen=True, slots=True)
class ReplayAblationDesign:
    """Canonical arm census and comparison semantics for one design version."""

    design_version: str
    arms: tuple[str, str, str]
    comparisons: tuple[ComparisonRoleMetadata, ComparisonRoleMetadata]
    legacy_missing_version_allowed: bool = False

    def __post_init__(self) -> None:
        _bounded_identifier(self.design_version, field="design_version")
        normalized_arms = _normalize_arm_census(self.arms)
        if normalized_arms != self.arms:
            raise ReplayAblationContractError(
                "replay_ablation_design_arm_order_not_canonical"
            )
        if len(self.comparisons) != 2:
            raise ReplayAblationContractError(
                "replay_ablation_design_comparison_census_invalid"
            )
        expected_pairs = ((self.arms[0], self.arms[1]), (self.arms[1], self.arms[2]))
        observed_pairs = tuple(
            (comparison.left_arm, comparison.right_arm)
            for comparison in self.comparisons
        )
        if observed_pairs != expected_pairs:
            raise ReplayAblationContractError(
                "replay_ablation_design_comparison_chain_invalid"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": REPLAY_ABLATION_CONTRACT_SCHEMA,
            "design_version": self.design_version,
            "arms": list(self.arms),
            "comparisons": [row.as_dict() for row in self.comparisons],
            "legacy_missing_version_allowed": self.legacy_missing_version_allowed,
            **SOURCE_ONLY_AUTHORITY_CONTRACT,
        }


@dataclass(frozen=True, slots=True)
class ParentDesignCensus:
    """Validated exact request identity for one three-arm parent."""

    parent_id: str
    design_version: str
    request_ids_by_arm: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _bounded_identifier(self.parent_id, field="paired_replay_parent_id")
        design = design_contract_for_version(self.design_version)
        observed_arms = tuple(arm for arm, _request_id in self.request_ids_by_arm)
        if observed_arms != design.arms:
            raise ReplayAblationContractError(
                "replay_ablation_parent_arm_order_invalid"
            )
        request_ids = []
        for arm, request_id in self.request_ids_by_arm:
            _bounded_identifier(arm, field="micro_reversion_replay_arm")
            request_ids.append(
                _bounded_identifier(request_id, field="paired_replay_id")
            )
        if len(request_ids) != len(set(request_ids)):
            raise ReplayAblationContractError(
                "replay_ablation_parent_request_id_duplicate"
            )

    @property
    def arms(self) -> tuple[str, str, str]:
        return design_contract_for_version(self.design_version).arms

    @property
    def request_ids(self) -> tuple[str, str, str]:
        return tuple(request_id for _arm, request_id in self.request_ids_by_arm)

    def as_dict(self) -> dict[str, Any]:
        return {
            "paired_replay_parent_id": self.parent_id,
            DESIGN_VERSION_FIELD: self.design_version,
            "request_ids_by_arm": {
                arm: request_id for arm, request_id in self.request_ids_by_arm
            },
            **SOURCE_ONLY_AUTHORITY_CONTRACT,
        }


LEGACY_DESIGN = ReplayAblationDesign(
    design_version=LEGACY_DESIGN_VERSION,
    arms=LEGACY_ARMS,
    comparisons=(
        ComparisonRoleMetadata(
            comparison_role="micro_context_effect",
            left_arm=LEGACY_ARMS[0],
            right_arm=LEGACY_ARMS[1],
            changed_axis="tactical_micro_reversion_context_only",
            source_candidate_role="diagnostic_feature_ablation",
        ),
        ComparisonRoleMetadata(
            comparison_role="prompt_contract_effect",
            left_arm=LEGACY_ARMS[1],
            right_arm=LEGACY_ARMS[2],
            changed_axis="prompt_and_response_contract_only",
            source_candidate_role="prompt_source_candidate_evidence",
        ),
    ),
    legacy_missing_version_allowed=True,
)

CURRENT_DESIGN = ReplayAblationDesign(
    design_version=CURRENT_DESIGN_VERSION,
    arms=CURRENT_ARMS,
    comparisons=(
        ComparisonRoleMetadata(
            comparison_role="ask_depletion_feature_effect",
            left_arm=CURRENT_ARMS[0],
            right_arm=CURRENT_ARMS[1],
            changed_axis="ask_liquidity_depletion_context_only",
            source_candidate_role="diagnostic_feature_ablation",
        ),
        ComparisonRoleMetadata(
            comparison_role=("prompt_contract_effect_conditional_on_ask_depletion"),
            left_arm=CURRENT_ARMS[1],
            right_arm=CURRENT_ARMS[2],
            changed_axis="prompt_and_response_contract_only",
            source_candidate_role="prompt_source_candidate_evidence",
        ),
    ),
)

_DESIGNS_BY_VERSION: Mapping[str, ReplayAblationDesign] = MappingProxyType(
    {
        LEGACY_DESIGN_VERSION: LEGACY_DESIGN,
        CURRENT_DESIGN_VERSION: CURRENT_DESIGN,
    }
)


def design_contract_for_version(design_version: object) -> ReplayAblationDesign:
    """Return one declared design; unknown or blank versions fail closed."""

    normalized = _bounded_identifier(design_version, field="design_version")
    try:
        return _DESIGNS_BY_VERSION[normalized]
    except KeyError as exc:
        raise ReplayAblationContractError(
            f"replay_ablation_design_version_unknown:{normalized}"
        ) from exc


def arm_set_for_design(design_version: object) -> tuple[str, str, str]:
    """Return the canonical ordered three-arm census for a design version."""

    return design_contract_for_version(design_version).arms


def comparison_roles_for_design(
    design_version: object,
) -> tuple[ComparisonRoleMetadata, ComparisonRoleMetadata]:
    """Return ordered A/B and B/C comparison metadata for one design."""

    return design_contract_for_version(design_version).comparisons


def resolve_replay_ablation_design_version(
    *, declared_design_version: object | None, arms: Iterable[object]
) -> str:
    """Resolve a design from one exact arm census.

    Missing design metadata is accepted only for the exact historical arm set.
    This supports already-written artifacts without allowing current rows to
    silently fall back to legacy semantics.
    """

    normalized_arms = _normalize_arm_census(arms)
    observed = frozenset(normalized_arms)
    if declared_design_version is None:
        if observed == frozenset(LEGACY_ARMS):
            return LEGACY_DESIGN_VERSION
        if observed == frozenset(CURRENT_ARMS):
            raise ReplayAblationContractError(
                "replay_ablation_current_design_version_required"
            )
        raise ReplayAblationContractError("replay_ablation_arm_set_unknown")

    design = design_contract_for_version(declared_design_version)
    if observed != frozenset(design.arms):
        raise ReplayAblationContractError(
            f"replay_ablation_design_arm_set_mismatch:{design.design_version}"
        )
    return design.design_version


def validate_exact_one_design_per_parent(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[ParentDesignCensus, ...]:
    """Validate exact, non-mixed three-arm identities for every parent.

    Different parents may belong to different historical designs so a rolling
    reader can ingest old and new artifacts together.  Within one parent,
    version presence, design version, arm census, and request identity must be
    exact and unambiguous.
    """

    if isinstance(rows, (str, bytes, Mapping)):
        raise ReplayAblationContractError("replay_ablation_rows_invalid")
    materialized = tuple(rows)
    if not materialized:
        raise ReplayAblationContractError("replay_ablation_rows_empty")

    by_parent: dict[str, list[tuple[str, str, object | None]]] = defaultdict(list)
    seen_request_ids: set[str] = set()
    for row in materialized:
        if not isinstance(row, Mapping):
            raise ReplayAblationContractError("replay_ablation_row_not_object")
        parent_id = _bounded_identifier(
            row.get("paired_replay_parent_id"), field="paired_replay_parent_id"
        )
        request_id = _bounded_identifier(
            row.get("paired_replay_id"), field="paired_replay_id"
        )
        arm = _bounded_identifier(
            row.get("micro_reversion_replay_arm"),
            field="micro_reversion_replay_arm",
        )
        if request_id in seen_request_ids:
            raise ReplayAblationContractError("replay_ablation_request_id_duplicate")
        seen_request_ids.add(request_id)
        declared_version = (
            row.get(DESIGN_VERSION_FIELD) if DESIGN_VERSION_FIELD in row else None
        )
        if declared_version is not None:
            declared_version = _bounded_identifier(
                declared_version, field=DESIGN_VERSION_FIELD
            )
        by_parent[parent_id].append((arm, request_id, declared_version))

    bindings: list[ParentDesignCensus] = []
    for parent_id, parent_rows in by_parent.items():
        if len(parent_rows) != 3:
            raise ReplayAblationContractError(
                f"replay_ablation_parent_request_census_invalid:{parent_id}"
            )
        present = [version is not None for _arm, _request_id, version in parent_rows]
        if any(present) and not all(present):
            raise ReplayAblationContractError(
                f"replay_ablation_parent_partial_design_version:{parent_id}"
            )
        declared_versions = {
            str(version)
            for _arm, _request_id, version in parent_rows
            if version is not None
        }
        if len(declared_versions) > 1:
            raise ReplayAblationContractError(
                f"replay_ablation_parent_mixed_design_versions:{parent_id}"
            )
        declared_version = next(iter(declared_versions), None)
        design_version = resolve_replay_ablation_design_version(
            declared_design_version=declared_version,
            arms=(arm for arm, _request_id, _version in parent_rows),
        )
        design = design_contract_for_version(design_version)
        by_arm: dict[str, str] = {}
        for arm, request_id, _version in parent_rows:
            if arm in by_arm:
                raise ReplayAblationContractError(
                    f"replay_ablation_parent_arm_duplicate:{parent_id}:{arm}"
                )
            by_arm[arm] = request_id
        if set(by_arm) != set(design.arms):
            raise ReplayAblationContractError(
                f"replay_ablation_parent_arm_census_invalid:{parent_id}"
            )
        bindings.append(
            ParentDesignCensus(
                parent_id=parent_id,
                design_version=design_version,
                request_ids_by_arm=tuple((arm, by_arm[arm]) for arm in design.arms),
            )
        )
    return tuple(bindings)


def build_current_design_replay_ids(base_parent_id: object) -> ParentDesignCensus:
    """Build bounded, deterministic parent/request IDs for the current design."""

    base = _bounded_identifier(base_parent_id, field="base_parent_id")
    if _DESIGN_MARKER in base:
        raise ReplayAblationContractError(
            "replay_ablation_base_parent_already_versioned"
        )
    digest = hashlib.sha256(
        f"{CURRENT_DESIGN_VERSION}\0{base}".encode("utf-8")
    ).hexdigest()[:24]
    tail = f"{_DESIGN_MARKER}{CURRENT_DESIGN_VERSION}:{digest}"
    longest_request_suffix = max(
        len(value) for value in _CURRENT_REQUEST_SUFFIX_BY_ARM.values()
    )
    maximum_parent_length = _MAX_IDENTIFIER_LENGTH - 1 - longest_request_suffix
    maximum_base_length = maximum_parent_length - len(tail)
    if maximum_base_length <= 0:  # pragma: no cover - constant contract guard
        raise RuntimeError("replay_ablation_identifier_contract_impossible")
    bounded_base = base[:maximum_base_length].rstrip()
    if not bounded_base:
        raise ReplayAblationContractError("replay_ablation_base_parent_not_preservable")
    parent_id = f"{bounded_base}{tail}"
    request_ids_by_arm = tuple(
        (arm, f"{parent_id}:{_CURRENT_REQUEST_SUFFIX_BY_ARM[arm]}")
        for arm in CURRENT_ARMS
    )
    return ParentDesignCensus(
        parent_id=parent_id,
        design_version=CURRENT_DESIGN_VERSION,
        request_ids_by_arm=request_ids_by_arm,
    )


def source_only_authority_findings(value: Mapping[str, Any]) -> tuple[str, ...]:
    """Return missing/conflicting canonical fields and positive aliases."""

    if not isinstance(value, Mapping):
        return ("source_only_authority_not_object",)
    canonical_findings = tuple(
        f"source_only_authority_invalid:{field}"
        for field, expected in SOURCE_ONLY_AUTHORITY_CONTRACT.items()
        if field not in value or value.get(field) is not expected
    )
    alias_findings = tuple(
        f"source_only_authority_alias_invalid:{field}"
        for field in SOURCE_ONLY_FALSE_AUTHORITY_ALIASES
        if field in value and value.get(field) is not False
    )
    return canonical_findings + alias_findings


def validate_source_only_authority(value: Mapping[str, Any]) -> None:
    """Fail closed when any source-only authority field is absent or changed."""

    findings = source_only_authority_findings(value)
    if findings:
        raise ReplayAblationContractError(findings[0])


__all__ = (
    "REPLAY_ABLATION_CONTRACT_SCHEMA",
    "DESIGN_VERSION_FIELD",
    "LEGACY_DESIGN_VERSION",
    "CURRENT_DESIGN_VERSION",
    "CURRENT_DESIGN_ACTIVATION_DATE",
    "LEGACY_PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA",
    "PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA",
    "PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE",
    "PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS",
    "PROVIDER_ABLATION_FLOOR_REQUIRED_TRADING_DAYS",
    "PROVIDER_ABLATION_FLOOR_REQUIRED_COMMON_PARENTS",
    "PROVIDER_ABLATION_FLOOR_REQUIRED_UNIQUE_SYMBOLS",
    "LEGACY_ARMS",
    "CURRENT_ARMS",
    "CURRENT_BASE_CONTROL_ARM",
    "CURRENT_ASK_CONTROL_ARM",
    "CURRENT_ASK_CANDIDATE_ARM",
    "SOURCE_ONLY_AUTHORITY_CONTRACT",
    "SOURCE_ONLY_FALSE_AUTHORITY_ALIASES",
    "ReplayAblationContractError",
    "ComparisonRoleMetadata",
    "ReplayAblationDesign",
    "ParentDesignCensus",
    "LEGACY_DESIGN",
    "CURRENT_DESIGN",
    "design_contract_for_version",
    "arm_set_for_design",
    "comparison_roles_for_design",
    "resolve_replay_ablation_design_version",
    "validate_exact_one_design_per_parent",
    "build_current_design_replay_ids",
    "source_only_authority_findings",
    "validate_source_only_authority",
)
