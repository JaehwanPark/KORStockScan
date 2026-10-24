"""Registered native-minute follow-up remains separate from policy/economics."""

from contextlib import closing
import json
import sqlite3

import pytest

from src.engine.automation import main_trailing_followup_research as followup
from src.engine.automation import main_trailing_minute_path_diagnostics as minute
from src.engine.automation.runtime_policy_bootstrap import _digest_json
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.lifecycle.research_input_budget import health
from src.engine.scalping.trailing_mechanical_policy import baseline_receipt
from src.tests.test_main_trailing_minute_path_diagnostics import (
    DAY,
    ISO_DAY,
    bars,
    clock,
    publish,
    seal,
    source_manifest,
)


def inputs(tmp_path, positions=None):
    source, root, manifest_path = source_manifest(tmp_path, positions)
    manifest = json.loads(manifest_path.read_text())
    receipt = baseline_receipt({}, source="operator_directed_m1_baseline")
    parent = dict(target_date=ISO_DAY, scalp_trailing_mechanical_policy_receipt=receipt)
    parent["manifest_sha256"] = _digest_json(parent)
    (root / "parent.json").write_text(json.dumps(parent))
    manifest.update(
        approved_parent_receipt=receipt,
        approved_parent_source=dict(
            path="parent.json", sha256=byte_generation(root / "parent.json")["sha256"]
        ),
        assembly_code_contract_sha256=followup.owner.code_contract(),
        consumed_dates=["2026-10-14", ISO_DAY],
        universe=[
            dict(symbol="005930", known_at=clock("08:00:00"), tradable=True),
            dict(symbol="000660", known_at=clock("08:00:00"), tradable=True),
        ],
        universe_source_sha256="a" * 64,
        coverage={},
        operating=[],
    )
    manifest.pop("artifact_sha256")
    seal(manifest_path, manifest)
    registration_path = tmp_path / "registration.json"
    seal(
        registration_path,
        dict(
            schema=followup.REGISTRATION_SCHEMA,
            input_manifest_path=str(manifest_path),
            input_manifest_generation=byte_generation(manifest_path),
            source_date=ISO_DAY,
            target_date="2026-10-16",
            as_of=clock(),
            landmarks_seconds=list(followup.LANDMARKS),
            horizon_minutes=list(followup.HORIZONS),
            modeled_cost_rate=0.0023,
            target_net_pct=0.4,
            comparison_loss_net_pct=-3,
            outcome_window=followup.OUTCOME_WINDOW,
            decision_authority="report_only",
            prefix_window="entry_to_landmark_completed_bars_only",
            path_geometry_labels=followup.GEOMETRY_LABELS,
            split_contract=followup.SPLIT_CONTRACT,
            holdout_start_date=ISO_DAY,
            holdout_end_date=ISO_DAY,
            allowed_runtime_apply=False,
            runtime_effect=False,
            actual_pid_consumed=False,
        ),
    )
    return source, root, manifest_path, registration_path, tmp_path / "out"


def run_fixture(paths):
    source, root, manifest, registration, out = paths
    return followup.run(
        registration, manifest, input_root=root, data_root=source, output_root=out
    )


def result_rows(paths, result):
    return {
        row["identity"]: row for row in storage.iter_tree(paths[-1], result["rows_ref"])
    }


@pytest.mark.parametrize(
    "low,high,label",
    [
        (98, 100, "below_break_even"),
        (101, 103, "at_or_above_break_even"),
        (99, 102, "mixed"),
    ],
)
def test_completed_prefix_geometry_has_no_direction_or_runtime_claim(low, high, label):
    at = clock("09:00:00")
    window = followup.completed_window(100, [(at, low, high)], at, at + 60)
    assert followup.prefix_geometry(window) == label
    assert window["full_interval_observed"]
    assert not window["intrabar_order_known"]


