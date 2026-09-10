"""Late same-day BUY terminal recovery in the original owner, fake broker only."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.tests.test_machine_adaptive_exit_episode_pending_buy import (
    loop,  # noqa: F401
    sibling,  # noqa: F401
    pending,  # noqa: F401
    leg,
    market,
    KEY as BUY_KEY,
)
from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from src.trading.order.adaptive_exit.episode_buy_recovery import (
    KEY,
    TerminalRecoveryServices,
)
from src.trading.order.adaptive_exit.episode_pending_buy import validate_projection

pytestmark = pytest.mark.parametrize("loop", ["episode"], indirect=True)


def install_recovery(p):
    p.allow_recovery = True
    p.recovery_requests = []

    def authorize(request):
        p.recovery_requests.append(deepcopy(request))
        return p.allow_recovery

    services = p.machine.adaptive_exit_services
    p.machine.adaptive_exit_services = replace(
        services,
        pending_buy=replace(
            services.pending_buy,
            terminal_recovery=TerminalRecoveryServices(2, 1000, 10000, authorize),
        ),
    )


@pytest.fixture
def recovery(pending):  # noqa: F811
    p = pending
    install_recovery(p)
    p.tick()
    p.original_journal = deepcopy(leg(p)[BUY_KEY])
    p.clock[0] = p.original_journal["deadline_ms"]
    return p


@pytest.mark.parametrize("filled", [0, 4])
def test_late_cancel_terminal_preserves_deadline_then_original_target(recovery, filled):
    p = recovery
    if filled == 0:
        # The intent observed two filled shares. A later zero is regression,
        # not evidence of a zero-fill terminal.
        market(p, filled=0, remaining=0, confirmed=10, requested=8, price=None)
        result = p.tick()
        assert "source_wait" in result["adaptive_exit_loop_status"]
        assert leg(p)["status"] == "BUY_OPEN"
        return
    market(p, filled=filled, remaining=0, confirmed=10 - filled, price="10005")
    selected = canonical_sha256(p.record())
    result = p.tick()
    assert (
        result["adaptive_exit_loop_status"]
        == "pending_buy_terminal_original_target_pending"
    )
    journal = leg(p)[BUY_KEY]
    assert journal["deadline_ms"] == p.original_journal["deadline_ms"]
    assert journal["action_id"] == p.original_journal["action_id"]
    assert len(journal[KEY]["observation_starts_ms"]) == 1
    assert canonical_sha256(p.record()) == selected
    assert leg(p)["position_qty"] == 4 and not p.original_target_writes
    p.machine._state = p.machine._load_state()
    p.tick()
    assert p.original_target_writes == [{"price": 10105, "quantity": 4}]
    assert len(p.cancel_writes) == 1 and not leg(p)["buy_filled_at"]


def test_open_source_uses_fixed_read_interval_budget_not_cancel_retry(recovery):
    p = recovery
    before = len(p.buy_queries)
    result = p.tick()
    assert "source_wait" in result["adaptive_exit_loop_status"]
    after = len(p.buy_queries)
    assert after > before
    p.machine._state = p.machine._load_state()
    assert p.tick()["adaptive_exit_loop_status"] == "terminal_recovery_interval_wait"
    assert len(p.buy_queries) == after
    p.clock[0] += 1000
    p.tick()
    after = len(p.buy_queries)
    p.clock[0] += 1000
    assert (
        p.tick()["adaptive_exit_loop_status"]
        == "terminal_recovery_observation_budget_exhausted"
    )
    assert len(p.buy_queries) == after and len(p.cancel_writes) == 1
    assert len(leg(p)[BUY_KEY][KEY]["observation_starts_ms"]) == 2


def test_late_first_observation_does_not_renew_recovery_window(recovery):
    p = recovery
    p.clock[0] += 10000
    queries = len(p.buy_queries)
    assert p.tick()["adaptive_exit_loop_status"] == "terminal_recovery_window_exhausted"
    assert len(p.buy_queries) == queries and KEY not in leg(p)[BUY_KEY]


@pytest.mark.parametrize(
    "field", ["maximum_observations", "minimum_interval_ms", "window_ms"]
)
def test_restarted_service_cannot_change_frozen_recovery_budget(recovery, field):
    p = recovery
    p.tick()
    services = p.machine.adaptive_exit_services
    recovery_services = services.pending_buy.terminal_recovery
    p.machine.adaptive_exit_services = replace(
        services,
        pending_buy=replace(
            services.pending_buy,
            terminal_recovery=replace(
                recovery_services, **{field: getattr(recovery_services, field) + 1}
            ),
        ),
    )
    before = len(p.buy_queries)
    assert (
        p.tick()["adaptive_exit_loop_status"]
        == "terminal_recovery_frozen_bounds_changed"
    )
    assert len(p.buy_queries) == before and len(p.cancel_writes) == 1


def test_clock_rollback_cannot_restore_original_write_phase(recovery):
    p = recovery
    p.tick()
    before = len(p.buy_queries)
    p.clock[0] = p.original_journal["created_at_ms"] + 1000
    assert p.tick()["adaptive_exit_loop_status"] == "terminal_recovery_clock_regression"
    assert len(p.buy_queries) == before and len(p.cancel_writes) == 1


@pytest.mark.parametrize("flag", ["recovery", "pending", "lock", "authority"])
def test_missing_authority_prevents_recovery_reads(recovery, flag):
    p = recovery
    if flag == "recovery":
        p.allow_recovery = False
    elif flag == "pending":
        p.allow_pending = False
    else:
        p.flags[flag] = False
    before = len(p.buy_queries)
    p.tick()
    assert len(p.buy_queries) == before and len(p.cancel_writes) == 1
    assert KEY not in leg(p)[BUY_KEY]


@pytest.mark.parametrize("after_publish", [False, True])
def test_read_budget_saved_before_io_and_never_rolled_back_on_reload(
    recovery, monkeypatch, after_publish
):
    p = recovery
    save = p.machine._save
    fired = False

    def persist():
        nonlocal fired
        if not fired and KEY in leg(p).get(BUY_KEY, {}):
            fired = True
            if after_publish:
                save()
            raise OSError("isolated_recovery_save_failure")
        save()

    monkeypatch.setattr(p.machine, "_save", persist)
    before = len(p.buy_queries)
    with pytest.raises(OSError):
        p.tick()
    assert len(p.buy_queries) == before
    monkeypatch.setattr(p.machine, "_save", save)
    if after_publish:
        # Stale memory must not overwrite the published read reservation.
        assert (
            p.tick()["adaptive_exit_loop_status"]
            == "terminal_recovery_durable_state_mismatch"
        )
        assert (
            len(
                p.machine._load_state()["legs"][1][BUY_KEY][KEY][
                    "observation_starts_ms"
                ]
            )
            == 1
        )
    p.machine._state = p.machine._load_state()
    p.clock[0] += 1000
    p.tick()
    assert len(leg(p)[BUY_KEY][KEY]["observation_starts_ms"]) == (
        2 if after_publish else 1
    )
    assert len(p.cancel_writes) == 1


@pytest.mark.parametrize("fault", ["extra", "close_starts", "future", "null", "hash"])
def test_invalid_recovery_accounting_blocks_source_and_projection(recovery, fault):
    p = recovery
    p.tick()
    journal = leg(p)[BUY_KEY]
    record = journal[KEY]
    if fault == "extra":
        record["observation_starts_ms"] *= 3
    elif fault == "close_starts":
        record["observation_starts_ms"].append(record["observation_starts_ms"][0] + 1)
    elif fault == "future":
        record["observation_starts_ms"][0] = record["contract"]["deadline_ms"]
    elif fault == "null":
        journal[KEY] = None
    record["canonical_sha256"] = canonical_sha256(record)
    if fault == "hash":
        record["canonical_sha256"] = "0" * 64
    journal["canonical_sha256"] = canonical_sha256(journal)
    p.machine._save()
    before = len(p.buy_queries)
    assert "terminal_recovery_" in p.tick()["adaptive_exit_loop_status"]
    assert len(p.buy_queries) == before and len(p.cancel_writes) == 1


def test_zero_fill_late_terminal_preserves_no_fill_and_null_economics(
    pending,  # noqa: F811
):
    p = pending
    install_recovery(p)
    market(p, filled=0, remaining=10, price=None)
    p.tick()
    p.clock[0] = leg(p)[BUY_KEY]["deadline_ms"]
    market(p, filled=0, remaining=0, confirmed=10, requested=10, price=None)
    assert p.tick()["adaptive_exit_loop_status"] == "pending_buy_terminal_no_fill"
    receipt = leg(p)["adaptive_sibling_full_buy_receipt"]
    assert receipt["filled_qty"] == 0 and receipt["fill_price"] is None
    assert receipt["realized_pnl_status"] == "unreconciled_exact_fill_cost_required"
    p.tick()
    assert not p.original_target_writes and len(p.cancel_writes) == 1


@pytest.mark.parametrize("closed", [False, True])
def test_unsent_journal_terminal_read_never_creates_cancel(
    pending, monkeypatch, closed  # noqa: F811
):
    p = pending
    install_recovery(p)
    save = p.machine._save
    advanced = False

    def expire_after_intent():
        nonlocal advanced
        save()
        if not advanced and BUY_KEY in leg(p):
            advanced = True
            p.clock[0] = leg(p)[BUY_KEY]["deadline_ms"]

    monkeypatch.setattr(p.machine, "_save", expire_after_intent)
    p.tick()
    assert leg(p)[BUY_KEY]["phase"] == "INTENT_SAVED" and not p.cancel_writes
    monkeypatch.setattr(p.machine, "_save", save)
    market(p, filled=10 if closed else 4, remaining=0 if closed else 6, price="10005")
    result = p.tick()
    if closed:
        assert (
            result["adaptive_exit_loop_status"]
            == "pending_buy_terminal_original_target_pending"
        )
        p.tick()
        assert p.original_target_writes == [{"price": 10105, "quantity": 10}]
    else:
        assert (
            "terminal_recovery_full_source_wait:" in result["adaptive_exit_loop_status"]
        )
        assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    assert not p.cancel_writes


@pytest.mark.parametrize("phase", ["reservation", "projection"])
@pytest.mark.parametrize(
    "next_clock", ["same", "pre_creation", "exhausted", "authority_lost"]
)
def test_published_state_never_overwritten_by_stale_memory(
    recovery, monkeypatch, phase, next_clock
):
    p = recovery
    market(p, filled=4, remaining=0, confirmed=6)
    save = p.machine._save
    fired = False

    def publish_then_fail():
        nonlocal fired
        save()
        journal = leg(p)[BUY_KEY]
        if (
            not fired
            and KEY in journal
            and (phase == "reservation" or journal["phase"] == "PROJECTED")
        ):
            fired = True
            raise OSError("isolated published state fsync failure")

    monkeypatch.setattr(p.machine, "_save", publish_then_fail)
    with pytest.raises(OSError):
        p.tick()
    monkeypatch.setattr(p.machine, "_save", save)
    durable = p.machine._load_state()
    before = len(p.buy_queries)
    if next_clock == "pre_creation":
        p.clock[0] = p.original_journal["created_at_ms"] - 1000
    elif next_clock == "exhausted":
        p.clock[0] += 10000
    elif next_clock == "authority_lost":
        p.flags["authority"] = False
    assert (
        p.tick()["adaptive_exit_loop_status"]
        == "terminal_recovery_durable_state_mismatch"
    )
    assert p.machine._load_state() == durable
    assert len(p.buy_queries) == before and not p.original_target_writes
    if phase == "projection":
        p.flags["authority"] = True
        p.machine._state = p.machine._load_state()
        p.clock[0] = p.original_journal["deadline_ms"] + 1000
        p.tick()
        assert p.original_target_writes == [{"price": 10095, "quantity": 4}]


@pytest.mark.parametrize(
    "lost", ["recovery", "pending", "lock", "authority", "service", "deadline"]
)
def test_authority_lost_during_terminal_read_cannot_project(
    recovery, monkeypatch, lost
):
    p = recovery
    market(p, filled=4, remaining=0, confirmed=6)
    factory = p.machine.gateway.adaptive_exit_adapter

    def make(**kwargs):
        adapter = factory(**kwargs)
        post = adapter.post

        def call(**request):
            result = post(**request)
            if request["api_id"] == "ka10075":
                if lost == "recovery":
                    p.allow_recovery = False
                elif lost == "pending":
                    p.allow_pending = False
                elif lost == "service":
                    p.machine.adaptive_exit_services = replace(
                        p.machine.adaptive_exit_services, pending_buy=None
                    )
                elif lost == "deadline":
                    p.clock[0] = p.original_journal["deadline_ms"] + 10000
                else:
                    p.flags[lost] = False
            return result

        adapter.post = call
        return adapter

    monkeypatch.setattr(p.machine.gateway, "adaptive_exit_adapter", make)
    p.tick()
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    assert len(p.cancel_writes) == 1
    assert (
        len(p.machine._load_state()["legs"][1][BUY_KEY][KEY]["observation_starts_ms"])
        == 1
    )


@pytest.mark.parametrize("fault", ["price", "confirmation", "date"])
def test_late_source_gaps_do_not_create_terminal(recovery, fault):
    p = recovery
    market(p, filled=4, remaining=0, confirmed=6)
    if fault == "price":
        p.buy_rows[0].pop("cntr_uv")
    elif fault == "confirmation":
        p.buy_rows[-1]["cnfm_qty"] = "0"
    else:
        p.clock[0] += 86400000
    before = len(p.buy_queries)
    p.tick()
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    assert len(p.cancel_writes) == 1
    if fault == "date":
        assert len(p.buy_queries) == before


def test_recovery_removal_and_clock_rollback_do_not_reopen_write_phase(recovery):
    p = recovery
    p.tick()
    services = p.machine.adaptive_exit_services
    p.machine.adaptive_exit_services = replace(
        services, pending_buy=replace(services.pending_buy, terminal_recovery=None)
    )
    p.clock[0] = p.original_journal["created_at_ms"] + 1000
    before = len(p.buy_queries)
    assert (
        p.tick()["adaptive_exit_loop_status"]
        == "pending_buy_confirmation_deadline_requires_recovery"
    )
    assert len(p.buy_queries) == before and len(p.cancel_writes) == 1


def test_original_target_consumer_revalidates_recovery_accounting(recovery):
    p = recovery
    market(p, filled=4, remaining=0, confirmed=6)
    p.tick()
    journal = leg(p)[BUY_KEY]
    record = journal[KEY]
    record["observation_starts_ms"] *= 3
    record["canonical_sha256"] = canonical_sha256(record)
    journal["canonical_sha256"] = canonical_sha256(journal)
    p.machine._save()
    with pytest.raises(ValueError, match="terminal_recovery_accounting_invalid"):
        validate_projection(p.machine, leg(p))
    p.tick()
    assert not p.original_target_writes


def test_last_read_authorization_cannot_roll_clock_back_and_project(recovery):
    p = recovery
    p.clock[0] += 3000
    market(p, filled=4, remaining=0, confirmed=6)
    before = len(p.buy_queries)
    callbacks = 0

    def authorize(_):
        nonlocal callbacks
        if len(p.buy_queries) >= before + 2:
            callbacks += 1
            if callbacks == 1:
                p.clock[0] += 10
            elif callbacks == 2:
                # Still after the reserved observation start, but before
                # this final guard call's own initial clock read.
                p.clock[0] -= 1
        return True

    services = p.machine.adaptive_exit_services
    p.machine.adaptive_exit_services = replace(
        services,
        pending_buy=replace(
            services.pending_buy,
            terminal_recovery=replace(
                services.pending_buy.terminal_recovery, authorize=authorize
            ),
        ),
    )
    p.tick()
    assert callbacks >= 2
    assert leg(p)["status"] == "BUY_OPEN" and not p.original_target_writes
    assert len(p.cancel_writes) == 1


@pytest.mark.parametrize(
    "field", ["maximum_observations", "minimum_interval_ms", "window_ms"]
)
@pytest.mark.parametrize("bad", [0, -1, True, 1.5, None])
def test_read_bounds_require_explicit_positive_integers(loop, field, bad):  # noqa: F811
    bounds = dict(maximum_observations=2, minimum_interval_ms=1000, window_ms=10000)
    bounds[field] = bad
    with pytest.raises(
        ValueError, match="explicit_terminal_recovery_read_bounds_required"
    ):
        TerminalRecoveryServices(**bounds, authorize=lambda _: True)


def test_read_bounds_require_independent_callable_and_coherent_interval(
    loop,  # noqa: F811
):
    with pytest.raises(ValueError):
        TerminalRecoveryServices(2, 1000, 10000, None)
    with pytest.raises(ValueError):
        TerminalRecoveryServices(2, 10001, 10000, lambda _: True)
