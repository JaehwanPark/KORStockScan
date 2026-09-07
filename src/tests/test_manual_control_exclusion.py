from datetime import datetime

import pytest

from src.engine import sniper_state_handlers
from src.engine.risk import manual_control_exclusion


@pytest.fixture(autouse=True)
def _isolate_symbol_owner_policy(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SYMBOL_OWNER_POLICY_FILE",
        str(tmp_path / "missing-symbol-owner-policy.json"),
    )


def test_manual_control_exclusion_matches_env_codes(monkeypatch):
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_ENV, "5930, 001820;A000660"
    )
    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")

    assert decision.excluded is True
    assert decision.code == "005930"
    assert decision.reason == "operator_manual_control_excluded_symbol"
    assert decision.source == manual_control_exclusion.EXCLUDED_CODES_ENV
    assert decision.as_log_fields()["actual_order_submitted"] is False
    assert decision.as_log_fields()["broker_order_forbidden"] is True
    assert (
        decision.as_log_fields()["decision_authority"]
        == "operator_manual_control_exclusion_no_bot_action"
    )


def test_manual_control_exclusion_loads_file_and_reloads_on_mtime_change(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # Samsung\n001820\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is False
    )

    path.write_text("000660\n", encoding="utf-8")

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is True
    )


def test_legacy_scale_in_qty_auto_handoff_is_retired_without_operator_owner(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "249420 # auto_scale_in_qty_guard_block source=late_loss_avg_down_retry\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    logs = []
    monkeypatch.setattr(
        sniper_state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {
        "id": 38741,
        "code": "249420",
        "name": "ILDONG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_exclusion_blocked": True,
        "manual_control_exclusion_reason": "operator_manual_control_excluded_symbol",
        "manual_control_exclusion_source": str(path),
        "manual_control_auto_scale_in_qty_blocked": True,
        "manual_control_auto_exclusion_source_stage": "late_loss_avg_down_retry",
    }

    blocked = sniper_state_handlers._manual_control_exclusion_blocked(
        stock,
        "249420",
        pipeline="holding",
        stage="manual_control_excluded_symbol_blocked",
        now_ts=1_000.0,
    )

    assert blocked is False
    assert "249420" not in path.read_text(encoding="utf-8")
    assert "manual_control_exclusion_blocked" not in stock
    assert "manual_control_auto_scale_in_qty_blocked" not in stock
    stage, fields = logs[-1]
    assert stage == "manual_control_legacy_scale_in_qty_handoff_retired"
    assert fields["legacy_auto_source"] == "auto_scale_in_qty_guard_block"
    assert fields["file_row_removed"] is True
    assert fields["broker_order_forbidden"] is True
    assert fields["automated_holding_monitor_restored"] is True


def test_legacy_scale_in_qty_flag_cannot_override_explicit_manual_operator(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "249420 # manual_operator operator_owned_holding\n", encoding="utf-8"
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    logs = []
    monkeypatch.setattr(
        sniper_state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {
        "id": 38741,
        "code": "249420",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_auto_scale_in_qty_blocked": True,
    }

    blocked = sniper_state_handlers._manual_control_exclusion_blocked(
        stock,
        "249420",
        pipeline="holding",
        stage="manual_control_excluded_symbol_blocked",
        now_ts=1_000.0,
    )

    assert blocked is True
    assert "249420" in path.read_text(encoding="utf-8")
    assert stock["manual_control_auto_scale_in_qty_blocked"] is True
    assert logs[-1][0] == "manual_control_excluded_symbol_blocked"

    path.write_text("", encoding="utf-8")
    assert (
        sniper_state_handlers._manual_control_exclusion_blocked(
            stock,
            "249420",
            pipeline="holding",
            stage="manual_control_excluded_symbol_blocked",
            now_ts=1_001.0,
        )
        is False
    )
    assert "manual_control_auto_scale_in_qty_blocked" not in stock
    assert logs[-1][0] == "manual_control_legacy_scale_in_qty_handoff_retired"


def test_retiring_quantity_handoff_preserves_independent_hard_stop_veto(
    monkeypatch, tmp_path
):
    path = tmp_path / "excluded.txt"
    path.write_text("249420 # auto_scale_in_qty_guard_block legacy\n")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    manual_control_exclusion.add_manual_control_exclusion_code(
        "249420", comment="auto_hard_stop_handoff current_loss"
    )
    stock = {"code": "249420", "status": "HOLDING", "strategy": "SCALPING"}
    assert sniper_state_handlers._manual_control_exclusion_blocked(
        stock, "249420", pipeline="holding", stage="test", now_ts=1000
    )
    assert path.read_text() == "249420 # auto_hard_stop_handoff current_loss\n"


def test_stale_in_memory_scale_in_qty_handoff_does_not_recreate_exclusion(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    logs = []
    monkeypatch.setattr(
        sniper_state_handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {
        "id": 38741,
        "code": "249420",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_exclusion_blocked": True,
        "manual_control_exclusion_source": "in_memory_scale_in_qty_guard_auto_exclusion",
        "manual_control_auto_scale_in_qty_blocked": True,
    }

    blocked = sniper_state_handlers._manual_control_exclusion_blocked(
        stock,
        "249420",
        pipeline="holding",
        stage="manual_control_excluded_symbol_blocked",
        now_ts=1_000.0,
    )

    assert blocked is False
    assert "manual_control_exclusion_blocked" not in stock
    assert "manual_control_auto_scale_in_qty_blocked" not in stock
    stage, fields = logs[-1]
    assert stage == "manual_control_legacy_scale_in_qty_handoff_retired"
    assert fields["legacy_auto_source"] == "stale_in_memory_only"
    assert fields["file_row_removed"] is False


def test_legacy_scale_in_qty_handoff_retirement_fails_closed_on_storage_error(
    monkeypatch,
):
    decisions = iter(
        [
            manual_control_exclusion.ManualControlExclusionDecision(
                True,
                "249420",
                "operator_manual_control_excluded_symbol",
                "/tmp/manual_control.txt",
            ),
            manual_control_exclusion.ManualControlExclusionDecision(
                False, "249420", "", ""
            ),
        ]
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "evaluate_manual_control_exclusion",
        lambda code: next(decisions),
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "manual_control_auto_exclusion_source",
        lambda code: "auto_scale_in_qty_guard_block",
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "remove_auto_manual_control_exclusion_code",
        lambda code, reason, **kwargs: manual_control_exclusion.ManualControlExclusionRemoval(
            False,
            "249420",
            "manual_control_exclusion_remove_failed:PermissionError",
            "/tmp/manual_control.txt",
        ),
    )
    stock = {
        "code": "249420",
        "status": "HOLDING",
        "manual_control_auto_scale_in_qty_blocked": True,
    }

    decision = (
        sniper_state_handlers._retire_unowned_scale_in_qty_manual_control_handoff(
            stock,
            "249420",
            pipeline="holding",
            now_ts=1_000.0,
        )
    )

    assert decision.excluded is True
    assert decision.reason.startswith("legacy_scale_in_qty_handoff_retirement_blocked:")
    assert stock["manual_control_auto_scale_in_qty_blocked"] is True


def test_manual_control_exclusion_append_adds_code_once(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    first = manual_control_exclusion.add_manual_control_exclusion_code(
        "5930",
        comment="auto_open_loss KRX_OPEN profit=-3.00% stop=-2.50%",
    )
    second = manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment="auto_open_loss KRX_OPEN profit=-3.00% stop=-2.50%"
    )

    assert first.excluded is True
    assert first.code == "005930"
    assert second.excluded is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert path.read_text(encoding="utf-8").count("005930") == 1


@pytest.mark.parametrize("comment", ["manual_operator explicit_user_veto", ""])
@pytest.mark.parametrize("newline", ["", "\n"])
def test_operator_registration_survives_existing_auto_veto_release(
    monkeypatch, tmp_path, comment, newline
):
    path = tmp_path / "excluded.txt"
    path.write_text("005930 # auto_open_loss loss=-3.0%" + newline)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    added = manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment=comment
    )
    assert added.excluded
    manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment=comment
    )
    assert path.read_text().count("005930") == 2
    assert manual_control_exclusion.remove_auto_manual_control_exclusion_code(
        "005930"
    ).removed
    assert manual_control_exclusion.evaluate_main_bot_control_exclusion(
        "005930", new_entry=False
    ).excluded


def test_operator_registration_is_persisted_even_with_env_veto(monkeypatch, tmp_path):
    path = tmp_path / "excluded.txt"
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    assert manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment="manual_operator explicit_user_veto"
    ).excluded
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV)
    assert manual_control_exclusion.evaluate_main_bot_control_exclusion(
        "005930"
    ).excluded


def test_appending_veto_after_unterminated_machine_marker_keeps_both_rows(
    monkeypatch, tmp_path
):
    path = tmp_path / "excluded.txt"
    path.write_text("005930 # machine_owner_scope samsung_electronics")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    assert manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment="manual_operator explicit_user_veto"
    ).excluded
    assert manual_control_exclusion.machine_owner_scope_source("005930")
    assert manual_control_exclusion.manual_control_operator_exclusion_source("005930")
    assert len(path.read_text().splitlines()) == 2


@pytest.mark.parametrize(
    "comment",
    ["machine_owner_scope samsung_electronics", "manual_operator samsung_electronics"],
)
def test_veto_registration_cannot_create_a_machine_authority_marker(
    monkeypatch, tmp_path, comment
):
    path = tmp_path / "excluded.txt"
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    result = manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment=comment
    )
    assert result.reason == "manual_control_registration_requires_veto_source"
    assert not path.exists()


