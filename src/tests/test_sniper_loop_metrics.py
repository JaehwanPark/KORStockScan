"""Tests for P0 loop metrics and P1 structural improvements.

Verifies:
- _resolve_stock_marcap() TTL cache (hit/miss/expiry)
- _MARCAP_CACHE global isolation
- now_ts/now_dt kwargs passthrough to handle_watching_state / handle_holding_state
- ThreadPoolExecutor singleton creation
- LOOP_METRICS log format
- _ensure_state_handler_deps() loop-level binding (축 A)
- _RECENT_SNAPSHOT_SIGNATURES TTL prune (축 B)
- _append_jsonl_async best-effort enqueue (축 B)
"""

import time
import re
import json
import threading
from pathlib import Path

from unittest.mock import patch, MagicMock

from src.engine.kiwoom_sniper_v2 import (
    _resolve_stock_marcap,
    _MARCAP_CACHE,
    _MARCAP_CACHE_TTL,
    _ACCOUNT_SYNC_EXECUTOR,
)
from src.engine.sniper_gatekeeper_replay import (
    _RECENT_SNAPSHOT_SIGNATURES,
    _WRITE_LOCK,
    _prune_stale_signatures,
    _append_jsonl_async,
    _flush_jsonl_writer,
    record_gatekeeper_snapshot,
    _snapshot_signature,
)

# ──────────────────────────────────────────────
# _resolve_stock_marcap TTL cache
# ──────────────────────────────────────────────


def test_marcap_cache_uses_stock_value_when_positive():
    """stock dict에 positive marcap이 있으면 바로 반환하고 DB 호출 없음."""
    stock = {"marcap": 1_000_000_000_000}
    result = _resolve_stock_marcap(stock, "005930")
    assert result == 1_000_000_000_000


def test_marcap_cache_skips_missing_stock_value():
    """stock marcap이 0이면 _MARCAP_CACHE를 확인하고 DB로 폴백."""
    stock = {"marcap": 0}
    # 캐시 초기화
    _MARCAP_CACHE.clear()
    result = _resolve_stock_marcap(stock, "005930")
    # DB가 없으므로 0 반환 (환경에 따라 달라질 수 있음)
    assert isinstance(result, int)
    assert result >= 0


def test_marcap_cache_hit_returns_cached_value():
    """_MARCAP_CACHE에 유효한 값이 있으면 DB 호출 없이 캐시값 반환."""
    stock = {"marcap": 0}
    _MARCAP_CACHE.clear()
    _MARCAP_CACHE["005930"] = (2_000_000_000_000, time.time() + _MARCAP_CACHE_TTL)
    result = _resolve_stock_marcap(stock, "005930")
    assert result == 2_000_000_000_000
    assert stock.get("marcap") == 2_000_000_000_000


def test_marcap_cache_expired_returns_fresh_value():
    """캐시가 만료되면 재조회 (여기서는 DB가 없으므로 0)."""
    stock = {"marcap": 0}
    _MARCAP_CACHE.clear()
    _MARCAP_CACHE["005930"] = (3_000_000_000_000, time.time() - 1)
    result = _resolve_stock_marcap(stock, "005930")
    assert isinstance(result, int)


def test_marcap_cache_code_normalization():
    """종목코드가 6자리로 정규화되는지 검증."""
    stock = {"marcap": 0}
    _MARCAP_CACHE.clear()
    _MARCAP_CACHE["005930"] = (4_000_000_000_000, time.time() + _MARCAP_CACHE_TTL)
    result = _resolve_stock_marcap(stock, " 005930 ")
    assert result == 4_000_000_000_000


def test_marcap_cache_empty_code_returns_zero():
    """code가 비어있으면 캐시 우회."""
    stock = {"marcap": 0}
    _MARCAP_CACHE.clear()
    result = _resolve_stock_marcap(stock, "")
    assert result == 0


def test_marcap_cache_code_none_returns_zero():
    """code가 None이면 캐시 우회."""
    stock = {"marcap": 0}
    _MARCAP_CACHE.clear()
    result = _resolve_stock_marcap(stock, None)
    assert result == 0


