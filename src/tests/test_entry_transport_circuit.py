"""Deadline recovery, concurrency and generation tests with no provider I/O."""

from concurrent.futures import Future, ThreadPoolExecutor
import pytest
from src.engine.ai.entry_transport_circuit import EntryTransportCircuit


@pytest.fixture(autouse=True)
def isolate_runtime_circuit_diagnostics(monkeypatch):
    from src.engine.monitoring import runtime_performance as R

    monkeypatch.setattr(R, "_CIRCUIT", {"state": "not_observed"})


@pytest.fixture
def circuit():
    now = [100.0]
    return EntryTransportCircuit(clock=lambda: now[0]), now


def open_circuit(c, future=None):
    for i in range(5):
        ticket = c.admit(str(i), eligible=True, deadline_remaining=0.694)
        assert ticket is not None
        c.failed(ticket, future=future)
    assert c.snapshot()["state"] == "OPEN"


def test_five_original_deadlines_open_only_entry_then_one_new_response_closes(circuit):
    c, now = circuit
    for i, budget in enumerate((3.007, 3.176, 0.694, 1.897, 3.395)):
        ticket = c.admit(str(i), eligible=True, deadline_remaining=budget)
        c.failed(ticket)
    assert c.admit("new", eligible=True, deadline_remaining=5) is None
    now[0] += 30
    ticket = c.admit("new", eligible=True, deadline_remaining=1)
    assert ticket["recovery"]
    assert c.admit("concurrent", eligible=True, deadline_remaining=5) is None
    assert c.succeeded(ticket, deadline_remaining=0.2, valid_response=True)
    assert c.snapshot()["state"] == "CLOSED"
    assert c.snapshot()["consecutive_failures"] == 0


@pytest.mark.parametrize(
    "field,value",
    [("eligible", False), ("deadline_remaining", 0), ("common_disabled", True)],
)
def test_recovery_cannot_bypass_native_deadline_or_common_provider_block(
    circuit, field, value
):
    c, now = circuit
    open_circuit(c)
    now[0] += 30
    args = dict(eligible=True, deadline_remaining=5, common_disabled=False)
    args[field] = value
    assert c.admit("new", **args) is None
    assert c.admit("4", eligible=True, deadline_remaining=5) is None


def test_unsettled_future_blocks_recovery_and_cancel_failure_is_not_unsent(circuit):
    c, now = circuit
    f = Future()
    f.set_running_or_notify_cancel()
    open_circuit(c, f)
    now[0] += 30
    assert not f.cancel()
    assert c.admit("new", eligible=True, deadline_remaining=5) is None
    f.set_result("late")
    ticket = c.admit("new", eligible=True, deadline_remaining=5)
    assert ticket is not None
    assert c.snapshot()["state"] == "HALF_OPEN"  # Settlement alone did not recover.


def test_parallel_recovery_has_one_lease_and_exact_backoff(circuit):
    c, now = circuit
    open_circuit(c)
    now[0] += 30
    with ThreadPoolExecutor(max_workers=8) as pool:
        tickets = list(
            pool.map(
                lambda i: c.admit(str(i + 10), eligible=True, deadline_remaining=5),
                range(8),
            )
        )
    chosen = [t for t in tickets if t]
    assert len(chosen) == 1
    old = chosen[0]
    c.failed(old)
    assert c.snapshot()["recovery_wait_seconds"] == 60
    assert not c.succeeded(old, deadline_remaining=5, valid_response=True)
    for delay in (120, 240, 300, 300):
        now[0] = c.next_probe
        ticket = c.admit(str(now[0]), eligible=True, deadline_remaining=5)
        c.failed(ticket)
        assert c.snapshot()["recovery_wait_seconds"] == delay