def test_partial_minutes_missing_bars_and_empty_thirty_seconds_are_retained():
    at = clock("09:00:30")
    window = followup.completed_window(100, [(clock("09:00:00"), 1, 999)], at, at + 30)
    assert (
        window["expected_completed_bar_count"]
        == window["observed_completed_bar_count"]
        == 0
    )
    assert followup.prefix_geometry(window) == "no_full_bar"
    assert window["net_high_bound_pct"] is None and not window["full_interval_observed"]
    gap = followup.completed_window(100, [(clock("09:01:00"), 98, 103)], at, at + 180)
    assert (
        gap["expected_completed_bar_count"] == 2
        and gap["missing_completed_bar_count"] == 1
    )
    assert gap["leading_unobserved_seconds"] == gap["trailing_unobserved_seconds"] == 30
    assert followup.prefix_geometry(gap) == "gap"


def test_same_bar_contact_is_ambiguous_even_when_both_bounds_are_known():
    at = clock("09:00:00")
    window = followup.completed_window(100, [(at, 96, 103)], at, at + 60)
    assert window["target_in_observed_completed_bars"] is True
    assert window["comparison_loss_in_observed_completed_bars"] is True
    assert window["observed_contact_order"] == "same_first_bar_ambiguous"
    assert window["both_levels_same_bar_count"] == 1
    assert not window["intrabar_order_known"]


def test_prefix_never_sees_later_outcome_and_landmark_end_uses_entry_horizon():
    at = clock("09:00:00")
    row = dict(entry_at=at, reference_price=100, landmarks=[])
    source = dict(
        bars=[(at, 98, 100), (at + 60, 101, 103), (at + 120, 96, 101)],
        revision_sha256="a" * 64,
        available_at=at + 180,
    )
    followup._measure_row(row, source)
    one = row["landmarks"][1]
    assert one["geometry"] == "below_break_even"
    future = one["outcomes"][0]
    assert future["start_at"] == at + 60 and future["end_at"] == at + 180
    assert future["observed_contact_order"] == "observed_target_bar_before_loss_bar"
    assert not one["selected_revision_available_at_or_before_landmark"]
    assert not one["entry_feature"] and not one["historical_revision_absence_proven"]
    assert row["landmarks"][-1]["outcomes"][0]["coverage"] == "no_full_bar"


def test_symbol_overlap_crosses_route_and_actual_cf_namespace_and_purges_train():
    boundary = clock("00:00:00")
    rows = [
        dict(identity="actual:1", symbol="005930", entry_at=boundary - 600),
        dict(identity="cf:1", symbol="005930", entry_at=boundary + 10),
        dict(identity="cf:2", symbol="000660", entry_at=boundary + 10),
        dict(identity="cf:3", symbol="005930", entry_at=boundary + 8000),
    ]
    clusters = followup._clusters(rows, ISO_DAY, clock())
    assert len(clusters) == 3
    assert rows[0]["overlap_cluster_id"] == rows[1]["overlap_cluster_id"]
    assert (
        rows[0]["split"] == "purged_overlap_boundary" and rows[1]["split"] == "holdout"
    )
    assert rows[2]["overlap_cluster_id"] != rows[1]["overlap_cluster_id"]
    assert rows[0]["overlap_cluster_size"] == 2


