"""Cross-process rate control for Kiwoom domestic-stock read TRs.

Kiwoom documents separate per-token limits of five order TRs and five read TRs
per second for domestic stocks.  This module owns only the read bucket.  It
must never be used to pace, retry, or replay broker order writes.

The coordinator stores only a digest of ``origin + token`` in the filename;
the bearer token itself is never persisted or logged.  A sliding one-second
window is shared by all participating processes.  Source-only callers reserve
one of the five production slots for runtime-required or execution-critical
reads.  Kiwoom's mock environment is scoped per TR at one request per second.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from src.utils.constants import DATA_DIR

DOMESTIC_READ_BUCKET = "domestic_stock_read_tr"
REQUEST_CLASS_SOURCE_ONLY = "source_only"
REQUEST_CLASS_RUNTIME_REQUIRED = "runtime_required"
REQUEST_CLASS_EXECUTION_CRITICAL = "execution_critical"
REQUEST_CLASSES = frozenset(
    {
        REQUEST_CLASS_SOURCE_ONLY,
        REQUEST_CLASS_RUNTIME_REQUIRED,
        REQUEST_CLASS_EXECUTION_CRITICAL,
    }
)
MAX_READ_REQUESTS_PER_WINDOW = 5
SOURCE_ONLY_REQUESTS_PER_WINDOW = 4
MOCK_READ_REQUESTS_PER_WINDOW = 1
READ_WINDOW_SEC = 1.0
DEFAULT_RATE_LIMIT_COOLDOWN_SEC = 3.0
DEFAULT_REQUIRED_MAX_WAIT_SEC = 3.25
DEFAULT_SOURCE_ONLY_MAX_WAIT_SEC = 1.25
RATE_LIMIT_RETURN_CODES = frozenset({"1700", "1701", "1702"})
STATE_SCHEMA_VERSION = "kiwoom_domestic_read_rate_control_v1"
DEFAULT_STATE_DIR = DATA_DIR / "runtime" / "kiwoom_read_rate_control"


@dataclass(frozen=True)
class ReadRequestAdmission:
    admitted: bool
    reason: str
    request_class: str
    request_owner: str
    api_id: str
    request_code: str
    pid: int
    waited_sec: float
    requests_in_window_before: int
    effective_limit: int
    max_limit: int
    window_sec: float
    cooldown_remaining_sec: float
    scope_digest: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_kiwoom_read_rate_limit(
    *, http_status_code: object = None, response_body: object = None
) -> bool:
    """Recognize Kiwoom HTTP and documented body-level read limits."""

    try:
        status_code = int(http_status_code or 0)
    except (TypeError, ValueError):
        status_code = 0
    if status_code == 429:
        return True
    if not isinstance(response_body, dict):
        return False
    code = str(
        response_body.get("return_code") or response_body.get("rt_cd") or ""
    ).strip()
    message = str(response_body.get("return_msg") or response_body.get("err_msg") or "")
    return bool(
        code in RATE_LIMIT_RETURN_CODES
        or "허용된 API 요청 개수" in message
        or "허용된 전체 요청 개수" in message
        or "허용된 그룹 요청 개수" in message
    )


def _safe_label(value: object, *, fallback: str, limit: int = 96) -> str:
    label = str(value or "").strip()
    if not label:
        return fallback
    return "".join(
        character if character.isalnum() or character in "._:-" else "_"
        for character in label[:limit]
    )


def _normalized_origin(endpoint: str) -> str:
    parsed = urlsplit(str(endpoint or ""))
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
    return "unknown_kiwoom_origin"


def _is_mock_origin(endpoint: str) -> bool:
    return urlsplit(str(endpoint or "")).hostname == "mockapi.kiwoom.com"


def _scope_digest(*, token: str, endpoint: str, api_id: str = "") -> str:
    normalized_token = str(token or "").replace("Bearer ", "").strip()
    mock_api_scope = (
        str(api_id or "unknown_api_id") if _is_mock_origin(endpoint) else "all_read_tr"
    )
    raw = (
        f"{DOMESTIC_READ_BUCKET}|{_normalized_origin(endpoint)}|"
        f"{mock_api_scope}|{normalized_token}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class KiwoomReadRequestCoordinator:
    """Reserve per-token domestic read capacity across local processes."""

    def __init__(
        self,
        *,
        state_dir: Path = DEFAULT_STATE_DIR,
        max_requests: int = MAX_READ_REQUESTS_PER_WINDOW,
        source_only_limit: int = SOURCE_ONLY_REQUESTS_PER_WINDOW,
        window_sec: float = READ_WINDOW_SEC,
        cooldown_sec: float = DEFAULT_RATE_LIMIT_COOLDOWN_SEC,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.state_dir = Path(state_dir)
        self.max_requests = max(1, int(max_requests))
        self.source_only_limit = max(1, min(int(source_only_limit), self.max_requests))
        self.window_sec = max(0.001, float(window_sec))
        self.cooldown_sec = max(0.0, float(cooldown_sec))
        self.clock = clock
        self.sleep = sleep

    def _state_path(
        self, *, token: str, endpoint: str, api_id: str = ""
    ) -> tuple[Path, str]:
        digest = _scope_digest(token=token, endpoint=endpoint, api_id=api_id)
        return self.state_dir / f"{digest}.json", digest

    def _open_locked_state(self, path: Path):
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.state_dir, 0o700)
        except OSError:
            pass
        handle = path.open("a+", encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    @staticmethod
    def _read_state(handle) -> tuple[dict[str, Any], str | None]:
        handle.seek(0)
        raw = handle.read().strip()
        if not raw:
            return {}, None
        try:
            state = json.loads(raw)
        except json.JSONDecodeError:
            return {}, "shared_read_rate_state_malformed"
        if not isinstance(state, dict):
            return {}, "shared_read_rate_state_not_object"
        schema = state.get("schema_version")
        if schema not in {None, STATE_SCHEMA_VERSION}:
            return {}, "shared_read_rate_state_schema_mismatch"
        return state, None

    @staticmethod
    def _write_state(handle, state: dict[str, Any]) -> None:
        handle.seek(0)
        handle.truncate()
        handle.write(json.dumps(state, ensure_ascii=True, separators=(",", ":")) + "\n")
        handle.flush()

    def _admission(
        self,
        *,
        admitted: bool,
        reason: str,
        request_class: str,
        request_owner: str,
        api_id: str,
        request_code: str,
        waited_sec: float,
        requests_before: int,
        effective_limit: int,
        max_limit: int,
        cooldown_remaining: float,
        scope_digest: str,
    ) -> ReadRequestAdmission:
        return ReadRequestAdmission(
            admitted=admitted,
            reason=reason,
            request_class=request_class,
            request_owner=request_owner,
            api_id=api_id,
            request_code=request_code,
            pid=os.getpid(),
            waited_sec=round(max(0.0, waited_sec), 6),
            requests_in_window_before=max(0, int(requests_before)),
            effective_limit=effective_limit,
            max_limit=max_limit,
            window_sec=self.window_sec,
            cooldown_remaining_sec=round(max(0.0, cooldown_remaining), 6),
            scope_digest=scope_digest,
        )

    def acquire(
        self,
        *,
        token: str,
        endpoint: str,
        request_owner: str,
        request_class: str,
        api_id: str,
        request_code: str = "",
        max_wait_sec: float | None = None,
    ) -> ReadRequestAdmission:
        normalized_token = str(token or "").replace("Bearer ", "").strip()
        normalized_class = _safe_label(
            request_class, fallback=REQUEST_CLASS_RUNTIME_REQUIRED
        )
        owner = _safe_label(request_owner, fallback="unknown_read_owner")
        api_label = _safe_label(api_id, fallback="unknown_api_id")
        code_label = _safe_label(request_code, fallback="not_applicable")
        mock_environment = _is_mock_origin(endpoint)
        max_limit = (
            MOCK_READ_REQUESTS_PER_WINDOW if mock_environment else self.max_requests
        )
        source_only_limit = (
            MOCK_READ_REQUESTS_PER_WINDOW
            if mock_environment
            else self.source_only_limit
        )
        effective_limit = (
            source_only_limit
            if normalized_class == REQUEST_CLASS_SOURCE_ONLY
            else max_limit
        )
        state_path, digest = self._state_path(
            token=normalized_token, endpoint=endpoint, api_id=api_label
        )
        if not normalized_token:
            return self._admission(
                admitted=False,
                reason="shared_read_rate_token_missing",
                request_class=normalized_class,
                request_owner=owner,
                api_id=api_label,
                request_code=code_label,
                waited_sec=0.0,
                requests_before=0,
                effective_limit=effective_limit,
                max_limit=max_limit,
                cooldown_remaining=0.0,
                scope_digest=digest,
            )
        if normalized_class not in REQUEST_CLASSES:
            return self._admission(
                admitted=False,
                reason="shared_read_rate_request_class_invalid",
                request_class=normalized_class,
                request_owner=owner,
                api_id=api_label,
                request_code=code_label,
                waited_sec=0.0,
                requests_before=0,
                effective_limit=effective_limit,
                max_limit=max_limit,
                cooldown_remaining=0.0,
                scope_digest=digest,
            )
        default_wait = (
            DEFAULT_SOURCE_ONLY_MAX_WAIT_SEC
            if normalized_class == REQUEST_CLASS_SOURCE_ONLY
            else DEFAULT_REQUIRED_MAX_WAIT_SEC
        )
        wait_budget = max(
            0.0, float(default_wait if max_wait_sec is None else max_wait_sec)
        )
        started = float(self.clock())
        deadline = started + wait_budget
        last_requests_before = 0
        last_cooldown_remaining = 0.0

        while True:
            handle = self._open_locked_state(state_path)
            try:
                state, state_error = self._read_state(handle)
                now = float(self.clock())
                if state_error:
                    return self._admission(
                        admitted=False,
                        reason=state_error,
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=0,
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                raw_timestamps = state.get("request_epochs", [])
                if not isinstance(raw_timestamps, list):
                    return self._admission(
                        admitted=False,
                        reason="shared_read_rate_request_epochs_invalid",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=0,
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                if any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or float(value) < 0.0
                    or float(value) > now + self.window_sec
                    for value in raw_timestamps
                ):
                    return self._admission(
                        admitted=False,
                        reason="shared_read_rate_request_epoch_value_invalid",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=0,
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                request_epochs = sorted(
                    timestamp
                    for value in raw_timestamps
                    if now - (timestamp := float(value)) < self.window_sec
                )
                cooldown_until = state.get("cooldown_until_epoch", 0.0)
                try:
                    cooldown_until = float(cooldown_until or 0.0)
                except (TypeError, ValueError):
                    return self._admission(
                        admitted=False,
                        reason="shared_read_rate_cooldown_invalid",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=len(request_epochs),
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                if not math.isfinite(cooldown_until) or cooldown_until < 0.0:
                    return self._admission(
                        admitted=False,
                        reason="shared_read_rate_cooldown_invalid",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=len(request_epochs),
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                if cooldown_until > now + 300.0:
                    return self._admission(
                        admitted=False,
                        reason="shared_read_rate_cooldown_future_invalid",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=len(request_epochs),
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=cooldown_until - now,
                        scope_digest=digest,
                    )
                cooldown_remaining = max(0.0, cooldown_until - now)
                last_requests_before = len(request_epochs)
                last_cooldown_remaining = cooldown_remaining
                if cooldown_remaining > 0:
                    if normalized_class == REQUEST_CLASS_SOURCE_ONLY:
                        return self._admission(
                            admitted=False,
                            reason="shared_read_rate_server_cooldown",
                            request_class=normalized_class,
                            request_owner=owner,
                            api_id=api_label,
                            request_code=code_label,
                            waited_sec=now - started,
                            requests_before=len(request_epochs),
                            effective_limit=effective_limit,
                            max_limit=max_limit,
                            cooldown_remaining=cooldown_remaining,
                            scope_digest=digest,
                        )
                    delay = cooldown_remaining
                elif (
                    len(request_epochs) < max_limit
                    and len(request_epochs) < effective_limit
                ):
                    request_epochs.append(now)
                    state.update(
                        {
                            "schema_version": STATE_SCHEMA_VERSION,
                            "bucket": DOMESTIC_READ_BUCKET,
                            "origin": _normalized_origin(endpoint),
                            "window_sec": self.window_sec,
                            "max_requests": max_limit,
                            "source_only_limit": source_only_limit,
                            "environment": (
                                "mock" if mock_environment else "production"
                            ),
                            "scope_api_id": (
                                api_label if mock_environment else "all_read_tr"
                            ),
                            "request_epochs": request_epochs,
                            "last_admission": {
                                "at_epoch": now,
                                "api_id": api_label,
                                "request_code": code_label,
                                "request_owner": owner,
                                "request_class": normalized_class,
                                "pid": os.getpid(),
                            },
                        }
                    )
                    self._write_state(handle, state)
                    return self._admission(
                        admitted=True,
                        reason="shared_read_rate_admitted",
                        request_class=normalized_class,
                        request_owner=owner,
                        api_id=api_label,
                        request_code=code_label,
                        waited_sec=now - started,
                        requests_before=len(request_epochs) - 1,
                        effective_limit=effective_limit,
                        max_limit=max_limit,
                        cooldown_remaining=0.0,
                        scope_digest=digest,
                    )
                else:
                    relevant_count = min(len(request_epochs), effective_limit)
                    release_index = max(0, len(request_epochs) - relevant_count)
                    delay = max(
                        0.001,
                        request_epochs[release_index] + self.window_sec - now + 0.001,
                    )
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                handle.close()

            now_after_lock = float(self.clock())
            if now_after_lock + delay > deadline:
                return self._admission(
                    admitted=False,
                    reason="shared_read_rate_wait_budget_exhausted",
                    request_class=normalized_class,
                    request_owner=owner,
                    api_id=api_label,
                    request_code=code_label,
                    waited_sec=now_after_lock - started,
                    requests_before=last_requests_before,
                    effective_limit=effective_limit,
                    max_limit=max_limit,
                    cooldown_remaining=last_cooldown_remaining,
                    scope_digest=digest,
                )
            self.sleep(delay)

    def record_rate_limit(
        self,
        *,
        token: str,
        endpoint: str,
        request_owner: str,
        request_class: str,
        api_id: str,
        request_code: str = "",
        http_status_code: object = None,
        response_code: object = None,
    ) -> dict[str, Any]:
        """Publish a shared cooldown after an explicit Kiwoom limit response."""

        normalized_token = str(token or "").replace("Bearer ", "").strip()
        mock_environment = _is_mock_origin(endpoint)
        max_limit = (
            MOCK_READ_REQUESTS_PER_WINDOW if mock_environment else self.max_requests
        )
        source_only_limit = (
            MOCK_READ_REQUESTS_PER_WINDOW
            if mock_environment
            else self.source_only_limit
        )
        path, digest = self._state_path(
            token=normalized_token, endpoint=endpoint, api_id=str(api_id or "")
        )
        if not normalized_token:
            return {
                "recorded": False,
                "reason": "shared_read_rate_token_missing",
                "scope_digest": digest,
            }
        owner = _safe_label(request_owner, fallback="unknown_read_owner")
        class_label = _safe_label(
            request_class, fallback=REQUEST_CLASS_RUNTIME_REQUIRED
        )
        api_label = _safe_label(api_id, fallback="unknown_api_id")
        code_label = _safe_label(request_code, fallback="not_applicable")
        handle = self._open_locked_state(path)
        try:
            state, state_error = self._read_state(handle)
            now = float(self.clock())
            if state_error:
                state = {}
            raw_timestamps = state.get("request_epochs", [])
            if not isinstance(raw_timestamps, list):
                raw_timestamps = []
            request_epochs = [
                float(value)
                for value in raw_timestamps
                if not isinstance(value, bool)
                and isinstance(value, (int, float))
                and math.isfinite(float(value))
                and 0.0 <= float(value) <= now + self.window_sec
                and now - float(value) < self.window_sec
            ]
            prior_cooldown = state.get("cooldown_until_epoch", 0.0)
            try:
                prior_cooldown = float(prior_cooldown or 0.0)
            except (TypeError, ValueError):
                prior_cooldown = 0.0
            if (
                not math.isfinite(prior_cooldown)
                or prior_cooldown < 0.0
                or prior_cooldown > now + 300.0
            ):
                prior_cooldown = 0.0
            cooldown_until = max(prior_cooldown, now + self.cooldown_sec)
            state.update(
                {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "bucket": DOMESTIC_READ_BUCKET,
                    "origin": _normalized_origin(endpoint),
                    "window_sec": self.window_sec,
                    "max_requests": max_limit,
                    "source_only_limit": source_only_limit,
                    "environment": "mock" if mock_environment else "production",
                    "scope_api_id": api_label if mock_environment else "all_read_tr",
                    "request_epochs": sorted(request_epochs),
                    "cooldown_until_epoch": cooldown_until,
                    "last_rate_limit": {
                        "at_epoch": now,
                        "api_id": api_label,
                        "request_code": code_label,
                        "request_owner": owner,
                        "request_class": class_label,
                        "pid": os.getpid(),
                        "http_status_code": http_status_code,
                        "response_code": response_code,
                    },
                }
            )
            self._write_state(handle, state)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
        return {
            "recorded": True,
            "reason": "shared_read_rate_server_cooldown_recorded",
            "scope_digest": digest,
            "cooldown_until_epoch": cooldown_until,
        }


DEFAULT_COORDINATOR = KiwoomReadRequestCoordinator()
