from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.engine.scalping.micro_reversion import replay_ablation_contract as contract


def _rows_from_binding(
    binding: contract.ParentDesignCensus,
    *,
    include_design_version: bool = True,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for arm, request_id in binding.request_ids_by_arm:
        row: dict[str, object] = {
            "paired_replay_parent_id": binding.parent_id,
            "paired_replay_id": request_id,
            "micro_reversion_replay_arm": arm,
        }
        if include_design_version:
            row[contract.DESIGN_VERSION_FIELD] = binding.design_version
        rows.append(row)
    return rows


def _legacy_rows(*, parent_id: str = "legacy-parent") -> list[dict[str, object]]:
    return [
        {
            "paired_replay_parent_id": parent_id,
            "paired_replay_id": f"{parent_id}:{index}",
            "micro_reversion_replay_arm": arm,
        }
        for index, arm in enumerate(contract.LEGACY_ARMS, start=1)
    ]


def test_source_only_authority_contract_is_exact_immutable_and_fail_closed() -> None:
    assert dict(contract.SOURCE_ONLY_AUTHORITY_CONTRACT) == {
        "runtime_effect": False,
        "runtime_authority": False,
        "order_authority": False,
        "provider_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    assert len(contract.SOURCE_ONLY_AUTHORITY_CONTRACT) == 7
    with pytest.raises(TypeError):
        contract.SOURCE_ONLY_AUTHORITY_CONTRACT[  # type: ignore[index]
            "runtime_effect"
        ] = True

    artifact = {**contract.SOURCE_ONLY_AUTHORITY_CONTRACT, "extra": "allowed"}
    assert contract.source_only_authority_findings(artifact) == ()
    contract.validate_source_only_authority(artifact)

    missing = dict(contract.SOURCE_ONLY_AUTHORITY_CONTRACT)
    missing.pop("provider_authority")
    assert contract.source_only_authority_findings(missing) == (
        "source_only_authority_invalid:provider_authority",
    )
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="source_only_authority_invalid:provider_authority",
    ):
        contract.validate_source_only_authority(missing)

    leaked = {**contract.SOURCE_ONLY_AUTHORITY_CONTRACT, "order_authority": True}
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="source_only_authority_invalid:order_authority",
    ):
        contract.validate_source_only_authority(leaked)


def test_designs_publish_exact_arm_and_comparison_role_metadata() -> None:
    assert contract.arm_set_for_design(contract.LEGACY_DESIGN_VERSION) == (
        "replay_control_exact_no_micro",
        "replay_control_exact_plus_micro",
        "replay_candidate_exact_plus_micro",
    )
    assert contract.arm_set_for_design(contract.CURRENT_DESIGN_VERSION) == (
        "replay_control_exact_plus_micro",
        "replay_control_exact_plus_micro_ask_depletion",
        "replay_candidate_exact_plus_micro_ask_depletion",
    )

    legacy_roles = contract.comparison_roles_for_design(contract.LEGACY_DESIGN_VERSION)
    assert [row.comparison_role for row in legacy_roles] == [
        "micro_context_effect",
        "prompt_contract_effect",
    ]
    current_roles = contract.comparison_roles_for_design(
        contract.CURRENT_DESIGN_VERSION
    )
    assert [row.comparison_role for row in current_roles] == [
        "ask_depletion_feature_effect",
        "prompt_contract_effect_conditional_on_ask_depletion",
    ]
    assert (current_roles[0].left_arm, current_roles[0].right_arm) == (
        contract.CURRENT_BASE_CONTROL_ARM,
        contract.CURRENT_ASK_CONTROL_ARM,
    )
    assert (current_roles[1].left_arm, current_roles[1].right_arm) == (
        contract.CURRENT_ASK_CONTROL_ARM,
        contract.CURRENT_ASK_CANDIDATE_ARM,
    )
    assert current_roles[0].changed_axis == ("ask_liquidity_depletion_context_only")
    assert current_roles[1].changed_axis == "prompt_and_response_contract_only"
    assert current_roles[0].as_dict()["runtime_effect"] is False
    assert current_roles[1].as_dict()["broker_order_forbidden"] is True

    with pytest.raises(FrozenInstanceError):
        current_roles[0].comparison_role = "mutated"  # type: ignore[misc]