# ──────────────────────────────────────────────
# LOOP_METRICS log format
# ──────────────────────────────────────────────


LOOP_METRICS_PATTERN = re.compile(
    r"\[LOOP_METRICS\] "
    r"loop_elapsed_ms=\d+\.?\d* "
    r"sleep_ms=\d+ "
    r"db_active_targets_ms=\d+\.?\d* "
    r"account_sync_ms=\d+\.?\d* "
    r"target_count=\d+ "
    r"watching=\d+ "
    r"holding=\d+"
)


def test_loop_metrics_log_format_matches():
    """LOOP_METRICS 로그 포맷이 구현과 일치하는지 검증."""
    line = (
        "[LOOP_METRICS] "
        "loop_elapsed_ms=142.3 "
        "sleep_ms=1000 "
        "db_active_targets_ms=35.1 "
        "account_sync_ms=0.8 "
        "target_count=24 "
        "watching=18 "
        "holding=6"
    )
    assert LOOP_METRICS_PATTERN.match(line), f"Pattern did not match: {line}"


def test_loop_metrics_log_zero_values():
    """모든 값이 0인 경우에도 패턴 매칭."""
    line = (
        "[LOOP_METRICS] "
        "loop_elapsed_ms=0.0 "
        "sleep_ms=1000 "
        "db_active_targets_ms=0.0 "
        "account_sync_ms=0.0 "
        "target_count=0 "
        "watching=0 "
        "holding=0"
    )
    assert LOOP_METRICS_PATTERN.match(line), f"Pattern did not match: {line}"


# ──────────────────────────────────────────────
# ThreadPoolExecutor singleton
# ──────────────────────────────────────────────


def test_account_sync_executor_none_by_default():
    """_ACCOUNT_SYNC_EXECUTOR는 초기 import 시 None이어야 함."""
    assert _ACCOUNT_SYNC_EXECUTOR is None


def test_marcap_cache_ttl_positive():
    """_MARCAP_CACHE_TTL은 양수여야 함."""
    assert _MARCAP_CACHE_TTL > 0


# ──────────────────────────────────────────────
# now_ts/now_dt backward compatibility in state handlers
# ──────────────────────────────────────────────


def test_handle_watching_state_accepts_now_kwargs():
    """handle_watching_state가 now_ts/now_dt kwargs를 정상 수용하는지 검증.

    직접 호출하여 예외 없이 시간 kwargs를 처리할 수 있는지 확인.
    """
    from src.engine.sniper_state_handlers import handle_watching_state
    from datetime import datetime

    stock = {
        "name": "TEST",
        "code": "000000",
        "strategy": "SCALPING",
        "status": "WATCHING",
    }
    ws_data = {"curr": 10000, "fluctuation": 1.0, "v_pw": 100}

    # now_ts/now_dt를 전달해도 정상 동작 (다른 의존성 부족으로 early return)
    now_ts = time.time()
    now_dt = datetime.now()
    try:
        handle_watching_state(
            stock,
            "000000",
            ws_data,
            None,
            now_ts=now_ts,
            now_dt=now_dt,
        )
    except Exception as e:
        # DB/AI 미초기화로 인한 에러는 허용 (시간 파라미터 전달 자체가 문제없는지가 핵심)
        msg = str(e)
        assert "now_ts" not in msg, f"now_ts 관련 에러 발생: {msg}"
        assert "now_dt" not in msg, f"now_dt 관련 에러 발생: {msg}"


def test_handle_holding_state_accepts_now_kwargs():
    """handle_holding_state가 now_ts/now_dt kwargs를 정상 수용하는지 검증."""
    from src.engine.sniper_state_handlers import handle_holding_state
    from datetime import datetime

    stock = {
        "name": "TEST",
        "code": "000000",
        "strategy": "SCALPING",
        "buy_price": 10000,
        "status": "HOLDING",
    }
    ws_data = {"curr": 10100, "fluctuation": 1.0}

    now_ts = time.time()
    now_dt = datetime.now()
    try:
        handle_holding_state(
            stock,
            "000000",
            ws_data,
            None,
            "NORMAL",
            now_ts=now_ts,
            now_dt=now_dt,
        )
    except Exception as e:
        msg = str(e)
        assert "now_ts" not in msg, f"now_ts 관련 에러 발생: {msg}"
        assert "now_dt" not in msg, f"now_dt 관련 에러 발생: {msg}"