def test_manual_control_operator_source_requires_explicit_owner_marker(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # manual_operator samsung\n"
        "034020 # auto_open_loss loss=-5.0%\n"
        "042660\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("005930")
        == "manual_operator"
    )
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("034020")
        == ""
    )
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("042660")
        == ""
    )


def test_machine_owner_scope_is_separate_from_operator_veto(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # machine_owner_scope samsung_electronics\n"
        "034020 # manual_operator explicit_user_veto\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert manual_control_exclusion.machine_owner_scope_source("005930") == (
        "machine_owner_scope"
    )
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("005930")
        == ""
    )
    assert manual_control_exclusion.machine_owner_scope_source("034020") == ""
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("034020")
        == "manual_operator"
    )


def test_machine_owner_scope_requires_exact_reviewed_symbol_label(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # machine_owner_scope wrong_episode\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert manual_control_exclusion.machine_owner_scope_source("005930") == ""
    decision = manual_control_exclusion.evaluate_main_bot_control_exclusion("005930")
    assert decision.excluded is True
    assert decision.reason == "operator_manual_control_excluded_symbol"


def test_machine_owner_scope_requires_one_symbol_per_marker_row(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930,000660 # machine_owner_scope samsung_electronics\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert manual_control_exclusion.machine_owner_scope_source("005930") == ""
    assert manual_control_exclusion.legacy_machine_owner_scope_source("005930") == ""
    assert manual_control_exclusion.evaluate_main_bot_control_exclusion(
        "005930"
    ).excluded


def test_auto_exclusion_appends_next_to_machine_scope_and_removes_independently(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # machine_owner_scope samsung_electronics\n", encoding="utf-8"
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    added = manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment="auto_hard_stop_handoff holding_loss"
    )

    assert added.excluded is True
    assert path.read_text(encoding="utf-8").count("005930") == 2
    assert manual_control_exclusion.manual_control_auto_exclusion_source("005930") == (
        "auto_hard_stop_handoff"
    )

    removed = manual_control_exclusion.remove_auto_manual_control_exclusion_code(
        "005930", reason="test_release"
    )

    assert removed.removed is True
    assert path.read_text(encoding="utf-8") == (
        "005930 # machine_owner_scope samsung_electronics\n"
    )


def test_auto_exclusion_appends_during_legacy_machine_scope_transition(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    label = manual_control_exclusion.LEGACY_MACHINE_OWNER_SCOPE_LABELS["005930"]
    legacy_row = f"005930 # manual_operator {label}\n"
    path.write_text(legacy_row, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert manual_control_exclusion.legacy_machine_owner_scope_source("005930") == (
        "legacy_machine_owner_scope"
    )
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("005930")
        == ""
    )
    assert (
        manual_control_exclusion.independent_machine_ownership_source(
            "005930", owner="episode"
        )
        == "legacy_machine_owner_scope"
    )

    added = manual_control_exclusion.add_manual_control_exclusion_code(
        "005930", comment="auto_hard_stop_handoff holding_loss"
    )

    assert added.excluded is True
    assert path.read_text(encoding="utf-8") == (
        legacy_row + "005930 # auto_hard_stop_handoff holding_loss\n"
    )


def test_new_scale_in_auto_row_is_retired_after_machine_scope_was_cached(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    machine_row = "005930 # machine_owner_scope samsung_electronics\n"
    path.write_text(machine_row, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    stock = {
        "id": 5930,
        "code": "005930",
        "status": "HOLDING",
        "strategy": "SCALPING",
    }

    sniper_state_handlers._retire_unowned_scale_in_qty_manual_control_handoff(
        stock, "005930", pipeline="holding", now_ts=1_000.0
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("005930 # auto_scale_in_qty_guard_block source=late_loss_retry\n")
    manual_control_exclusion._invalidate_file_cache()
    stock["manual_control_auto_scale_in_qty_blocked"] = True
    stock["manual_control_auto_exclusion_source_stage"] = "late_loss_retry"

    decision = (
        sniper_state_handlers._retire_unowned_scale_in_qty_manual_control_handoff(
            stock, "005930", pipeline="holding", now_ts=1_001.0
        )
    )

    assert decision.excluded is True
    assert path.read_text(encoding="utf-8") == machine_row
    assert "manual_control_auto_scale_in_qty_blocked" not in stock
    assert "manual_control_auto_exclusion_source_stage" not in stock


def test_machine_scope_migration_changes_only_exact_legacy_rows(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # manual_operator samsung_electronics\n"
        "034020 # manual_operator explicit_user_veto\n"
        "042660 # machine_owner_scope hanwha_widget_and_episode_independent_owners\n",
        encoding="utf-8",
    )
    path.chmod(0o664)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    receipt = manual_control_exclusion.migrate_legacy_machine_owner_scope_markers(
        {
            "005930": "samsung_electronics",
            "034020": "doosan_widget_and_episode_independent_owners",
            "042660": "hanwha_widget_and_episode_independent_owners",
        }
    )

    assert receipt["migrated_symbols"] == ["005930"]
    assert receipt["already_migrated_symbols"] == ["042660"]
    assert receipt["preserved_operator_veto_symbols"] == ["034020"]
    assert receipt["changed"] is True
    assert path.read_text(encoding="utf-8") == (
        "005930 # machine_owner_scope samsung_electronics\n"
        "034020 # manual_operator explicit_user_veto\n"
        "042660 # machine_owner_scope hanwha_widget_and_episode_independent_owners\n"
    )
    assert path.stat().st_mode & 0o777 == 0o664

    retry = manual_control_exclusion.migrate_legacy_machine_owner_scope_markers(
        {
            "005930": "samsung_electronics",
            "042660": "hanwha_widget_and_episode_independent_owners",
        }
    )
    assert retry["migrated_symbols"] == []
    assert retry["already_migrated_symbols"] == ["005930", "042660"]
    assert retry["changed"] is False


def test_machine_scope_migration_preserves_same_symbol_explicit_veto(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    label = manual_control_exclusion.LEGACY_MACHINE_OWNER_SCOPE_LABELS["005930"]
    path.write_text(
        f"005930 # manual_operator {label}\n"
        "005930 # manual_operator explicit_user_veto\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    receipt = manual_control_exclusion.migrate_legacy_machine_owner_scope_markers(
        {"005930": label}
    )

    assert receipt["migrated_symbols"] == ["005930"]
    assert receipt["preserved_operator_veto_symbols"] == ["005930"]
    assert path.read_text(encoding="utf-8") == (
        f"005930 # machine_owner_scope {label}\n"
        "005930 # manual_operator explicit_user_veto\n"
    )


def test_post_migration_manual_row_reusing_legacy_label_remains_a_veto(
    monkeypatch, tmp_path
):
    path = tmp_path / "excluded.txt"
    original = (
        "005930 # machine_owner_scope samsung_electronics\n"
        "005930 # manual_operator samsung_electronics\n"
    )
    path.write_text(original)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    result = manual_control_exclusion.migrate_legacy_machine_owner_scope_markers(
        {"005930": "samsung_electronics"}
    )
    assert result["migrated_symbols"] == []
    assert path.read_text() == original
    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("005930")
        == "manual_operator"
    )
    assert not manual_control_exclusion.legacy_machine_owner_scope_source("005930")
    assert manual_control_exclusion.evaluate_main_bot_control_exclusion(
        "005930"
    ).excluded


def test_machine_scope_migration_preserves_generic_and_auto_veto_rows(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    label = manual_control_exclusion.LEGACY_MACHINE_OWNER_SCOPE_LABELS["005930"]
    path.write_text(
        f"005930 # manual_operator {label}\n"
        "005930 # temporary_operator_veto\n"
        "005930 # auto_open_loss loss=-3.0%\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    manual_control_exclusion.migrate_legacy_machine_owner_scope_markers(
        {"005930": label}
    )

    assert path.read_text(encoding="utf-8") == (
        f"005930 # machine_owner_scope {label}\n"
        "005930 # temporary_operator_veto\n"
        "005930 # auto_open_loss loss=-3.0%\n"
    )
    assert manual_control_exclusion.evaluate_main_bot_control_exclusion(
        "005930"
    ).excluded
    assert manual_control_exclusion.manual_control_auto_exclusion_source("005930") == (
        "auto_open_loss"
    )


def test_manual_control_operator_source_accepts_explicit_env(monkeypatch, tmp_path):
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "034020")
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_FILE_ENV,
        str(tmp_path / "missing.txt"),
    )

    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("034020")
        == manual_control_exclusion.EXCLUDED_CODES_ENV
    )


def test_manual_control_operator_source_rejects_legacy_watch_env(monkeypatch, tmp_path):
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(
        manual_control_exclusion.LEGACY_WATCH_EXCLUDED_CODES_ENV, "034020"
    )
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_FILE_ENV,
        str(tmp_path / "missing.txt"),
    )

    assert (
        manual_control_exclusion.manual_control_operator_exclusion_source("034020")
        == ""
    )


def test_manual_control_exclusion_remove_deletes_file_code(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # Samsung manual control\n000660,001820 # grouped\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code(
        "A005930",
        reason="periodic_sync_completed_no_broker_holding",
    )

    assert result.removed is True
    assert result.code == "005930"
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is True
    )
    assert "005930" not in path.read_text(encoding="utf-8")


def test_manual_control_exclusion_remove_preserves_manual_operator_row(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    original = (
        "005930 # manual_operator explicit_user_veto\n"
        "000660 # auto_open_loss KRX_OPEN\n"
    )
    path.write_text(original, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code(
        "005930",
        reason="periodic_sync_completed_no_broker_holding",
    )

    assert result.removed is False
    assert result.reason == "manual_control_exclusion_manual_operator_protected"
    assert path.read_text(encoding="utf-8") == original
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )


def test_manual_control_exclusion_remove_preserves_legacy_machine_scope_row(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    label = manual_control_exclusion.LEGACY_MACHINE_OWNER_SCOPE_LABELS["005930"]
    original = f"005930 # manual_operator {label}\n"
    path.write_text(original, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("005930")

    assert result.removed is False
    assert result.reason == "manual_control_machine_owner_scope_protected"
    assert path.read_text(encoding="utf-8") == original


def test_generic_veto_can_be_removed_without_removing_machine_scope(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    original = (
        "005930 # machine_owner_scope samsung_electronics\n"
        "005930 # temporary_operator_veto\n"
    )
    path.write_text(original, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("005930")

    assert result.removed is True
    assert path.read_text(encoding="utf-8") == (
        "005930 # machine_owner_scope samsung_electronics\n"
    )
    assert manual_control_exclusion.machine_owner_scope_source("005930")


def test_manual_control_exclusion_generic_remove_preserves_auto_row(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    original = "950160 # auto_open_loss KRX_OPEN profit=-29.72% stop=-5.00%\n"
    path.write_text(original, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code(
        "950160",
        reason="periodic_sync_completed_no_broker_holding",
    )

    assert result.removed is False
    assert (
        result.reason == "manual_control_auto_exclusion_average_price_release_required"
    )
    assert path.read_text(encoding="utf-8") == original
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("950160").excluded
        is True
    )


def test_manual_control_exclusion_manual_operator_vetoes_duplicate_auto_row_removal(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    original = (
        "005930 # auto_open_loss KRX_OPEN\n"
        "005930 # manual_operator explicit_user_veto\n"
    )
    path.write_text(original, encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code(
        "005930",
        reason="periodic_sync_completed_no_broker_holding",
    )

    assert result.removed is False
    assert result.reason == "manual_control_exclusion_manual_operator_protected"
    assert path.read_text(encoding="utf-8") == original


def test_manual_control_exclusion_remove_preserves_other_codes_on_same_line(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930,000660,001820 # grouped\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("000660")

    assert result.removed is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("001820").excluded
        is True
    )
    assert path.read_text(encoding="utf-8") == "005930,001820 # grouped\n"


def test_manual_control_exclusion_remove_file_code_does_not_clear_env_override(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # Samsung manual control\n", encoding="utf-8")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("005930")

    assert result.removed is True
    assert path.read_text(encoding="utf-8") == ""
    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")
    assert decision.excluded is True
    assert decision.source == manual_control_exclusion.EXCLUDED_CODES_ENV


def test_auto_exclusion_remove_only_deletes_supported_auto_rows(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # auto_open_loss KRX_OPEN profit=-3.00%\n"
        "000660 # operator manual control\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert (
        manual_control_exclusion.manual_control_auto_exclusion_source("005930")
        == "auto_open_loss"
    )
    assert manual_control_exclusion.manual_control_auto_exclusion_source("000660") == ""

    auto_result = manual_control_exclusion.remove_auto_manual_control_exclusion_code(
        "005930", reason="average_price_reached"
    )
    manual_result = manual_control_exclusion.remove_auto_manual_control_exclusion_code(
        "000660", reason="average_price_reached"
    )

    assert auto_result.removed is True
    assert manual_result.removed is False
    assert path.read_text(encoding="utf-8") == "000660 # operator manual control\n"


def test_auto_exclusion_remove_does_not_override_env_guard(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # auto_open_loss KRX_OPEN\n", encoding="utf-8")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_auto_manual_control_exclusion_code(
        "005930", reason="average_price_reached"
    )

    assert result.removed is False
    assert result.reason == "manual_control_auto_exclusion_env_override_active"
    assert "005930" in path.read_text(encoding="utf-8")


def test_auto_exclusion_releases_only_after_fresh_price_reaches_average(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "950160 # auto_open_loss KRX_OPEN profit=-29.72% stop=-5.00%\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.setattr(
        sniper_state_handlers,
        "_log_holding_pipeline",
        lambda *args, **kwargs: None,
    )
    stock = {
        "code": "950160",
        "name": "TEST",
        "status": "HOLDING",
        "buy_price": 60_900,
        "manual_control_exclusion_blocked": True,
        "manual_control_auto_open_loss_blocked": True,
    }

    assert (
        sniper_state_handlers._maybe_release_auto_manual_control_at_average_price(
            stock,
            "950160",
            ws_data={"curr": 30_050, "last_ws_update_ts": 999.0},
            now_ts=1_000.0,
        )
        is False
    )
    assert "950160" in path.read_text(encoding="utf-8")

    assert (
        sniper_state_handlers._maybe_release_auto_manual_control_at_average_price(
            stock,
            "950160",
            ws_data={"curr": 60_900, "last_ws_update_ts": 999.0},
            now_ts=1_000.0,
        )
        is True
    )
    assert path.read_text(encoding="utf-8") == ""
    assert "manual_control_exclusion_blocked" not in stock
    assert "manual_control_auto_open_loss_blocked" not in stock


def test_auto_exclusion_does_not_release_on_stale_price(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # auto_hard_stop_handoff source=holding\n", encoding="utf-8"
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    stock = {
        "code": "005930",
        "status": "HOLDING",
        "buy_price": 70_000,
        "manual_control_auto_hard_stop_blocked": True,
    }

    assert (
        sniper_state_handlers._maybe_release_auto_manual_control_at_average_price(
            stock,
            "005930",
            ws_data={"curr": 71_000, "last_ws_update_ts": 900.0},
            now_ts=1_000.0,
        )
        is False
    )
    assert "005930" in path.read_text(encoding="utf-8")


def test_auto_exclusion_does_not_release_from_simulated_holding(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # auto_open_loss KRX_OPEN\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    stock = {
        "code": "005930",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 70_000,
        "simulation_book": sniper_state_handlers.SCALP_SIMULATION_BOOK,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    assert (
        sniper_state_handlers._maybe_release_auto_manual_control_at_average_price(
            stock,
            "005930",
            ws_data={"curr": 71_000, "last_ws_update_ts": 999.0},
            now_ts=1_000.0,
        )
        is False
    )
    assert "005930" in path.read_text(encoding="utf-8")


def test_holding_handler_releases_auto_exclusion_before_block_guard(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # auto_open_loss KRX_OPEN\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    stock = {
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 70_000,
        "manual_control_exclusion_blocked": True,
        "manual_control_auto_open_loss_blocked": True,
    }
    observed = {}

    def stop_after_release(target, code, *, now_ts):
        observed["excluded"] = (
            manual_control_exclusion.evaluate_manual_control_exclusion(code).excluded
        )
        observed["in_memory_blocked"] = target.get(
            "manual_control_auto_open_loss_blocked"
        )
        return True

    monkeypatch.setattr(
        sniper_state_handlers,
        "_retry_pending_hard_stop_manual_handoff",
        stop_after_release,
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_log_holding_pipeline",
        lambda *args, **kwargs: None,
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 70_000, "last_ws_update_ts": 999.0},
        admin_id="admin",
        market_regime="BULL",
        now_ts=1_000.0,
        now_dt=datetime(2026, 7, 22, 10, 0),
    )

    assert observed == {"excluded": False, "in_memory_blocked": None}
    assert path.read_text(encoding="utf-8") == ""


def test_manual_control_exclusion_empty_config_does_not_block(monkeypatch, tmp_path):
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(tmp_path / "missing.txt")
    )

    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")

    assert decision.excluded is False
    assert decision.code == "005930"


def test_manual_control_exclusion_blocks_pending_order_cancellations(monkeypatch):
    emitted = []
    stock = {
        "id": 1,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "odno": "123",
        "order_time": 1.0,
    }
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_cancel(*args, **kwargs):
        raise AssertionError(
            "cancel order must not be called for manual-control excluded symbols"
        )

    monkeypatch.setattr(
        sniper_state_handlers.kiwoom_orders, "send_cancel_order", fail_cancel
    )

    assert (
        sniper_state_handlers.process_order_cancellation(
            stock, "005930", "123", db=None, strategy="SCALPING"
        )
        is False
    )

    assert stock["status"] == "BUY_ORDERED"
    assert stock["odno"] == "123"
    assert emitted[-1]["stage"] == "manual_control_excluded_buy_cancel_blocked"
    assert emitted[-1]["fields"]["manual_control_exclusion_applied"] is True


def test_manual_control_exclusion_blocks_holding_handler_before_sell_logic(monkeypatch):
    emitted = []
    stock = {
        "id": 2,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 70000,
    }
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_reconcile(*args, **kwargs):
        raise AssertionError(
            "holding control path must not run for manual-control excluded symbols"
        )

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", fail_reconcile
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 71000},
        admin_id="admin",
        market_regime={},
        now_ts=1000.0,
    )

    assert stock["status"] == "HOLDING"
    assert emitted[-1]["stage"] == "manual_control_excluded_symbol_blocked"
    assert emitted[-1]["fields"]["manual_control_exclusion_applied"] is True


def test_open_loss_holding_auto_exclusion_blocks_before_reconcile(
    monkeypatch, tmp_path
):
    emitted = []
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 3,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "position_tag": "BULL",
        "buy_price": 10000,
    }
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_reconcile(*args, **kwargs):
        raise AssertionError(
            "open-loss auto exclusion must run before reconcile/sell control"
        )

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", fail_reconcile
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 9700},
        admin_id="admin",
        market_regime="BULL",
        now_ts=1000.0,
        now_dt=datetime(2026, 7, 2, 9, 0, 5),
    )

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert "005930" in path.read_text(encoding="utf-8")
    assert stock["manual_control_exclusion_blocked"] is True
    assert stock["manual_control_auto_exclusion_session"] == "KRX_OPEN"
    assert emitted[-1]["stage"] == "manual_control_open_loss_auto_excluded"
    assert emitted[-1]["fields"]["manual_control_auto_exclusion_triggered"] is True
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True


def test_open_loss_session_resolves_nxt_and_krx_windows(monkeypatch):
    monkeypatch.delenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_OPEN_LOSS_EXCLUSION_WINDOW_SEC", raising=False
    )

    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 8, 0, 0)
        )
        == "NXT_OPEN"
    )
    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 9, 0, 0)
        )
        == "KRX_OPEN"
    )
    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 9, 6, 0)
        )
        == ""
    )
    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 9, 0, 0, tzinfo=sniper_state_handlers._KST)
        )
        == "KRX_OPEN"
    )


