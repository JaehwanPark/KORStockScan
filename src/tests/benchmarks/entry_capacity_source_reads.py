"""Bounded offline baseline/candidate capacity replay; no account/network I/O.

Ownership: test benchmark, beside entry_postclose_replay.py. AST loading executes
only the reviewed helpers, never module startup or authentication. Source files
are explicit so an immutable baseline can be compared without editing runtime.
"""

import argparse
import ast
import copy
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import threading
import time
from types import SimpleNamespace
from uuid import uuid4


def load_functions(path, names, namespace):
    tree = ast.parse(Path(path).read_text())
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)


def replay(args):
    clock = SimpleNamespace(time=lambda: 1790928000.0, monotonic=time.monotonic)
    counts = {"physical_http": 0, "logical": 0, "required_http": 0}
    rows = deque(maxlen=8)  # Production logger streams; do not retain an entire sample in RAM.
    diagnostic_count = [0]
    def log(line):
        diagnostic_count[0] += 1
        rows.append(line)
    metadata = {"source": "api_fresh", "amount": 100000, "raw_amount": 100000,
                "effective_amount": 100000, "fallback_used": False,
                "deposit_source_receipt": {"generation": "b" * 64, "observed_epoch": clock.time(),
                    "scope_sha256": hashlib.sha256(b"token:fixture-token").hexdigest(), "raw_amount": 100000}}
    namespace = dict(copy=copy, threading=threading, datetime=datetime, time=clock,
                     os=os, json=json, hashlib=hashlib, re=re, uuid4=uuid4,
                     KIWOOM_TOKEN="fixture-token", _KST=timezone.utc,
                     _ENTRY_NONENTRY_CAPACITY_REUSE_MAX_AGE_SEC=5.0,
                     log_info=log)
    orders = dict(hashlib=hashlib, re=re, time=clock,
                  get_last_deposit_meta=lambda: {**metadata, "deposit_source_receipt": dict(metadata["deposit_source_receipt"])},
                  _deposit_cache_key=lambda token: "token:" + token)
    load_functions(args.orders, {"entry_capacity_deposit_identity"}, orders)
    if not orders.get("entry_capacity_deposit_identity"):
        # The pre-change deposit producer did not publish the new receipt field.
        orders["get_last_deposit_meta"] = lambda: {
            key: value for key, value in metadata.items() if key != "deposit_source_receipt"}
    namespace["kiwoom_orders"] = SimpleNamespace(**{
        "get_last_deposit_meta": orders["get_last_deposit_meta"],
        "entry_capacity_deposit_identity": orders.get("entry_capacity_deposit_identity")})
    # The full financial signature still hashes a fixed 30-target state.
    inventory = [{"code": str(100000 + i), "status": "WATCHING", "buy_qty": 0,
                  "ord_no": None, "pending_buy_msg": None} for i in range(30)]
    namespace["_scale_in_budget_inventory_signature"] = lambda: hashlib.sha256(
        json.dumps({"inventory": inventory, "owner_generation": [1, 2, 0, 3]}, sort_keys=True).encode()).hexdigest()
    for name in ("RECEIPTS", "INFLIGHT", "RETRY_AFTER", "PENDING", "EVENTS", "SOURCE_INFLIGHT", "STATS"):
        namespace["_ENTRY_CAPACITY_" + name] = {}
    namespace["_ENTRY_CAPACITY_LOCK"] = threading.Lock()
    namespace["_ENTRY_CAPACITY_STATS_LOCK"] = threading.Lock()
    load_functions(args.handlers, {"_entry_capacity_receipt_valid", "_entry_capacity_cache_miss",
        "_entry_capacity_read_totals", "_read_entry_capacity_snapshot"}, namespace)
    # Account hash computation is equivalent to the real helper's local import,
    # but this benchmark must not read operator configuration.
    def key(code, price):
        identity = (orders["entry_capacity_deposit_identity"]("fixture-token")
                    if orders.get("entry_capacity_deposit_identity") else orders["get_last_deposit_meta"]())
        return (("token-hash", "fixture-origin", "2026-10-02"), "account-hash", code,
                price, namespace["_scale_in_budget_inventory_signature"](),
                hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest())
    namespace["_entry_capacity_receipt_key"] = key

    # Run the real kt00011 response parser, with a deterministic fake transport.
    from src.utils import kiwoom_utils
    parser_namespace = dict(vars(kiwoom_utils))
    parser_namespace["get_api_url"] = lambda path: "https://example.test" + path
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromtimestamp(clock.time(), tz or timezone.utc)
    parser_namespace["datetime"] = FrozenDatetime
    def transport(**kwargs):
        counts["physical_http"] += 1
        counts["required_http"] += int(kwargs.get("request_class") != "source_only")
        data = {"return_code": 0, "entr": "100000", "aplc_rt": "100%",
                "min_ord_alow_amt": "100000", "min_ord_alowq": "10",
                "profa_100ord_alow_amt": "100000", "profa_100ord_alowq": "10"}
        proof = {"request_attempt_count": 1, "admission_attempt_count": 1,
                 "read_rate_control_status": "admitted", "read_rate_control_waited_sec": 0,
                 "first_http_started_epoch": clock.time(), "last_http_received_epoch": clock.time(),
                 "last_http_status_code": 200}
        return ([data], proof) if kwargs.get("return_meta") else [data]
    parser_namespace["fetch_kiwoom_api_continuous"] = transport
    load_functions(args.utils, {"get_orderable_by_margin_kt00011"}, parser_namespace)
    namespace["kiwoom_utils"] = SimpleNamespace(
        get_orderable_by_margin_kt00011=parser_namespace["get_orderable_by_margin_kt00011"])
    read = namespace["_read_entry_capacity_snapshot"]
    usable = {action: 0 for action in ("ENTER_NOW", "BLOCK", "RECHECK")}
    evidence = []
    wall, cpu = time.perf_counter(), time.process_time()
    for batch in range(args.batches):
        price = 10000 + batch
        for i in range(10):
            metadata.update(source="api_fresh" if i == 0 else "loop_cache",
                            age_sec=i / 100, cache_hit=bool(i))
            snapshot = read("005930", price, source_only=True)
            counts["logical"] += 1
            assert snapshot.get("return_code") == 0
            evidence.append((snapshot["capacity_observed_at"], snapshot["capacity_source_sha256"],
                             snapshot["cash_only_orderable_qty"]))
        for action in usable:
            snapshot = read("005930", price, source_only=True, reuse_only=action != "ENTER_NOW")
            counts["logical"] += 1
            usable[action] += int(snapshot.get("return_code") == 0)
        for _ in range(5):
            assert read("005930", price)["return_code"] == 0
            counts["logical"] += 1
    return {"wall_sec": time.perf_counter() - wall, "cpu_sec": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "counts": counts, "usable_capacity_by_fixed_action": usable,
        "evidence_digest": hashlib.sha256(json.dumps(evidence).encode()).hexdigest(),
        "diagnostic_rows": diagnostic_count[0], "transport": "mocked_zero_network_latency_real_parser",
        "actual_api_calls": 0, "policy_writes": 0,
        "action_labels_are_fixed_fixture_not_machine_policy_performance": True,
        "source_sha256": {name: hashlib.sha256(Path(getattr(args, name)).read_bytes()).hexdigest()
                          for name in ("handlers", "orders", "utils")}}


def main():
    parser = argparse.ArgumentParser()
    for source in ("handlers", "orders", "utils"):
        parser.add_argument("--" + source, required=True)
    parser.add_argument("--batches", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.batches <= 1000:
        parser.error("batches must be within 1..1000")
    print(json.dumps(replay(args), sort_keys=True))


if __name__ == "__main__":
    main()