@pytest.mark.parametrize("remaining,valid", [(0, True), (1, False)])
def test_late_or_semantically_invalid_response_cannot_recover(
    circuit, remaining, valid
):
    c, now = circuit
    open_circuit(c)
    now[0] += 30
    ticket = c.admit("new", eligible=True, deadline_remaining=1)
    assert not c.succeeded(ticket, deadline_remaining=remaining, valid_response=valid)
    c.abandon(ticket)
    assert c.snapshot()["state"] == "OPEN"


def test_different_endpoint_or_old_generation_success_cannot_unlock(circuit):
    c, now = circuit
    open_circuit(c)
    now[0] += 30
    ticket = c.admit("new", eligible=True, deadline_remaining=1)
    fake = dict(ticket, token="holding-response")
    assert not c.succeeded(fake, deadline_remaining=1, valid_response=True)
    c.abandon(ticket)
    assert not c.succeeded(ticket, deadline_remaining=1, valid_response=True)


@pytest.mark.parametrize(
    "status,recoverable", [(401, False), (403, False), (429, True), (503, True)]
)
def test_engine_preserves_common_auth_block_and_leases_only_typed_transient(
    status, recoverable, monkeypatch
):
    import httpx
    from openai import APIStatusError
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as engine_module

    engine = _build_engine()
    now = [100.0]
    engine._provider_common_circuit = EntryTransportCircuit(
        clock=lambda: now[0], owner="provider_common"
    )
    monkeypatch.setattr(engine_module, "log_error", lambda *a, **k: None)
    error = APIStatusError(
        "fixture",
        response=httpx.Response(
            status,
            headers={"retry-after": "600"},
            request=httpx.Request("POST", "https://example.invalid"),
        ),
        body=None,
    )
    for _ in range(5):
        engine._record_failure_and_maybe_disable(context_name="entry", error=error)
    assert engine.ai_disabled
    now[0] += 30
    assert (
        engine._admit_common_recovery(
            ("new", "hash"), eligible=True, deadline_remaining=5
        )
        is None
    )
    now[0] += 570
    ticket = engine._admit_common_recovery(
        ("new", "hash"), eligible=True, deadline_remaining=5
    )
    assert (ticket is not None) is recoverable
    assert engine.ai_disabled  # A lease never opens the global switch.
    assert (
        engine._admit_common_recovery(
            ("other", "hash"), eligible=True, deadline_remaining=5
        )
        is None
    )


def test_unknown_failure_or_holding_success_cannot_unlock_open_common(monkeypatch):
    import httpx
    from openai import APIStatusError
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as engine_module

    engine = _build_engine()
    now = [100.0]
    engine._provider_common_circuit = EntryTransportCircuit(
        clock=lambda: now[0], owner="provider_common"
    )
    monkeypatch.setattr(engine_module, "log_error", lambda *a, **k: None)
    error = APIStatusError(
        "fixture",
        response=httpx.Response(
            503, request=httpx.Request("POST", "https://example.invalid")
        ),
        body=None,
    )
    engine._record_failure_and_maybe_disable(
        context_name="entry", error=RuntimeError("unknown")
    )
    for _ in range(4):
        engine._record_failure_and_maybe_disable(context_name="entry", error=error)
    now[0] += 1000
    assert (
        engine.ai_disabled
        and engine._admit_common_recovery(
            ("new", "hash"), eligible=True, deadline_remaining=5
        )
        is None
    )
    engine._mark_successful_ai_call()
    assert engine.ai_disabled  # An unrelated callback cannot reset the global switch.


def test_normal_transport_success_resets_preopen_failure_chain_without_early_open():
    from src.tests.test_ai_engine_openai_transport import _build_engine

    engine = _build_engine()
    c = engine._common_circuit()
    for i in range(3):
        c.failed(c.admit(str(i), eligible=False, deadline_remaining=1))
    assert c.snapshot()["consecutive_failures"] == 3
    engine._mark_successful_ai_call()
    assert c.snapshot()["consecutive_failures"] == 0
    for i in range(2):
        c.failed(c.admit(str(i), eligible=False, deadline_remaining=1))
    assert c.snapshot()["state"] == "CLOSED"