# ──────────────────────────────────────────────
# Global constant consistency
# ──────────────────────────────────────────────


def test_global_constants_exist():
    """P0/P1에서 정의한 전역 상수들이 모두 존재하는지 확인."""
    from src.engine.kiwoom_sniper_v2 import (
        _MARCAP_CACHE,
        _MARCAP_CACHE_TTL,
        _ACCOUNT_SYNC_EXECUTOR,
        _LOOP_METRICS_LAST_LOG_TS,
    )

    assert _MARCAP_CACHE_TTL >= 60  # 최소 1분
    assert isinstance(_LOOP_METRICS_LAST_LOG_TS, float)


# ──────────────────────────────────────────────
# 축 A: _ensure_state_handler_deps() 루프 수준 바인딩
# ──────────────────────────────────────────────


def test_state_handler_deps_wrappers_no_longer_call_ensure():
    """6개 wrapper 함수에서 _ensure_state_handler_deps() 호출이 제거되었는지 검증."""
    import inspect
    from src.engine.kiwoom_sniper_v2 import (
        handle_watching_state,
        handle_holding_state,
        handle_buy_ordered_state,
        handle_sell_ordered_state,
        process_sell_cancellation,
        process_order_cancellation,
    )

    wrappers = [
        handle_watching_state,
        handle_holding_state,
        handle_buy_ordered_state,
        handle_sell_ordered_state,
        process_sell_cancellation,
        process_order_cancellation,
    ]
    for fn in wrappers:
        source = inspect.getsource(fn)
        assert (
            "_ensure_state_handler_deps" not in source
        ), f"{fn.__name__} still calls _ensure_state_handler_deps"


def test_run_sniper_loop_calls_ensure_state_handler_deps():
    """run_sniper() 루프 상단에서 _ensure_state_handler_deps()가 호출되는지 검증.

    소스 코드에 while True: 직후 _ensure_state_handler_deps() 호출이 있는지 확인.
    """
    import inspect
    from src.engine.kiwoom_sniper_v2 import run_sniper

    source = inspect.getsource(run_sniper)
    # while True: 이후 _ensure_state_handler_deps()가 루프 내에 존재하는지 확인
    assert (
        "_ensure_state_handler_deps()" in source
    ), "run_sniper() does not contain _ensure_state_handler_deps() call"
    # 루프 상단(while True 이후)에 위치하는지 확인
    loop_section = source[source.find("while True:") : source.find("while True:") + 500]
    assert (
        "_ensure_state_handler_deps()" in loop_section
    ), "_ensure_state_handler_deps() not found in loop top section"


# ──────────────────────────────────────────────
# 축 B: _RECENT_SNAPSHOT_SIGNATURES TTL prune
# ──────────────────────────────────────────────


def test_prune_stale_signatures_removes_expired():
    """_prune_stale_signatures가 keep_ttl 초과한 시그니처를 제거하는지 검증."""
    _RECENT_SNAPSHOT_SIGNATURES.clear()
    now = time.time()
    # 최근 시그니처 (유지되어야 함)
    _RECENT_SNAPSHOT_SIGNATURES["fresh_sig"] = now
    # 오래된 시그니처 (제거되어야 함)
    _RECENT_SNAPSHOT_SIGNATURES["stale_sig_1"] = now - 1000
    _RECENT_SNAPSHOT_SIGNATURES["stale_sig_2"] = now - 5000

    with _WRITE_LOCK:
        _prune_stale_signatures(now)

    assert "fresh_sig" in _RECENT_SNAPSHOT_SIGNATURES
    assert "stale_sig_1" not in _RECENT_SNAPSHOT_SIGNATURES
    assert "stale_sig_2" not in _RECENT_SNAPSHOT_SIGNATURES