def test_open_loss_holding_auto_exclusion_ignores_non_open_window(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 4,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
    }
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    called = {"reconcile": False}

    def mark_reconcile(*args, **kwargs):
        called["reconcile"] = True

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", mark_reconcile
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_ws_freshness_recover_or_block",
        lambda *args, **kwargs: (args[2], False, {}),
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_maybe_submit_rising_missed_scout_upgrade",
        lambda *args, **kwargs: True,
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 9700},
        admin_id="admin",
        market_regime="BULL",
        now_ts=2000.0,
        now_dt=datetime(2026, 7, 2, 9, 10, 0),
    )

    assert called["reconcile"] is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )


def test_hard_stop_manual_handoff_registers_and_blocks_real_sell(monkeypatch, tmp_path):
    emitted = []
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 5,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )

    blocked = sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
        stock,
        "005930",
        strategy="SCALPING",
        sell_reason_type="LOSS",
        exit_rule="scalp_hard_stop_pct",
        profit_rate=-2.6,
        peak_profit=0.2,
        curr_price=9750,
        buy_price=10000,
        now_ts=1000.0,
        source_stage="standard_hard_stop_after_quote_revalidation",
    )

    assert blocked is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert path.read_text(encoding="utf-8").count("005930") == 1
    assert stock["status"] == "HOLDING"
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert stock["manual_control_hard_stop_handoff_pending"] is False
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff"
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True
    assert (
        emitted[-1]["fields"]["source_quality_gate"]
        == "manual_control_exclusion_active"
    )


