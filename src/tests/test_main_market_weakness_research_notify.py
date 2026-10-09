import copy

import pytest
from src.engine.automation import main_market_weakness_research_notify as N
from src.engine.automation import main_market_weakness_research as A
from src.engine.scalping import market_weakness_research as R
from src.tests.test_main_market_weakness_research import row, registry, favorable


def comparison():
    a = R.Aggregator(registry(row()))
    favorable(a)
    x = a.comparison("generation")
    a.close()
    return x


def call(root, c, **kwargs):
    return N.reconcile(
        root,
        c,
        send_enabled=True,
        data_root=root,
        gate=lambda: True,
        parent_matches=lambda *a: True,
        source_matches=lambda: True,
        transport=lambda _: dict(status="sent", message_id=1),
        **kwargs,
    )


def invoke(root, c, transport, **kwargs):
    params = dict(
        send_enabled=True,
        data_root=root,
        gate=lambda: True,
        parent_matches=lambda *a: True,
        source_matches=lambda: True,
        transport=transport,
    )
    params.update(kwargs)
    return N.reconcile(root, c, **params)


def test_semantic_id_excludes_date_report_generation_and_code():
    c = comparison()["comparisons"][0]
    d = dict(c, generation="new", source_dates=["2026-10-09"], code_sha256="changed")
    assert N.recommendation_id(c) == N.recommendation_id(d)
    d = copy.deepcopy(c)
    d["definition"]["after"] = 0.9
    assert N.recommendation_id(c) != N.recommendation_id(d)


@pytest.mark.parametrize(
    "field,value",
    [
        ("delta_raw_win_rate", 0),
        ("empirical_lower_5pct_delta", None),
        ("bootstrap_valid_iterations", 999),
        ("excluded_opportunities", 0),
        ("scope_winner", False),
        ("comparison_complete", False),
    ],
)
def test_ineligible_comparison_never_sends(tmp_path, field, value):
    c = comparison()
    c["comparisons"][0][field] = value
    c = R.seal(c)
    r = invoke(tmp_path, c, lambda _: pytest.fail("send"))
    assert r["eligible_candidates"] == 0


def test_stale_parent_or_source_blocks_before_transport(tmp_path):
    r = invoke(
        tmp_path,
        comparison(),
        lambda _: pytest.fail("send"),
        parent_matches=lambda *a: False,
    )
    assert r["status"] == "notification_blocked"
    r = invoke(
        tmp_path,
        comparison(),
        lambda _: pytest.fail("send"),
        source_matches=lambda: False,
    )
    assert r["status"] == "deferred_resource_or_window"


def test_sent_receipt_deduplicates_generation_changes(tmp_path):
    calls = []
    c = comparison()
    r = invoke(
        tmp_path, c, lambda m: calls.append(m) or dict(status="sent", message_id=123)
    )
    assert r["status"] == "completed"
    assert len(calls) == 1
    assert "자동 적용 없음" in calls[0]
    newer = R.seal(dict(c, generation="next"))
    invoke(tmp_path, newer, lambda _: pytest.fail("duplicate"))
    state = A.read_json(tmp_path / "outbox/state.json")
    assert len(state["events"]) == 1
    assert next(iter(state["events"].values()))["message_id"] == 123


@pytest.mark.parametrize(
    "result",
    [
        {"status": "sent"},
        {"status": "sent", "message_id": True},
        {"status": "sent", "message_id": 0},
        {"status": "delivery_uncertain"},
        {"status": "unknown"},
    ],
)
def test_ambiguous_delivery_never_retries(tmp_path, result):
    c = comparison()
    r = invoke(tmp_path, c, lambda _: result)
    assert r["status"] == "delivery_uncertain"
    invoke(tmp_path, c, lambda _: pytest.fail("uncertain delivery retry"))


def test_process_crash_after_atomic_claim_recovers_uncertain(tmp_path):
    def crash(_):
        raise KeyboardInterrupt

    c = comparison()
    with pytest.raises(KeyboardInterrupt):
        invoke(tmp_path, c, crash)
    event = next(iter(A.read_json(tmp_path / "outbox/state.json")["events"].values()))
    assert event["status"] == "sending"
    r = invoke(tmp_path, c, lambda _: pytest.fail("claim retry"))
    assert r["status"] == "delivery_uncertain"


def test_rate_limit_bounded_retry_and_not_completed(tmp_path):
    c = comparison()
    calls = []

    def reject(_):
        calls.append(1)
        return dict(
            status="failed_definite", reason="notification_rate_limit", retry_after=60
        )

    assert (
        invoke(tmp_path, c, reject, now=lambda: 100)["status"] == "notification_blocked"
    )
    assert (
        invoke(tmp_path, c, reject, now=lambda: 120)["status"]
        == "deferred_resource_or_window"
    )
    for t in (160, 220, 280):
        invoke(tmp_path, c, reject, now=lambda: t)
    assert len(calls) == 3