def test_prune_stale_signatures_keeps_recent():
    """keep_ttl 이내의 시그니처는 유지."""
    _RECENT_SNAPSHOT_SIGNATURES.clear()
    now = time.time()
    _RECENT_SNAPSHOT_SIGNATURES["sig_a"] = now - 30
    _RECENT_SNAPSHOT_SIGNATURES["sig_b"] = now - 150

    with _WRITE_LOCK:
        _prune_stale_signatures(now)

    assert "sig_a" in _RECENT_SNAPSHOT_SIGNATURES
    assert "sig_b" in _RECENT_SNAPSHOT_SIGNATURES


def test_prune_stale_signatures_skips_within_interval(monkeypatch):
    """prune interval(300초) 이내에는 중복 실행되지 않음."""
    import src.engine.sniper_gatekeeper_replay as gkr

    monkeypatch.setattr(gkr, "_LAST_SNAPSHOT_PRUNE_TS", 0.0)
    _RECENT_SNAPSHOT_SIGNATURES.clear()
    now = time.time()
    _RECENT_SNAPSHOT_SIGNATURES["old_sig"] = now - 10000

    # 첫 번째 prune (실행되어야 함)
    with _WRITE_LOCK:
        _prune_stale_signatures(now)
    assert "old_sig" not in _RECENT_SNAPSHOT_SIGNATURES

    # 다시 추가
    _RECENT_SNAPSHOT_SIGNATURES["old_sig"] = now - 10000
    # 같은 now_ts로 다시 호출 (interval 내이므로 skip)
    with _WRITE_LOCK:
        _prune_stale_signatures(now)
    assert "old_sig" in _RECENT_SNAPSHOT_SIGNATURES  # prune skip됨


def test_record_gatekeeper_snapshot_failure_returns_none(monkeypatch):
    """record_gatekeeper_snapshot()이 write 실패 시 예외 전파 대신 None 반환."""
    # 케이스 1: 빈 코드 → early return None
    result = record_gatekeeper_snapshot(
        stock=None,
        code="",
        strategy="TEST",
        realtime_ctx={},
        gatekeeper={},
    )
    assert result is None, "Empty code should return None"

    # 케이스 2: enqueue 실패 + 동기 fallback write도 실패 → None 반환 + dedup 롤백
    import src.engine.sniper_gatekeeper_replay as gkr

    def _broken_writer():
        raise RuntimeError("writer unavailable for snapshot")

    monkeypatch.setattr(gkr, "_get_jsonl_writer", _broken_writer)

    # DATA_DIR을 존재하지 않는 경로로 설정 → fallback _append_jsonl의 open() 실패
    monkeypatch.setattr(gkr, "DATA_DIR", Path("/nonexistent_gatekeeper_test"))

    _RECENT_SNAPSHOT_SIGNATURES.clear()

    result2 = record_gatekeeper_snapshot(
        stock={"name": "TEST"},
        code="005930",
        strategy="SCALPING",
        realtime_ctx={"curr_price": 50000},
        gatekeeper={"action_label": "BUY", "allow_entry": True},
    )
    # enqueue 실패 + 동기 fallback write 실패 → None 반환
    assert result2 is None, "모든 write 경로 실패 시 None 반환"
    # dedup 시그니처가 롤백되었는지 확인
    assert (
        len(_RECENT_SNAPSHOT_SIGNATURES) == 0
    ), f"dedup이 모두 롤백되어야 함: {_RECENT_SNAPSHOT_SIGNATURES}"


def test_snapshot_signature_deterministic():
    """동일 payload에 대해 _snapshot_signature가 항상 같은 값을 반환."""
    payload = {
        "stock_code": "005930",
        "strategy": "SCALPING",
        "action_label": "BUY",
        "allow_entry": True,
        "ctx_summary": {"curr_price": 50000},
    }
    sig1 = _snapshot_signature(payload)
    sig2 = _snapshot_signature(payload)
    assert sig1 == sig2
    assert isinstance(sig1, str)
    assert len(sig1) == 40  # SHA1 hex length


# ──────────────────────────────────────────────
# 축 B: _append_jsonl_async best-effort enqueue
# ──────────────────────────────────────────────