def test_hard_stop_manual_handoff_preserves_emergency_and_simulated_exit(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    common = {
        "strategy": "SCALPING",
        "sell_reason_type": "LOSS",
        "exit_rule": "scalp_preset_hard_stop_pct",
        "profit_rate": -3.0,
        "peak_profit": 0.0,
        "curr_price": 9700,
        "buy_price": 10000,
        "now_ts": 1000.0,
        "source_stage": "preset_hard_stop_after_quote_confirmation",
    }
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            {"status": "HOLDING", "strategy": "SCALPING"},
            "005930",
            emergency=True,
            **common,
        )
        is False
    )
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            {
                "status": "HOLDING",
                "strategy": "SCALPING",
                "scalp_live_simulator": True,
            },
            "000660",
            **common,
        )
        is False
    )
    assert not path.exists()


def test_hard_stop_manual_handoff_blocks_and_retries_when_registration_fails(
    monkeypatch,
):
    emitted = []
    add_calls = []
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "name": "SAMSUNG",
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_RETRY_SEC", "5")

    def fake_add(code, comment=""):
        add_calls.append((code, comment))
        if len(add_calls) == 1:
            return manual_control_exclusion.ManualControlExclusionDecision(
                False,
                "005930",
                "manual_control_exclusion_append_failed:OSError",
                "/read-only/manual.txt",
            )
        return manual_control_exclusion.ManualControlExclusionDecision(
            True,
            "005930",
            "operator_manual_control_excluded_symbol",
            "/tmp/manual.txt",
        )

    monkeypatch.setattr(
        sniper_state_handlers, "add_manual_control_exclusion_code", fake_add
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )

    kwargs = {
        "strategy": "SCALPING",
        "sell_reason_type": "LOSS",
        "exit_rule": "scalp_hard_stop_pct",
        "profit_rate": -2.6,
        "peak_profit": 0.0,
        "curr_price": 9750,
        "buy_price": 10000,
        "source_stage": "standard_hard_stop_after_quote_revalidation",
    }
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            stock, "005930", now_ts=1000.0, **kwargs
        )
        is True
    )
    assert stock["manual_control_hard_stop_handoff_pending"] is True
    assert stock.get("manual_control_auto_hard_stop_blocked") is None
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff_deferred"
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1002.0
        )
        is True
    )
    assert len(emitted) == 1
    assert len(add_calls) == 1

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1006.0
        )
        is True
    )
    assert len(add_calls) == 2
    assert stock["manual_control_hard_stop_handoff_pending"] is False
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert "manual_control_hard_stop_handoff_exit_rule" not in stock
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff"
    assert emitted[-1]["fields"]["hard_stop_manual_handoff_retry_attempt"] is True