def test_arm_resolver_infers_only_exact_legacy_and_requires_current_version() -> None:
    assert (
        contract.resolve_replay_ablation_design_version(
            declared_design_version=None,
            arms=reversed(contract.LEGACY_ARMS),
        )
        == contract.LEGACY_DESIGN_VERSION
    )
    assert (
        contract.resolve_replay_ablation_design_version(
            declared_design_version=contract.CURRENT_DESIGN_VERSION,
            arms=reversed(contract.CURRENT_ARMS),
        )
        == contract.CURRENT_DESIGN_VERSION
    )
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="current_design_version_required",
    ):
        contract.resolve_replay_ablation_design_version(
            declared_design_version=None,
            arms=contract.CURRENT_ARMS,
        )
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="design_arm_set_mismatch",
    ):
        contract.resolve_replay_ablation_design_version(
            declared_design_version=contract.CURRENT_DESIGN_VERSION,
            arms=contract.LEGACY_ARMS,
        )
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="arm_census_invalid",
    ):
        contract.resolve_replay_ablation_design_version(
            declared_design_version=contract.CURRENT_DESIGN_VERSION,
            arms=(contract.CURRENT_ARMS[0],) * 3,
        )
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="design_version_unknown",
    ):
        contract.arm_set_for_design("unknown_design_v1")


def test_exact_parent_validator_accepts_legacy_and_current_without_mixing() -> None:
    current = contract.build_current_design_replay_ids("exact-pair-current")
    rows = _legacy_rows() + _rows_from_binding(current)

    bindings = contract.validate_exact_one_design_per_parent(rows)

    assert [binding.design_version for binding in bindings] == [
        contract.LEGACY_DESIGN_VERSION,
        contract.CURRENT_DESIGN_VERSION,
    ]
    assert bindings[0].arms == contract.LEGACY_ARMS
    assert bindings[1] == current
    assert bindings[1].as_dict()["runtime_authority"] is False


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (
            lambda rows: rows[:-1],
            "parent_request_census_invalid",
        ),
        (
            lambda rows: [
                *rows[:1],
                {**rows[1], contract.DESIGN_VERSION_FIELD: None},
                *rows[2:],
            ],
            "parent_partial_design_version",
        ),
        (
            lambda rows: [
                *rows[:1],
                {
                    **rows[1],
                    contract.DESIGN_VERSION_FIELD: contract.LEGACY_DESIGN_VERSION,
                },
                *rows[2:],
            ],
            "parent_mixed_design_versions",
        ),
        (
            lambda rows: [
                rows[0],
                {
                    **rows[1],
                    "micro_reversion_replay_arm": rows[0]["micro_reversion_replay_arm"],
                },
                rows[2],
            ],
            "arm_census_invalid",
        ),
        (
            lambda rows: [
                rows[0],
                {**rows[1], "paired_replay_id": rows[0]["paired_replay_id"]},
                rows[2],
            ],
            "request_id_duplicate",
        ),
    ],
)
def test_exact_parent_validator_fails_closed_on_ambiguous_census(
    mutate, error: str
) -> None:
    rows = _rows_from_binding(
        contract.build_current_design_replay_ids("ambiguous-parent")
    )
    with pytest.raises(contract.ReplayAblationContractError, match=error):
        contract.validate_exact_one_design_per_parent(mutate(rows))


def test_current_parent_without_explicit_version_is_not_legacy_inferred() -> None:
    current = contract.build_current_design_replay_ids("missing-version-parent")
    rows = _rows_from_binding(current, include_design_version=False)
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="current_design_version_required",
    ):
        contract.validate_exact_one_design_per_parent(rows)


def test_current_design_id_helper_is_bounded_deterministic_and_collision_safe() -> None:
    first = contract.build_current_design_replay_ids("base-parent")
    repeated = contract.build_current_design_replay_ids("base-parent")
    other = contract.build_current_design_replay_ids("base-parent-other")
    long = contract.build_current_design_replay_ids("x" * 256)
    long_same_prefix = contract.build_current_design_replay_ids("x" * 255 + "y")

    assert first == repeated
    assert first.parent_id != other.parent_id
    assert f":ablation:{contract.CURRENT_DESIGN_VERSION}:" in first.parent_id
    assert first.design_version == contract.CURRENT_DESIGN_VERSION
    assert tuple(arm for arm, _request_id in first.request_ids_by_arm) == (
        contract.CURRENT_ARMS
    )
    assert len(set(first.request_ids)) == 3
    assert len(long.parent_id) <= 256
    assert all(len(request_id) <= 256 for request_id in long.request_ids)
    assert long.parent_id != long_same_prefix.parent_id

    validated = contract.validate_exact_one_design_per_parent(_rows_from_binding(first))
    assert validated == (first,)

    with pytest.raises(
        contract.ReplayAblationContractError,
        match="base_parent_already_versioned",
    ):
        contract.build_current_design_replay_ids(first.parent_id)
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="base_parent_id_must_be_bounded_printable",
    ):
        contract.build_current_design_replay_ids("bad\nparent")
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="base_parent_id_must_be_bounded_printable",
    ):
        contract.build_current_design_replay_ids("bad\x7fparent")
    with pytest.raises(
        contract.ReplayAblationContractError,
        match="base_parent_id_must_be_bounded_printable",
    ):
        contract.build_current_design_replay_ids(" padded-parent ")