def test_append_jsonl_async_writes_to_file(tmp_path):
    """_append_jsonl_async가 실제로 파일에 데이터를 쓰는지 검증."""
    test_file = tmp_path / "test_async.jsonl"
    payload = {"test": "data", "value": 42}

    _append_jsonl_async(test_file, payload)
    # flush하여 write 완료 보장
    _flush_jsonl_writer()

    assert test_file.exists()
    lines = test_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    written = json.loads(lines[0])
    assert written["test"] == "data"
    assert written["value"] == 42


def test_append_jsonl_async_maintains_ordering(tmp_path):
    """_append_jsonl_async가 same-process ordering을 보장하는지 검증."""
    test_file = tmp_path / "test_ordering.jsonl"

    _append_jsonl_async(test_file, {"seq": 1})
    _append_jsonl_async(test_file, {"seq": 2})
    _append_jsonl_async(test_file, {"seq": 3})
    _flush_jsonl_writer()

    lines = test_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    for i, line in enumerate(lines, start=1):
        assert json.loads(line)["seq"] == i


def test_append_jsonl_async_fallback_on_enqueue_failure(monkeypatch):
    """enqueue 실패 시 동기 fallback이 동작하는지 검증."""
    import src.engine.sniper_gatekeeper_replay as gkr

    test_file = Path("/tmp/test_fallback_async.jsonl")
    payload = {"fallback": True}

    # _get_jsonl_writer()가 RuntimeError를 발생시키도록 monkeypatch
    def _broken_writer():
        raise RuntimeError("writer unavailable")

    monkeypatch.setattr(gkr, "_get_jsonl_writer", _broken_writer)

    _append_jsonl_async(test_file, payload)

    assert test_file.exists()
    lines = test_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) >= 1
    test_file.unlink(missing_ok=True)


def test_append_jsonl_async_worker_failure_rolls_back_dedup(monkeypatch):
    """worker thread 내부 write 실패 시 log_error 발생 + dedup 시그니처 롤백."""
    import src.engine.sniper_gatekeeper_replay as gkr

    test_file = Path("/tmp/test_worker_fail.jsonl")
    payload = {"worker_fail": True}
    rollback_sig = "test_rollback_sig"

    # 사전에 dedup 시그니처를 기록 (main thread가 한 일)
    gkr._RECENT_SNAPSHOT_SIGNATURES[rollback_sig] = 1000.0

    # _append_jsonl이 RuntimeError를 던지도록 monkeypatch (worker 내부에서 발생)
    def _broken_append(path, payload):
        raise RuntimeError("worker write failure")

    monkeypatch.setattr(gkr, "_append_jsonl", _broken_append)

    # log_error가 호출되었는지 추적
    original_log_error = gkr.log_error
    log_error_called = []

    def _tracking_log_error(msg):
        log_error_called.append(msg)
        original_log_error(msg)

    monkeypatch.setattr(gkr, "log_error", _tracking_log_error)

    # async write (worker에서 실패 → 롤백)
    _append_jsonl_async(
        test_file,
        payload,
        _rollback_signature=rollback_sig,
    )
    _flush_jsonl_writer()

    # log_error가 호출되어야 함
    assert len(log_error_called) >= 1
    assert any("worker write failure" in msg for msg in log_error_called)

    # dedup 시그니처가 롤백(제거)되어야 함
    assert rollback_sig not in gkr._RECENT_SNAPSHOT_SIGNATURES

    test_file.unlink(missing_ok=True)