def test_native_path_changes_do_not_accumulate_nonconsecutive_transport_timeouts(
    circuit,
):
    c, _ = circuit
    # Observed sequence: on-time model replies alternate with HTTP timeouts;
    # each reply loses live native eligibility before the final order guard.
    for i in range(8):
        failed = c.admit("timeout-" + str(i), eligible=True, deadline_remaining=3)
        assert c.failed(failed)
        replied = c.admit("reply-" + str(i), eligible=True, deadline_remaining=3)
        assert c.succeeded(
            replied, deadline_remaining=0.2, valid_response=True, execution_valid=False
        )
        assert c.snapshot()["state"] == "CLOSED"
        assert c.snapshot()["consecutive_failures"] == 0


@pytest.mark.parametrize(
    "remaining,response_valid,execution_valid",
    [(0, True, True), (1, False, True), (1, True, False)],
)
def test_recovery_cannot_use_a_late_malformed_or_native_invalid_reply(
    circuit, remaining, response_valid, execution_valid
):
    c, now = circuit
    open_circuit(c)
    now[0] += 30
    ticket = c.admit("new", eligible=True, deadline_remaining=5)
    assert not c.succeeded(
        ticket,
        deadline_remaining=remaining,
        valid_response=response_valid,
        execution_valid=execution_valid,
    )
    assert c.snapshot()["state"] == "HALF_OPEN"
    c.abandon(ticket)
    assert c.snapshot()["state"] == "OPEN"


def test_late_success_cannot_restore_recovery_after_auth_error(monkeypatch):
    import httpx
    from openai import APIStatusError
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as engine_module

    engine = _build_engine()
    now = [100.0]
    engine._provider_common_circuit = EntryTransportCircuit(
        clock=lambda: now[0], owner="provider_common"
    )
    monkeypatch.setattr(engine_module, "log_error", lambda *a, **k: None)

    def error(status):
        return APIStatusError(
            "fixture",
            response=httpx.Response(
                status, request=httpx.Request("POST", "https://example.invalid")
            ),
            body=None,
        )

    for _ in range(5):
        engine._record_failure_and_maybe_disable(context_name="entry", error=error(503))
    engine._record_failure_and_maybe_disable(context_name="entry", error=error(401))
    engine._mark_successful_ai_call()
    now[0] += 1000
    assert engine.ai_disabled and engine.consecutive_failures == 6
    assert (
        engine._admit_common_recovery(
            ("new", "hash"), eligible=True, deadline_remaining=5
        )
        is None
    )


def test_rate_limit_before_final_deadline_keeps_common_priority_and_future(monkeypatch):
    import httpx
    from openai import RateLimitError
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as O

    engine = _build_engine()
    now = [100.0]
    engine._provider_common_circuit = EntryTransportCircuit(
        clock=lambda: now[0], owner="provider_common"
    )
    monkeypatch.setattr(O, "log_error", lambda *a, **k: None)
    limited = RateLimitError(
        "fixture",
        response=httpx.Response(
            429,
            headers={"retry-after": "600"},
            request=httpx.Request("POST", "https://example.invalid"),
        ),
        body=None,
    )
    future = Future()
    future.set_running_or_notify_cancel()
    timeout = O.OpenAIResponsesHTTPError("final deadline")
    timeout.provider_common_error = limited
    timeout.entry_deadline_timeout = True
    timeout.provider_future = future
    for _ in range(5):
        engine._record_failure_and_maybe_disable(context_name="entry", error=timeout)
    assert (
        engine.ai_disabled
        and engine._common_circuit().snapshot()["reason"] == "provider_http_429"
    )
    now[0] += 601
    assert (
        engine._admit_common_recovery(
            ("new", "hash"), eligible=True, deadline_remaining=5
        )
        is None
    )
    future.set_result("late")
    assert engine._admit_common_recovery(
        ("new", "hash"), eligible=True, deadline_remaining=5
    )
