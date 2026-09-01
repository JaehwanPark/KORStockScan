"""Bounded Kiwoom read request control for episode machines.

The official Kiwoom contract identifies ``1700`` as a request-count error but
does not publish a pacing interval.  This module therefore owns a conservative
local guard shared by episode-machine ``ka10080`` market-data reads and
``kt00007`` dated order/execution plus ``ka10075`` current-unfilled
reconciliation reads.  Broker writes must not use this retry path because
replaying an ambiguous order can duplicate it.
"""

from __future__ import annotations

import fcntl
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from src.utils.constants import DATA_DIR

KA10080_API_ID = "ka10080"
KA10075_API_ID = "ka10075"
KT00007_API_ID = "kt00007"
EPISODE_READ_API_IDS = frozenset(
    {KA10080_API_ID, KA10075_API_ID, KT00007_API_ID}
)
DEFAULT_MIN_INTERVAL_SEC = 0.4
DEFAULT_PACER_PATH = DATA_DIR / "runtime" / "kiwoom_episode_ka10080.lock"
MAX_RATE_LIMIT_RETRIES = 2
_RATE_LIMIT_BACKOFF_SEC = (0.8, 1.6)

ResponseT = TypeVar("ResponseT")
PostResult = tuple[ResponseT, dict[str, Any]]


def is_kiwoom_request_limit(response: object, body: dict[str, Any] | object) -> bool:
    """Return whether a Kiwoom response is an explicit request-limit failure."""

    status_code = int(getattr(response, "status_code", 0) or 0)
    if not isinstance(body, dict):
        return status_code == 429
    code = str(body.get("return_code", body.get("rt_cd", "")) or "")
    message = str(body.get("return_msg") or body.get("err_msg") or "")
    return bool(
        status_code == 429
        or code == "1700"
        or "[1700" in message
        or "허용된 요청 개수" in message
    )


class KiwoomEpisodeReadPacer:
    """Serialize supported episode reads across independent processes."""

    def __init__(
        self,
        *,
        state_path: Path = DEFAULT_PACER_PATH,
        min_interval_sec: float = DEFAULT_MIN_INTERVAL_SEC,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.state_path = Path(state_path)
        self.min_interval_sec = max(0.0, float(min_interval_sec))
        self.clock = clock
        self.sleep = sleep

    def wait(self, api_id: str) -> None:
        if str(api_id) not in EPISODE_READ_API_IDS or self.min_interval_sec <= 0:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("a+", encoding="ascii") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            try:
                last_request_at = float(handle.read().strip() or "0")
            except ValueError:
                last_request_at = 0.0
            now = float(self.clock())
            # Ignore corrupt/future state instead of imposing an unbounded wait.
            if last_request_at < 0 or last_request_at > now + self.min_interval_sec:
                last_request_at = 0.0
            reserved_at = max(now, last_request_at + self.min_interval_sec)
            delay = reserved_at - now
            if delay > 0:
                self.sleep(delay)
            handle.seek(0)
            handle.truncate()
            handle.write(f"{reserved_at:.9f}\n")
            handle.flush()
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class SameMinuteSnapshotCache:
    """Process-local cache; completed one-minute bars change at minute boundaries."""

    def __init__(self) -> None:
        self._key: tuple[object, object] | None = None
        self._snapshot: object | None = None

    def get(self, key: tuple[object, object]) -> object | None:
        return self._snapshot if self._key == key else None

    def put(self, key: tuple[object, object], snapshot: object) -> None:
        self._key = key
        self._snapshot = snapshot


class ShortTtlSnapshotCache:
    """Process-local cache used to collapse duplicate account reads per cycle."""

    def __init__(
        self,
        *,
        ttl_sec: float = 1.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.ttl_sec = max(0.0, float(ttl_sec))
        self.clock = clock
        self._key: object | None = None
        self._snapshot: object | None = None
        self._stored_at = 0.0

    def get(self, key: object) -> object | None:
        now = float(self.clock())
        if (
            self._key == key
            and self._snapshot is not None
            and now >= self._stored_at
            and now - self._stored_at <= self.ttl_sec
        ):
            return self._snapshot
        return None

    def put(self, key: object, snapshot: object) -> None:
        self._key = key
        self._snapshot = snapshot
        self._stored_at = float(self.clock())


def snapshot_contains_latest_completed_minute(
    *, latest_timestamp: datetime, minute_floor: datetime
) -> bool:
    """Allow minute-wide reuse only after the immediately prior bar is present."""

    return minute_floor - timedelta(minutes=1) <= latest_timestamp < minute_floor


_DEFAULT_PACER = KiwoomEpisodeReadPacer()


def post_kiwoom_episode_read(
    *,
    api_id: str,
    post_once: Callable[[], PostResult[ResponseT]],
    pacing_enabled: bool,
    pacer: KiwoomEpisodeReadPacer | None = None,
    sleep: Callable[[float], None] = time.sleep,
    cache: ShortTtlSnapshotCache | None = None,
    cache_key: object | None = None,
) -> PostResult[ResponseT]:
    """POST one read with bounded 1700 recovery; reject non-read retry use."""

    if str(api_id) not in EPISODE_READ_API_IDS:
        raise ValueError("episode_read_retry_requires_supported_read_api")
    if cache is not None and cache_key is not None:
        cached = cache.get(cache_key)
        if cached is not None:
            return cast(PostResult[ResponseT], cached)
    active_pacer = pacer or _DEFAULT_PACER
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        if pacing_enabled:
            active_pacer.wait(api_id)
        response, body = post_once()
        if not is_kiwoom_request_limit(response, body):
            code = str(body.get("return_code", body.get("rt_cd", "")))
            if (
                cache is not None
                and cache_key is not None
                and int(getattr(response, "status_code", 0) or 0) == 200
                and code == "0"
            ):
                cache.put(cache_key, (response, body))
            return response, body
        if attempt >= MAX_RATE_LIMIT_RETRIES:
            return response, body
        sleep(_RATE_LIMIT_BACKOFF_SEC[attempt])
    raise AssertionError("unreachable_episode_read_retry_loop")
