"""Isolated execution of the existing holding policy for AVG_DOWN evidence.

The live module is never patched in the report process. A disposable interpreter
reuses its actual functions with frozen inputs and virtual inventory. Unrecorded
I/O aborts via BaseException (live defensive ``except Exception`` must not turn
missing replay evidence into a successful HOLD). This is quote-counterfactual
evidence, not broker execution or live promotion authority.
"""

from __future__ import annotations

import argparse
import base64
import builtins
import errno
import hashlib
import gzip
import io
import json
import inspect
import os
import subprocess
import sys
import time
from collections import deque
from decimal import Decimal
from copy import deepcopy
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace, CodeType
from typing import Any

from src.engine.lifecycle.avg_down_replay import canonical_digest, finite_number

SNAPSHOT_SCHEMA = "avg_down_full_policy_snapshot_v1"
ADAPTER_VERSION = "existing_holding_policy_isolated_v1"
REPO = Path(__file__).resolve().parents[3]
IMPLEMENTATION_PATHS = (
    "src/engine/sniper_state_handlers.py",
    "src/engine/sniper_scale_in.py",
    "src/engine/sniper_execution_receipts.py",
    "src/engine/holding_exit_matrix_runtime.py",
    "src/engine/lifecycle_decision_matrix_runtime.py",
    "src/engine/lifecycle/avg_down_policy_replay.py",
    "src/engine/lifecycle/avg_down_replay.py",
    "src/engine/trade_profit.py",
    "src/engine/ai_engine_openai.py",
    "src/engine/kiwoom_orders.py",
    "src/engine/scalping/micro_estimator_state.py",
)
_KST = timezone(timedelta(hours=9))


class ReplayInputGap(BaseException):
    """Deliberately not swallowed by production fallback/retry handlers."""

    def __init__(self, reason: str, request: dict | None = None):
        self.reason = reason
        self.request = request
        frame = sys._getframe(1)
        self.call_path = []
        for _ in range(12):
            if frame is None:
                break
            self.call_path.append(frame.f_code.co_name)
            frame = frame.f_back
        super().__init__(reason)


class VirtualAction(BaseException):
    def __init__(self, action: str, detail: dict | None = None):
        self.action = action
        self.detail = detail or {}


def implementation_identity() -> dict[str, str]:
    return {
        name: hashlib.sha256((REPO / name).read_bytes()).hexdigest()
        for name in IMPLEMENTATION_PATHS
    }


def snapshot_version(snapshot: dict) -> str:
    return "avg_down_exit_policy:" + canonical_digest(snapshot)


def _code_digest(code: CodeType) -> str:
    def constant(value):
        if isinstance(value, CodeType):
            return {"code": _code_digest(value)}
        if isinstance(value, bytes):
            return {"bytes": value.hex()}
        if isinstance(value, tuple):
            return [constant(item) for item in value]
        if isinstance(value, frozenset):
            return {"frozenset": sorted((constant(item) for item in value), key=repr)}
        if value is Ellipsis:
            return {"ellipsis": True}
        if isinstance(value, complex):
            return {"complex": [value.real, value.imag]}
        return value

    # marshal includes interpreter interning/reference-table details that can
    # differ between importing a module and running it as __main__.
    return canonical_digest(
        {
            "bytecode": code.co_code.hex(),
            "constants": constant(code.co_consts),
            "names": code.co_names,
            "locals": code.co_varnames,
            "free": code.co_freevars,
            "cells": code.co_cellvars,
            "flags": code.co_flags,
            "args": [code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount],
            "exceptions": code.co_exceptiontable.hex(),
        }
    )


def loaded_code_identity(handlers) -> dict:
    identities = {
        name: _code_digest(getattr(handlers, name).__code__)
        for name in (
            "handle_holding_state",
            "evaluate_and_dispatch_fast_scalp_exit",
            "execute_scale_in_order",
        )
    }
    # Long-running processes may have old imported helpers even when the three
    # entry points did not change. Hash loaded functions, not just disk files.
    for path in IMPLEMENTATION_PATHS:
        module_name = path.removesuffix(".py").replace("/", ".")
        module = sys.modules.get(module_name)
        if (
            module is None
            and module_name == "src.engine.lifecycle.avg_down_policy_replay"
        ):
            module = sys.modules[__name__]
        if module is None:
            continue
        for name, value in vars(module).items():
            if inspect.isfunction(value) and value.__module__ == module.__name__:
                identities[module_name + "." + name] = _code_digest(value.__code__)
            elif inspect.isclass(value) and value.__module__ == module.__name__:
                for method_name, method in vars(value).items():
                    if isinstance(method, (classmethod, staticmethod)):
                        method = method.__func__
                    if inspect.isfunction(method):
                        identities[module_name + "." + name + "." + method_name] = (
                            _code_digest(method.__code__)
                        )
    return identities


def _json_value(value: Any) -> Any:
    """No repr/default=str normalization of unknown policy state."""
    if isinstance(value, datetime):
        return {"__replay_datetime__": value.isoformat()}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non_finite_decimal_state")
        return {"__replay_decimal__": str(value)}
    if isinstance(value, deque):
        return {
            "__replay_deque__": [_json_value(item) for item in value],
            "maxlen": value.maxlen,
        }
    if isinstance(value, (tuple, set, frozenset)):
        values = [_json_value(item) for item in value]
        if isinstance(value, (set, frozenset)):
            values.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return {"__replay_collection__": type(value).__name__, "items": values}
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("non_string_snapshot_key")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        # canonical_digest also rejects NaN/inf.
        canonical_digest(value)
        return value
    if type(value).__module__.startswith("numpy") and hasattr(value, "item"):
        return _json_value(value.item())
    raise ValueError("unsupported_snapshot_value:" + type(value).__name__)