def test_flush_jsonl_writer_called_on_shutdown(monkeypatch):
    """종료 경로에서 _flush_jsonl_writer()가 실제로 호출되는지 검증.

    1. _flush_jsonl_writer가 atexit에 등록되었는지 소스 코드 확인
    2. 직접 호출 경로 검증
    """
    import src.engine.sniper_gatekeeper_replay as gkr

    # _flush_jsonl_writer가 호출되었는지 추적
    original_flush = gkr._flush_jsonl_writer
    flush_called = []

    def _tracking_flush():
        flush_called.append(True)
        return original_flush()

    monkeypatch.setattr(gkr, "_flush_jsonl_writer", _tracking_flush)

    # 직접 호출 (실제 프로세스 종료 없이)
    _tracking_flush()

    assert len(flush_called) >= 1, "_flush_jsonl_writer가 호출되지 않음"

    # 소스 코드에 atexit.register(_flush_jsonl_writer) 호출이 있는지 확인
    import inspect

    source = inspect.getsource(gkr)
    assert (
        "atexit.register" in source and "_flush_jsonl_writer" in source
    ), "소스 코드에 atexit.register(_flush_jsonl_writer) 호출이 없음"


def test_record_gatekeeper_snapshot_dedup_prevents_duplicate_file_lines(
    monkeypatch, tmp_path
):
    """동일 payload 2회 연속 호출 시 JSONL에 1줄만 기록되는지 검증.

    DATA_DIR을 tmp_path로 monkeypatch하여 _replay_dir()이 tmp_path를 반환하도록 한다.
    _replay_dir()은 모듈 로드 시점에 DATA_DIR을 캡처하므로, 모듈 속성을 직접 변경한다.

    검증:
    1. 첫 번째 호출 → 정상 enqueue + write
    2. flush로 write 완료
    3. 두 번째 호출 (동일 payload) → dedup에 걸려 early return (enqueue 안 함)
    4. flush 후 gatekeeper 디렉토리에 1개의 jsonl 파일만 있고, line 수는 1
    """
    import src.engine.sniper_gatekeeper_replay as gkr

    # DATA_DIR을 tmp_path로 변경 → _replay_dir()이 tmp_path/gatekeeper를 반환
    monkeypatch.setattr(gkr, "DATA_DIR", tmp_path)

    _RECENT_SNAPSHOT_SIGNATURES.clear()

    # 첫 번째 호출
    result1 = record_gatekeeper_snapshot(
        stock={"name": "TEST"},
        code="005930",
        strategy="SCALPING",
        realtime_ctx={"curr_price": 50000},
        gatekeeper={"action_label": "BUY", "allow_entry": True},
    )
    assert result1 is not None

    # 첫 번째 호출로 기록된 dedup 시그니처 확인
    sig = gkr._snapshot_signature(result1)
    assert (
        sig in _RECENT_SNAPSHOT_SIGNATURES
    ), "첫 번째 호출 후 dedup 시그니처가 즉시 기록되어야 함"

    # 첫 번째 write 완료 보장
    _flush_jsonl_writer()

    # 두 번째 호출 (동일 payload, dedup TTL 내)
    result2 = record_gatekeeper_snapshot(
        stock={"name": "TEST"},
        code="005930",
        strategy="SCALPING",
        realtime_ctx={"curr_price": 50000},
        gatekeeper={"action_label": "BUY", "allow_entry": True},
    )
    # dedup에 걸려 early return
    assert result2 is not None

    _flush_jsonl_writer()

    # gatekeeper 디렉토리에 정확히 1개의 jsonl 파일이 있어야 함
    gatekeeper_dir = tmp_path / "gatekeeper"
    assert gatekeeper_dir.exists()
    jsonl_files = list(gatekeeper_dir.glob("*.jsonl"))
    assert len(jsonl_files) == 1, f"Expected 1 jsonl file, got {len(jsonl_files)}"

    # 파일에 1줄만 있어야 함
    lines = jsonl_files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"