def test_public_native_pipeline_preserves_scope_census_sources_and_no_economics(
    tmp_path,
):
    base = dict(
        symbol="005930",
        item="005930",
        route="KRX",
        entry_at=clock("09:00:30"),
        evidence_kind="enter_pass_opportunity_cf",
        entry_reference_ask=100,
        entry_reference_role="native_entry_ask_price_path_only",
        automatic_management_allowed=True,
    )
    positions = [
        dict(base, position_key="cf:one"),
        dict(base, position_key="cf:two", automatic_management_allowed=False),
        dict(base, position_key="cf:gap", entry_reference_ask=None),
        dict(
            base,
            position_key="actual:one",
            evidence_kind="actual_completed",
            qty=2,
            buy_basis_krw=200,
        ),
        dict(
            base,
            position_key="alternative:one",
            evidence_kind="actual_entry_alternative_exit",
        ),
    ]
    paths = inputs(tmp_path, positions)
    path, receipt = publish(paths[0], bars(10))
    before = minute.carrier_generation(path)
    protected = {
        p: byte_generation(p)
        for p in (paths[2], paths[3], paths[1] / "part.json", paths[1] / "parent.json")
    }
    result = run_fixture(paths)
    rows = result_rows(paths, result)
    assert result["status"] == "complete" and result["input_population_count"] == 5
    assert (
        result["population_count"] == 4
        and result["excluded_alternative_exit_count"] == 1
    )
    assert set(rows) == {"cf:one", "cf:two", "cf:gap", "actual:one"}
    assert result["scope"]["scope_count"] == 16
    assert result["scope"]["scopes_ref"]["count"] == 16
    assert rows["cf:gap"]["status"] == "source_gap"
    assert (
        rows["cf:one"]["revision_sha256"] == receipt["shared_history_revision_sha256"]
    )
    assert rows["cf:two"]["automatic_management_allowed"] is False
    assert rows["actual:one"]["reference_role"] == "verified_buy_leg_price_path_only"
    assert [row["landmark_seconds"] for row in rows["cf:one"]["landmarks"]] == [
        30,
        60,
        120,
        180,
    ]
    assert rows["cf:one"]["landmarks"][0]["geometry"] == "no_full_bar"
    assert all(
        not row["full_interval_observed"]
        for row in rows["cf:one"]["landmarks"][1]["outcomes"]
    )
    assert (
        not result["allowed_runtime_apply"] and result["economic_eligible_count"] == 0
    )
    assert not result["actual_profit_verified"] and not result["runtime_effect"]
    assert minute.carrier_generation(path) == before
    assert all(byte_generation(p) == generation for p, generation in protected.items())
    assert followup.owner._sealed(paths[-1] / "report.json") == result
    assert health()["used_bytes"] == 0


def test_db_and_wal_are_copied_once_per_day_for_multiple_items(tmp_path, monkeypatch):
    base = dict(
        item="005930",
        symbol="005930",
        route="KRX",
        entry_at=clock("09:00:30"),
        evidence_kind="enter_pass_opportunity_cf",
        entry_reference_ask=100,
        entry_reference_role="native_entry_ask_price_path_only",
    )
    paths = inputs(
        tmp_path,
        [
            dict(base, position_key="cf:a"),
            dict(base, position_key="cf:b", item="000660", symbol="000660"),
        ],
    )
    path, _ = publish(paths[0], bars(2), now=clock("09:02:00"))
    with closing(sqlite3.connect(path)) as keeper:
        keeper.execute("SELECT count(*) FROM current").fetchone()
        publish(paths[0], bars(10))
        publish(paths[0], bars(10), item="000660")
        before = minute.carrier_generation(path)
        assert before["wal"]["size"] > 0
        calls, snapshot = [], minute._snapshot

        def counted(*args, **kwargs):
            calls.append(args[1])
            return snapshot(*args, **kwargs)

        monkeypatch.setattr(minute, "_snapshot", counted)
        result = run_fixture(paths)
        assert calls == [DAY] and len(result["source_revisions"]) == 2
        assert minute.carrier_generation(path) == before


@pytest.mark.parametrize(
    "fault",
    [
        "model_cost",
        "cutoff",
        "manifest_generation",
        "schema",
        "authority",
        "holdout",
        "manifest_path",
        "prefix_window",
        "path_geometry_labels",
        "split_contract",
        "runtime_effect",
        "actual_pid_consumed",
        "numeric_false",
    ],
)
def test_registration_mismatch_fails_before_output_or_source_read(
    tmp_path, monkeypatch, fault
):
    paths = inputs(tmp_path)
    value = json.loads(paths[3].read_text())
    if fault == "model_cost":
        value["modeled_cost_rate"] = 0
    elif fault == "cutoff":
        value["as_of"] += 1
    elif fault == "manifest_generation":
        value["input_manifest_generation"]["sha256"] = "f" * 64
    elif fault == "schema":
        value["schema"] = "unregistered"
    elif fault == "authority":
        value["allowed_runtime_apply"] = True
    elif fault == "holdout":
        value["holdout_start_date"] = "2026-10-14"
    elif fault == "manifest_path":
        value["input_manifest_path"] = str(tmp_path / "other.json")
    elif fault in {"runtime_effect", "actual_pid_consumed"}:
        value[fault] = True
    elif fault == "numeric_false":
        value["allowed_runtime_apply"] = 0
    else:
        value[fault] = "different_definition"
    value.pop("artifact_sha256")
    seal(paths[3], value)
    monkeypatch.setattr(
        minute, "_snapshot", lambda *a, **k: pytest.fail("unregistered source access")
    )
    with pytest.raises(ValueError):
        run_fixture(paths)
    assert not paths[-1].exists()