def thaw(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"__replay_decimal__"}:
            return Decimal(value["__replay_decimal__"])
        if set(value) == {"__replay_deque__", "maxlen"}:
            return deque(
                (thaw(item) for item in value["__replay_deque__"]),
                maxlen=value["maxlen"],
            )
        if set(value) == {"__replay_datetime__"}:
            return datetime.fromisoformat(value["__replay_datetime__"])
        if set(value) == {"__replay_collection__", "items"}:
            constructor = {"tuple": tuple, "set": set, "frozenset": frozenset}.get(
                value["__replay_collection__"]
            )
            if constructor is None:
                raise ReplayInputGap("snapshot_collection_invalid")
            return constructor(thaw(item) for item in value["items"])
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [thaw(item) for item in value]
    return value


def external_call_key(name: str, args: Any, kwargs: Any) -> str:
    return canonical_digest(
        {"call": name, "args": _json_value(args), "kwargs": _json_value(kwargs)}
    )


def decode_market_inputs(value: dict) -> dict:
    decoded = deepcopy(value)
    for row in decoded.values():
        if not isinstance(row, dict):
            raise ReplayInputGap("recorded_market_input_schema_invalid")
        if "value_gzip_b64" in row:
            # Limit decompression before decoding JSON, not after allocating an
            # arbitrary gzip bomb from a malformed source event.
            with gzip.GzipFile(
                fileobj=io.BytesIO(base64.b64decode(row["value_gzip_b64"]))
            ) as source:
                raw = source.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ReplayInputGap("recorded_market_input_size_limit")
            data = json.loads(raw)
            if canonical_digest(data) != row.get("value_sha256"):
                raise ReplayInputGap("recorded_market_input_digest_mismatch")
            row["value"] = data
    return decoded