def test_withdrawal_is_bound_to_sent_receipt_and_does_not_need_old_parent(tmp_path):
    c = comparison()
    call(tmp_path, c)
    updated = copy.deepcopy(c)
    updated["comparisons"][0].update(status="hold_observation", scope_winner=False)
    updated = R.seal(updated)
    messages = []
    invoke(
        tmp_path,
        updated,
        lambda m: messages.append(m) or dict(status="sent", message_id=2),
        parent_matches=lambda *a: False,
    )
    assert len(messages) == 1
    assert "철회" in messages[0]
    state = A.read_json(tmp_path / "outbox/state.json")
    withdrawn = next(
        e for e in state["events"].values() if e["transition"] == "withdrawal"
    )
    assert withdrawn["previous_sent_event"] in state["events"]
    assert withdrawn["message_id"] == 2
    invoke(tmp_path, c, lambda _: pytest.fail("withdrawn semantic candidate resend"))


def test_source_correction_not_created_without_prior_sent(tmp_path):
    c = comparison()
    invoke(tmp_path, c, lambda _: dict(status="failed_definite"))
    empty = R.seal(
        dict(
            c,
            comparisons=[],
            candidate_count=0,
            invalidated_source_dates=["2026-10-08"],
        )
    )
    invoke(tmp_path, empty, lambda _: pytest.fail("no prior sent receipt"))
    assert all(
        e["transition"] == "recommendation"
        for e in A.read_json(tmp_path / "outbox/state.json")["events"].values()
    )


def test_current_source_rechecked_after_durable_claim(tmp_path):
    matches = iter([True, False])
    r = invoke(
        tmp_path,
        comparison(),
        lambda _: pytest.fail("stale after claim"),
        source_matches=lambda: next(matches),
    )
    assert r["status"] == "deferred_resource_or_window"
    assert (
        next(iter(A.read_json(tmp_path / "outbox/state.json")["events"].values()))[
            "status"
        ]
        == "prepared"
    )


def test_pending_withdrawal_cancelled_when_original_evidence_recovers(tmp_path):
    c = comparison()
    call(tmp_path, c)
    weak = copy.deepcopy(c)
    weak["comparisons"][0].update(status="hold_observation", scope_winner=False)
    weak = R.seal(weak)
    invoke(tmp_path, weak, lambda _: pytest.fail("deferred"), gate=lambda: False)
    invoke(tmp_path, c, lambda _: pytest.fail("obsolete withdrawal"))
    assert any(
        e.get("reason") == "invalidation_no_longer_current"
        for e in A.read_json(tmp_path / "outbox/state.json")["events"].values()
    )


def test_replacement_keeps_one_current_sent_and_preserves_receipts(tmp_path):
    c = comparison()
    call(tmp_path, c)
    next_c = copy.deepcopy(c)
    next_c["comparisons"][0]["definition"]["after"] = 0.8
    next_c["comparisons"][0]["definition"]["feature_max_exclusive"] = 0.8
    next_c = R.seal(next_c)
    messages = []
    invoke(
        tmp_path,
        next_c,
        lambda m: messages.append(m) or dict(status="sent", message_id=2),
    )
    state = A.read_json(tmp_path / "outbox/state.json")
    assert sum(r["status"] == "sent" for r in state["recommendations"].values()) == 1
    assert sum(e["status"] == "sent" for e in state["events"].values()) == 2
    assert "이전 안내를 이 후보로 대체" in messages[0]


def test_scoped_parent_binding_does_not_require_unrelated_bundle_identity(
    tmp_path, monkeypatch
):
    from src.engine.scalping import mechanistic_entry_runtime_policy as P

    c = comparison()["comparisons"][0]
    definition = c["definition"]
    machine = {"patterns": ["one"]}
    binding = {
        "prompt_version": "p",
        "response_schema_sha256": "s",
        "provider": "provider",
        "model": "model",
    }
    definition.update(
        policy_scope="samsung|REGULAR|ALL|SOR",
        scope_parent_machine_payload_sha256=R.digest(machine),
        auxiliary_binding=binding,
        auxiliary_hash=R.digest(binding),
    )
    auxiliary = {"arm": "one", "binding": binding}
    bundle = dict(
        bundle_sha256="unrelated_scope_changed",
        continuous_reversal=dict(
            machine_cells={
                "samsung|REGULAR|ALL": {
                    "routes": {
                        "SOR": dict(payload=machine, payload_sha256=R.digest(machine))
                    }
                }
            },
            auxiliary_cells={
                "samsung|REGULAR|ALL": {
                    "routes": {
                        "SOR": dict(
                            payload=auxiliary, payload_sha256=R.digest(auxiliary)
                        )
                    }
                }
            },
        ),
    )
    monkeypatch.setattr(P, "load_effective", lambda **k: bundle)
    assert N.current_parent_matches(tmp_path, c)
    machine["patterns"] = ["changed"]
    assert not N.current_parent_matches(tmp_path, c)