def test_exact_item_and_missing_carrier_remain_rows_not_empty_success(tmp_path):
    base = dict(
        item="005930_NX",
        symbol="005930",
        route="NXT",
        entry_at=clock("09:00:30"),
        evidence_kind="enter_pass_opportunity_cf",
        entry_reference_ask=100,
        entry_reference_role="native_entry_ask_price_path_only",
        position_key="cf:a",
    )
    paths = inputs(tmp_path, [base])
    publish(paths[0], bars(10))
    result = run_fixture(paths)
    row = result_rows(paths, result)["cf:a"]
    assert (
        row["status"] == "source_gap"
        and row["reason"] == "minute_history_exact_item_or_known_revision_missing"
    )
    assert result["scope"]["scope_count"] == 16 and result["population_count"] == 1


@pytest.mark.parametrize("fault", ["partition", "registration", "code"])
def test_mutation_before_final_publication_never_produces_report(
    tmp_path, monkeypatch, fault
):
    paths = inputs(tmp_path)
    publish(paths[0], bars(10))
    read = minute._read_series

    def changing(*args, **kwargs):
        result = read(*args, **kwargs)
        if fault in {"partition", "registration"}:
            path = paths[1] / "part.json" if fault == "partition" else paths[3]
            with path.open("a") as handle:
                handle.write(" ")
        else:
            monkeypatch.setattr(followup, "_code_generation", lambda: {"changed": True})
        return result

    monkeypatch.setattr(minute, "_read_series", changing)
    with pytest.raises(ValueError):
        run_fixture(paths)
    assert not (paths[-1] / "report.json").exists()
    assert health()["used_bytes"] == 0


def test_output_cannot_overwrite_input_or_prior_research_and_cli_requires_registration(
    tmp_path,
):
    paths = inputs(tmp_path)
    with pytest.raises(ValueError):
        followup.run(
            paths[3],
            paths[2],
            input_root=paths[1],
            data_root=paths[0],
            output_root=paths[1] / "new",
        )
    paths[-1].mkdir()
    (paths[-1] / "prior.json").write_text("original")
    with pytest.raises(ValueError):
        run_fixture(paths)
    assert (paths[-1] / "prior.json").read_text() == "original"
    with pytest.raises(SystemExit) as exc:
        followup.main(["--manifest", str(paths[2])])
    assert exc.value.code == 2


def test_missing_carrier_and_pre_window_exclusion_keep_original_ids(tmp_path):
    base = dict(
        item="005930",
        symbol="005930",
        route="KRX",
        entry_at=clock("09:00:30"),
        evidence_kind="enter_pass_opportunity_cf",
        entry_reference_ask=100,
        entry_reference_role="native_entry_ask_price_path_only",
    )
    paths = inputs(
        tmp_path,
        [
            dict(base, position_key="cf:a"),
            dict(
                base,
                position_key="cf:old",
                source_gap="original_gap",
                research_entry_window_exclusion="entry_before_research_window",
            ),
        ],
    )
    result = run_fixture(paths)
    rows = result_rows(paths, result)
    assert rows["cf:a"]["reason"] == "minute_history_not_stored"
    assert rows["cf:old"]["status"] == "research_excluded"
    assert rows["cf:old"]["original_source_gap"] == "original_gap"
    assert result["population_count"] == 2