class RecordedServices:
    def __init__(self, records: dict, *, cutoff: str, policy_version: str = ""):
        self.records = records
        self.cutoff = cutoff
        self.policy_version = policy_version

    def call(self, name: str, *args, **kwargs):
        key = external_call_key(name, args, kwargs)
        row = self.records.get(key)
        if not isinstance(row, dict):
            raise ReplayInputGap(
                "exact_state_external_input_missing:" + name,
                {
                    "call": name,
                    "input_digest": key,
                    "args": _json_value(args),
                    "kwargs": _json_value(kwargs),
                    "input_cutoff": self.cutoff,
                    "policy_version": self.policy_version,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            )
        if (
            row.get("input_digest") != key
            or row.get("input_cutoff") != self.cutoff
            or row.get("actual_order_submitted") is not False
            or row.get("broker_order_forbidden") is not True
            or (
                self.policy_version and row.get("policy_version") != self.policy_version
            )
            or "result" not in row
        ):
            raise ReplayInputGap("recorded_external_input_contract_invalid:" + name)
        return thaw(deepcopy(row["result"]))

    def proxy(self, prefix: str):
        owner = self

        class Proxy:
            def __getattr__(self, key):
                return lambda *a, **kw: owner.call(prefix + "." + key, *a, **kw)

        return Proxy()


class FrozenFiles:
    """Virtual data namespace, including explicit absence; no current-day reads."""

    def __init__(self, files: dict):
        self.files = files
        self.real_open = builtins.open
        self.real_io_open = io.open
        self.real_stat = os.stat

    def _path(self, value):
        if isinstance(value, int):
            raise ReplayInputGap("unrecorded_file_descriptor_read")
        return os.path.abspath(os.fspath(value))

    def _row(self, name):
        path = self._path(name)
        if path not in self.files:
            raise ReplayInputGap("unrecorded_file_read:" + path)
        return self.files[path]

    def open(self, file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            raise ReplayInputGap("offline_file_write_forbidden")
        path = self._path(file)
        row = self._row(path)
        if row is None:
            raise FileNotFoundError(errno.ENOENT, "recorded_absence", path)
        if "content_gzip_b64" in row:
            with gzip.GzipFile(
                fileobj=io.BytesIO(base64.b64decode(row["content_gzip_b64"]))
            ) as source:
                raw = source.read(32_000_001)
            if len(raw) > 32_000_000 or len(raw) != row.get("size"):
                raise ReplayInputGap("frozen_policy_file_size_mismatch_or_limit")
            content = raw.decode("utf-8")
        else:
            content = row["content"]
        return (
            io.BytesIO(content.encode("utf-8")) if "b" in mode else io.StringIO(content)
        )

    def stat(self, path, *args, **kwargs):
        prefix = self._path(path).rstrip(os.sep) + os.sep
        if any(name.startswith(prefix) for name in self.files):
            return SimpleNamespace(
                st_mtime=0, st_mtime_ns=0, st_size=0, st_mode=0o40555
            )
        row = self._row(path)
        if row is None:
            raise FileNotFoundError(errno.ENOENT, "recorded_absence", os.fspath(path))
        return SimpleNamespace(
            st_mtime=row["mtime"],
            st_mtime_ns=row["mtime_ns"],
            st_size=row.get("size", len(row.get("content", "").encode())),
            st_mode=0o100444,
        )

    def install(self):
        builtins.open = self.open
        io.open = self.open
        os.stat = self.stat

        # Glob/discovery must not consult today's directory inventory.
        def glob(path, pattern, **kwargs):
            import fnmatch

            prefix = str(path).rstrip(os.sep) + os.sep
            return iter(
                Path(name)
                for name, row in self.files.items()
                if row is not None
                and name.startswith(prefix)
                and fnmatch.fnmatch(name[len(prefix) :], pattern)
            )

        Path.glob = glob


class VirtualInventoryDB:
    """One hypothetical position, not a copy of real account buying power."""

    def __init__(self, stock):
        self.row = deepcopy(stock)

    def get_session(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def query(self, model):
        if getattr(model, "__name__", "") != "RecommendationHistory":
            raise ReplayInputGap("unrecorded_virtual_database_table")
        db = self

        class Query:
            matched = True

            def filter_by(self, **kwargs):
                self.matched = self.matched and all(
                    db.row.get(key) == value for key, value in kwargs.items()
                )
                return self

            def filter(self, *expressions):
                from sqlalchemy.sql.elements import (
                    BinaryExpression,
                    BindParameter,
                    BooleanClauseList,
                )
                from sqlalchemy.sql import operators

                def resolve(value):
                    if isinstance(value, BindParameter):
                        return value.value
                    if isinstance(value, BinaryExpression):
                        left, right = resolve(value.left), resolve(value.right)
                        if value.operator not in {
                            operators.eq,
                            operators.ne,
                            operators.gt,
                            operators.ge,
                            operators.lt,
                            operators.le,
                            operators.is_,
                            operators.is_not,
                        }:
                            raise ReplayInputGap(
                                "virtual_inventory_predicate_unsupported"
                            )
                        return value.operator(left, right)
                    if isinstance(value, BooleanClauseList):
                        values = [bool(resolve(item)) for item in value.clauses]
                        if value.operator is operators.and_:
                            return all(values)
                        if value.operator is operators.or_:
                            return any(values)
                    key = getattr(value, "key", None)
                    if key in db.row:
                        return db.row[key]
                    raise ReplayInputGap("virtual_inventory_column_missing:" + str(key))

                self.matched = self.matched and all(
                    bool(resolve(item)) for item in expressions
                )
                return self

            def first(self):
                class Row(SimpleNamespace):
                    def __getattr__(self, key):
                        raise ReplayInputGap("virtual_inventory_column_missing:" + key)

                return Row(**deepcopy(db.row)) if self.matched else None

            def update(self, values, **kwargs):
                if not self.matched:
                    return 0
                for key, value in values.items():
                    db.row[key if isinstance(key, str) else key.key] = deepcopy(value)
                return 1

        return Query()

    def __getattr__(self, key):
        raise ReplayInputGap("virtual_inventory_operation_unsupported:" + key)


def _install_effect_guard():
    phase = {"importing": True}

    def audit(event, args):
        if (
            (event.startswith("socket.") and event != "socket.__new__")
            or event.startswith("sqlite3.connect")
            or (
                not phase["importing"]
                and event in {"os.listdir", "os.scandir", "ctypes.dlopen"}
            )
            or event
            in {"subprocess.Popen", "os.system", "os.fork", "os.exec", "os.posix_spawn"}
            or event
            in {
                "os.remove",
                "os.rename",
                "os.rmdir",
                "os.mkdir",
                "os.truncate",
                "os.chmod",
                "os.link",
                "os.symlink",
            }
            or (
                event == "open"
                and (
                    int(args[2] or 0)
                    & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                )
            )
        ):
            if phase["importing"]:
                raise OSError("offline_import_side_effect_forbidden:" + event)
            raise ReplayInputGap("offline_side_effect_forbidden:" + event)

    sys.addaudithook(audit)
    return phase


def _worker_replay(observation: dict, frames: list[dict]) -> dict:
    # Import before freezing the input filesystem, but prohibit network and
    # writes even during imports. Import-time .pyc writes are disabled by -B.
    snapshot = observation["policy_snapshot"]
    if any(
        not key.startswith("KORSTOCKSCAN_") for key in snapshot.get("environment", {})
    ):
        raise ReplayInputGap("unexpected_policy_environment_namespace")
    os.environ.clear()
    os.environ.update(snapshot["environment"])
    phase = _install_effect_guard()
    from src.engine import sniper_state_handlers as handlers
    from src.engine import sniper_execution_receipts as receipts
    from src.engine import lifecycle_decision_matrix_runtime as ldm
    from src.engine.scalping.avg_down_replay_capture import AI_STATE_FIELDS
    from src.engine.lifecycle.avg_down_replay import replay_exit_paths
    from src.engine.ai.hot_path_ai_symbol_budget import HotPathAISymbolBudget
    from src.engine.ai_engine_openai import GPTSniperEngine
    from src.engine.scalping.micro_estimator_state import (
        MicroEstimatorConfig,
        MicroEstimatorStore,
        SymbolMicroEstimatorState,
    )
    import threading
    import time
    import uuid

    phase["importing"] = False

    if snapshot.get("schema") != SNAPSHOT_SCHEMA or snapshot_version(
        snapshot
    ) != observation.get("exit_policy_version"):
        raise ReplayInputGap("full_policy_snapshot_digest_mismatch")
    if snapshot.get("implementation") != implementation_identity():
        raise ReplayInputGap("recorded_policy_implementation_changed")
    current_code = loaded_code_identity(handlers)
    if not snapshot.get("loaded_code") or any(
        current_code.get(name) != digest
        for name, digest in snapshot["loaded_code"].items()
    ):
        mismatch = next(
            (
                name
                for name, digest in snapshot.get("loaded_code", {}).items()
                if current_code.get(name) != digest
            ),
            "missing_identity",
        )
        raise ReplayInputGap(
            "loaded_runtime_policy_differs_from_recorded_source:" + mismatch
        )
    initial = thaw(observation["initial_policy_state"]["stock"])
    if (
        initial.get("buy_qty") != finite_number(observation.get("pre_add_buy_qty"))
        or initial.get("buy_price")
        != finite_number(observation.get("pre_add_buy_price"))
        or str(initial.get("code", ""))[:6] != observation.get("stock_code")
        or initial.get("status") != "HOLDING"
        or initial.get("strategy") not in {"SCALPING", "SCALP"}
        or initial.get("pending_add_order")
        or initial.get("pending_entry_orders")
        or initial.get("sell_submit_pending")
    ):
        raise ReplayInputGap("initial_holding_identity_inventory_or_pending_conflict")
    rules = thaw(snapshot["rules"])
    if not isinstance(rules, dict) or not rules:
        raise ReplayInputGap("full_policy_rules_missing")
    # An absent field is not permission to substitute the current code default.
    # Defaults encoded in the fingerprinted implementation are part of the
    # frozen policy too (getattr defaults are often intentionally undeclared).
    Rules = SimpleNamespace

    original_modules = [
        module
        for name, module in list(sys.modules.items())
        if name.startswith("src.") and module is not None
    ]
    original_time = time.time
    original_monotonic = time.monotonic
    original_perf_counter = time.perf_counter
    current = {"epoch": 0.0, "input_digest": "", "uuid_ordinal": 0}

    def deterministic_uuid4():
        current["uuid_ordinal"] += 1
        return uuid.UUID(
            hex=canonical_digest([current["input_digest"], current["uuid_ordinal"]])[
                :32
            ],
            version=4,
        )

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromtimestamp(current["epoch"], tz=tz or _KST).replace(
                tzinfo=tz if tz is not None else None
            )

        @classmethod
        def today(cls):
            return cls.now()

        @classmethod
        def utcnow(cls):
            return datetime.fromtimestamp(current["epoch"], tz=timezone.utc).replace(
                tzinfo=None
            )

    class CalendarDate(date):
        @classmethod
        def today(cls):
            return datetime.fromtimestamp(current["epoch"], tz=_KST).date()

    def quiet(*args, **kwargs):
        return None

    # Only telemetry is elided. Trading/quote/matrix/safety decisions are not
    # replaced with preselected outcomes.
    for module in original_modules:
        for name in ("log_info", "log_error", "record_ai_decision_trace"):
            if hasattr(module, name):
                setattr(module, name, quiet)
        if getattr(module, "datetime", None) is datetime:
            module.datetime = Clock
        for name in ("date", "date_cls"):
            if getattr(module, name, None) is date:
                setattr(module, name, CalendarDate)
        if getattr(module, "uuid4", None) is uuid.uuid4:
            module.uuid4 = deterministic_uuid4
    uuid.uuid4 = deterministic_uuid4
    handlers._log_holding_pipeline = quiet
    handlers._log_entry_pipeline = quiet
    handlers._observe_avg_down_runtime_config = quiet
    handlers._observe_avg_down_route_arbitration = quiet
    handlers._persist_scalping_position_peak = quiet
    for name in (
        "_log_holding_pipeline",
        "_update_db_for_add",
        "record_add_history_event",
        "_request_broker_snapshot_refresh",
        "_publish_add_execution_notification",
    ):
        setattr(receipts, name, quiet)
    handlers.ENTRY_LOCK = threading.RLock()
    # Do not create dispatcher threads inside the replay interpreter.
    threading.Thread.start = lambda self: (_ for _ in ()).throw(
        ReplayInputGap("offline_thread_dispatch_forbidden")
    )
    FrozenFiles(snapshot["files"]).install()
    time.time = lambda: current["epoch"]
    time.monotonic = lambda: current["epoch"]
    time.perf_counter = lambda: current["epoch"]
    requests = []
    original_add_gate = handlers.can_consider_scale_in
    original_execute_add = handlers.execute_scale_in_order
    original_utils = handlers.kiwoom_utils
    original_orders = handlers.kiwoom_orders

    class ReplayAI(GPTSniperEngine):
        def _rotate_client(self):
            self.client = None

        def _capture_prepromotion_context_candidate(self, **kwargs):
            return {}

        def evaluate_scalping_holding_score(self, *args, **kwargs):
            if not self.recorded_state_ready:
                raise ReplayInputGap("initial_ai_engine_policy_state_missing")
            return super().evaluate_scalping_holding_score(*args, **kwargs)

        def evaluate_scalping_holding_flow(self, *args, **kwargs):
            if not self.recorded_state_ready:
                raise ReplayInputGap("initial_ai_engine_policy_state_missing")
            return super().evaluate_scalping_holding_flow(*args, **kwargs)

        def _call_openai_safe(self, *args, **kwargs):
            result = self.services.call("ai_provider.current_prompt", *args, **kwargs)
            if (
                not isinstance(result, dict)
                or result.get("schema") != "avg_down_raw_provider_reply_v1"
            ):
                raise ReplayInputGap("offline_provider_reply_envelope_invalid")
            self._set_last_transport_meta(result.get("transport_meta", {}))
            return result["provider_response"]

    def evaluate(state, frame, policy, input_digest):
        current["epoch"] = datetime.fromisoformat(frame["emitted_at"]).timestamp()
        current["input_digest"] = input_digest
        current["uuid_ordinal"] = 0
        context = state["policy_state"]
        if context.get("schema") != "avg_down_holding_state_v1":
            raise ReplayInputGap("full_holding_state_schema_invalid")
        stock = thaw(deepcopy(context["stock"]))
        if not isinstance(context.get("ldm_promote_counter"), dict):
            raise ReplayInputGap("initial_ldm_promotion_state_missing")
        ldm._PROMOTE_COUNTER = thaw(deepcopy(context["ldm_promote_counter"]))
        services = RecordedServices(
            frame.get("external_results", {}),
            cutoff=frame["emitted_at"],
            policy_version=policy,
        )
        stages = []

        def record_stage(stock, code, stage, **fields):
            stages.append(
                {
                    "stage": str(stage),
                    "reason": fields.get("reason")
                    or fields.get("manual_control_exclusion_reason"),
                }
            )
            del stages[:-64]

        handlers._log_holding_pipeline = record_stage
        runtime_rules = Rules(**rules)
        if state["min_buy_pressure"] is not None:
            runtime_rules.SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE = state[
                "min_buy_pressure"
            ]
        for module in original_modules:
            if hasattr(module, "TRADING_RULES"):
                digest = snapshot.get("module_rules", {}).get(module.__name__)
                if digest:
                    values = snapshot["rule_blobs"].get(digest)
                    if values is None or canonical_digest(values) != digest:
                        raise ReplayInputGap("module_rules_digest_mismatch")
                    fixed = Rules(**thaw(values))
                    if state["min_buy_pressure"] is not None and hasattr(
                        fixed, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
                    ):
                        fixed.SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE = state[
                            "min_buy_pressure"
                        ]
                    module.TRADING_RULES = fixed
        handlers.TRADING_RULES = runtime_rules
        for name, value in context["globals"].items():
            if name not in {
                "COOLDOWNS",
                "ALERTED_STOCKS",
                "HIGHEST_PRICES",
                "LAST_AI_CALL_TIMES",
                "LAST_LOG_TIMES",
            }:
                raise ReplayInputGap("unexpected_replay_global:" + name)
            setattr(handlers, name, thaw(deepcopy(value)))
        handlers.HIGHEST_PRICES[
            handlers._price_tracking_key(stock, observation["stock_code"])
        ] = state["peak_price"]
        receipts.highest_prices = handlers.HIGHEST_PRICES
        handlers.DB = VirtualInventoryDB(stock)
        handlers.KIWOOM_TOKEN = "offline_credential_not_valid"
        handlers.EVENT_BUS = services.proxy("EVENT_BUS")
        handlers.WS_MANAGER = SimpleNamespace(
            get_latest_data=lambda code: (
                deepcopy(frame["market"]["ws_data"])
                if code[:6] == observation["stock_code"]
                else services.call("WS_MANAGER.get_latest_data", code)
            )
        )
        recorded_inputs = decode_market_inputs(
            frame["market"].get("recorded_inputs", {})
        )

        def bounded_rest(code, timeout_ms):
            source = recorded_inputs.get("bounded_rest_orderbook") or {}
            value = source.get("value") or {}
            age = current["epoch"] - source.get("observed_at", float("inf"))
            if (
                not 0 <= age <= 5
                or value.get("request_code") != code
                or value.get("timeout_ms") != timeout_ms
            ):
                raise ReplayInputGap("bounded_rest_quote_request_or_cutoff_gap")
            result = thaw(deepcopy(value.get("result")))
            if (
                not isinstance(result, list)
                or len(result) != 3
                or not isinstance(result[0], dict)
            ):
                raise ReplayInputGap("bounded_rest_quote_result_schema_gap")
            return tuple(result)

        handlers._fetch_rest_orderbook_snapshot_bounded = bounded_rest
        micro = frame["market"].get("micro_estimator_state")
        if micro is not None:
            micro_store = MicroEstimatorStore(
                MicroEstimatorConfig(**thaw(micro["config"]))
            )
            if micro.get("state") is not None:
                micro_store._states[observation["stock_code"]] = (
                    SymbolMicroEstimatorState(**thaw(micro["state"]))
                )
            handlers._SCALPING_MICRO_ESTIMATOR_STORE = micro_store
        else:

            class MissingMicro:
                def __getattr__(self, name):
                    raise ReplayInputGap("market_micro_estimator_state_missing")

            handlers._SCALPING_MICRO_ESTIMATOR_STORE = MissingMicro()

        def market_source(code):
            source = recorded_inputs.get("holding_score_market_source")
            if (
                not isinstance(source, dict)
                or source.get("observed_at", float("inf")) > current["epoch"]
                or source.get("value", {}).get("request_code") != code
            ):
                raise ReplayInputGap("holding_market_source_request_or_cutoff_gap")
            return thaw(deepcopy(source["value"]))

        class MarketServices:
            def get_tick_history_ka10003(self, token, code, *, limit=10):
                return market_source(code)["recent_ticks"][:limit]

            def __getattr__(self, key):
                # Local price arithmetic is reusable; all transport stays in
                # the recorded-service boundary and cannot silently fall back.
                if key in {
                    "get_tick_size",
                    "get_target_price_up",
                    "get_target_price_down",
                }:
                    return getattr(original_utils, key)
                return getattr(services.proxy("kiwoom_utils"), key)

        handlers.kiwoom_utils = MarketServices()

        def candles(code, *, decision_kind, ws_data, position_ctx, now_ts, **kwargs):
            request_code = handlers._resolve_holding_context_request_code(
                code,
                ws_data=ws_data,
                position_ctx=position_ctx,
                decision_kind=decision_kind,
                now_ts=now_ts,
            )
            source = market_source(request_code)
            return source["recent_candles"], source["recent_candle_meta"]

        handlers._get_holding_minute_candles_with_meta = candles
        handlers.DUAL_PERSONA_ENGINE = services.proxy("ai_engine")
        ai_engine = ReplayAI(["offline_credential_not_valid"], announce_startup=False)
        ai_engine.services = services
        ai_state = context.get("ai_engine_state")
        ai_engine.recorded_state_ready = isinstance(ai_state, dict) and set(
            ai_state
        ) == set(AI_STATE_FIELDS)
        if ai_engine.recorded_state_ready:
            for name, value in ai_state.items():
                setattr(ai_engine, name, thaw(value))
        budget = context.get("ai_budget")
        if not isinstance(budget, dict):
            raise ReplayInputGap("initial_ai_cadence_state_missing")
        from collections import deque

        handlers.DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET = HotPathAISymbolBudget(
            window_sec=budget["window_sec"],
            total_cap=budget["total_cap"],
            group_cap=budget["group_cap"],
        )
        handlers.DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET._events = {
            key: deque(thaw(rows)) for key, rows in budget["events"].items()
        }

        # The broker facade has no transport. Requests terminate evaluation and
        # never return a made-up receipt/acceptance to the live handler.
        class Orders:
            def send_buy_order(self, code, qty, price, order_type_code, **kwargs):
                # The unchanged scale-in owner has reached its broker boundary.
                # One full limit leg can be modelled; never coalesce split or
                # market orders into a fictional full limit fill.
                if (
                    code != observation["stock_code"]
                    or state["no_add_control"]
                    or state["pending_add"] is not None
                    or stock.get("pending_add_qty") != qty
                    or order_type_code != "00"
                    or not stock.get("pending_add_order")
                ):
                    raise ReplayInputGap(
                        "subsequent_add_split_market_or_pending_model_gap"
                    )
                raise VirtualAction(
                    "ADD",
                    {
                        "add_order": {
                            "qty": qty,
                            "price": price,
                            "expires_at": datetime.fromtimestamp(
                                current["epoch"] + 20, tz=_KST
                            ).isoformat(),
                            "add_type": stock.get("pending_add_type"),
                            "reason": stock.get("pending_add_reason", ""),
                            "existing_sizing_price_and_safety_evaluated": True,
                        },
                        "broker_acceptance_assumed_not_evaluated": True,
                    },
                )

            def send_smart_sell_order(self, *args, **kwargs):
                if kwargs.get("qty") != state["qty"]:
                    raise ReplayInputGap(
                        "independent_partial_exit_requires_receipt_model"
                    )
                raise VirtualAction("EXIT", {"broker_execution_assumed": True})

            def __getattr__(self, name):
                if name in {
                    "get_sell_side_open_time_block_fields",
                    "sell_side_open_time_passthrough_reason",
                    "resolve_order_dmst_stex_tp",
                    "describe_order_route_resolution",
                }:
                    return getattr(original_orders, name)
                return lambda *a, **kw: services.call("kiwoom_orders." + name, *a, **kw)

        handlers.kiwoom_orders = Orders()

        def virtual_exit(code, qty, token, **kwargs):
            if code != observation["stock_code"] or qty != state["qty"]:
                raise ReplayInputGap("virtual_exit_quantity_or_symbol_mismatch")
            raise VirtualAction("EXIT", {"broker_execution_assumed": True})

        handlers.SEND_EXIT_BEST_IOC = virtual_exit
        # NO_ADD is the explicitly defined control intervention, not a policy
        # relaxation. No real handler or real rules are changed by these hooks.
        handlers.can_consider_scale_in = (
            (lambda *a, **kw: {"allowed": False, "reason": "no_add_control"})
            if state["no_add_control"]
            else original_add_gate
        )
        handlers.execute_scale_in_order = (
            (lambda *a, **kw: None) if state["no_add_control"] else original_execute_add
        )

        def virtual_remaining(code, order_no, token, expected_qty, **kwargs):
            if (
                order_no
                or stock.get("pending_entry_orders")
                or stock.get("sell_cancel_reconciliation_required")
            ):
                raise ReplayInputGap("virtual_open_order_reconciliation_required")
            if int(expected_qty) != state["qty"]:
                raise ReplayInputGap("virtual_inventory_quantity_conflict")
            return int(expected_qty)

        handlers._confirm_cancel_or_reload_remaining = virtual_remaining

        def virtual_durability(stock, code, *, target_id, **kwargs):
            if (
                stock.get("sell_submit_pending") is not True
                or stock.get("sell_submit_target_id") != target_id
                or stock.get("sell_submit_requested_qty") != state["qty"]
                or stock.get("sell_submit_context_sha256")
                != handlers._sell_submit_context_sha256(stock)
            ):
                raise ReplayInputGap("virtual_sell_generation_contract_invalid")
            return True

        handlers._persist_sell_submit_pre_call_boundary = virtual_durability

        cancellation = {"completed": False}

        def virtual_cancel(stock, *args, **kwargs):
            if state["pending_add"] is None:
                raise ReplayInputGap("virtual_cancel_without_pending_order")
            handlers._clear_pending_add_meta(stock)
            state["pending_add"] = None
            state.pop("pending_add_expired", None)
            cancellation["completed"] = True
            # Preserve control flow: the real policy can cancel then EXIT in
            # the same evaluation. Do not invent an extra one-frame delay.
            return {"cleared": True, "reason": "virtual_full_unfilled_cancel"}

        handlers._cancel_or_reconcile_pending_add = virtual_cancel
        action, detail = "HOLD", {}
        try:
            if state["filled_add_qty"] != context.get("filled_add_qty", 0):
                fill = state.get("last_virtual_fill") or {}
                delta = state["filled_add_qty"] - context.get("filled_add_qty", 0)
                if fill.get("qty") != delta or fill.get("add_type") not in {
                    "AVG_DOWN",
                    "PYRAMID",
                }:
                    raise ReplayInputGap("independent_add_fill_lineage_invalid")
                virtual_order = str(90000000 + len(state["legs"]) - 1)
                stock.update(
                    pending_add_order=True,
                    pending_add_ord_no=virtual_order,
                    pending_add_qty=delta,
                    pending_add_type=fill["add_type"],
                    pending_add_reason=fill.get("reason", ""),
                    pending_add_requested_at=datetime.fromisoformat(
                        fill["filled_at"]
                    ).timestamp()
                    - 0.001,
                )
                receipts._handle_add_buy_execution(
                    target_id=stock["id"],
                    target_stock=stock,
                    code=observation["stock_code"],
                    order_no=virtual_order,
                    exec_price=int(fill["price"]),
                    exec_qty=delta,
                    now=datetime.fromtimestamp(current["epoch"], tz=_KST),
                    order_qty=delta,
                    remaining_qty=0,
                    cumulative_exec_amount=int(fill["price"] * delta),
                    execution_no="offline-counterfactual-" + input_digest,
                    unit_exec_price=int(fill["price"]),
                    unit_exec_qty=delta,
                )
                if (
                    stock.get("buy_qty") != state["qty"]
                    or abs(stock.get("buy_price", 0) - state["buy_price"]) > 0.0001
                ):
                    raise ReplayInputGap("independent_add_receipt_state_mismatch")
            else:
                stock.update(buy_qty=state["qty"], buy_price=state["buy_price"])
            if state["pending_add"] is not None:
                pending = state["pending_add"]
                stock.update(
                    pending_add_order=True,
                    pending_add_ord_no=str(90000000 + len(state["legs"])),
                    pending_add_qty=pending["qty"],
                    pending_add_type=pending.get("add_type", "AVG_DOWN"),
                    pending_add_reason=pending.get("reason", ""),
                    pending_add_requested_at=pending["expires_at"] - 20.0,
                )
            # Receipt persistence is virtual too; later inventory predicates
            # must see this arm's rebased quantity/average, not the pre-fill row.
            handlers.DB = VirtualInventoryDB(stock)
            handlers.evaluate_and_dispatch_fast_scalp_exit(
                stock,
                observation["stock_code"],
                deepcopy(frame["market"]["ws_data"]),
                now_ts=current["epoch"],
            )
            regime_row = recorded_inputs.get("market_regime")
            regime = frame["market"].get("market_regime")
            if regime_row is not None:
                if regime_row["observed_at"] > current["epoch"]:
                    raise ReplayInputGap("future_market_regime_input")
                regime = regime_row["value"]
            if not regime or regime == "UNKNOWN":
                raise ReplayInputGap("recorded_market_regime_missing")
            handlers.handle_holding_state(
                stock,
                observation["stock_code"],
                deepcopy(frame["market"]["ws_data"]),
                0,
                regime,
                now_ts=current["epoch"],
                now_dt=datetime.fromtimestamp(current["epoch"], tz=_KST),
                radar=services.proxy("radar"),
                ai_engine=ai_engine,
            )
        except VirtualAction as outcome:
            action, detail = outcome.action, outcome.detail
        except ReplayInputGap as gap:
            if gap.request:
                requests.append(gap.request)
            return {
                "replay_input_gap": gap.reason,
                "evaluated_stages": stages,
                "call_path": gap.call_path,
            }
        after = deepcopy(context)
        after["filled_add_qty"] = state["filled_add_qty"]
        after["ldm_promote_counter"] = _json_value(ldm._PROMOTE_COUNTER)
        if ai_engine.recorded_state_ready:
            after["ai_engine_state"] = {
                name: _json_value(getattr(ai_engine, name)) for name in AI_STATE_FIELDS
            }
        after["stock"] = _json_value(stock)
        after["globals"] = {
            name: _json_value(getattr(handlers, name)) for name in context["globals"]
        }
        after["ai_budget"]["events"] = {
            key: _json_value(list(rows))
            for key, rows in handlers.DEFAULT_HOT_PATH_AI_SYMBOL_BUDGET._events.items()
        }
        return {
            "input_digest": input_digest,
            "policy_version": policy,
            "source_event_id": "avgdn-policy-" + input_digest,
            "input_cutoff": frame["emitted_at"],
            "full_policy_evaluation": True,
            "policy_state_after": after,
            "action": action,
            "peak_price_after": handlers.HIGHEST_PRICES.get(
                handlers._price_tracking_key(stock, observation["stock_code"]),
                state["peak_price"],
            ),
            "buy_price_after": stock.get("buy_price"),
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "adapter_version": ADAPTER_VERSION,
            "evaluated_stages": stages,
            "exit_rule": stock.get("last_exit_rule"),
            "virtual_inventory_and_order_durability_assumed": True,
            "policy_evaluation_latency_model": "zero_latency_at_observed_frame",
            "pending_add_cancelled": cancellation["completed"],
            "virtual_cancel_acknowledgement_assumed": cancellation["completed"],
            **detail,
        }

    # Snapshot-backed production evidence must execute the adapter. A recorded
    # label must not take precedence over current-state full-policy execution.
    frames = [{**frame, "full_policy_decisions": {}} for frame in frames]

    def safe_evaluate(*args):
        try:
            return evaluate(*args)
        except ReplayInputGap as gap:
            if gap.request:
                requests.append(gap.request)
            return {"replay_input_gap": gap.reason, "call_path": gap.call_path}

    result = replay_exit_paths(observation, frames, full_exit_evaluator=safe_evaluate)
    result["external_replay_requests"] = requests
    result["policy_adapter"] = ADAPTER_VERSION
    result["evidence_digest"] = canonical_digest(
        {key: value for key, value in result.items() if key != "evidence_digest"}
    )
    # Restore clocks only for interpreter shutdown; the worker is single-use.
    time.time = original_time
    time.monotonic = original_monotonic
    time.perf_counter = original_perf_counter
    return result


def isolated_replay(
    observation: dict, frames: list[dict], *, timeout_sec: float = 45
) -> dict:
    """One disposable process per episode; no live-process monkeypatching."""
    payload = json.dumps(
        {"observation": observation, "frames": frames}, allow_nan=False
    )
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": str(REPO),
        "PYTHONDONTWRITEBYTECODE": "1",
        "TZ": "Asia/Seoul",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
    }
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "src.engine.lifecycle.avg_down_policy_replay",
                "--worker",
            ],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            cwd=REPO,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return {"adapter_error": "isolated_policy_worker_failed"}
        output = json.loads(result.stdout)
        return (
            output
            if isinstance(output, dict)
            else {"adapter_error": "isolated_policy_worker_invalid_output"}
        )
    except subprocess.TimeoutExpired:
        return {"adapter_error": "isolated_policy_worker_timeout"}
    except (ValueError, OSError):
        return {"adapter_error": "isolated_policy_worker_unavailable"}


def _provider_worker(payload: dict) -> dict:
    """Only the existing AI transport, never a holding/broker handler."""
    snapshot, request = payload["policy_snapshot"], payload["request"]
    if (
        request.get("call") != "ai_provider.current_prompt"
        or request.get("actual_order_submitted") is not False
        or request.get("broker_order_forbidden") is not True
        or request.get("policy_version") != snapshot_version(snapshot)
        or snapshot.get("implementation") != implementation_identity()
    ):
        raise ReplayInputGap("provider_replay_request_contract_invalid")
    args, kwargs = thaw(request["args"]), thaw(request["kwargs"])
    if request.get("input_digest") != external_call_key(request["call"], args, kwargs):
        raise ReplayInputGap("provider_replay_input_digest_mismatch")
    if kwargs.get("endpoint_name") not in {"holding_score", "holding_flow"}:
        raise ReplayInputGap("provider_replay_endpoint_forbidden")
    environment = snapshot["environment"]
    if any(not key.startswith("KORSTOCKSCAN_") for key in environment):
        raise ReplayInputGap("unexpected_policy_environment_namespace")
    for key in list(os.environ):
        if key.startswith("KORSTOCKSCAN_"):
            os.environ.pop(key)
    os.environ.update(environment)
    # Freeze import-time endpoint configuration before loading the AI owner.
    from src.engine.ai_engine_openai import GPTSniperEngine
    from src.engine.scalping.ai_decision_quality import _offline_openai_api_keys

    keys = _offline_openai_api_keys()
    if not keys:
        raise ReplayInputGap("configured_ai_credentials_unavailable")
    rules = SimpleNamespace(**thaw(snapshot["rules"]))
    for name, module in list(sys.modules.items()):
        if name.startswith("src.") and hasattr(module, "TRADING_RULES"):
            digest = snapshot.get("module_rules", {}).get(name)
            values = snapshot.get("rule_blobs", {}).get(digest) if digest else None
            module.TRADING_RULES = SimpleNamespace(**thaw(values)) if values else rules
    metadata = dict(kwargs.get("metadata_extra") or {})
    metadata.update(
        source_event_stage="avg_down_offline_policy_replay",
        decision_authority="source_only_paired_exit_replay",
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
        broker_order_forbidden=True,
        replay_input_digest=request["input_digest"],
        replay_input_cutoff=request["input_cutoff"],
    )
    kwargs["metadata_extra"] = metadata
    engine = GPTSniperEngine(keys, announce_startup=False)
    try:
        result = engine._call_openai_safe(*args, **kwargs)
        if not isinstance(result, dict) or result.get("ai_fallback_score_50"):
            raise ReplayInputGap("offline_provider_response_unusable")
        return {
            **request,
            "result": {
                "schema": "avg_down_raw_provider_reply_v1",
                "provider_response": _json_value(result),
                "transport_meta": _json_value(engine._consume_last_transport_meta()),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "generated_at": datetime.now(_KST).isoformat(),
        }
    finally:
        engine._http_deadline_executor.shutdown(wait=False, cancel_futures=True)


def current_provider_replay(snapshot: dict, request: dict) -> dict:
    """Bounded subprocess; existing configured endpoint route and prompt only."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "src.engine.lifecycle.avg_down_policy_replay",
                "--provider-worker",
            ],
            input=json.dumps(
                {"policy_snapshot": snapshot, "request": request}, allow_nan=False
            ),
            text=True,
            capture_output=True,
            cwd=REPO,
            timeout=40,
            check=False,
        )
        if result.returncode:
            return {"adapter_error": "offline_provider_worker_failed"}
        output = json.loads(result.stdout)
        return (
            output
            if isinstance(output, dict)
            else {"adapter_error": "offline_provider_output_invalid"}
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"adapter_error": "offline_provider_unavailable_or_timeout"}


def replay_with_current_policy_ai(
    observation: dict,
    frames: list[dict],
    *,
    executor=current_provider_replay,
    max_provider_calls: int = 16,
    cached_records: list[dict] | None = None,
    deadline: float | None = None,
) -> dict:
    """Complete state-bound AI requests in the existing postclose job.

    No AI is invoked for missing market/policy data, and no arbitrary callback
    name from an artifact is executable. Completed cached replies remain bound
    to their exact frozen policy, input and cutoff, not merely the symbol.
    """
    frames = deepcopy(frames)
    deadline = (
        min(deadline, time.monotonic() + 180)
        if deadline is not None
        else time.monotonic() + 180
    )
    snapshot = observation["policy_snapshot"]
    records = []
    for row in cached_records or []:
        if (
            isinstance(row, dict)
            and row.get("policy_version") == observation["exit_policy_version"]
            and row.get("call") == "ai_provider.current_prompt"
            and isinstance(row.get("input_digest"), str)
            and row.get("actual_order_submitted") is False
            and row.get("broker_order_forbidden") is True
            and "result" in row
        ):
            records.append(deepcopy(row))
    calls = 0
    seen = set()
    while True:
        for row in records:
            for frame in frames:
                if frame["emitted_at"] == row.get("input_cutoff"):
                    frame.setdefault("external_results", {})[row["input_digest"]] = row
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            result = {"adapter_error": "policy_replay_wall_time_budget_exhausted"}
            pending = []
            repaired = False
        else:
            result = isolated_replay(
                observation, frames, timeout_sec=min(45, remaining)
            )
            pending = [
                request
                for request in result.get("external_replay_requests", [])
                if request.get("call") == "ai_provider.current_prompt"
            ]
            repaired = False
        for request in pending:
            identity = (request.get("input_digest"), request.get("input_cutoff"))
            if (
                identity in seen
                or calls >= max_provider_calls
                or deadline - time.monotonic() < 40
            ):
                continue
            seen.add(identity)
            calls += 1
            answer = executor(snapshot, request)
            if (
                isinstance(answer, dict)
                and "result" in answer
                and all(
                    answer.get(key) == request.get(key)
                    for key in (
                        "input_digest",
                        "input_cutoff",
                        "policy_version",
                        "call",
                    )
                )
                and answer.get("actual_order_submitted") is False
                and answer.get("broker_order_forbidden") is True
            ):
                records.append(answer)
                repaired = True
        if not repaired:
            result["policy_ai_provider_call_count"] = calls
            result["policy_ai_budget_exhausted"] = bool(
                pending and calls >= max_provider_calls
            )
            result["policy_ai_replay_records"] = records
            result["policy_replay_wall_time_budget_exhausted"] = (
                deadline - time.monotonic() < 40 and bool(pending)
            )
            result["evidence_digest"] = canonical_digest(
                {
                    key: value
                    for key, value in result.items()
                    if key != "evidence_digest"
                }
            )
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--worker", action="store_true")
    modes.add_argument("--provider-worker", action="store_true")
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    # Keep import/library diagnostics out of the JSON wire protocol.
    protocol = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = (
            _provider_worker(payload)
            if args.provider_worker
            else _worker_replay(payload["observation"], payload["frames"])
        )
    except ReplayInputGap as exc:
        result = {"adapter_error": exc.reason}
    except Exception as exc:
        result = {"adapter_error": "isolated_policy_error:" + type(exc).__name__}
    protocol.write(json.dumps(result, allow_nan=False))
    protocol.flush()


if __name__ == "__main__":
    main()