def test_pending_hard_stop_manual_handoff_runtime_off_clears_pending(monkeypatch):
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_hard_stop_handoff_pending": True,
        "manual_control_hard_stop_handoff_last_attempt_ts": 1000.0,
        "manual_control_hard_stop_handoff_exit_rule": "scalp_hard_stop_pct",
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "false")

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1006.0
        )
        is False
    )
    assert "manual_control_hard_stop_handoff_pending" not in stock
    assert "manual_control_hard_stop_handoff_exit_rule" not in stock


def test_holding_handler_retries_pending_hard_stop_handoff_before_quote_logic(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 6,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_hard_stop_handoff_pending": True,
        "manual_control_hard_stop_handoff_last_attempt_ts": 1000.0,
        "manual_control_hard_stop_handoff_exit_rule": "scalp_hard_stop_pct",
        "manual_control_hard_stop_handoff_profit_rate": -2.6,
        "manual_control_hard_stop_handoff_peak_profit": 0.1,
        "manual_control_hard_stop_handoff_curr_price": 9750,
        "manual_control_hard_stop_handoff_buy_price": 10000,
        "manual_control_hard_stop_handoff_source_stage": (
            "standard_hard_stop_after_quote_revalidation"
        ),
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_RETRY_SEC", "5")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)

    def fail_quote_logic(*args, **kwargs):
        raise AssertionError(
            "pending handoff retry must run before holding quote logic"
        )

    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_ws_freshness_recover_or_block",
        fail_quote_logic,
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 10100},
        admin_id="admin",
        market_regime="BULL",
        now_ts=1006.0,
        now_dt=datetime(2026, 7, 14, 15, 0, 0),
    )

    assert stock["status"] == "HOLDING"
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