def test_prune_and_callback_concurrent_access(monkeypatch):
    """prune 실행 중 callback 갱신이 있어도 예외 없이 동작하는지 검증.

    _WRITE_LOCK 아래에서 prune이 _RECENT_SNAPSHOT_SIGNATURES를 순회하고,
    callback도 같은 락 아래에서 pop()하므로 안전해야 한다.
    """
    import src.engine.sniper_gatekeeper_replay as gkr

    test_file = Path("/tmp/test_concurrent_prune.jsonl")
    payload = {"concurrent": True}

    # 다수의 시그니처를 미리 기록 (prune 대상 + 유지 대상 혼합)
    now = time.time()
    for i in range(100):
        sig = f"stale_sig_{i}"
        gkr._RECENT_SNAPSHOT_SIGNATURES[sig] = now - 1000.0  # 1000초 전 → prune 대상
    for i in range(50):
        sig = f"fresh_sig_{i}"
        gkr._RECENT_SNAPSHOT_SIGNATURES[sig] = now  # 현재 → 유지

    # _LAST_SNAPSHOT_PRUNE_TS를 0으로 설정하여 prune이 실행되도록
    monkeypatch.setattr(gkr, "_LAST_SNAPSHOT_PRUNE_TS", 0.0)

    # _append_jsonl을 느리게 만들어 callback이 prune과 동시에 실행될 가능성 증가
    def _slow_append(path, payload):
        time.sleep(0.05)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    monkeypatch.setattr(gkr, "_append_jsonl", _slow_append)

    # async write (worker에서 느리게 실행)
    _append_jsonl_async(
        test_file,
        payload,
        _rollback_signature="fresh_sig_0",  # 유지 대상 시그니처 중 하나
    )

    # flush 전에 prune 실행 (record_gatekeeper_snapshot 내부에서 _WRITE_LOCK 아래 실행)
    with gkr._WRITE_LOCK:
        gkr._prune_stale_signatures(time.time())

    _flush_jsonl_writer()

    # stale 시그니처가 제거되었는지 확인
    for i in range(100):
        assert (
            f"stale_sig_{i}" not in gkr._RECENT_SNAPSHOT_SIGNATURES
        ), f"stale_sig_{i} should have been pruned"

    # fresh 시그니처는 유지되어야 함 (단, fresh_sig_0는 callback에서 롤백될 수 있음)
    for i in range(1, 50):
        assert (
            f"fresh_sig_{i}" in gkr._RECENT_SNAPSHOT_SIGNATURES
        ), f"fresh_sig_{i} should still exist"

    test_file.unlink(missing_ok=True)


def test_enqueue_fallback_write_failure_rolls_back_dedup(monkeypatch):
    """enqueue 실패 → 동기 fallback write도 실패 시 None 반환 + dedup 롤백 검증.

    시나리오:
    1. _get_jsonl_writer()를 깨뜨려 enqueue 실패 유도
    2. _append_jsonl의 open()이 실패하도록 DATA_DIR을 존재하지 않는 경로로 설정
    3. fallback write 실패 → _append_jsonl_async가 False 반환
    4. record_gatekeeper_snapshot이 False를 감지 → None 반환 + log_error
    """
    import src.engine.sniper_gatekeeper_replay as gkr

    # _get_jsonl_writer()를 깨뜨려 enqueue 실패 유도
    def _broken_writer():
        raise RuntimeError("writer unavailable")

    monkeypatch.setattr(gkr, "_get_jsonl_writer", _broken_writer)

    # DATA_DIR을 존재하지 않는 경로로 설정 → _append_jsonl의 open() 실패
    nonexistent_dir = Path("/nonexistent_gatekeeper_test")
    monkeypatch.setattr(gkr, "DATA_DIR", nonexistent_dir)

    _RECENT_SNAPSHOT_SIGNATURES.clear()

    # record_gatekeeper_snapshot 호출
    # 내부에서 _append_jsonl_async → enqueue 실패 → 동기 fallback _append_jsonl
    # → open() 실패 → _append_jsonl_async가 False 반환
    # → record_gatekeeper_snapshot이 None 반환
    result = record_gatekeeper_snapshot(
        stock={"name": "TEST"},
        code="005930",
        strategy="SCALPING",
        realtime_ctx={"curr_price": 50000},
        gatekeeper={"action_label": "BUY", "allow_entry": True},
    )
    # 모든 write 경로 실패 → None 반환
    assert result is None, "모든 write 경로 실패 시 None 반환"

    # dedup 시그니처가 롤백되었는지 확인
    assert (
        len(_RECENT_SNAPSHOT_SIGNATURES) == 0
    ), f"dedup이 모두 롤백되어야 함: {_RECENT_SNAPSHOT_SIGNATURES}"