def test_full_2605_symbol_scope_is_sharded_without_dropping_unobserved_scopes(tmp_path):
    paths = inputs(tmp_path)
    manifest = json.loads(paths[2].read_text())
    manifest["universe"] = [
        dict(symbol=f"{index:06d}", known_at=clock("08:00:00"), tradable=True)
        for index in range(2604)
    ] + [dict(symbol="005930", known_at=clock("08:00:00"), tradable=True)]
    manifest.pop("artifact_sha256")
    seal(paths[2], manifest)
    registration = json.loads(paths[3].read_text())
    registration["input_manifest_generation"] = byte_generation(paths[2])
    registration.pop("artifact_sha256")
    seal(paths[3], registration)
    result = run_fixture(paths)
    assert result["scope"]["symbol_count"] == 2605
    assert result["scope"]["scope_count"] == 20840
    assert result["scope"]["counts"] == {"registered_nonoperating": 20840}
    assert (
        sum(1 for _ in storage.iter_tree(paths[-1], result["scope"]["scopes_ref"]))
        == 20840
    )
    assert result["population_count"] == 1 and health()["used_bytes"] == 0


def test_cli_calls_same_public_writer_with_required_arguments(tmp_path, capsys):
    paths = inputs(tmp_path)
    assert (
        followup.main(
            [
                "--registration",
                str(paths[3]),
                "--manifest",
                str(paths[2]),
                "--input-root",
                str(paths[1]),
                "--data-root",
                str(paths[0]),
                "--output-root",
                str(paths[-1]),
            ]
        )
        == 0
    )
    assert "complete population=1 scope=16" in capsys.readouterr().out
    assert followup.owner._sealed(paths[-1] / "report.json")["population_count"] == 1


@pytest.mark.parametrize("kind", ["actual_completed", "enter_pass_opportunity_cf"])
def test_source_date_end_excludes_later_entry_without_losing_ids_or_original_gaps(
    tmp_path, monkeypatch, kind
):
    end = clock("00:00:00") + 86400
    base = dict(
        item="005930",
        symbol="005930",
        route="KRX",
        evidence_kind=kind,
        entry_reference_ask=100,
        entry_reference_role="native_entry_ask_price_path_only",
        source_gap="original_gap",
    )
    paths = inputs(
        tmp_path,
        [
            dict(base, position_key="last", entry_at=end - 0.001),
            dict(base, position_key="next", entry_at=end),
        ],
    )
    manifest = json.loads(paths[2].read_text())
    manifest["as_of"] = end + 600
    manifest.pop("artifact_sha256")
    seal(paths[2], manifest)
    registration = json.loads(paths[3].read_text())
    registration.update(
        as_of=end + 600, input_manifest_generation=byte_generation(paths[2])
    )
    registration.pop("artifact_sha256")
    seal(paths[3], registration)
    publish(paths[0], bars(10))
    snapshot, days = minute._snapshot, []

    def counted(*args, **kwargs):
        days.append(args[1])
        return snapshot(*args, **kwargs)

    monkeypatch.setattr(minute, "_snapshot", counted)
    result = run_fixture(paths)
    rows = result_rows(paths, result)
    assert result["population_count"] == result["input_population_count"] == 2
    assert rows["last"]["status"] == "retrospective_path_geometry"
    assert rows["last"]["split"] == "holdout"
    assert rows["next"]["status"] == "research_excluded"
    assert rows["next"]["reason"] == "entry_after_research_window"
    assert rows["next"]["split"] == "outside_source_period"
    assert (
        rows["next"]["overlap_cluster_id"] is None and rows["next"]["landmarks"] == []
    )
    assert (
        rows["next"]["entry_at"] == rows["next"]["research_entry_window_end_at"] == end
    )
    assert (
        rows["next"]["original_source_gap"]
        == rows["last"]["original_source_gap"]
        == "original_gap"
    )
    assert days == [DAY]
