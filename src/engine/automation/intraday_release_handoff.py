"""Preserve verified same-day policies across an authorized immutable code handoff.

Ownership: startup automation. This does not create PREOPEN success, policies,
orders, or trading authority; the native custody and bootstrap gates still apply.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from contextvars import ContextVar
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.infrastructure.runtime_release_router import selected_release
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
CONFIRM = "APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF"
_STOPPED_PREPARATION = ContextVar("intraday_stopped_preparation", default=None)
_NATIVE_PREDECESSOR = ContextVar("intraday_native_predecessor", default=None)
_OBSERVER_CUSTODY = ContextVar("intraday_observer_custody", default=None)
_PREDECESSOR_REVIEW = ContextVar("intraday_predecessor_review", default=None)

# Reviewed delivery/observation repair. Exact source pairs, not a blanket
# exception for the large runtime functions. Policy generation, quote timing
# and safety guards retain the original contract; any further byte change
# requires another review. Evidence: docs/audits/machine-auxiliary-signal-delivery-review-2026-10-12.md.
REVIEWED_ENTRY_CONSUMER_SOURCES = {
    # Exact native readiness/claim/timing repair reviewed for this code-only handoff.
    # Evidence: docs/audits/main-native-readiness-deployment-review-2026-10-12.md.
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "26300fee49e3ca28568b07db2b0b7030e577c8070a78bef2477340f34dfba981",
        "d08f8e220cf76f2b2b867e40eb5382bf17491391161277367acf407143e65a21",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "4cbd06363b1156761fd748c51ac9fbb4f54e69b64771f9f86e6770bba5ce177c",
        "45a139a2ed413afb888cd244ae73d60d5f312b503a8e1c54cc1ce599b048d279",
    ),
    "src/engine/sniper_state_handlers.py": (
        "4caaddc9d38008bd55968e2ec7b0553bd50e294c1f687eabf588f34a972c847d",
        "773ba18e4297ffb85be10f53d9490a4f1860f68dab0472b1ead2f1d4ee5c5117",
    ),
    "src/engine/scalping/scanner_async_eval.py": (
        "89742c044a782e9058ab43f91cc3969f0910beff506b51218079225fb6a28220",
        "bfb445c6d44d717ae1fa0cbac6bef5774daadff06199128dcec22c12f7998239",
    ),
    "src/utils/pipeline_event_logger.py": (
        "35bc6825a1e6788a8cb876a6c7eb2774581bc7bc6771f90cb42d2cfe70fcfd1a",
        "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
    ),
    "src/engine/ai_engine_openai.py": (
        "3f3d0baed55847c146c5ef86ca3d1ca52742f307ffc5004e05b038b89a1e8796",
        "b1c79f0fdce031b947280b3472101c5b87797dedc1b7a183eb64a973bbbeb5ae",
    ),
}

# Source-exact shared-deadline latency repair; retain the older reviewed pairs
# above for their already-consumed handoffs. This is no function-wide exemption.
# Evidence: docs/audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md.
REVIEWED_ENTRY_LATENCY_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca",
        "903cd8b37e9e60ecfe51a454a1933484f08d0c3c1c7629f7e55e369608770425",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20",
        "d19c471856511889cf9728a3fee7f13c4bcdfce29566dbea80ae5b581d9e8777",
    ),
    "src/engine/scalping/scanner_async_eval.py": (
        "bfb445c6d44d717ae1fa0cbac6bef5774daadff06199128dcec22c12f7998239",
        "54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748",
    ),
    "src/engine/ai_engine_openai.py": (
        "4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed",
        "34332f4541b381184ca47d371ecc6598b6f2e10534085bf3893c76fef553c7f2",
    ),
}

# Final synchronous provider-boundary repair; previous consumed pairs remain
# valid for their immutable releases. Exact source pair, no broader exemption.
REVIEWED_ENTRY_BOUNDARY_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed",
        "7a2d9795aa7501e0f510368f59282d849456c310c91b46d993d2d540867d678a",
    ),
}

# Response transport health and fresh post-response validation. Exact reviewed
# bytes only; preserve every previously consumed source pair.
# Evidence: docs/audits/main-restart-machine-monitoring-and-timeout-structural-repair-review-2026-10-13.md.
REVIEWED_ENTRY_RESPONSE_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "4d5ff0cc0451365f17feb8ed8f6a113f984abf416f24ac7bd5cb24f2ca596eed",
        "dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671",
    ),
}

# Diagnostic state snapshots reference successfully appended canonical replay
# evidence instead of echoing its frozen code. Older release pairs stay valid.
REVIEWED_ENTRY_STORAGE_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca",
        "0afbd461d2ba0f60fa385179c0f03a7c0aaf0e3972e9b73401776012519783fb",
    ),
}

# Reviewed joint/source diagnostics and compact replay context. The original
# policy and every order guard remain bound; only these exact bytes qualify.
# Evidence: docs/audits/main-joint-operating-and-source-repair-implementation-review-2026-10-13.md.
REVIEWED_JOINT_CONSUMER_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca",
        "fd35f4ccd99ab3aa665737253c5209ec84755a6b67152b3ff0552ae5c4a8d52d",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20",
        "51280b79c7eee85279c9d649c76888cb03954f73c18c1e0ba41a863c4ea8a0a1",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "d08f8e220cf76f2b2b867e40eb5382bf17491391161277367acf407143e65a21",
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
    ),
}

# Reviewed optional REST removal and completed-only initial entry inputs.
# Exact original PREOPEN-to-candidate bytes; retain all earlier consumed pairs.
# Evidence: docs/audits/main-rest-call-removal-and-reduced-input-implementation-review-2026-10-13.md.
REVIEWED_REST_REDUCTION_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "5c0b5e1b97e50ed1bd80c4084795a40eaa430c62a8d52cb30b338dbbf7c574ca",
        "b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20",
        "6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e",
    ),
}

# Observer-only verification reuse; original publication/startup checks remain full.
REVIEWED_IO_OBSERVER_SOURCES = {
    "src/engine/automation/runtime_policy_bootstrap.py": (
        "f58cafa2207bbb2f1457173ff2d63bb41ca038ddb948c25df4f18b12c9e1499b",
        "0df0b5d81707fe66bd38f140a3bcb3c40d7d526d9afa55755a87b8dc8123d5a8",
    ),
}

# Exact original PREOPEN to reviewed digest/observer bytes. No policy verdict reuse.
# Evidence: docs/audits/main-io-residual-implementation-review-2026-10-14.md.
REVIEWED_IO_DIGEST_SOURCES = {
    "src/engine/automation/runtime_policy_bootstrap.py": (
        "0df0b5d81707fe66bd38f140a3bcb3c40d7d526d9afa55755a87b8dc8123d5a8",
        "7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "fa572589c6b2f0ceedd943f16195ac43573d02d285438fd6c28d23e4a1157be9",
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        "5f80256f9484c5fb485502bbdad461639c4d471d070fabde37c1743c3c8fd444",
        "2d9a6c71c088671ff4349117d4df302dec46ebb55f39e98beca703c9fac28d0a",
    ),
}

# Incumbent stop consumer compatibility only; numerical selection and research
# remain pinned to the full current implementation generation.
# Evidence: docs/audits/main-entry-auxiliary-shared-deadline-latency-implementation-review-2026-10-13.md.
REVIEWED_STOP_CONSUMER_SOURCES = {
    "src/engine/scalping/main_stop_policy.py": (
        "70fde9e700d3a56d873029ddde2824d4f166d31301199833da87dc3c02e6216f",
        "c444f74e9da0339b564543322da389bcbe38552c4ed56531e8ebf5c21676752e",
    ),
    "src/engine/automation/main_stop_postclose.py": (
        "efb6eefeeca91b6a91891dffee06cfff996f47095ef70aa637d9afb0f0613a7d",
        "68628fd7c9758946344c5841b90d8073929665d2b61eba40041c74fabc843255",
    ),
}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError("intraday_handoff_object_required")
    return value


def _native_predecessor(day, commit, previous, previous_commit, identity, path, sha):
    """Verify immutable evidence captured while the native Main was alive.

    This never infers old consumption from a stopped process or writes a fake
    intraday consumed receipt. The ordered transition owns the original proof.
    """
    expected = (
        DATA_DIR
        / "runtime/release_transitions"
        / day
        / commit
        / "native-predecessor.json"
    )
    if str(path) != str(expected) or expected.is_symlink() or _sha(expected) != sha:
        raise ValueError("intraday_native_predecessor_hash_invalid")
    value = _read(expected)
    proof = value.get("verification") or {}
    before = expected.parent / "selection-before.json"
    selection = _read(before)
    manifest = _read(bootstrap.manifest_path(day))
    index = DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"
    ref = _read(index)
    receipt = Path(ref["receipt_path"])
    required = {
        str(p)
        for p in [
            bootstrap.env_path(day),
            bootstrap.manifest_path(day),
            _preopen_path(day),
            index,
            receipt,
        ]
    }
    if (
        value.get("schema") != "native_preopen_predecessor_v1"
        or value.get("authority") != "APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART"
        or value.get("candidate_commit") != commit
        or proof.get("schema") != "intraday_pid_consumption_verification_v1"
        or proof.get("status") != "pass"
        or proof.get("basis") != "native_preopen"
        or proof.get("actual_pid_consumed") is not True
        or proof.get("target_date") != day
        or proof.get("pid_identity") != identity
        or not identity.get("start_ticks")
        or identity.get("cwd") != str(Path(previous) / "src")
        or proof.get("selected_release_commit") != previous_commit
        or proof.get("release_root") != str(previous)
        or proof.get("manifest_sha256") != manifest.get("manifest_sha256")
        or manifest.get("target_date") != day
        or manifest.get("selected_release_sha") != previous_commit
        or _preopen(day).get("selected_release_commit") != previous_commit
        or selection.get("actual_pid_consumed") is not True
        or selection.get("schema") != "runtime_release_selection_v1"
        or selection.get("git_commit") != previous_commit
        or selection.get("release_root") != str(previous)
        or (selection.get("actual_pid_receipt") or {}).get("pid") != identity.get("pid")
        or value.get("selection_before_sha256") != _sha(before)
        or receipt.resolve().parent.parent != index.parent.resolve()
        or value.get("prepared_receipt_path") != str(receipt)
        or value.get("prepared_receipt_sha256") != ref.get("receipt_sha256")
        or _sha(receipt) != ref.get("receipt_sha256")
        or set(value.get("frozen_files", {})) != required
        or any(_sha(p) != s for p, s in value["frozen_files"].items())
    ):
        raise ValueError("intraday_native_predecessor_binding_invalid")
    return dict(
        path=str(expected),
        sha256=sha,
        identity=identity,
        verification=proof,
        frozen_files=value["frozen_files"],
    )


def preserve_checklist(day, *, original_content=None):
    """Save the exact already-sealed document before authorized owner edits."""
    index = DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"
    ref = _read(index)
    prepared_path = Path(ref["receipt_path"])
    if _sha(prepared_path) != ref["receipt_sha256"]:
        raise ValueError("intraday_original_prepared_invalid")
    prepared = _read(prepared_path)
    if (
        prepared.get("status") != "prepared_verified"
        or prepared.get("target_date") != day
    ):
        raise ValueError("intraday_original_prepared_invalid")
    controller = _read(
        DATA_DIR
        / "report/postclose_done_controller"
        / ("postclose_done_controller_" + prepared["source_date"] + ".json")
    )
    strict = _read(controller["verification_attempt_path"])
    expected = strict["generation_binding"]["checklist_sha256"]
    source = DATA_DIR.parent / "docs/checklists" / (day + "-stage2-todo-checklist.md")
    dest = (
        DATA_DIR / "runtime/policy_bootstrap/historical_checklists" / (expected + ".md")
    )
    content = source.read_bytes() if original_content is None else original_content
    if not isinstance(content, bytes) or not 0 < len(content) <= 2 * 1024 * 1024:
        raise ValueError("intraday_checklist_original_content_invalid")
    # An editable checklist can advance after native PREOPEN. Reuse only the
    # immutable document whose bytes still match the original strict receipt;
    # never replace the edited operating checklist or reseal its new content.
    if (
        original_content is None
        and hashlib.sha256(content).hexdigest() != expected
        and dest.is_file()
        and not dest.is_symlink()
    ):
        if not 0 < dest.stat().st_size <= 2 * 1024 * 1024:
            raise ValueError("intraday_historical_checklist_snapshot_changed")
        content = dest.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("intraday_checklist_not_current_sealed_generation")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise ValueError("intraday_historical_checklist_snapshot_changed")
    if dest.exists():
        if dest.read_bytes() != content:
            raise ValueError("intraday_historical_checklist_snapshot_changed")
    else:
        with dest.open("xb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
    return dict(
        path=str(dest),
        sha256=expected,
        source_date=prepared["source_date"],
        target_date=day,
    )


def _historical_predecessor(day, commit, expected):
    """Reuse only a snapshot sealed and actually consumed by the predecessor."""
    path, consumed_path = _paths(day, commit)
    prior, consumed = _read(path), _read(consumed_path)
    historical = (prior.get("postclose_source_reseal") or {}).get(
        "historical_checklist"
    ) or {}
    snapshot = path.parent / (commit + ".historical-checklist.md")
    if (
        prior.get("schema") != "intraday_policy_preserving_release_handoff_v1"
        or prior.get("status") != "prepared_verified"
        or prior.get("authority") != CONFIRM
        or prior.get("target_date") != day
        or prior.get("selected_release_commit") != commit
        or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
        or consumed.get("status") != "pass"
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("target_date") != day
        or consumed.get("selected_release_commit") != commit
        or consumed.get("handoff_sha256") != _sha(path)
        or historical.get("path") != str(snapshot)
        or historical.get("sha256") != expected
        or historical.get("git_path")
        != "docs/checklists/" + day + "-stage2-todo-checklist.md"
        or prior.get("frozen_files", {}).get(str(snapshot)) != expected
        or _sha(snapshot) != expected
    ):
        raise ValueError("intraday_historical_predecessor_invalid")
    return historical, {
        "handoff_path": str(path),
        "handoff_sha256": _sha(path),
        "consumed_path": str(consumed_path),
        "consumed_sha256": _sha(consumed_path),
    }


def _paths(day, commit):
    root = DATA_DIR / "runtime/policy_bootstrap/intraday_handoff" / day
    return root / f"{commit}.json", root / f"{commit}.consumed.json"


def _identity(pid):
    proc = Path("/proc") / str(int(pid))
    fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
    if fields[0] == "Z":
        raise ValueError("intraday_pid_zombie")
    cmdline = (proc / "cmdline").read_bytes().split(b"\0")
    if not any(arg.endswith(b"bot_main.py") for arg in cmdline):
        raise ValueError("intraday_pid_not_main")
    return {
        "pid": int(pid),
        "start_ticks": fields[19],
        "cwd": str((proc / "cwd").resolve(strict=True)),
    }


def closed_consumption_observation(day=None, *, now=None):
    """Authenticate prior policy consumption after normal or interrupted process exit.

    The native market terminal, postclose stop and EOD completion are separate
    evidence. This never verifies a new PID, launches Main or activates policy.
    """
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.error_detectors.artifact_freshness import _postclose_main_absent
    from src.engine.error_detectors.process_health import _is_expected_thread_terminal

    current = (now or datetime.now(KST)).astimezone(KST)
    data = DATA_DIR.resolve()
    paths = [
        data / "runtime/runtime_release_selection.json",
        data.parent / "tmp/error_detector_heartbeat.json",
    ]
    records = [router._startup_receipt(p) for p in paths]
    selected, heartbeat = [record[0] for record in records]
    receipt = selected.get("actual_pid_receipt") or {}
    recorded = datetime.fromisoformat(str(receipt.get("recorded_at_kst") or ""))
    day = day or recorded.astimezone(KST).date().isoformat()
    if (
        recorded.tzinfo is None
        or recorded.astimezone(KST).date().isoformat() != day
        or day > current.date().isoformat()
        or selected.get("actual_pid_consumed") is not True
    ):
        raise ValueError("intraday_closed_consumption_scope_invalid")
    root, commit = _selection(require_selected_cwd=False)
    handoff_path, consumed_path = _paths(day, commit)
    consumed, consumed_raw = router._startup_receipt(consumed_path)
    identity = consumed.get("pid_identity") or {}
    expected = dict(
        pid=receipt.get("pid"),
        start_ticks=receipt.get("start_ticks"),
        cwd=receipt.get("process_cwd"),
    )
    if (
        receipt.get("schema") != "runtime_release_pid_receipt_v1"
        or receipt.get("git_commit") != commit
        or receipt.get("release_root") != str(root)
        or expected.get("cwd") != str(root / "src")
        or type(expected.get("pid")) is not int
        or not isinstance(expected.get("start_ticks"), str)
        or not expected["start_ticks"].isdigit()
        or identity != expected
        or consumed.get("target_date") != day
        or consumed.get("selected_release_commit") != commit
        or consumed.get("release_root") != str(root)
        or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
        or consumed.get("status") != "pass"
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("handoff_sha256") != _sha(handoff_path)
    ):
        raise ValueError("intraday_closed_consumption_receipt_invalid")
    try:
        _identity(identity["pid"])
    except FileNotFoundError:
        pass
    else:
        raise ValueError("intraday_closed_consumption_pid_present")
    if not _postclose_main_absent():
        raise ValueError("intraday_closed_consumption_process_inventory_unknown")
    beat = datetime.fromisoformat(
        str((heartbeat.get("main_loop") or {}).get("last_beat") or "")
    )
    terminal = (heartbeat.get("threads") or {}).get("sniper_engine") or {}
    circuit = heartbeat.get("ai_circuit") or {}
    if terminal.get("alive") is True:
        # Abrupt exit is never a normal market terminal or source admission.
        # Authenticate only the already consumed policy generation. The ordered
        # owner independently preserves the unfinished collector before launch.
        collector_path = (
            data / "runtime/scalp_micro_reversion_forward_collector/latest.json"
        )
        collector, collector_raw = router._startup_receipt(collector_path)
        snapshot = collector.get("collector_snapshot") or {}
        observed = datetime.fromisoformat(str(collector.get("generated_at") or ""))
        terminal_at = datetime.fromisoformat(str(terminal.get("last_beat") or ""))
        manifest = _read(bootstrap.manifest_path(day))
        checked = _verify_handoff(day, commit, now=current, historical_observer=True)
        if (
            day != current.date().isoformat()
            or beat.tzinfo is None
            or observed.tzinfo is None
            or terminal_at.tzinfo is None
            or not recorded <= beat <= terminal_at <= current
            or not recorded <= observed <= current
            or (heartbeat.get("main_loop") or {}).get("pid") != identity["pid"]
            or circuit.get("pid") != identity["pid"]
            or circuit.get("process_start_ticks") != identity["start_ticks"]
            or collector.get("schema") != "scalp_micro_reversion_canary_monitor_v1"
            or snapshot.get("process_pid") != identity["pid"]
            or snapshot.get("process_start_ticks") != identity["start_ticks"]
            or snapshot.get("source_contract") != "main_market_source_v1"
            or snapshot.get("collector_lifecycle") != "running"
            or type(snapshot.get("sequence_epoch")) is not int
            or snapshot["sequence_epoch"] <= 0
            or consumed.get("manifest_sha256") != manifest.get("manifest_sha256")
            or checked["status"] != "pass"
        ):
            raise ValueError("intraday_interrupted_consumption_unproven")
        paths.append(collector_path)
        records.append((collector, collector_raw))
        if (
            any(
                router._startup_receipt(p)[1] != record[1]
                for p, record in zip(paths, records)
            )
            or router._startup_receipt(consumed_path)[1] != consumed_raw
            or not _postclose_main_absent()
        ):
            raise ValueError("intraday_interrupted_consumption_generation_changed")
        sources = {
            str(p): hashlib.sha256(record[1]).hexdigest()
            for p, record in zip(paths, records)
        }
        sources.update(
            {
                str(consumed_path): hashlib.sha256(consumed_raw).hexdigest(),
                str(handoff_path): _sha(handoff_path),
                str(bootstrap.manifest_path(day)): _sha(bootstrap.manifest_path(day)),
                **checked.get("handoff", {}).get("frozen_files", {}),
            }
        )
        return dict(
            schema="intraday_closed_consumption_observation_v1",
            target_date=day,
            release_commit=commit,
            basis="interrupted_consumed_process",
            pid_identity=identity,
            terminal_verified=False,
            collector_epoch=snapshot["sequence_epoch"],
            collector_path=str(collector_path),
            collector_sha256=hashlib.sha256(collector_raw).hexdigest(),
            source_admission="unverified_interrupted_epoch",
            selection_sha256=hashlib.sha256(records[0][1]).hexdigest(),
            consumed_sha256=hashlib.sha256(consumed_raw).hexdigest(),
            source_hashes=sources,
            runtime_effect=False,
            current_observation_verified=False,
            new_pid_consumption_claimed=False,
        )
    isolation_path = data.parent / "tmp/postclose_bot_isolation.json"
    isolation, isolation_raw = router._startup_receipt(isolation_path)
    paths.append(isolation_path)
    records.append((isolation, isolation_raw))
    stopped = datetime.fromisoformat(str(isolation.get("started_at") or ""))
    if (
        isolation.get("schema_version") != 1
        or isolation.get("active") is not True
        or isolation.get("target_date") != day
        or isolation.get("session") != "bot"
        or isolation.get("action") not in {"stop", "restart"}
        or isolation.get("reason") != "threshold_cycle_postclose_resource_isolation"
        or (heartbeat.get("main_loop") or {}).get("pid") != identity["pid"]
        or circuit.get("pid") != identity["pid"]
        or circuit.get("process_start_ticks") != identity["start_ticks"]
        or terminal.get("alive") is not False
        or terminal.get("unresolved_scalping_count") != 0
        or type(terminal.get("unresolved_scalping_count")) is not int
        or terminal.get("unresolved_scalping_codes") != ""
        or beat.tzinfo is None
        or stopped.tzinfo is None
        or stopped.astimezone(KST).date().isoformat() != day
        or not recorded <= beat <= stopped <= current
        or not 0 <= (stopped - beat).total_seconds() <= 600
        or not _is_expected_thread_terminal(
            "sniper_engine", terminal, now_ts=stopped.timestamp()
        )
    ):
        raise ValueError("intraday_closed_consumption_terminal_invalid")
    eod_path = data / "runtime/update_kospi_status" / f"update_kospi_{day}.json"
    eod, eod_raw = router._startup_receipt(eod_path)
    finished = datetime.fromisoformat(str(eod.get("finished_at") or ""))
    if finished.tzinfo is None:
        finished = finished.replace(tzinfo=KST)
    db = eod.get("db_state") or {}
    manifest = _read(bootstrap.manifest_path(day))
    checked = _verify_handoff(day, commit, now=current, historical_observer=True)
    if (
        eod.get("target_date") != day
        or eod.get("status") not in {"completed", "completed_with_warnings"}
        or finished.astimezone(KST).date().isoformat() != day
        or finished > stopped
        or db.get("latest_quote_date") != day
        or type(db.get("rows_on_latest_date")) is not int
        or db["rows_on_latest_date"] <= 0
        or consumed.get("manifest_sha256") != manifest.get("manifest_sha256")
        or checked["status"] != "pass"
    ):
        raise ValueError("intraday_closed_consumption_sources_invalid")
    if (
        any(
            router._startup_receipt(p)[1] != record[1]
            for p, record in zip(paths, records)
        )
        or router._startup_receipt(consumed_path)[1] != consumed_raw
        or router._startup_receipt(eod_path)[1] != eod_raw
        or not _postclose_main_absent()
    ):
        raise ValueError("intraday_closed_consumption_generation_changed")
    sources = {
        str(p): hashlib.sha256(record[1]).hexdigest()
        for p, record in zip(paths, records)
    }
    sources.update(
        {
            str(consumed_path): hashlib.sha256(consumed_raw).hexdigest(),
            str(eod_path): hashlib.sha256(eod_raw).hexdigest(),
            str(handoff_path): _sha(handoff_path),
            **checked.get("handoff", {}).get("frozen_files", {}),
        }
    )
    return dict(
        schema="intraday_closed_consumption_observation_v1",
        target_date=day,
        release_commit=commit,
        pid_identity=identity,
        stopped_at=stopped.isoformat(),
        terminal_at=terminal["last_beat"],
        selection_sha256=hashlib.sha256(records[0][1]).hexdigest(),
        consumed_sha256=hashlib.sha256(consumed_raw).hexdigest(),
        source_hashes=sources,
        runtime_effect=False,
        current_observation_verified=False,
        new_pid_consumption_claimed=False,
    )


@contextmanager
def consumed_observation_scope(*, data_root=None):
    """Existing diagnostic readers may inspect sealed custody after normal stop."""
    if (
        data_root is not None
        and Path(data_root).resolve() != DATA_DIR.resolve()
        or _OBSERVER_CUSTODY.get() is not None
    ):
        yield
        return
    selected = _read(DATA_DIR / "runtime/runtime_release_selection.json")
    if selected.get("actual_pid_consumed") is not True:
        # An unconsumed preparation retains its ordinary native launch checks.
        yield
        return
    from src.engine.infrastructure.startup_validation_code_context import _main_context

    if _main_context() is not None:
        # Isolated P5 already binds the native source/code proof. The body
        # still runs its exact consumer validator; no operational probe belongs
        # inside this process- and write-denied loader.
        yield
        return
    from src.engine.error_detectors.artifact_freshness import _postclose_main_absent

    if not _postclose_main_absent():
        yield
        return
    proof = closed_consumption_observation()
    token = _OBSERVER_CUSTODY.set(proof)
    try:
        yield
        if closed_consumption_observation(proof["target_date"]) != proof:
            raise ValueError("intraday_closed_consumption_generation_changed")
    finally:
        _OBSERVER_CUSTODY.reset(token)


def predecessor_review_matches(review, day, root, commit, code_root):
    """One custody predicate for live, closed and failed-preparation readers."""
    if (
        not review
        or review.get("day") != day
        or review.get("root") != root
        or review.get("commit") != commit
        or review.get("code_root") != code_root
    ):
        return False
    observation = review.get("prepared_observation") or review.get(
        "postclose_observation"
    )
    if observation is not None:
        if review.get("postclose_observation") is not None:
            from src.engine.scalping import mechanistic_entry_runtime_policy as N

            matches = lambda path, sha: N.source_receipt_matches(
                dict(path=path, sha256=sha), data_root=DATA_DIR.resolve()
            )
        else:
            matches = lambda path, sha: _sha(path) == sha
        return (
            observation.get("target_date") == day
            and observation.get("release_commit") == commit
            and all(
                observation.get(k) is False
                for k in (
                    "runtime_effect",
                    "actual_pid_consumed",
                    "allowed_runtime_apply",
                )
            )
            and bool(observation.get("source_hashes"))
            and all(
                matches(path, sha) for path, sha in observation["source_hashes"].items()
            )
        )
    identity = review.get("identity") or {}
    if identity.get("cwd") != str(root / "src"):
        return False
    if review.get("closed_observation"):
        return closed_consumption_observation(day) == review["closed_observation"]
    return _identity(identity["pid"]) == identity


@contextmanager
def stopped_postclose_review(target_date):
    """A clean workflow revalidates a native cold selection, without a PID.

    Both selected and successor active-parent receipts must already validate.
    This scope permits the repaired reader only; it does not substitute the
    preceding P5 for a fresh candidate P5 or close current postclose sources.
    """
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.automation.next_preopen_readiness import target_after_postclose
    from src.engine.infrastructure import runtime_release_router as R
    from src.engine.infrastructure import research_release_transition as T
    from src.engine.scalping import reversal_code_handoff as A
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    data = DATA_DIR.resolve()
    workspace = data.parent
    candidate = Path(__file__).resolve().parents[3]
    selector = data / "runtime/runtime_release_selection.json"
    selection, selected_raw, _ = D._owned_metadata(selector)
    root, commit = R.selected_release(workspace)
    candidate_commit = R.git(candidate, "rev-parse", "HEAD")
    R.validate_release(
        workspace,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(workspace),
            release_root=str(candidate),
            git_commit=candidate_commit,
        ),
    )
    day = datetime.now(KST).date().isoformat()
    source = selection.get("source_date")
    if (
        root == candidate
        or selection.get("approved_by") != "user"
        or selection.get("approval_scope")
        != "after_postclose_deploy_for_next_regular_start"
        or selection.get("actual_pid_consumed") is not False
        or selection.get("main_start_authorized") is not False
        or selection.get("actual_pid_receipt")
        or selection.get("deployment_transition")
        or selection.get("next_operating_date") != target_date
        or not isinstance(source, str)
        or not source <= day <= target_date
    ):
        raise ValueError("postclose_review_cold_selection_required")
    if target_after_postclose(source) != target_date:
        from src.engine.automation.next_preopen_readiness import require_failed_preopen_recovery
        from src.utils.market_day import next_krx_trading_date

        require_failed_preopen_recovery(data, target_date)
        if next_krx_trading_date(datetime.fromisoformat(source).date()).isoformat() != target_date:
            raise ValueError("postclose_review_recovery_source_target_invalid")
    protected = (
        data / "runtime/operator_startup_hold.json",
        workspace / "restart.flag",
    )

    def stopped():
        if (
            D._main_pids()
            or not D._session_absent()
            or any(p.exists() or p.is_symlink() for p in protected)
            or selector.read_bytes() != selected_raw
            or R.selected_release(workspace) != (root, commit)
            or datetime.now(KST).date().isoformat() != day
        ):
            raise ValueError("postclose_review_stopped_generation_changed")

    stopped()
    backup = Path(selection.get("previous_selection_backup", ""))
    directory = backup.parent
    if (
        not backup.is_absolute()
        or directory.parent != data / "runtime/research_release_transition"
        or directory.resolve() != directory
        or backup.is_symlink()
    ):
        raise ValueError("postclose_review_transition_path_invalid")
    transition_path = directory / "transition.json"
    transition, transition_raw = (
        T._record(transition_path),
        D._owned_metadata(transition_path)[1],
    )
    entries = transition.get("entries") or []
    if (
        transition.get("state") != "verified"
        or transition.get("transition_id") != directory.name
        or len(entries) != 1
        or transition.get("written") != [str(selector)]
    ):
        raise ValueError("postclose_review_verified_transition_required")
    entry = entries[0]
    prior, prior_raw, _ = D._owned_metadata(backup)
    after = directory / str(entry.get("after_snapshot", ""))
    if (
        entry.get("path") != str(selector)
        or entry.get("before_snapshot") != backup.name
        or entry.get("before_sha256") != T.sha(prior_raw)
        or T.sha(prior_raw) != selection.get("predecessor_selection_sha256")
        or entry.get("after_sha256") != T.sha(selected_raw)
        or set(
            entry.get("accepted_sha256")
            or [entry.get("before_sha256"), entry.get("after_sha256")]
        )
        != {T.sha(prior_raw), T.sha(selected_raw)}
        or after.parent != directory
        or after.name != "after-" + T.sha(selected_raw) + ".bytes"
        or D._owned_metadata(after)[1] != selected_raw
        or transition_path.read_bytes() != transition_raw
        or prior.get("git_commit") != selection.get("previous_git_commit")
        or prior.get("release_root") != selection.get("previous_release_root")
    ):
        raise ValueError("postclose_review_transition_binding_invalid")
    R.validate_release(workspace, prior)
    p5_path = Path(selection.get("candidate_p5_path", ""))
    D.verify_candidate_p5(
        workspace,
        target_date,
        root,
        commit,
        p5_path,
        selection.get("candidate_p5_sha256"),
        prior,
    )
    pointer = N.root(data) / "current.json"
    ptr, pointer_raw, _ = D._owned_metadata(pointer)
    if ptr.get("effective_date") != source:
        raise ValueError("postclose_review_active_source_changed")
    sources = {
        str(p): _sha(p)
        for p in (selector, backup, after, transition_path, p5_path, pointer)
    }
    origin_receipt_day = day
    for code_root, code_commit in ((root, commit), (candidate, candidate_commit)):
        proof = A._validated_origin_receipt(
            data, day, code_root, code_commit, ptr["bundle_sha256"], T.sha(pointer_raw)
        )
        if proof is None and code_root == root:
            # Predecessor custody uses its original issue contract. This
            # authenticates ancestry only, never target-day activation/PID.
            issued = datetime.fromisoformat(selection["selected_at_kst"])
            issued_day = issued.astimezone(KST).date().isoformat()
            if issued.tzinfo is None or not source <= issued_day < day <= target_date:
                raise ValueError("postclose_review_origin_issue_date_invalid")
            proof = A._validated_origin_receipt(
                data, issued_day, code_root, code_commit, ptr["bundle_sha256"],
                T.sha(pointer_raw),
            )
            origin_receipt_day = issued_day
        if proof is None:
            raise ValueError("postclose_review_active_parent_receipt_missing")
        for name, sha in proof["source_hashes"].items():
            if name in sources and sources[name] != sha:
                raise ValueError("postclose_review_source_conflict")
            sources[name] = sha
    successor = N._read(A.path(data, day, candidate_commit, ptr["bundle_sha256"]))
    if (
        successor.get("origin_root") != str(root)
        or successor.get("origin_commit") != commit
        or successor.get("origin_selection_sha256") != T.sha(selected_raw)
        or successor.get("code_hashes") != A.code_hashes()
        or successor.get("actual_pid_consumed") is not False
        or (origin_receipt_day != day and (
            successor.get("activation_date") != target_date
            or successor.get("source_trading_date") != source
        ))
    ):
        raise ValueError("postclose_review_successor_parent_unbound")
    proof = dict(
        target_date=day,
        prepared_target_date=target_date,
        source_date=source,
        release_commit=commit,
        source_hashes=sources,
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
    )
    review = dict(
        day=day,
        root=root,
        commit=commit,
        code_root=candidate,
        code_commit=candidate_commit,
        postclose_observation=proof,
    )
    token = _PREDECESSOR_REVIEW.set(review)
    try:
        stopped()
        if not predecessor_review_matches(review, day, root, commit, candidate):
            raise ValueError("postclose_review_source_changed")
        yield proof
        stopped()
        if not predecessor_review_matches(review, day, root, commit, candidate):
            raise ValueError("postclose_review_source_changed")
    finally:
        _PREDECESSOR_REVIEW.reset(token)


@contextmanager
def stopped_preparation_review(day):
    """Read sealed failed-preparation sources, without renewing launch expiry."""
    from src.engine.automation import ordered_intraday_deploy as D
    from src.engine.infrastructure import runtime_release_router as R

    _today(day, None)
    candidate = Path(__file__).resolve().parents[3]
    driver = D.StoppedDeploymentRecovery(
        DATA_DIR.resolve().parent, candidate, day, D.CONFIRM
    )
    origin = driver.inspect_stopped_origin()
    root, commit = origin["failed_root"], origin["failed_commit"]
    if candidate == root:
        raise ValueError("intraday_stopped_review_requires_clean_successor")
    candidate_commit = R.git(candidate, "rev-parse", "HEAD")
    R.validate_release(
        driver.workspace,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(driver.workspace),
            release_root=str(candidate),
            git_commit=candidate_commit,
        ),
    )
    if origin["selected"].get("native_predecessor_path"):
        native = _native_predecessor(
            day,
            commit,
            driver.previous,
            driver.previous_commit,
            driver.identity,
            origin["selected"]["native_predecessor_path"],
            origin["selected"]["native_predecessor_sha256"],
        )
    else:
        native = D._stopped_intraday_predecessor(
            day,
            driver.previous,
            driver.previous_commit,
            driver.identity,
            origin["failed_path"],
        )
    paths = [driver.selection, driver.hold, origin["failed_path"], origin["prior_path"]]
    sources = {
        **native["frozen_files"],
        **origin["preparation_sources"],
        **{str(path): _sha(path) for path in paths},
    }
    handoff_path, consumed = _paths(day, commit)
    if consumed.exists() or consumed.is_symlink():
        raise ValueError("intraday_stopped_review_consumed_selection")
    body = _read(handoff_path)
    sources.update(body["frozen_files"])
    sources[str(handoff_path)] = _sha(handoff_path)
    proof = dict(
        target_date=day,
        release_commit=commit,
        source_hashes=sources,
        original_first_launch_before=body["first_launch_before"],
        runtime_effect=False,
        actual_pid_consumed=False,
        allowed_runtime_apply=False,
    )
    review = dict(
        day=day,
        root=root,
        commit=commit,
        code_root=candidate,
        code_commit=candidate_commit,
        identity=driver.identity,
        prepared_observation=proof,
    )
    token = _PREDECESSOR_REVIEW.set(review)
    try:
        checked = _verify_handoff(day, commit)
        if checked["status"] != "pass":
            raise ValueError("intraday_stopped_review_source_invalid")
        yield proof
        driver.inspect_stopped_origin()
        if (
            any(_sha(path) != sha for path, sha in sources.items())
            or consumed.exists()
            or consumed.is_symlink()
        ):
            raise ValueError("intraday_stopped_review_generation_changed")
    finally:
        _PREDECESSOR_REVIEW.reset(token)


@contextmanager
def closed_predecessor_review(day):
    """A clean candidate revalidates the closed origin without claiming a PID."""
    from src.engine.infrastructure import runtime_release_router as router

    proof = closed_consumption_observation(day)
    root, commit = _selection(require_selected_cwd=False)
    candidate = Path(__file__).resolve().parents[3]
    candidate_commit = router.git(candidate, "rev-parse", "HEAD")
    router.validate_release(
        DATA_DIR.resolve().parent,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(DATA_DIR.resolve().parent),
            release_root=str(candidate),
            git_commit=candidate_commit,
        ),
    )
    review = _PREDECESSOR_REVIEW.set(
        dict(
            day=day,
            root=root,
            commit=commit,
            code_root=candidate,
            code_commit=candidate_commit,
            identity=proof["pid_identity"],
            closed_observation=proof,
        )
    )
    custody = _OBSERVER_CUSTODY.set(proof)
    try:
        yield proof
        if closed_consumption_observation(day) != proof:
            raise ValueError("intraday_closed_predecessor_changed")
    finally:
        _OBSERVER_CUSTODY.reset(custody)
        _PREDECESSOR_REVIEW.reset(review)


def verify_closed_predecessor_consumption(day):
    with closed_predecessor_review(day) as proof:
        checked = _checked_bootstrap(day, None)
        root, commit = _selection(require_selected_cwd=False)
        return dict(
            schema="intraday_closed_predecessor_verification_v1",
            status="pass",
            target_date=day,
            selected_release_commit=commit,
            release_root=str(root),
            pid_identity=proof["pid_identity"],
            closed_observation=proof,
            manifest_sha256=checked["manifest_sha256"],
            historical_consumption_verified=True,
            actual_pid_consumed=False,
            runtime_effect=False,
        )


def _selection(*, require_selected_cwd=True):
    root, commit = selected_release(DATA_DIR.parent)
    if require_selected_cwd and Path.cwd().resolve() not in (root, root / "src"):
        raise ValueError("intraday_handoff_selected_root_required")
    return root, commit


def _today(day, now):
    current = (now or datetime.now(KST)).astimezone(KST)
    if day != current.date().isoformat() or not is_krx_trading_day(current.date()):
        raise ValueError("intraday_handoff_not_current_trading_day")
    return current


def _preopen_path(day):
    return (
        DATA_DIR
        / "report/threshold_cycle_preopen_status"
        / f"threshold_cycle_preopen_{day}.status.json"
    )


def _preopen(day):
    value = _read(_preopen_path(day))
    updated = datetime.fromisoformat(str(value.get("updated_at") or ""))
    if (
        value.get("target_date") != day
        or value.get("status") != "succeeded"
        or value.get("exit_code") != 0
        or value.get("runtime_env_exists") is not True
        or updated.tzinfo is None
        or updated.astimezone(KST).date().isoformat() != day
    ):
        raise ValueError("intraday_original_preopen_invalid")
    return value


def verify_entry_consumer_code(day, *, family, policy_sha, expected, paths, actual):
    """Verify frozen policy custody and a narrow, immutable entry-only code delta.

    This also works before prepare seals its own handoff: the predecessor must
    have consumed the original manifest and still be the exact live process.
    No policy bytes, producer selection or research acceptance are rewritten.
    """
    from src.engine.infrastructure.startup_validation_code_context import (
        verify_validation_consumer_code,
    )

    validation = verify_validation_consumer_code(
        day,
        family=family,
        policy_sha=policy_sha,
        expected=expected,
        paths=paths,
        actual=actual,
    )
    if validation is not None:
        return validation
    if (DATA_DIR / "runtime/policy_bootstrap/code_handoffs" / day).exists():
        from src.engine.automation import prepared_policy_code_handoff as prepared_code

        review = _PREDECESSOR_REVIEW.get()
        if review is None:
            selection = _read(DATA_DIR / "runtime/runtime_release_selection.json")
            if (
                selection.get("main_start_authorized") is False
                and selection.get("approval_scope")
                == "after_postclose_deploy_for_next_regular_start"
                and Path(__file__).resolve().parents[3]
                != Path(selection.get("release_root") or "")
            ):
                # Controller/strict readers run outside the preparation caller.
                # Authenticate the same stopped native transition independently.
                with stopped_postclose_review(day):
                    return verify_entry_consumer_code(
                        day,
                        family=family,
                        policy_sha=policy_sha,
                        expected=expected,
                        paths=paths,
                        actual=actual,
                    )
        if review is not None:
            root, commit = _selection(require_selected_cwd=False)
            candidate = Path(__file__).resolve().parents[3]
            observation = review.get("postclose_observation")
            custody_day = day
            if observation is not None:
                if observation.get("prepared_target_date") != day:
                    raise ValueError("entry_consumer_prepared_target_unbound")
                custody_day = datetime.now(KST).date().isoformat()
            if not predecessor_review_matches(
                review, custody_day, root, commit, candidate
            ):
                raise ValueError("entry_consumer_prepared_predecessor_unbound")
            origin = prepared_code.resolve_prepared_code_origin(
                DATA_DIR,
                day,
                family=family,
                policy_sha=policy_sha,
                expected=expected,
                paths=paths,
                selected_root=root,
                selected_commit=commit,
            )
            candidate_actual = prepared_code._digest(
                {key: _sha(candidate / name) for key, name in paths.items()}
            )
            if candidate_actual != actual:
                raise ValueError("entry_consumer_prepared_candidate_code_changed")
            changed = _verify_entry_code_delta(
                candidate,
                review["code_commit"],
                origin["origin_commit"],
                paths,
                expected,
            )
            if not predecessor_review_matches(
                review, custody_day, root, commit, candidate
            ) or any(
                _sha(name) != digest for name, digest in origin["sources"].items()
            ):
                raise ValueError("entry_consumer_prepared_predecessor_changed")
            return dict(
                status="verified_intraday_consumer_repair",
                verification_basis="verified_prepared_predecessor_consumer_repair",
                target_date=day,
                policy_sha256=policy_sha,
                origin_commit=origin["origin_commit"],
                release_commit=review["code_commit"],
                code_contract_sha256=expected,
                runtime_code_contract_sha256=actual,
                changed_consumer_paths=changed,
                policy_effect="unchanged",
                actual_pid_consumed=False,
            )
        prepared = prepared_code.verify(
            DATA_DIR,
            day,
            family=family,
            policy_sha=policy_sha,
            expected=expected,
            paths=paths,
            actual=actual,
        )
        if prepared is not None:
            return prepared
    observer = _OBSERVER_CUSTODY.get()
    closed = (
        isinstance(observer, dict)
        and observer.get("schema") == "intraday_closed_consumption_observation_v1"
    )
    if not closed or observer.get("target_date") != day:
        _today(day, None)
    root, commit = _selection(require_selected_cwd=False)
    code_root, code_commit = root, commit
    if Path(__file__).resolve().parents[3] != root:
        review = _PREDECESSOR_REVIEW.get()
        if not predecessor_review_matches(
            review, day, root, commit, Path(__file__).resolve().parents[3]
        ):
            raise ValueError("entry_consumer_release_mismatch")
        code_root, code_commit = review["code_root"], review["code_commit"]
    manifest = _read(bootstrap.manifest_path(day))
    original = _preopen(day)
    origin = manifest.get("selected_release_sha")
    if not origin or origin != original.get("selected_release_commit"):
        raise ValueError("entry_consumer_origin_invalid")
    if family == "pre_submit_delay":
        bound = manifest.get("pre_submit_delay_handoff") or {}
        if (
            bound.get("policy_sha256") != policy_sha
            or bound.get("code_contract_sha256") != expected
            or bound.get("target_date") != day
        ):
            raise ValueError("entry_consumer_policy_binding_invalid")
    elif family == "holding_vote":
        bound = manifest.get("holding_path_vote_policy_receipt") or {}
        if bound.get("bundle_sha256") != policy_sha or bound.get("target_date") != day:
            raise ValueError("entry_consumer_policy_binding_invalid")
    elif family == "main_stop":
        bound = manifest.get("main_stop_confirmation_receipt") or {}
        if (
            bound.get("policy_sha256") != policy_sha
            or bound.get("target_date") != day
            or bound.get("status") != "verified_carried"
        ):
            raise ValueError("entry_consumer_policy_binding_invalid")
    else:
        raise ValueError("entry_consumer_family_invalid")
    current_path, consumed_path = _paths(day, commit)
    review = _PREDECESSOR_REVIEW.get()
    if review is not None and origin == commit and not current_path.exists():
        # First same-day transition from native PREOPEN has no intraday receipt
        # yet. The outer verifier rechecks bootstrap, live env and frozen files;
        # this branch proves only the candidate's exact code compatibility.
        selection = _read(DATA_DIR / "runtime/runtime_release_selection.json")
        receipt = selection.get("actual_pid_receipt") or {}
        identity = review["identity"]
        if (
            manifest.get("target_date") != day
            or selection.get("schema") != "runtime_release_selection_v1"
            or selection.get("actual_pid_consumed") is not True
            or selection.get("release_root") != str(root)
            or selection.get("git_commit") != commit
            or receipt.get("pid") != identity["pid"]
            or str(receipt.get("start_ticks")) != identity["start_ticks"]
            or receipt.get("process_cwd") != identity["cwd"]
            or identity["cwd"] != str(root / "src")
        ):
            raise ValueError("entry_consumer_native_live_predecessor_invalid")
        changed = _verify_entry_code_delta(
            code_root, code_commit, origin, paths, expected
        )
        return dict(
            status="verified_intraday_consumer_repair",
            target_date=day,
            policy_sha256=policy_sha,
            origin_commit=origin,
            release_commit=code_commit,
            code_contract_sha256=expected,
            runtime_code_contract_sha256=actual,
            changed_consumer_paths=changed,
            policy_effect="unchanged",
            candidate_pid_consumed=False,
        )
    if current_path.exists():
        # A policy already consumed by this exact live PID keeps its sealed
        # authority when the editable work checklist changes. No new launch or
        # policy activation uses this read-only proof.
        checked = (
            _verify_handoff(day, commit, historical_observer=True)
            if closed
            else (
                _verify_consumed_handoff(day, commit)
                if consumed_path.exists()
                else verify(day, commit)
            )
        )
        if checked.get("status") != "pass":
            raise ValueError("entry_consumer_handoff_invalid")
    else:
        native = _NATIVE_PREDECESSOR.get()
        if native is not None:
            proof = native["verification"]
            identity = native["identity"]
            if (
                _STOPPED_PREPARATION.get()
                != (day, identity["pid"], proof["release_root"])
                or proof["selected_release_commit"] != origin
                or Path("/proc", str(identity["pid"])).exists()
            ):
                raise ValueError("entry_consumer_native_predecessor_not_stopped")
            _native_predecessor(
                day,
                commit,
                proof["release_root"],
                origin,
                identity,
                native["path"],
                native["sha256"],
            )
            changed = _verify_entry_code_delta(root, commit, origin, paths, expected)
            return dict(
                status="verified_intraday_consumer_repair",
                target_date=day,
                policy_sha256=policy_sha,
                origin_commit=origin,
                release_commit=commit,
                code_contract_sha256=expected,
                runtime_code_contract_sha256=actual,
                changed_consumer_paths=changed,
                policy_effect="unchanged",
            )
        selection = _read(DATA_DIR / "runtime/runtime_release_selection.json")
        previous = selection.get("previous_git_commit")
        prior_path, consumed_path = _paths(day, previous)
        prior, consumed = _read(prior_path), _read(consumed_path)
        if (
            selection.get("approved_by") != "user"
            or selection.get("approval_scope")
            not in {
                "machine_auxiliary_path_repair_deploy_and_restart",
                "entry_input_deadline_repair_deploy_and_restart",
                "ordered_intraday_deploy_and_restart",
            }
            or prior.get("schema") != "intraday_policy_preserving_release_handoff_v1"
            or prior.get("authority") != CONFIRM
            or prior.get("status") != "prepared_verified"
            or prior.get("target_date") != day
            or prior.get("selected_release_commit") != previous
            or prior.get("release_root") != selection.get("previous_release_root")
            or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
            or consumed.get("status") != "pass"
            or consumed.get("actual_pid_consumed") is not True
            or consumed.get("target_date") != day
            or consumed.get("selected_release_commit") != previous
            or consumed.get("handoff_sha256") != _sha(prior_path)
            or consumed.get("release_root") != prior.get("release_root")
            or consumed.get("manifest_sha256") != manifest.get("manifest_sha256")
        ):
            raise ValueError("entry_consumer_predecessor_invalid")
        identity = consumed.get("pid_identity") or {}
        stopped = _STOPPED_PREPARATION.get() == (
            day,
            identity.get("pid"),
            prior["release_root"],
        )
        if (
            not identity.get("start_ticks")
            or identity.get("cwd") != str(Path(prior["release_root"]) / "src")
            or (
                Path("/proc", str(identity.get("pid"))).exists()
                if stopped
                else _identity(identity.get("pid")) != identity
            )
        ):
            raise ValueError("entry_consumer_predecessor_pid_changed")
        required = (
            bootstrap.manifest_path(day),
            bootstrap.env_path(day),
            _preopen_path(day),
        )
        if any(prior.get("frozen_files", {}).get(str(p)) != _sha(p) for p in required):
            raise ValueError("entry_consumer_original_generation_changed")
    changed = _verify_entry_code_delta(code_root, code_commit, origin, paths, expected)
    return dict(
        status="verified_intraday_consumer_repair",
        target_date=day,
        policy_sha256=policy_sha,
        origin_commit=origin,
        release_commit=commit,
        code_contract_sha256=expected,
        runtime_code_contract_sha256=actual,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
    )


# Reviewed B0/B2/B3/B4 consumer repair; original PREOPEN policy and guards stay bound.
REVIEWED_NONFIXED_SUBMIT_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "ab743fd49b99cef9c9c3570fc8b542e3b7f54f983335da5bbdfc5465f5e9943a",
    ),
    "src/engine/ai_engine_openai.py": (
        "dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671",
        "6aa60869d8516af5222902761f412d87864125c8f160a2b6866aecae57d7dc58",
    ),
    "src/engine/sniper_state_handlers.py": (
        "b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3",
        "ff7e21f742986c71711b79dc45c2044291f6e6b80155e343b7ccd1424721e2c4",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e",
        "2498fb498de2d796fd9abc695caad99ccc61b914c2999a640d88f3f5c96f8dac",
    ),
    "src/engine/scalping/scanner_async_eval.py": (
        "54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748",
        "f0dc2bbeca1d3365185df9dac27765e7ec8f16d488a1ef352646374517679441",
    ),
}

# Exact PREOPEN-to-reviewed projection and native-ready delivery consumer bytes.
# Evidence: docs/audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md.
REVIEWED_ENTRY_PROJECTION_DELIVERY_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671",
        "3831d30ef13ab190b07b64d8159d2e2c23ee6ce4b124f0c6504cb053ca145a3a",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e",
        "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "c1abc77a5bfdc983bb4cdf5fa02cd886337f9b71b68204906f6fbe476cdac723",
    ),
    "src/engine/runtime_approval_summary.py": (
        "ed940e9fd88d328b489400055aceba793b9d0ad83b591053fb1912ac501e1aa3",
        "cc43d8de315cc07cd9545c06d1ce4fbfa32eb432d52d39ccb67b16e22f0c8cfd",
    ),
}


# Canonical trusted data mount in the report-only entry-split consumer.
REVIEWED_ENTRY_PROJECTION_MOUNT_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "d276463a93a03a3c161a202811056eeae88a5def1e684ea3d0f5ee8a6217b7eb",
    )
}


# Report-only observer generation and first-current-publication ordering.
REVIEWED_STARTUP_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "112e22fde60ceb305450183883ffe6e3b338df6eb47e8c5d3ce78c282b968558",
    )
}

# Source-exact observer availability and bounded handoff diagnosis; no trading authority.
# Evidence: docs/audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md section8.
REVIEWED_OBSERVER_HEALTH_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "6287ec98260f02ae85e61a2f25147d3011a89ebb276a962f215888fcd409f541",
    )
}


# Exact original PREOPEN-to-reviewed submission and observer repair.
# Preserve native deadlines, policy values, custody and every order guard.
# Evidence: docs/audits/main-submission-crisis-timeout-implementation-review-2026-10-14.md.
REVIEWED_SUBMISSION_TIMEOUT_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "dabda2cb9fee6fd17263465f38866d90ec66f62b7305a2b5bb7a8dd9fc9a1671",
        "58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937",
    ),
    "src/engine/sniper_state_handlers.py": (
        "b7435b6001fc5901f601879a08fa4e61b7c337187e1ac58db5e93984768beaa3",
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
    ),
    "src/engine/scalping/scanner_async_eval.py": (
        "54d8584efa5350575d687b92486e205702f94cfde7a87da0acda46d1f3522748",
        "bfd354bbfbc371e912e873a3cbb40fd1ec2b9f5a78427602f214cfb0543b1d21",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "3f53a161bf5ca4857ec0b6b817ffe1c5bbf0b5e8712444334a421e200f9a40a4",
    ),
}


# Exact original PREOPEN-to-reviewed report-only terminal-session census.
# Earlier consumed source pairs remain valid; no machine/entry policy changes.
# Evidence: docs/audits/main-submission-crisis-timeout-implementation-review-2026-10-14.md.
REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "95bd122be3b47d18236c2cc1127eefc9d0b9dd60771cf387637e9c838790e6fd",
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
    ),
}


# Exact native 2026-10-15 PREOPEN-to-reviewed venue/pending observer repair.
# No source or signal guard is waived; retain all earlier consumed pairs.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_PREMARKET_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "7484dde211aeca61eb8172072f432c7d24bf7803e39c0f73ef9561cb64d0bfcf",
    ),
}


# Exact PREOPEN origin to active-report and native fixed-watch wait repair.
# Earlier deployed pairs remain verifiable; no policy or execution change.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_ACTIVE_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "dd164faf5619deb20eef0456cd1187164f09d7f2094c474a2c691e9b700a253f",
    ),
}


# Exact PREOPEN to quiet current-PID/index and pre-birth incident classification.
# Capability receipts are separate report-only evidence; policies stay unchanged.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_CURRENT_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "8525a03215257c97d8497ad6a55f4b9c7ffd543763c35d31e3730c85759f2221",
    ),
}


# Exact source-bound regular-session observer and approved 92785b7da integration.
# Historical policies/receipts stay intact; entry scheduling retains original TTL.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "628d60031f1b787ad8fe661a261063f6925276e189fd6116d1948dd7db479f8a",
    ),
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "b39ddafe82bfbeab1d48502cce349b0e355e6008a1012a661d3e71973e2afe0e",
    ),
    "src/engine/monitoring/runtime_performance.py": (
        "3021477fe2ce6841e2d8acb734fc2fe0812939cd5b1be74333d18c2e6ed379f9",
        "767fe6bb4e874d8d2e6b56a693f028ecebc02f30ea8cf96a050e47ca6b76ebf8",
    ),
}


# Observer continuation separates small incident/cursor custody from full reports.
# Exact origin/successor pair; no policy or trading path changed.
REVIEWED_OBSERVER_STATE_READER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "f4815942b04cf7cfda9d6db977d9987eb3a5d549e69a0ecdf5a77de10931ef22",
    ),
}


# Native incomplete observations retain UNKNOWN/expired evidence without admission.
# Exact reviewed source pair; see the 10:01 repair in the 2026-10-15 audit.
REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "ad8d684a71c2e6e8917f4a9db539da3df8ed1ef5b77b48cc6c892defc4318582",
    ),
}


# Exact report-only native feature-gap census; no admission or source-coverage grant.
# Evidence: docs/audits/main-submission-observer-native-feature-gap-repair-2026-10-15.md.
REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "c241bc4e58f9025229fb7abce51475a1b6ec4b4c2c79c54e6a35fa53cfb98236",
    ),
}


# Scope-bound raw/selected ready census; no machine/provider admission.
# Review: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_SCOPE_READY_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
    ),
}

# Snapshot-only holding observer concurrency repair. Preserve the original
# PREOPEN contract and every execution gate; bind only these reviewed bytes.
# Evidence: docs/audits/main-holding-context-dictionary-race-repair-2026-10-15.md.
REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "92f4c9380e4bd5caec8f252bbb8deb4f3012de1031ec5d37389c430623efde8d",
    ),
}

# Exact carried-stop source snapshot repair. Publication and consumed sources
# retain strict immutable validation; native future-only appends are locked.
# Evidence: docs/audits/main-finalization-live-vote-read-race-repair-2026-10-15.md.
REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES = {
    "src/engine/automation/main_stop_postclose.py": (
        "360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224",
        "e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13",
    ),
}

# Preserve the frozen predecessor while ordered startup has not completed.
# The producer defers publication; detector deadlines and failures stay strict.
REVIEWED_ORDERED_PUBLICATION_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "182e0a4b73b18536a7acdfe6aef36c88d7a9d919ca0647e6646df9f4c0569456",
    ),
}

# Approved e6326b0b1: classify local opportunity custody without changing the
# preserved policy, provider failure counters or retry/order authority.
# Evidence: docs/audits/main-premarket-error-repair-and-restart-2026-10-15.md.
REVIEWED_OPPORTUNITY_CUSTODY_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937",
        "9731f7d729506494fc088ed74dcd54d7f5daa96604364dcac55131bf53a0cc32",
    ),
}

# Preserve original async identity on early non-provider receipts. Exact bytes;
# no request/deadline renewal, provider admission or policy-selection change.
# Evidence: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES = {
    "src/engine/ai_engine_openai.py": (
        "58aa3ca78af08ef2cac6ec0501cc212947c4c5fa743c58b2daea26c0ba205937",
        "e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6",
    ),
}

# Original result custody across a fixed-watch session boundary. Route conflict
# remains nonexecution; no fallback route, new request or deadline is admitted.
REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "c3ac7e88532734dcd14c1037ecaecea82064701c3a6cc03ae1871e158bc38f80",
    ),
}

# Bind the live KST terminal decision/receipt and exclude proven manual custody
# only when no order or reconciliation is pending. No historical HOLD is inferred.
# Evidence: docs/audits/main-entry-price-progress-deployment-review-2026-10-15.md.
REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
    ),
}


# Exact PREOPEN-to-candidate arm cleanup, with unchanged original deadlines and
# policy/source custody. This is a code check, not selection/startup authority.
# Evidence: docs/audits/main-native-entry-arm-handoff-repair-2026-10-15.md.
REVIEWED_NATIVE_ARM_COMPLETION_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "93285e4678038c07e56b34187dc4a9b4ba7b6ee70c380a32f18eaf622fd57335",
    ),
}


# Carried policy readers exclude only later, never-consumed observation tails.
# Exact reviewed source bytes; full research and numeric selection stay strict.
REVIEWED_CARRIED_SOURCE_BINDING_SOURCES = {
    # Preserve a previous PID's delay incident after current native proof.
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "90388bc7badb918a01763c9f1aa0c1bd10a322c8760034a3768714edba94809d",
        "2f897e3b30c912faba4a96bc4482bd23cd404d70e2ae7fc3593d4492d2395ca4",
    ),
    # Operator-approved 40b931254: long-probe allocation and exact Main weak-veto scope.
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "493b9802652ac820803a5887e7e5670f7bbe8b42d000547abf3f45df06479563",
    ),
    "src/engine/automation/main_stop_postclose.py": (
        "360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224",
        "72334470389eed899eed84da5fb3d157bd8ae6078e2d38bfb10b0bc96b79ba6f",
    ),
}


# Exact reviewed HPSP replay/receipt and 06deaab source-recovery code.
# Policy values, sources and all execution guards remain independently checked.
REVIEWED_HPSP_SOURCE_RECOVERY_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "f19298ecdebfe6bb936c8d3700c50073592da6bdd1548dc104bfc9595399023d",
    ),
    "src/engine/sniper_execution_receipts.py": (
        "97ca5efc27896fb31cf04eeccf596efe389e41b2332907b36039357e3f77472c",
        "dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1",
    ),
    "src/engine/scalping/trailing_mechanical_strength.py": (
        "b2c425e1fff3f8241b9fd5b55c590eeb264b0a1ab909b0059bc32198e6ad6c1a",
        "6e6ff97542868f4624efb18e8b31c1fab6142b37921b98e67f1ace614e79ceb3",
    ),
    "src/engine/scalping/trailing_mechanical_replay.py": (
        "78d8f61e0105818402608bff314bfb11f70850a8701812ab0ddce1cdf9274895",
        "de989aadd577f78f298677d10b6054fb4e11530af6920ba9f0841212c47ddfe2",
    ),
}


# Reviewed preset/cost-clock/manual-handoff observations; original policies stay sealed.
REVIEWED_HOLDING_CONTRACT_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "b87f2ecdd7ef43a9f5268e06a5a9fbf8991223acffd58c3258aec68d77832500",
        "8eaa7493ce235c64e8ccea966afee2a87ef6ee201dd080407584b51925d45ec2",
    ),
    "src/engine/scalping/main_stop_policy.py": (
        "c444f74e9da0339b564543322da389bcbe38552c4ed56531e8ebf5c21676752e",
        "8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087",
    ),
    "src/engine/scalping/main_stop_replay.py": (
        "f609161b46296329cb08a4f4b71a07f465f6e412429286348901d85e66c90363",
        "3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe",
    ),
    "src/engine/automation/main_stop_postclose.py": (
        "360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224",
        "0a33ccf900e7d512ff03ee62923efa95842ea87caeb2987fbd1b479aa18f8258",
    ),
    "src/engine/automation/main_stop_source_index.py": (
        "ddaab50afeee7a47c4a49565f27dc699532aabf8197e5276eb0d57cf974dfdce",
        "802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d",
    ),
}


# Reviewed full-byte pair for one-pass source verification only. Qualification,
# selection, policy values and the original native source proof are unchanged.
# Evidence: main-postclose-read-reduction-deployment-review-2026-10-16.md.
REVIEWED_POSTCLOSE_READ_SOURCES = {
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0",
        "037af000399c501362c62a63e4361501c041e3db0289b1edd059b839e36e0a47",
    ),
}

# Carried stop dependency prefixes remain byte-sealed across later native rows.
REVIEWED_CARRIED_VOTE_PREFIX_SOURCES = {
    "src/engine/automation/main_stop_postclose.py": (
        "e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13",
        "cce1f797bd17f5ddde0aa5eec68cdb285c224e198fea7bb184d03a444ff32c05",
    ),
}

# Completed overnight SELL receipts use their sealed broker/BUY identity only.
REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES = {
    "src/engine/error_detector.py": (
        "6da85a87a0d32d2a2815ee452353394afc2abaeac009084d1f69aa1d2934f875",
        "96c4218b76cd19310afc3d089a1fc6ff0e80a2b0c45316e546600ca6a5d9fb77",
    ),
    "src/engine/holding_exit_observation_report.py": (
        "2ec0a7be672eb04044a9094b7ee445af66cef17720df83efe24e6148110ded03",
        "da364a9f0a6933158e95046f82e7669f0609244c51cd8f35e119949cc0bc0969",
    ),
    "src/engine/scalping/ai_decision_trace.py": (
        "de1eb13ce98abe99980a387e87ab852764d6a4b8f94a24c0c1540234d6e478f4",
        "4ca36bfcf257cb8dc39738cff5e71b3da32f458e8e9febabc31f4acef1277bc4",
    ),
    "src/engine/scalping/continuous_reversal_policy.py": (
        "3522757d44f2cb9201892757dc40a0a9650e2c962709d15b2f7b99b737987627",
        "2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd",
    ),
    "src/engine/scalping/continuous_reversal_policy_v2.py": (
        "1ccf5f2ab3bca1e5f6fbb09d7173979fe48f0019ae1aed8e95df279dcd47fad8",
        "bdee85eff700fae45e0725066180b3336985fec25af49819d01928ccfe06d4c6",
    ),
    "src/engine/scalping/continuous_reversal_policy_v3.py": (
        "905232875ec6767cb4169fd9c8935ccf800f05fa7e3316687398518cae54f0fb",
        "86b942fa51b2079fb9b51df50f8da92e9b92d0fdab4d397ca7f297abe453399b",
    ),
    "src/engine/scalping/continuous_reversal_policy_v4.py": (
        "f37709fb11b2b13006b268c401541749d18e8845de16174b9b6736dfd16ea3d4",
        "9b1e7ba3fefb6df1c6dc20a0c336f30b006ce982f38764c819a91f5e3f091e4f",
    ),
    "src/engine/scalping/continuous_reversal_policy_v5.py": (
        "1d60a547a5730ff34da9c144a14feedfa322e09604bde84a46aafd04999941f6",
        "b222050e81150a95751bcb7f4614e61dadc3ded1232bc76cae81b010b3a7c1e7",
    ),
    "src/engine/scalping/continuous_reversal_policy_v6.py": (
        "568c46b69d35a9c6d4ab03ab92b10c609c711cd311706508e287e1d1431f81f7",
        "d669d8831add3b2a62d51e0e2c98baa7e6eb8e45d45f574d75883fb260cec273",
    ),
    "src/engine/scalping/mechanistic_entry_runtime_policy.py": (
        "671f655287ff452f4dc5162c754c98a9e05e9397eb2a9e217f34fc193db1104d",
        "215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867",
    ),
    "src/engine/scalping/reversal_code_handoff.py": (
        "f73faae0d4eb1e4f844d2cc7b6ab27f0c03316cb6d2aa85a8dbbae44e43c9fec",
        "5fc405a276c114e9ac6966b3d56b662863a5e01ccc4bb61c133db916f9448ab9",
    ),
    "src/engine/scalping/reversal_source_diagnostics.py": (
        "f3d66158bbeae90f8258333d90efb45e652ca95d6b4ef5f868066e0509c18783",
        "bf7dd538048888ce9793ccdf39a6c5c4a463c9e3379f4c3c5c1a09173f543eb8",
    ),
    "src/engine/sniper_execution_receipts.py": (
        "dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1",
        "14faf52dc561d6f0f3f859cae9ea2ec69a7d9dc298f7ddda691bb2e665654880",
    ),
    "src/engine/sniper_post_sell_feedback.py": (
        "8b6d50ce6c5693338942fcbfeeb397d8ac13f244188cc6a8ec50229c19efe501",
        "8fcbf7de95acc2e5ba3121be0f20ece3bbefc7bd22fb57cc4cebe938115fc2d9",
    ),
    "src/engine/sniper_trade_review_report.py": (
        "5267041fe305ab93d636e3fe27f6633c86bddd49f7250418c2898ca55706cefd",
        "fd08e8db61295786759280e46ddaa4d8198a04053d6c702495a26cee76346c39",
    ),
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0",
        "74adf3c630fa6ed24819f371007faa8f8b4ee086c330be2cd8431cfe89af4c52",
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        "c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810",
        "e677004513e6c3b5382ea58933aa39e12feac9dcfafbdd93b88dda53e173bf76",
    ),
    "src/engine/automation/runtime_policy_bootstrap.py": (
        "7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56",
        "1dcbb457a66330ff9285574c2182b146aa4663ac171358249df7571ee6be2b6a",
    ),
    "src/engine/infrastructure/validation_digest_session.py": (
        "8fc28395c82a3efa15896c21362d3be7162656fec506fbba6f939e8c6b5101a3",
        "bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9",
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        "b00edf437d65017bdf10760bac8ebf1a4f603e0a45b6ccc0d32159d5e73985d2",
        "b05fdfdd1f2bb0560c8af33c08d6aa046791d46db90a3b56b5eb2e9d7bbeb326",
    ),
}

# Warning-only health for proven preassessment traces with lazy journals absent.
REVIEWED_PREASSESSMENT_OBSERVER_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
        "a1284490d780a882b8c7591765ccf5f081b53cf9320fe350d03b620263310e55",
    ),
}


# Exact reviewed source-gap/crossing repair; fresh capability fixtures remain required.
# Review: docs/audits/main-postclose-source-gap-final-release-review-2026-10-16.md.
REVIEWED_SOURCE_GAP_CROSSING_SOURCES = {
    "src/engine/ai/holding_exit_vote.py": (
        "05ba419f5affd9f8b329d3719e77cfcf5f3b4c73ac7496ba15336d76faa340c6",
        "8d97be85f1d1e0a5cc1408d1060cd2c43a8014be9456ae10b4251431b190ee6a",
    ),
    "src/engine/ai/holding_vote_replay_source.py": (
        "0d67dab01f0cf1d5ef4657659ab433d892d854ecb6e9a656a5d93b2e439ff7cf",
        "6362843a02931562326ce6d700e25dfc3cb2588c42479edbe204ac2aeadf677f",
    ),
    "src/engine/ai_engine_openai.py": (
        "e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6",
        "61d3cfc4e8bca5348ee2816b5451d294e7d825e2f78fe3d134f4ef30c3bdeb5c",
    ),
    "src/engine/automation/entry_cancel_wait_tuning.py": (
        "5bdf8f81db148490457f2ab36a9f2c1c6fe6a300b7f5ef9f1d720a91bc44491a",
        "8313bcfc096d43dbc62d3e4e5938d1ddd47ef1127e6131aae88b160e3736938e",
    ),
    "src/engine/automation/main_stop_source_index.py": (
        "802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d",
        "791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff",
    ),
    "src/engine/scalping/ai_decision_quality.py": (
        "218b2d1ed9133ed11894d729d27afdef4288b712262811d6c13e6a1fa013e34f",
        "d64bd9fcc77969b326d0ac12938a50ae84b7ad5bf27af113530ce21253b8787f",
    ),
    "src/engine/scalping/entry_cancel_wait_runtime.py": (
        "32dfb19821fb2df08a51da16cc158625c53e468f0cd63a4b5930c321b37e9e0e",
        "8c4871d3064e36d8a57e581bac1ce0b4122325e5f5a2365739f8118adc633b4e",
    ),
    "src/engine/scalping/entry_split_order_plan.py": (
        "ed738295a7de91c3972c8360b655d222b26f69e4d1976b2ef27c2c0f0e660c5c",
        "bf3c8b69f4c92270f8084bbb44373aa213af1dc94da22d91cf4cbd23e300d37f",
    ),
    "src/engine/scalping/holding_profit_exit_semantics.py": (
        "0815edbd37d2932ec57337fe579f5576ffce2fc2140c5273cbdcf26589268454",
        "7512700df7e7d3bf705ec3e5d866bf9b916e564d60312fa3918f950c34431b78",
    ),
    "src/engine/scalping/main_stop_policy.py": (
        "8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087",
        "a5faea8355cc607e795df2a7f6bf48c385ca509579240a9e23589ec41fa435ad",
    ),
    "src/engine/scalping/main_stop_replay.py": (
        "3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe",
        "a9351c17a3b9a7cd84a4be7c6672a801ff77f2c537459d95a9eb18b4eca6ff15",
    ),
    "src/engine/sniper_state_handlers.py": (
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
        "706a7dccde4559254bb9ec2d4bb860fed1bf15c8b7d7c9b2b36103da8c3d797f",
    ),
    "src/engine/sniper_trade_review_report.py": (
        "5267041fe305ab93d636e3fe27f6633c86bddd49f7250418c2898ca55706cefd",
        "b513734f2fe58503f916ff1a513875faf72b75e64cd5fb07c87c68d7b8e61c66",
    ),
}


# Exact reviewed probe partial custody and native WS adoption consumer bytes.
# Review: docs/audits/main-probe-partial-integrated-deployment-review-2026-10-16.md.
REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
        "81a29f9f19090487a48983120f9395e29565603c108d42481915b9ca3b0ab35c",
    ),
    "src/engine/sniper_execution_receipts.py": (
        "dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1",
        "c6e5a208c32165ca112b5f33643494030df79302680e4b93f316a91696d7e7a1",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
        "e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e",
    ),
    "src/engine/kiwoom_websocket.py": (
        "e60b5435694e74fc9afa65101b4b407af4da365d07dbac0b38263c66bf8e8921",
        "9aca69dc06a8fffee8999d8c8c2cdece1760e9fdb21e3c8eddf8cda87a6da9e2",
    ),
}


# Exact source pairs reviewed in long4-source-retention-integration-review-2026-10-16.md.
REVIEWED_LONG4_SOURCE_RETENTION_SOURCES = {
    "src/engine/ai/holding_exit_vote.py": (
        "05ba419f5affd9f8b329d3719e77cfcf5f3b4c73ac7496ba15336d76faa340c6",
        "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
    ),
    "src/engine/ai/holding_vote_replay_source.py": (
        "0d67dab01f0cf1d5ef4657659ab433d892d854ecb6e9a656a5d93b2e439ff7cf",
        "6aa1db742f4f2354c17ed9bd24cfb1bcfaace5e0130a8d0dceef84343ea6a428",
    ),
    "src/engine/ai_engine_openai.py": (
        "e75c946a70ec6513162c5a657604830a82e4d718bd5400076d0e05a1639e56f6",
        "32ad96c3959cfbc934716a2af3d62f9ef2989a6ae3b3a30e3426be2d1fe7c75f",
    ),
    "src/engine/automation/main_stop_postclose.py": (
        "e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13",
        "c3aa703f54661aeae94143fb36afd2d2ac7a4337c1ba346062c21ca2be12a9cc",
    ),
    "src/engine/automation/main_stop_source_index.py": (
        "802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d",
        "791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff",
    ),
    "src/engine/automation/runtime_policy_bootstrap.py": (
        "7a2e67d6d537ccc0a322bbbde8935f96de74869bc48e456bd13071225dd84b56",
        "1dcbb457a66330ff9285574c2182b146aa4663ac171358249df7571ee6be2b6a",
    ),
    "src/engine/holding_exit_observation_report.py": (
        "2ec0a7be672eb04044a9094b7ee445af66cef17720df83efe24e6148110ded03",
        "d9310a1136cc2086e83037c020d5d44a9d3b3f57d1207697bcd8eac8f6cf73fe",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
        "e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
        "1588764df3b3bdedd628d860d832c2ac950171a3928719f4f780ed4a80840ea2",
    ),
    "src/engine/scalping/continuous_reversal_policy.py": (
        "3522757d44f2cb9201892757dc40a0a9650e2c962709d15b2f7b99b737987627",
        "2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd",
    ),
    "src/engine/scalping/holding_path_vote_policy.py": (
        "80950db0e9d7420a29cd9ea2b6c6b1b620227a5e13a6e1929c2361b92eb53ab6",
        "6b739dcdfac2614712e03eb74fb4afeec99cefa28946537c507efc5cc1e5895a",
    ),
    "src/engine/scalping/holding_path_vote_replay.py": (
        "886860aa6181bafb08d5151c4ac1ff0ca5ed6df575cab13e33a0b455cf06366a",
        "cd700be6898f87860182379c768cb2960eb79186b187a27e2ed610707924a7cd",
    ),
    "src/engine/scalping/main_stop_policy.py": (
        "8cdd21315d3d0db00f3383406dbb7d885ca02fef7ed957edf4f9535f0f022087",
        "a5faea8355cc607e795df2a7f6bf48c385ca509579240a9e23589ec41fa435ad",
    ),
    "src/engine/scalping/main_stop_replay.py": (
        "3194cc743fc664176245ccb5ffbb26469d68c4276bc8c86aa4d0d87377615ffe",
        "a9351c17a3b9a7cd84a4be7c6672a801ff77f2c537459d95a9eb18b4eca6ff15",
    ),
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0",
        "74adf3c630fa6ed24819f371007faa8f8b4ee086c330be2cd8431cfe89af4c52",
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        "c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810",
        "e677004513e6c3b5382ea58933aa39e12feac9dcfafbdd93b88dda53e173bf76",
    ),
    "src/engine/sniper_execution_receipts.py": (
        "dc4a57286b38f72c96e538e7eb3851f806af1b9c07e0145f3f5aed51ea00bbe1",
        "179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05",
    ),
    "src/engine/sniper_state_handlers.py": (
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
        "f0277cdfb0e2de299d725afc0d047a6c21aa4ec0608d7139e357dba5eb3be459",
    ),
}

# Exact reviewed delay source/zero-cell/observer repair. The two added
# dependencies did not belong to the incumbent delay contract; their exact
# candidate bytes are verified independently without changing its old digest.
# Evidence: docs/audits/pre-submit-semantic-implementation-review-2026-10-16.md.
REVIEWED_DELAY_SITUATION_SOURCES = {
    "src/engine/automation/pre_submit_delay_partitioned_research.py": (
        "ad5186b7058a1cf7aeefa099cb59e3b03ae51cca7fc26be0e021d90c8e721bdc",
        "1f92ea9be98b4a9d0cce66d4105959b21eb03b5d060c501d628b9cef2cc73d65",
    ),
    "src/engine/automation/pre_submit_delay_source_ledger.py": (
        "8b97e228f167eebcf9e6009325d73f1507e1e00eedf53d21985af64b6e8701f7",
        "8d6a8b3d66af66bba270ba835016403e1740bba16ae374133efb9c3efa681ef0",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
        "b0b3ddc61584f4cfce9890ab97a90160f941ebcf024188f5de4aac316418bb33",
    ),
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "ea2f93040975dcf7b9fc247ad57c706fd2bab6a9b717da7f754a0364e43dccf0",
        "9bf1914b5445ad687d2480352cb01d6ca3ab742709175a3ba7181d1747499edc",
    ),
    "src/engine/scalping/pre_submit_delay_observation.py": (
        "909104c8623dd6219ba0a1cb2b964e8998e5eb52a9bae834db26e9f2cb55a0fa",
        "5128d73f6d45777c5671fd26a774dae5d4839203035607b5bb53a9bcc860e964",
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        "c577f885ca02eef999aad71f514fa7a4ef4f7f13e328c0614e93e46b5be6f810",
        "c2fb791a41e35c326ca874562c332fac0e7ea16cda0066fc82f34679cd93ef1a",
    ),
    "src/engine/sniper_state_handlers.py": (
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
        "4a2545b9d796aab6c9df68f08e57ea5f681a856395cde272a613ddea977d7258",
    ),
}
REVIEWED_DELAY_CONTRACT_EXTENSIONS = {
    (
        "23a13aba62884a5d3a0d48a3f91ebff4262571f6",
        "afb82ed5c746f939e20ea2a7df7dda595b6091f61e46ca2d1ad3e308c1db73bc",
    ): {
        "src/engine/automation/pre_submit_delay_situation_projection.py": "c77e565c1f29b64551e690f0e0901226c73baba2c53a61b6c49239be76c39f28",
        "src/engine/scalping/reversal_extended_catalog.py": "c03dddde3e642bfa9be01c130eabfcfcc420a182108411099339944c594d4f95",
    }
}


# Exact original-policy to reviewed source continuity/control-evidence consumer bytes.
REVIEWED_NONFIXED_CONTINUITY_SOURCES = {
    "src/engine/kiwoom_sniper_v2.py": (
        "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
        "3b35fc7133fc87cf5b23ae6f03c3272b9b78b61840f3bc1c6f0e84db5ba8def4",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
        "2b8af49c0dca2527dd6ab9caea3d8e9e5e98eb73a7f8e069836934d88446ecb6",
    ),
    "src/engine/sniper_state_handlers.py": (
        "bb6108b506bebfb957f7257bbf4e466837f19a48eff6a742a245f5c3b3e57dcf",
        "b18c9204588e52239be3d9167c42fd2ff74855a9244dbb1acd1c36dc78d25fe5",
    ),
}

# Exact report-only as-of retention repair, reviewed with the actual 118 rows.
# Review: docs/audits/main-source-cursor-and-auxiliary-integration-review-2026-10-16.md.
REVIEWED_CURSOR_ASOF_SOURCES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "203b397835edf5ff0d578aa8d5b25126f8c61307adbe92031371b9000d710e56",
        "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
    ),
}


# Exact prepared 10/19 origin to the reviewed quote-delivery consumer bytes.
# No numeric policy, provider or order authority changes cross this boundary.
REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES = {
    "src/engine/automation/postclose_summary_handoff.py": (
        "4a3ba9a16111e709e067083265b4d80f5f887be59414987b52bdb27c12d98575",
        "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
    ),
    "src/engine/runtime_approval_summary.py": (
        "d5cdd024e395aaeb78b7eacbb7cfad077694a2baeccd56125d0d9909c3f3ae11",
        "91dbb00d92f0aeb51de17f92dc0bea31591f1d41ad3bcab24579c8cb3c1dd14d",
    ),
    "src/engine/ai_engine_openai.py": (
        "b5c8b6e262678c5354ced1fd30ae4d20b974e50fbb01187b4ab2a9df61a010d7",
        "fb228f284ff0898c1f260149b653d03c71f8f17f1544fe5bf46cc0aa396c0cc4",
    ),
    "src/engine/sniper_state_handlers.py": (
        "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
        "bc7885265ca7f0f59d2fec49eb56c114d7759b641f68fa80d3285fe9f48429e0",
    ),
}


# Exact 10/19 prepared-policy origin to the reviewed auxiliary input opt-in.
# Registry projection is scope-bound and machine ENTER_NOW-only; the SDK adds
# the selected input contract to provider identity. Delay/holding/stop numeric
# policies, provider selection, order authority and hard guards stay unchanged.
# Review: docs/audits/main-auxiliary-direct-current-combined-comparison-review-2026-10-17.md.
REVIEWED_AUXILIARY_PRODUCTION_INPUT_SOURCES = {
    "src/engine/scalping/reversal_auxiliary_registry.py": (
        "a9ca6ebc7b924fcb8de2dc4b141d99500aacc5f3700fe566b3fea190b24cbd31",
        "5702bd5b558ca0e61c52eb4c3679c4f57d6bc877629ea9635ad6f0143fe413da",
    ),
    "src/engine/ai_engine_openai.py": (
        "b5c8b6e262678c5354ced1fd30ae4d20b974e50fbb01187b4ab2a9df61a010d7",
        "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
    ),
}


# Exact original 10/19 prepared-policy code to the reviewed post-auxiliary
# nonexecution recovery and final AI-expiry guards. The original policy code
# predates the selected release; receipts must retain that original digest.
# Delay, holding and stop numeric policy bytes and SELL custody are unchanged.
# Review: docs/audits/main-post-auxiliary-priority-repair-review-2026-10-17.md.
REVIEWED_POST_AUX_GUARD_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
        "b18dab5939fd13ab09c7e24463785b1677324e3957a3efd07e60d82c085fc235",
    ),
}


# Exact 7f2552 prepared-policy sources to the reviewed quantity-only cost
# producer/reader repair. Research allocation never becomes canonical actual
# holding economics, custody, policy values or execution authority. Existing
# prepared-origin, full inventory, source hash and target-date checks remain.
# Review: docs/proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md section 8.
REVIEWED_QUANTITY_RESEARCH_COST_SOURCES = {
    "src/engine/strategy_position_performance_report.py": (
        "4b7e718a1f8a2e9838095b618067729a94901cc41423e274a9ef07ee464d8bd4",
        "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
    ),
    "src/engine/lifecycle/broker_cost_reconciliation.py": (
        "9b30d53d288834e7e3ae372bd8460e1275a392b6b058181b79ee83e7160f2588",
        "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
    ),
}


# Exact original 10/19 policy to the reviewed delay research/source repair.
# Existing numeric selection, zero-delay policy and machine/auxiliary decisions
# remain unchanged. New quote/recheck receipts and bounded research reads do
# not authorize a numeric successor or replace original source qualification.
# Review: docs/audits/pre-submit-delay-situation-research-implementation-review-2026-10-17.md.
REVIEWED_DELAY_RESEARCH_SOURCES = {
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "9bf1914b5445ad687d2480352cb01d6ca3ab742709175a3ba7181d1747499edc",
        "9cc8929c2bd319694ac86d73e4128013825bf5fdf98289b1b26edadb36ce3a77",
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        "c2fb791a41e35c326ca874562c332fac0e7ea16cda0066fc82f34679cd93ef1a",
        "288e04bcbef55ab04a59585b7ecee7a79838ccf9eae6437205f39fec8812d1e4",
    ),
    "src/engine/scalping/pre_submit_delay_observation.py": (
        "5128d73f6d45777c5671fd26a774dae5d4839203035607b5bb53a9bcc860e964",
        "aff325d1d6f49496bb4548295cae57431980f7d28efb43156cffc61b44bfafa9",
    ),
    "src/engine/sniper_state_handlers.py": (
        "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
        "9d21e30b7cb3070992bfd96c5e7083937686c6441fe6042b72599e879b7efe01",
    ),
    "src/engine/lifecycle/research_storage.py": (
        "fa93d4ac728999184e3d238d9050cb51898b9f62780e80929786385421b719af",
        "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
    ),
    "src/engine/automation/pre_submit_delay_partitioned_research.py": (
        "1f92ea9be98b4a9d0cce66d4105959b21eb03b5d060c501d628b9cef2cc73d65",
        "848ec2b494d8f040348627bf381278602a220606c288c2784cac95d785dcabb7",
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
        "60ab1c4f07c71928f33523b49e8a4143fb1d4e01583dabf3beda6290758f4e23",
    ),
}
# Exact original prepared-policy bytes to the shared read-only startup loader.
# The delay cache gains explicit content date/root and loading receipts; its
# runtime selection and source qualification remain unchanged. Main prepares
# delay/trailing through the same helper before its existing sink initialization.
# No prepared validation grants execution, rewrites a policy or attests a PID.
# Review: docs/proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md.
REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES = {
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        "9bf1914b5445ad687d2480352cb01d6ca3ab742709175a3ba7181d1747499edc",
        "0853914ebbc643de4301b87209c9db106662bd60485146b0d16e495b77c0cd33",
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        "c2fb791a41e35c326ca874562c332fac0e7ea16cda0066fc82f34679cd93ef1a",
        "c5fdf030c87f4faf94a70ecf1d2c4c40a753b4da6069a58ed105f5e43cb76605",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
        "4454e6051c47ef959f0b8201526901fe5bd2dfff3b25aaa5593605cf7f53cd33",
    ),
}
# Exact original 7f policy code to the reviewed 57a4659f4 holding research
# integration. Original policies, economics, stop/trailing thresholds and order
# authority remain unchanged. Changed research functions tighten causal cost,
# original-position equivalence and source provenance; runtime changes only
# attach/clear research references on the existing entry/holding log path.
# Review: docs/audits/main-policy-holding-integrated-candidate-review-2026-10-18.md.
REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES = {
    "src/engine/sniper_state_handlers.py": (
        "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
        "d3a264a90a04bc2f4c6f760f221586e461e8eda8abe389727b846d812a48d9dd",
    ),
    "src/engine/ai/holding_vote_replay_source.py": (
        "6aa1db742f4f2354c17ed9bd24cfb1bcfaace5e0130a8d0dceef84343ea6a428",
        "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
        "39449970d0024236ccaaed2eb996b8b1222f9ec804450071c090dd6eb4bd2955",
    ),
    "src/engine/scalping/holding_vote_exit_models.py": (
        "ae90fb096a17677d313e6d3865d03468b6375f8a1fabe78749ee5aa48190de90",
        "d62e05a36ce59bf7db16f6eae8354f77fdf00b992146fd6e2f0bd2bbed4a2a1b",
    ),
    "src/engine/scalping/universal_trailing_replay.py": (
        "7e8826902ef8a93320455fc5136184834709775629e2f0677445562d7733726e",
        "b3dbcee3a3d2de49e4b58ee71b7d444e4acadb4b515454d03b2ab956aef7f17e",
    ),
}
# The reviewed handler introduces a source-only helper outside the historical
# inventories. Its real-account provenance reader is part of that same source
# closure. Check both exact bytes and candidate Git objects on EVERY native
# handoff verification, without changing the original frozen policy digests.
# Historical handlers do not acquire these new dependencies.
REVIEWED_HOLDING_RESEARCH_DEPENDENCIES = {
    "src/engine/sniper_state_handlers.py": {
        "d3a264a90a04bc2f4c6f760f221586e461e8eda8abe389727b846d812a48d9dd": {
            "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
            "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
        },
    },
}
# Bind omitted historical dependencies and the new shared startup consumer to
# reviewed bytes without adding them to the original sealed policy digest.
REVIEWED_DELAY_CONTRACT_EXTENSIONS[
    (
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
    )
] = {
    "src/engine/pipeline_event_summary.py": "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
    "src/utils/threshold_cycle_registry.py": "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
    "src/engine/infrastructure/main_policy_loading.py": "da58eb3fc403b5117cba011d6bb92f6e15790248d181ada4b73b263d38e073db",
}


# Completed stop/holding research integrated with the native startup loader.
# Exact original 7f-to-reviewed bytes only. Preserve all earlier source pairs;
# this admits incumbent policy carry, never the CPU-blocked grace=0 candidate.
# Review: docs/audits/main-research-integrated-p5-p6-deployment-review-2026-10-18.md.
REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES = {
    "src/engine/automation/main_stop_postclose.py": (
        "531f1498332196f0e54d17b76ed8d30295009a5e5ee9363ad9397613f0740ad2",
        "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
    ),
    "src/engine/automation/main_stop_source_index.py": (
        "791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff",
        "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
        "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
    ),
    "src/engine/kiwoom_orders.py": (
        "53da4d99d98a956b16a9c6b26d256bb95c2625f09381b729666573f6035a82b3",
        "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
        "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
    ),
    "src/engine/lifecycle/broker_cost_source.py": (
        "75cf069ff4529e3d2ae429112e105028f51d757eb87378af15a6e97dba16711c",
        "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
    ),
    "src/engine/log_archive_service.py": (
        "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
        "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
    ),
    "src/engine/monitoring/runtime_performance.py": (
        "767fe6bb4e874d8d2e6b56a693f028ecebc02f30ea8cf96a050e47ca6b76ebf8",
        "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
    ),
    "src/engine/pipeline_event_summary.py": (
        "8500f48239f82c9959ece854b6358df1502ff43d7ce7ec5336dc06853959b2e4",
        "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
    ),
    "src/engine/scalping/holding_vote_exit_models.py": (
        "ae90fb096a17677d313e6d3865d03468b6375f8a1fabe78749ee5aa48190de90",
        "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
    ),
    "src/engine/scalping/initial_quantity_bundle_state.py": (
        "52571601eb807862733b6c878df0a38e2060e4c17a72b097281987813e0253f8",
        "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
    ),
    "src/engine/scalping/main_stop_policy.py": (
        "74600db4eb6897546f266ee87cd3f7001d5562ca8668dbd08ba15371484cafad",
        "8d7bcb0bf87db0dc2a44c99f41e67249831463af8157d23688f0c82e5362bc07",
    ),
    "src/engine/scalping/main_stop_replay.py": (
        "a9351c17a3b9a7cd84a4be7c6672a801ff77f2c537459d95a9eb18b4eca6ff15",
        "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
    ),
    "src/engine/scalping/universal_trailing_replay.py": (
        "7e8826902ef8a93320455fc5136184834709775629e2f0677445562d7733726e",
        "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
    ),
    "src/engine/sniper_execution_receipts.py": (
        "179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05",
        "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
    ),
    "src/engine/sniper_state_handlers.py": (
        "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
        "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
    ),
    "src/utils/threshold_cycle_registry.py": (
        "41c0a941d66a66bd1e6827960e225439e4af185f1d5635939a362f8345096541",
        "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
    ),
}

# Shared Claim ownership and its direct policy-code consumers. These exact
# source pairs supplement, rather than replace, the reviewed research pairs.
# The helper was already in delay's original digest; stop/holding add it as a
# separately verified extension and retain their original 17/22-key digests.
REVIEWED_RESEARCH_BUDGET_INTEGRATION_SOURCES = {
    "src/engine/lifecycle/research_input_budget.py": (
        "a29ba8caeddd652e764e1a760218006038cc83ebc9aec89e5b78055598eedcf2",
        "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
    ),
    "src/engine/scalping/main_stop_policy.py": (
        "74600db4eb6897546f266ee87cd3f7001d5562ca8668dbd08ba15371484cafad",
        "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
    ),
    "src/engine/scalping/holding_vote_experiment.py": (
        "0086eb212c3187c5b89e8680adacb28d96aad56d7f45e96788839f0824bdeaae",
        "93633c0a9cea34837dd3bea2297dcb5305eb23651133e67d3788bc4fa2ad1007",
    ),
}

# The original stop digest covers 17 keys. Added current implementation keys
# are verified separately, without rewriting that sealed historical digest.
REVIEWED_DELAY_CONTRACT_EXTENSIONS[
    (
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        "687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533",
    )
] = {
    "src/engine/../database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
    "src/engine/../database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
    "src/engine/../trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
    "src/engine/../trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
    "src/engine/../utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
    "src/engine/../utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
    "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
    "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
    "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
    "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
    "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
    "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
    "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
    "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
    "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
    "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
    "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
    "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
    "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
    "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
    "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
    "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
    "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
    "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
    "src/engine/sniper_execution_receipts.py": "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
    "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
}

REVIEWED_DELAY_CONTRACT_EXTENSIONS[
    (
        "7f2552aedde8fec6ef904a43105827907e50dfc8",
        "6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112",
    )
] = {
    "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63"
}

# All three native families include this exact handler. Bind its integrated
# source/quantity/reader and holding/helper closure on every verification;
# another handler generation gains no exception through this dependency map.
REVIEWED_HOLDING_RESEARCH_DEPENDENCIES["src/engine/sniper_state_handlers.py"][
    "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf"
] = {
    "src/database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
    "src/database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
    "src/engine/ai/holding_exit_vote.py": "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
    "src/engine/ai/holding_vote_replay_source.py": "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
    "src/engine/ai_prompt_contracts.py": "53c589056f5732e550616a371fa95fd63fdcb92341d50216d18d91795aa4c1e5",
    "src/engine/ai_response_contracts.py": "f94031a3776b4aba1045593ee0f9fd2f5432b88f68b97faad43e549f0b83004b",
    "src/engine/automation/main_holding_allocated_cost_diagnostics.py": "7f1bf1c32568b004f2913bf8e1705d8b003e21dc6f8916784282df202291c313",
    "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
    "src/engine/automation/main_stop_postclose.py": "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
    "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
    "src/engine/automation/main_stop_source_index.py": "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
    "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
    "src/engine/automation/main_trailing_all_scope_research.py": "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
    "src/engine/automation/main_trailing_source_assembler.py": "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
    "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
    "src/engine/holding_exit_observation_report.py": "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
    "src/engine/infrastructure/main_policy_loading.py": "da58eb3fc403b5117cba011d6bb92f6e15790248d181ada4b73b263d38e073db",
    "src/engine/infrastructure/main_prompt_policy_loading.py": "563976e1aa7a8867a330a1db0e897023ab87f9c56784264841029bdf8a6cb4f1",
    "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
    "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
    "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
    "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
    "src/engine/lifecycle/holding_research_cost.py": "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
    "src/engine/lifecycle/holding_window_generation.py": "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
    "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
    "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
    "src/engine/lifecycle/research_json_stream.py": "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
    "src/engine/lifecycle/research_storage.py": "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
    "src/engine/lifecycle/snapshot_archive.py": "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
    "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
    "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
    "src/engine/scalping/entry_setup_live_policy.py": "7899aff816388574b57dd51d44156547b433f3fc153f1ea69bfde15b04d82512",
    "src/engine/scalping/entry_setup_scalping_rollout.py": "368f9007ea9f3d248bc2242e660f3e8d4f589dcb90a26993303b61ded3aba0d9",
    "src/engine/scalping/entry_split_order_plan.py": "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
    "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
    "src/engine/scalping/holding_path_vote_policy.py": "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
    "src/engine/scalping/holding_prompt_live_policy.py": "b8229b59d6633a27b025427a07485bbe759a798452bebac45c97c8298deed1bd",
    "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
    "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
    "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
    "src/engine/scalping/main_stop_policy.py": "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
    "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
    "src/engine/scalping/main_stop_replay.py": "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
    "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
    "src/engine/scalping/position_sizing_allocator.py": "c3decb9a56f14d81c27e7628034468185876c1c06c2b3aae1d5baf17da9b8029",
    "src/engine/scalping/reversal_evaluation_context.py": "109bf1d154bf12c0656fcf1694567f4fefe0cd6e6f85d98cdaa8b9439f13ed59",
    "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
    "src/engine/scalping/trailing_exit_decision.py": "11221ba40df78f181b1c5a8236a8481bd7dad75351c94f36d2ce84a53a8ca61a",
    "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
    "src/engine/sniper_execution_receipts.py": "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
    "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
    "src/engine/strategy_position_performance_report.py": "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
    "src/trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
    "src/trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
    "src/utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
    "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
    "src/utils/market_day.py": "ef42333260854caa6c69b12488b62d16e6ea58c1e32b8edc48ffeefd66206ca8",
    "src/utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
}


# Exact read-only startup preparation and immutable auxiliary source carry.
# Preserve the historical 59-file closure above. This selector admits one
# complete 75-file generation (59 + 9 read-only + 8 OS-proof + 1 carry owner,
# with the two previously listed readers deduplicated), never mixed hashes.
# Original policy digests and the historical delay extension stay unchanged.
REVIEWED_STARTUP_READONLY_DEPENDENCY_VARIANTS = {
    (
        "src/engine/sniper_state_handlers.py",
        "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
    ): {
        "contract_extensions": {
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
            ): {
                "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
                "src/engine/pipeline_event_summary.py": "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
                "src/utils/threshold_cycle_registry.py": "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
            }
        },
        "dependencies": {
            "src/database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
            "src/database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
            "src/engine/ai/holding_exit_vote.py": "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "src/engine/ai/holding_vote_replay_source.py": "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "src/engine/ai_prompt_contracts.py": "53c589056f5732e550616a371fa95fd63fdcb92341d50216d18d91795aa4c1e5",
            "src/engine/ai_response_contracts.py": "f94031a3776b4aba1045593ee0f9fd2f5432b88f68b97faad43e549f0b83004b",
            "src/engine/automation/auxiliary_reader_readiness.py": "2d96e61045539ad81d6ef8dcec0ce40543d6bf0bebdfcdc5fb197153c0a016b2",
            "src/engine/automation/main_holding_allocated_cost_diagnostics.py": "7f1bf1c32568b004f2913bf8e1705d8b003e21dc6f8916784282df202291c313",
            "src/engine/automation/main_startup_validation.py": "8465844d01241c4d95f80e207184f2cfa1adac3ca49d7b87d6260fc61d531ce0",
            "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
            "src/engine/automation/main_stop_postclose.py": "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
            "src/engine/automation/main_stop_source_index.py": "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
            "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
            "src/engine/automation/main_trailing_all_scope_research.py": "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "src/engine/automation/main_trailing_source_assembler.py": "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
            "src/engine/holding_exit_observation_report.py": "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
            "src/engine/infrastructure/main_prompt_policy_loading.py": "563976e1aa7a8867a330a1db0e897023ab87f9c56784264841029bdf8a6cb4f1",
            "src/engine/infrastructure/startup_validation_code_context.py": "61891fd2727d59eeee4596690d614d17e9b390aa860c15e81569587e07fd8a02",
            "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
            "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
            "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
            "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
            "src/engine/lifecycle/holding_research_cost.py": "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "src/engine/lifecycle/holding_window_generation.py": "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
            "src/engine/lifecycle/research_json_stream.py": "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
            "src/engine/lifecycle/research_storage.py": "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
            "src/engine/lifecycle/snapshot_archive.py": "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
            "src/engine/scalping/continuous_reversal_policy_v4.py": "85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437",
            "src/engine/scalping/continuous_reversal_policy_v5.py": "5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8",
            "src/engine/scalping/continuous_reversal_policy_v6.py": "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
            "src/engine/scalping/entry_machine_source_recovery.py": "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "src/engine/scalping/entry_setup_live_policy.py": "7899aff816388574b57dd51d44156547b433f3fc153f1ea69bfde15b04d82512",
            "src/engine/scalping/entry_setup_scalping_rollout.py": "368f9007ea9f3d248bc2242e660f3e8d4f589dcb90a26993303b61ded3aba0d9",
            "src/engine/scalping/entry_split_order_plan.py": "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
            "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
            "src/engine/scalping/holding_path_vote_policy.py": "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
            "src/engine/scalping/holding_prompt_live_policy.py": "b8229b59d6633a27b025427a07485bbe759a798452bebac45c97c8298deed1bd",
            "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
            "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
            "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
            "src/engine/scalping/main_stop_policy.py": "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
            "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
            "src/engine/scalping/main_stop_replay.py": "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
            "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
            "src/engine/scalping/position_sizing_allocator.py": "c3decb9a56f14d81c27e7628034468185876c1c06c2b3aae1d5baf17da9b8029",
            "src/engine/scalping/reversal_anchor_index.py": "1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b",
            "src/engine/scalping/reversal_auxiliary_input_transition.py": "07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb",
            "src/engine/scalping/reversal_auxiliary_next_session.py": "301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa",
            "src/engine/scalping/reversal_auxiliary_source_handoff.py": "147d5e7aadec848f947400b87547cc67acb235fc0245afd303bfa71b623580e6",
            "src/engine/scalping/reversal_current_backend.py": "c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153",
            "src/engine/scalping/reversal_evaluation_context.py": "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "src/engine/scalping/reversal_extended_runtime.py": "f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b",
            "src/engine/scalping/reversal_operating_backend.py": "df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6",
            "src/engine/scalping/reversal_operating_runtime.py": "344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e",
            "src/engine/scalping/reversal_path_runtime.py": "ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36",
            "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
            "src/engine/scalping/trailing_exit_decision.py": "11221ba40df78f181b1c5a8236a8481bd7dad75351c94f36d2ce84a53a8ca61a",
            "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
            "src/engine/sniper_execution_receipts.py": "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
            "src/engine/strategy_position_performance_report.py": "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "src/trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "src/trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
            "src/utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
            "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
            "src/utils/market_day.py": "ef42333260854caa6c69b12488b62d16e6ea58c1e32b8edc48ffeefd66206ca8",
            "src/utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
        },
        "selector_path": "src/engine/scalping/reversal_evaluation_context.py",
        "selector_sha256": "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
    }
}


# P5 reuses an observed native parent validation only inside its attested
# child context. Keep the historical 59- and 75-source generations intact; this
# exact selector binds the complete 76-source successor and its proof owners.
REVIEWED_DELAY_PARENT_VERIFICATION_SOURCES = {
    "src/engine/automation/pre_submit_delay_partitioned_research.py": (
        "1f92ea9be98b4a9d0cce66d4105959b21eb03b5d060c501d628b9cef2cc73d65",
        "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
    )
}

REVIEWED_DELAY_PARENT_VERIFICATION_DEPENDENCY_VARIANTS = {
    (
        "src/engine/sniper_state_handlers.py",
        "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
    ): {
        "contract_extensions": {
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
            ): {
                "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
                "src/engine/pipeline_event_summary.py": "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
                "src/utils/threshold_cycle_registry.py": "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
            }
        },
        "dependencies": {
            "src/database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
            "src/database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
            "src/engine/ai/holding_exit_vote.py": "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "src/engine/ai/holding_vote_replay_source.py": "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "src/engine/ai_prompt_contracts.py": "53c589056f5732e550616a371fa95fd63fdcb92341d50216d18d91795aa4c1e5",
            "src/engine/ai_response_contracts.py": "f94031a3776b4aba1045593ee0f9fd2f5432b88f68b97faad43e549f0b83004b",
            "src/engine/automation/auxiliary_reader_readiness.py": "2d96e61045539ad81d6ef8dcec0ce40543d6bf0bebdfcdc5fb197153c0a016b2",
            "src/engine/automation/main_holding_allocated_cost_diagnostics.py": "7f1bf1c32568b004f2913bf8e1705d8b003e21dc6f8916784282df202291c313",
            "src/engine/automation/main_startup_validation.py": "81a290d5f5a63accf15753f56f5e1761676afde8d06236718270804c69d0c1d4",
            "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
            "src/engine/automation/main_stop_postclose.py": "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
            "src/engine/automation/main_stop_source_index.py": "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
            "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
            "src/engine/automation/main_trailing_all_scope_research.py": "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "src/engine/automation/main_trailing_source_assembler.py": "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "src/engine/automation/pre_submit_delay_partitioned_research.py": "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
            "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
            "src/engine/holding_exit_observation_report.py": "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
            "src/engine/infrastructure/main_prompt_policy_loading.py": "563976e1aa7a8867a330a1db0e897023ab87f9c56784264841029bdf8a6cb4f1",
            "src/engine/infrastructure/startup_validation_code_context.py": "b6dca7d83d0290c55b733c932405c8aea6bd9a7144ced95992103aa1fbc418d4",
            "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
            "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
            "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
            "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
            "src/engine/lifecycle/holding_research_cost.py": "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "src/engine/lifecycle/holding_window_generation.py": "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
            "src/engine/lifecycle/research_json_stream.py": "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
            "src/engine/lifecycle/research_storage.py": "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
            "src/engine/lifecycle/snapshot_archive.py": "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
            "src/engine/scalping/continuous_reversal_policy_v4.py": "85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437",
            "src/engine/scalping/continuous_reversal_policy_v5.py": "5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8",
            "src/engine/scalping/continuous_reversal_policy_v6.py": "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
            "src/engine/scalping/entry_machine_source_recovery.py": "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "src/engine/scalping/entry_setup_live_policy.py": "7899aff816388574b57dd51d44156547b433f3fc153f1ea69bfde15b04d82512",
            "src/engine/scalping/entry_setup_scalping_rollout.py": "368f9007ea9f3d248bc2242e660f3e8d4f589dcb90a26993303b61ded3aba0d9",
            "src/engine/scalping/entry_split_order_plan.py": "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
            "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
            "src/engine/scalping/holding_path_vote_policy.py": "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
            "src/engine/scalping/holding_prompt_live_policy.py": "b8229b59d6633a27b025427a07485bbe759a798452bebac45c97c8298deed1bd",
            "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
            "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
            "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
            "src/engine/scalping/main_stop_policy.py": "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
            "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
            "src/engine/scalping/main_stop_replay.py": "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
            "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
            "src/engine/scalping/position_sizing_allocator.py": "c3decb9a56f14d81c27e7628034468185876c1c06c2b3aae1d5baf17da9b8029",
            "src/engine/scalping/reversal_anchor_index.py": "1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b",
            "src/engine/scalping/reversal_auxiliary_input_transition.py": "07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb",
            "src/engine/scalping/reversal_auxiliary_next_session.py": "301bbe9cc29efa2be9ed9f84b4d919ab1f9adaeae7b2e36ec45a58f3842bdefa",
            "src/engine/scalping/reversal_auxiliary_source_handoff.py": "147d5e7aadec848f947400b87547cc67acb235fc0245afd303bfa71b623580e6",
            "src/engine/scalping/reversal_current_backend.py": "c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153",
            "src/engine/scalping/reversal_evaluation_context.py": "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "src/engine/scalping/reversal_extended_runtime.py": "f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b",
            "src/engine/scalping/reversal_operating_backend.py": "df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6",
            "src/engine/scalping/reversal_operating_runtime.py": "344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e",
            "src/engine/scalping/reversal_path_runtime.py": "ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36",
            "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
            "src/engine/scalping/trailing_exit_decision.py": "11221ba40df78f181b1c5a8236a8481bd7dad75351c94f36d2ce84a53a8ca61a",
            "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
            "src/engine/sniper_execution_receipts.py": "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
            "src/engine/strategy_position_performance_report.py": "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "src/trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "src/trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
            "src/utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
            "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
            "src/utils/market_day.py": "ef42333260854caa6c69b12488b62d16e6ea58c1e32b8edc48ffeefd66206ca8",
            "src/utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
        },
        "selector_path": "src/engine/automation/pre_submit_delay_partitioned_research.py",
        "selector_sha256": "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
    }
}


# Exact stopped PREOPEN auxiliary carry; preserve prior dependency generations.
# Review: docs/audits/preopen-alert-repair-2026-10-19.md.
REVIEWED_STOPPED_PREOPEN_DEPENDENCY_VARIANTS = {
    (
        "src/engine/sniper_state_handlers.py",
        "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
    ): {
        "contract_extensions": {
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
            ): {
                "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
                "src/engine/pipeline_event_summary.py": "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
                "src/utils/threshold_cycle_registry.py": "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
            }
        },
        "dependencies": {
            "src/database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
            "src/database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
            "src/engine/ai/holding_exit_vote.py": "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "src/engine/ai/holding_vote_replay_source.py": "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "src/engine/ai_prompt_contracts.py": "53c589056f5732e550616a371fa95fd63fdcb92341d50216d18d91795aa4c1e5",
            "src/engine/ai_response_contracts.py": "f94031a3776b4aba1045593ee0f9fd2f5432b88f68b97faad43e549f0b83004b",
            "src/engine/automation/auxiliary_reader_readiness.py": "2d96e61045539ad81d6ef8dcec0ce40543d6bf0bebdfcdc5fb197153c0a016b2",
            "src/engine/automation/main_holding_allocated_cost_diagnostics.py": "7f1bf1c32568b004f2913bf8e1705d8b003e21dc6f8916784282df202291c313",
            "src/engine/automation/main_startup_validation.py": "81a290d5f5a63accf15753f56f5e1761676afde8d06236718270804c69d0c1d4",
            "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
            "src/engine/automation/main_stop_postclose.py": "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
            "src/engine/automation/main_stop_source_index.py": "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
            "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
            "src/engine/automation/main_trailing_all_scope_research.py": "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "src/engine/automation/main_trailing_source_assembler.py": "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "src/engine/automation/pre_submit_delay_partitioned_research.py": "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
            "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
            "src/engine/holding_exit_observation_report.py": "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
            "src/engine/infrastructure/main_prompt_policy_loading.py": "563976e1aa7a8867a330a1db0e897023ab87f9c56784264841029bdf8a6cb4f1",
            "src/engine/infrastructure/startup_validation_code_context.py": "7b3bfea027c860e2fbe329b7ea193c1c10cb95875952ef21045bd687deeb435c",
            "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
            "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
            "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
            "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
            "src/engine/lifecycle/holding_research_cost.py": "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "src/engine/lifecycle/holding_window_generation.py": "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
            "src/engine/lifecycle/research_json_stream.py": "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
            "src/engine/lifecycle/research_storage.py": "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
            "src/engine/lifecycle/snapshot_archive.py": "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
            "src/engine/scalping/continuous_reversal_policy_v4.py": "85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437",
            "src/engine/scalping/continuous_reversal_policy_v5.py": "5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8",
            "src/engine/scalping/continuous_reversal_policy_v6.py": "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
            "src/engine/scalping/entry_machine_source_recovery.py": "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "src/engine/scalping/entry_setup_live_policy.py": "7899aff816388574b57dd51d44156547b433f3fc153f1ea69bfde15b04d82512",
            "src/engine/scalping/entry_setup_scalping_rollout.py": "368f9007ea9f3d248bc2242e660f3e8d4f589dcb90a26993303b61ded3aba0d9",
            "src/engine/scalping/entry_split_order_plan.py": "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
            "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
            "src/engine/scalping/holding_path_vote_policy.py": "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
            "src/engine/scalping/holding_prompt_live_policy.py": "b8229b59d6633a27b025427a07485bbe759a798452bebac45c97c8298deed1bd",
            "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
            "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
            "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
            "src/engine/scalping/main_stop_policy.py": "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
            "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
            "src/engine/scalping/main_stop_replay.py": "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
            "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
            "src/engine/scalping/position_sizing_allocator.py": "c3decb9a56f14d81c27e7628034468185876c1c06c2b3aae1d5baf17da9b8029",
            "src/engine/scalping/reversal_anchor_index.py": "1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b",
            "src/engine/scalping/reversal_auxiliary_input_transition.py": "07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb",
            "src/engine/scalping/reversal_auxiliary_next_session.py": "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1",
            "src/engine/scalping/reversal_auxiliary_source_handoff.py": "f114eaa85987d72d2361a25e7d5aa2fa41ac5fcf6ad74992c0fe40658e038d82",
            "src/engine/scalping/reversal_current_backend.py": "c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153",
            "src/engine/scalping/reversal_evaluation_context.py": "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "src/engine/scalping/reversal_extended_runtime.py": "f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b",
            "src/engine/scalping/reversal_operating_backend.py": "df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6",
            "src/engine/scalping/reversal_operating_runtime.py": "344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e",
            "src/engine/scalping/reversal_path_runtime.py": "ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36",
            "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
            "src/engine/scalping/trailing_exit_decision.py": "11221ba40df78f181b1c5a8236a8481bd7dad75351c94f36d2ce84a53a8ca61a",
            "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
            "src/engine/sniper_execution_receipts.py": "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
            "src/engine/strategy_position_performance_report.py": "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "src/trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "src/trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
            "src/utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
            "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
            "src/utils/market_day.py": "ef42333260854caa6c69b12488b62d16e6ea58c1e32b8edc48ffeefd66206ca8",
            "src/utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
        },
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": "7b3bfea027c860e2fbe329b7ea193c1c10cb95875952ef21045bd687deeb435c",
    }
}


# Exact partial-sell and closed-window research dependency generation.
REVIEWED_PARTIAL_SELL_OBSERVER_DEPENDENCY_VARIANTS = {
    (
        "src/engine/sniper_state_handlers.py",
        "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
    ): {
        "contract_extensions": {
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533",
            ): {
                "src/engine/../database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
                "src/engine/../database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
                "src/engine/../trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
                "src/engine/../trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
                "src/engine/../utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
                "src/engine/../utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
                "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
                "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
                "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
                "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
                "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
                "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
                "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
                "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
                "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
                "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
                "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
                "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
                "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
                "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
                "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
                "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
                "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
                "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
                "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
                "src/engine/sniper_execution_receipts.py": "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
                "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
            },
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112",
            ): {
                "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63"
            },
            (
                "7f2552aedde8fec6ef904a43105827907e50dfc8",
                "bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256",
            ): {
                "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
                "src/engine/pipeline_event_summary.py": "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
                "src/utils/threshold_cycle_registry.py": "5e914fc73837324d312a97672b0aa7d8bd49c788bcd54ff7e0a6ab3c0d08ce8a",
            },
        },
        "dependencies": {
            "src/database/db_manager.py": "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
            "src/database/models.py": "7afc7e63a5fdb334df889c5d6ed0a91dd16b1ca077cdf498558f8289077ad784",
            "src/engine/ai/holding_exit_vote.py": "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "src/engine/ai/holding_vote_replay_source.py": "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "src/engine/ai_prompt_contracts.py": "53c589056f5732e550616a371fa95fd63fdcb92341d50216d18d91795aa4c1e5",
            "src/engine/ai_response_contracts.py": "f94031a3776b4aba1045593ee0f9fd2f5432b88f68b97faad43e549f0b83004b",
            "src/engine/automation/auxiliary_reader_readiness.py": "2d96e61045539ad81d6ef8dcec0ce40543d6bf0bebdfcdc5fb197153c0a016b2",
            "src/engine/automation/main_holding_allocated_cost_diagnostics.py": "7f1bf1c32568b004f2913bf8e1705d8b003e21dc6f8916784282df202291c313",
            "src/engine/automation/main_startup_validation.py": "81a290d5f5a63accf15753f56f5e1761676afde8d06236718270804c69d0c1d4",
            "src/engine/automation/main_stop_performance.py": "692e986c6379d24591e390db04407de78ac43fe5acdf7ccf06fa595f132923d4",
            "src/engine/automation/main_stop_postclose.py": "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "src/engine/automation/main_stop_runtime_workload.py": "9f3acc7324e3a218c430a96b751245d5610cedc5a33cb912f7ab870efe8beb38",
            "src/engine/automation/main_stop_source_index.py": "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
            "src/engine/automation/main_stop_source_projection.py": "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
            "src/engine/automation/main_trailing_all_scope_research.py": "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "src/engine/automation/main_trailing_source_assembler.py": "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
            "src/engine/automation/pre_submit_delay_partitioned_research.py": "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
            "src/engine/dashboard_data_repository.py": "fa291db63c49d3e6fd8161c3369b114aba0dd4f6e1d28f1a075478fe7123ec84",
            "src/engine/holding_exit_observation_report.py": "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "src/engine/infrastructure/main_policy_loading.py": "12e3efee0307e875da8f8f011df656db056a0adfd1c8ea821f8574a3d4feb57b",
            "src/engine/infrastructure/main_prompt_policy_loading.py": "563976e1aa7a8867a330a1db0e897023ab87f9c56784264841029bdf8a6cb4f1",
            "src/engine/infrastructure/startup_validation_code_context.py": "7b3bfea027c860e2fbe329b7ea193c1c10cb95875952ef21045bd687deeb435c",
            "src/engine/kiwoom_orders.py": "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
            "src/engine/kiwoom_sniper_v2.py": "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "src/engine/lifecycle/broker_cost_allocation.py": "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
            "src/engine/lifecycle/broker_cost_reconciliation.py": "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
            "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
            "src/engine/lifecycle/holding_research_cost.py": "07bfb6b81c0f304df8c6418b0e056bda3f710d5897bdab26496ef5582a9d6b4e",
            "src/engine/lifecycle/holding_window_generation.py": "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "src/engine/lifecycle/main_stop_research_cost.py": "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "src/engine/lifecycle/research_input_budget.py": "4e831253a975345863bc216623fe12618cc933510ed0154360b38ac068906c63",
            "src/engine/lifecycle/research_json_stream.py": "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
            "src/engine/lifecycle/research_storage.py": "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
            "src/engine/lifecycle/snapshot_archive.py": "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "src/engine/log_archive_service.py": "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "src/engine/monitoring/runtime_performance.py": "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
            "src/engine/scalping/continuous_reversal_policy_v4.py": "85b0611a73c4d7fbbc3b2c2e264a0f7858f78f604f8e58e5face4f760ad4b437",
            "src/engine/scalping/continuous_reversal_policy_v5.py": "5f0ce37100b6453c0d143c79007ca45ba77466ffad40f7298a802709c926acb8",
            "src/engine/scalping/continuous_reversal_policy_v6.py": "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
            "src/engine/scalping/entry_machine_source_recovery.py": "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "src/engine/scalping/entry_setup_live_policy.py": "7899aff816388574b57dd51d44156547b433f3fc153f1ea69bfde15b04d82512",
            "src/engine/scalping/entry_setup_scalping_rollout.py": "368f9007ea9f3d248bc2242e660f3e8d4f589dcb90a26993303b61ded3aba0d9",
            "src/engine/scalping/entry_split_order_plan.py": "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
            "src/engine/scalping/exit_safety_monitor.py": "a7dac48b1659431f15e187021856d5482d4d13426c442b73aba40d8918622b4c",
            "src/engine/scalping/holding_path_vote_policy.py": "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
            "src/engine/scalping/holding_prompt_live_policy.py": "b8229b59d6633a27b025427a07485bbe759a798452bebac45c97c8298deed1bd",
            "src/engine/scalping/holding_vote_exit_models.py": "084f6e6036bc9a3807fe68f2b389fc02d628905d7ba0b08d58e451667547c481",
            "src/engine/scalping/initial_quantity_bundle_state.py": "3dd0ad1be14e821d9b402184aba9b68ee989cf7d8ee45fb47206bdcf3e39da70",
            "src/engine/scalping/main_stop_experiment.py": "d7a23d1742d1b73ddd75af876839eb03500f8ef4baad23d33f0d007102720ffa",
            "src/engine/scalping/main_stop_policy.py": "a9a5f40ac773590816900becaa0f1c9ee5d83203c524d7bb855ee50116675f93",
            "src/engine/scalping/main_stop_quantity_source.py": "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
            "src/engine/scalping/main_stop_replay.py": "4121f176553433e2d07cdc1b8466c4a54edfa6cf00bbe09bde4e12a74258730d",
            "src/engine/scalping/main_stop_runtime_source.py": "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
            "src/engine/scalping/position_sizing_allocator.py": "c3decb9a56f14d81c27e7628034468185876c1c06c2b3aae1d5baf17da9b8029",
            "src/engine/scalping/reversal_anchor_index.py": "1070133ec9af5500ab139a25f77f2ad9aef3049e9232d341d89188a689a7c37b",
            "src/engine/scalping/reversal_auxiliary_input_transition.py": "07f6af4e43b8fb69a9f1e414d60a4930c7063074f78ffdb0a80789987070cbcb",
            "src/engine/scalping/reversal_auxiliary_next_session.py": "c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1",
            "src/engine/scalping/reversal_auxiliary_source_handoff.py": "f114eaa85987d72d2361a25e7d5aa2fa41ac5fcf6ad74992c0fe40658e038d82",
            "src/engine/scalping/reversal_current_backend.py": "c831b0366ee488eddb9f709ef7811c44cceef58646c1b1e00b2bcc3eb55f4153",
            "src/engine/scalping/reversal_evaluation_context.py": "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "src/engine/scalping/reversal_extended_runtime.py": "f6a6b1c7319cf06e29cd08b73f4955e52f4e35f8142978b02999cc47ed976a9b",
            "src/engine/scalping/reversal_operating_backend.py": "df60d4ef78cca385b9b7b57a9c82a74efb8d943da6855ac34dd6bf1ebb24b0a6",
            "src/engine/scalping/reversal_operating_runtime.py": "344a03decd050bbd6767e0073c96b8da6384b9ad329e41a70e1ad7f62066533e",
            "src/engine/scalping/reversal_path_runtime.py": "ffc5e5f6d1f4f50733a7a22d0112c85fdaeaf4b22a319a86f41bd2f89ec5ea36",
            "src/engine/scalping/trailing_entry_research_source.py": "b5e66cf46adbf666ca73271fea1c775ef68874849fdd06fd723b88334233ad41",
            "src/engine/scalping/trailing_exit_decision.py": "11221ba40df78f181b1c5a8236a8481bd7dad75351c94f36d2ce84a53a8ca61a",
            "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
            "src/engine/sniper_execution_receipts.py": "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
            "src/engine/sniper_trade_utils.py": "c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac",
            "src/engine/strategy_position_performance_report.py": "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "src/trading/market/session_contract.py": "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "src/trading/order/owner_custody_registry.py": "95bd5b8696115567a3549f99532d072cd57b0773f7537a41f7272ff773669001",
            "src/utils/constants.py": "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
            "src/utils/kiwoom_utils.py": "ecef123abab917af0a8a9de934d927b40e561ec1b91836f010814ca9b9117120",
            "src/utils/market_day.py": "ef42333260854caa6c69b12488b62d16e6ea58c1e32b8edc48ffeefd66206ca8",
            "src/utils/pipeline_event_logger.py": "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
        },
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": "1c0746f95b03e908ad867540af945d0bfb1abd927d34a8d89954634e6c56baf4",
    }
}

# One complete successor of the reviewed partial-sell generation. Historical
# generations remain immutable; selection requires the exact repaired reader.
REVIEWED_AUXILIARY_HISTORY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/reversal_auxiliary_source_handoff.py",
        "selector_sha256": "f5724a19f06ef4417226c801259e00378217b8e6ebd49355cad2d21e4ad15c0f",
        "dependencies": {
            **value["dependencies"],
            "src/engine/scalping/reversal_auxiliary_source_handoff.py": "f5724a19f06ef4417226c801259e00378217b8e6ebd49355cad2d21e4ad15c0f",
        },
        "contract_extensions": {
            origin: {
                path: (
                    "f5724a19f06ef4417226c801259e00378217b8e6ebd49355cad2d21e4ad15c0f"
                    if path
                    == "src/engine/scalping/reversal_auxiliary_source_handoff.py"
                    else sha
                )
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PARTIAL_SELL_OBSERVER_DEPENDENCY_VARIANTS.items()
}
# Exact report-only historical incident/latency-guard observer successor.
# Preserve every complete historical dependency generation and policy digest.
REVIEWED_SCANNER_HISTORY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": "5a3861b05149893db38be6cc7c56a0f4cbf93911e0a209d31edf222b3b3943bf",
        "dependencies": {
            **value["dependencies"],
            "src/engine/monitoring/submission_bottleneck_monitor.py": "5a3861b05149893db38be6cc7c56a0f4cbf93911e0a209d31edf222b3b3943bf",
        },
        "contract_extensions": {
            origin: {
                path: (
                    "5a3861b05149893db38be6cc7c56a0f4cbf93911e0a209d31edf222b3b3943bf"
                    if path == "src/engine/monitoring/submission_bottleneck_monitor.py"
                    else sha
                )
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AUXILIARY_HISTORY_DEPENDENCY_VARIANTS.items()
}

REVIEWED_AUXILIARY_HISTORY_SOURCES = {
    "src/engine/scalping/reversal_auxiliary_source_handoff.py": (
        "f114eaa85987d72d2361a25e7d5aa2fa41ac5fcf6ad74992c0fe40658e038d82",
        "f5724a19f06ef4417226c801259e00378217b8e6ebd49355cad2d21e4ad15c0f",
    )
}

REVIEWED_PARTIAL_SELL_RESEARCH_SOURCE_PAIRS = {
    "src/engine/automation/main_trailing_research_handoff.py": (
        (
            "7220a496df445299ce758f8d79eee0205fa51e1fdacc9440503f1854c9fda677",
            "f0e4cbe8ba222e361f9726fea04408dfe9b2dc2b40ac7db23106f4d543e2eda6",
        ),
        (
            "23b05aac5bbf6bf20d4463ccdc4f9ffc290c759cfab269540d1afefbbea0a117",
            "f0e4cbe8ba222e361f9726fea04408dfe9b2dc2b40ac7db23106f4d543e2eda6",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
        ),
    ),
    "src/engine/lifecycle/holding_research_cost.py": (
        (
            "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "07bfb6b81c0f304df8c6418b0e056bda3f710d5897bdab26496ef5582a9d6b4e",
        ),
    ),
    "src/engine/sniper_execution_receipts.py": (
        (
            "179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05",
            "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
        ),
        (
            "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
        ),
    ),
}

# Exact reviewed report-only synchronous lineage extension; see 2026-10-19 repair audit.
REVIEWED_SYNC_PROVIDER_OBSERVER_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
            "1c0746f95b03e908ad867540af945d0bfb1abd927d34a8d89954634e6c56baf4",
        ),
        (
            "60ab1c4f07c71928f33523b49e8a4143fb1d4e01583dabf3beda6290758f4e23",
            "1c0746f95b03e908ad867540af945d0bfb1abd927d34a8d89954634e6c56baf4",
        ),
    )
}

REVIEWED_SCANNER_HISTORY_OBSERVER_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": tuple(
        (origin, "5a3861b05149893db38be6cc7c56a0f4cbf93911e0a209d31edf222b3b3943bf")
        for origin in (
            "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
            "60ab1c4f07c71928f33523b49e8a4143fb1d4e01583dabf3beda6290758f4e23",
            "1c0746f95b03e908ad867540af945d0bfb1abd927d34a8d89954634e6c56baf4",
        )
    )
}

# Negative-only carry-census header preflight. The existing full validation,
# archival writer, stop policy and execution paths are unchanged.
REVIEWED_PRIOR_SNAPSHOT_IO_PAIRS = {
    "src/engine/log_archive_service.py": tuple(
        (origin, "f3350ab07429f263dd16e534becccfbe47bb87c62cc97b1b43f096043743aad4")
        for origin in (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
        )
    )
}

# Select one complete successor of the scanner-history generation. This keeps
# the original policy digest and every other dependency hash bound together.
REVIEWED_PRIOR_SNAPSHOT_IO_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/log_archive_service.py",
        "selector_sha256": "f3350ab07429f263dd16e534becccfbe47bb87c62cc97b1b43f096043743aad4",
        "dependencies": {
            **value["dependencies"],
            "src/engine/log_archive_service.py": "f3350ab07429f263dd16e534becccfbe47bb87c62cc97b1b43f096043743aad4",
        },
        "contract_extensions": {
            origin: {
                path: (
                    "f3350ab07429f263dd16e534becccfbe47bb87c62cc97b1b43f096043743aad4"
                    if path == "src/engine/log_archive_service.py"
                    else sha
                )
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SCANNER_HISTORY_DEPENDENCY_VARIANTS.items()
}


# Exact reviewed historical-source repair. A single complete successor binds
# bounded carry reads, quantity event projection and native registry folding.
REVIEWED_ARTIFACT_SOURCE_HASHES = {
    "src/engine/log_archive_service.py": "fd5cb478cb40b70ee2dd7fdcc5bc1ef18afa7cef1659e6be9eaaabab1084eca4",
    "src/engine/scalping/initial_quantity_policy.py": "a6e57b600500e10b20ebf1ca2ac097a2433fbd5f8696e28f8ec1ef97601b627a",
    "src/engine/sniper_trade_review_report.py": "1c8ad45cc988a038935b3b7beab8e9ad9cc26257ea1c3597588e7802c2446adb",
    "src/engine/lifecycle/holding_research_cost.py": "12e76859310d617dc7cdb2c0f758f935f8d7c6619c76cdf02f92aefa92a0627a",
}
REVIEWED_ARTIFACT_SOURCE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/log_archive_service.py",
        "selector_sha256": REVIEWED_ARTIFACT_SOURCE_HASHES[
            "src/engine/log_archive_service.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ARTIFACT_SOURCE_HASHES},
        "contract_extensions": {
            origin: {
                path: REVIEWED_ARTIFACT_SOURCE_HASHES.get(path, sha)
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRIOR_SNAPSHOT_IO_DEPENDENCY_VARIANTS.items()
}
REVIEWED_ARTIFACT_SOURCE_PAIRS = {
    "src/engine/log_archive_service.py": tuple(
        (origin, REVIEWED_ARTIFACT_SOURCE_HASHES["src/engine/log_archive_service.py"])
        for origin in (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "f3350ab07429f263dd16e534becccfbe47bb87c62cc97b1b43f096043743aad4",
        )
    ),
    "src/engine/lifecycle/holding_research_cost.py": tuple(
        (
            origin,
            REVIEWED_ARTIFACT_SOURCE_HASHES[
                "src/engine/lifecycle/holding_research_cost.py"
            ],
        )
        for origin in (
            "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "07bfb6b81c0f304df8c6418b0e056bda3f710d5897bdab26496ef5582a9d6b4e",
        )
    ),
}


# Source bytes revalidation after evidence-only inode metadata changes.
# Preserve the exact preceding source repair as its own complete generation.
REVIEWED_SNAPSHOT_METADATA_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_stop_postclose.py",
        "selector_sha256": "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772",
        "dependencies": {
            **value["dependencies"],
            "src/engine/automation/main_stop_postclose.py": "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772",
        },
        "contract_extensions": {
            origin: {
                path: (
                    "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772"
                    if path == "src/engine/automation/main_stop_postclose.py"
                    else sha
                )
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ARTIFACT_SOURCE_DEPENDENCY_VARIANTS.items()
}
REVIEWED_SNAPSHOT_METADATA_PAIRS = {
    "src/engine/automation/main_stop_postclose.py": (
        (
            "531f1498332196f0e54d17b76ed8d30295009a5e5ee9363ad9397613f0740ad2",
            "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772",
        ),
        (
            "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772",
        ),
    )
}


# Original snapshot identities may survive evidence-only ctime changes only
# after native complete-byte revalidation. Keep one exact complete generation.
REVIEWED_PRESERVED_SNAPSHOT_HASHES = {
    "src/engine/lifecycle/snapshot_archive.py": "f2a8eb56daf861d1ffb10bae945a9753e77ed5e0ed2c935cc1382b17c18f79c3",
    "src/engine/lifecycle/holding_window_generation.py": "b31337f09b51d7d1ad1b06b24f92eda3bc2b19b0f160166e25d603708940926c",
    "src/engine/strategy_position_performance_report.py": "714c9351f73008f06affe988e67fdd104fd0d8d3c23eb8657635b3fa8ff79082",
    "src/engine/holding_exit_observation_report.py": "108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f",
    "src/engine/scalping/initial_quantity_source_cache.py": "b746d9c9d131ab2795953f3e2401f2fe367525dc0d7dc2c85051fdaac73af97c",
}
REVIEWED_PRESERVED_SNAPSHOT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/lifecycle/snapshot_archive.py",
        "selector_sha256": REVIEWED_PRESERVED_SNAPSHOT_HASHES[
            "src/engine/lifecycle/snapshot_archive.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_PRESERVED_SNAPSHOT_HASHES},
        "contract_extensions": {
            origin: {
                path: REVIEWED_PRESERVED_SNAPSHOT_HASHES.get(path, sha)
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SNAPSHOT_METADATA_DEPENDENCY_VARIANTS.items()
}
REVIEWED_PRESERVED_SNAPSHOT_PAIRS = {
    "src/engine/lifecycle/snapshot_archive.py": (
        (
            "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "f2a8eb56daf861d1ffb10bae945a9753e77ed5e0ed2c935cc1382b17c18f79c3",
        ),
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        (
            "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "b31337f09b51d7d1ad1b06b24f92eda3bc2b19b0f160166e25d603708940926c",
        ),
    ),
    "src/engine/strategy_position_performance_report.py": (
        (
            "4b7e718a1f8a2e9838095b618067729a94901cc41423e274a9ef07ee464d8bd4",
            "714c9351f73008f06affe988e67fdd104fd0d8d3c23eb8657635b3fa8ff79082",
        ),
        (
            "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "714c9351f73008f06affe988e67fdd104fd0d8d3c23eb8657635b3fa8ff79082",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "4dfa3c22640ee0f94fdac37633e7adbb0b6be4ecdaa14efe25ca04d840c799a7",
            "b746d9c9d131ab2795953f3e2401f2fe367525dc0d7dc2c85051fdaac73af97c",
        ),
        (
            "910f1a50b7191cf47815b6707dae489847d25f1e45f1b40104a0c38d20eaa846",
            "b746d9c9d131ab2795953f3e2401f2fe367525dc0d7dc2c85051fdaac73af97c",
        ),
    ),
}


# Exact native request/sent/full-fill proof resolves subsecond policy ordering.
# Original fill timestamps, execution guards and every earlier generation remain.
REVIEWED_CAUSAL_QUANTITY_HASHES = {
    "src/engine/scalping/initial_quantity_policy.py": "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": "5311174d8495ed9560ff6421027700ff7acf89bd43315ba1c63484bb50bfb3e9",
    "src/engine/automation/main_trailing_source_assembler.py": "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
    "src/engine/lifecycle/main_stop_research_cost.py": "a6ad1dc12223a07b33a3d6b3748b33c120dd531a3c5e7baa22fa902385966054",
    "src/engine/lifecycle/holding_window_generation.py": "925904f2505a15a0b179aeca4a8ecb6badac76130c50fe6d29973eb76b8cf2d1",
    "src/engine/holding_exit_observation_report.py": "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
}
REVIEWED_CAUSAL_QUANTITY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_policy.py",
        "selector_sha256": REVIEWED_CAUSAL_QUANTITY_HASHES[
            "src/engine/scalping/initial_quantity_policy.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_CAUSAL_QUANTITY_HASHES},
        "contract_extensions": {
            origin: {
                path: REVIEWED_CAUSAL_QUANTITY_HASHES.get(path, sha)
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRESERVED_SNAPSHOT_DEPENDENCY_VARIANTS.items()
}
REVIEWED_CAUSAL_QUANTITY_PAIRS = {
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "dbd20ac53e9ebb59dbb6b465a214558eb838b8f012636eda73cb02f65c5304c6",
            "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
        ),
        (
            "a6e57b600500e10b20ebf1ca2ac097a2433fbd5f8696e28f8ec1ef97601b627a",
            "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
        ),
        (
            "2710cc18ab0289b1318cb53af8cd45bebcbd9ad9354d82ba2fa180ed3eb9fd90",
            "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
        ),
    ),
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": (
        (
            "779a0d679ec1b7e1704ad368d8896d166a545e358438fda8e2f51ef0dde800fa",
            "5311174d8495ed9560ff6421027700ff7acf89bd43315ba1c63484bb50bfb3e9",
        ),
        (
            "798f15352dc47787bc3d3bd571f45fbed2911cdaafbdcab5487998745442bbe4",
            "5311174d8495ed9560ff6421027700ff7acf89bd43315ba1c63484bb50bfb3e9",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
        ),
        (
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
        ),
    ),
    "src/engine/lifecycle/main_stop_research_cost.py": (
        (
            "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "a6ad1dc12223a07b33a3d6b3748b33c120dd531a3c5e7baa22fa902385966054",
        ),
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        (
            "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "925904f2505a15a0b179aeca4a8ecb6badac76130c50fe6d29973eb76b8cf2d1",
        ),
        (
            "b31337f09b51d7d1ad1b06b24f92eda3bc2b19b0f160166e25d603708940926c",
            "925904f2505a15a0b179aeca4a8ecb6badac76130c50fe6d29973eb76b8cf2d1",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
        ),
        (
            "108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f",
            "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
        ),
    ),
}


# Preserve position quantity separately from the first acknowledged BUY fill.
REVIEWED_PARTIAL_CLOCK_HASHES = {
    "src/engine/scalping/initial_quantity_policy.py": "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
}
REVIEWED_PARTIAL_CLOCK_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_policy.py",
        "selector_sha256": REVIEWED_PARTIAL_CLOCK_HASHES[
            "src/engine/scalping/initial_quantity_policy.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_PARTIAL_CLOCK_HASHES},
        "contract_extensions": {
            origin: {
                path: REVIEWED_PARTIAL_CLOCK_HASHES.get(path, sha)
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CAUSAL_QUANTITY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_PARTIAL_CLOCK_PAIRS = {
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "dbd20ac53e9ebb59dbb6b465a214558eb838b8f012636eda73cb02f65c5304c6",
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
        ),
        (
            "2710cc18ab0289b1318cb53af8cd45bebcbd9ad9354d82ba2fa180ed3eb9fd90",
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
        ),
        (
            "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
        ),
    ),
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": (
        (
            "779a0d679ec1b7e1704ad368d8896d166a545e358438fda8e2f51ef0dde800fa",
            "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
        ),
        (
            "798f15352dc47787bc3d3bd571f45fbed2911cdaafbdcab5487998745442bbe4",
            "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
        ),
        (
            "5311174d8495ed9560ff6421027700ff7acf89bd43315ba1c63484bb50bfb3e9",
            "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
        ),
    ),
}


# Exact reviewed writer/index/consumer, source sampler and immutable submit view.
# Every dependency is one complete Git-bound generation; no per-file alternatives.
REVIEWED_TRAILING_REUSE_HASHES = {
    "src/engine/../utils/pipeline_event_logger.py": "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
    "src/engine/ai/holding_exit_vote.py": "16960922bda613851599ad47870ac7c3820f04cc94440e395d9d29b0169988ce",
    "src/engine/ai/holding_vote_replay_source.py": "52a1e362c6ac8ad551428a840f96e100a5bb7ee679555ebe2933dfa2f5b95559",
    "src/engine/automation/main_trailing_all_scope_research.py": "a4433ef1560280d8cfc198bb95357414f01373ba55757c4197315a2b3d0f2dab",
    "src/engine/automation/main_trailing_completed_store.py": "6cd944f303ba9851761ca0166bd757dd1f3210f0abeda3468510979142fd25da",
    "src/engine/automation/main_trailing_partitioned_research.py": "142ef75169de9fc68664a7e556f0a4cbb2e79918b450a5c7a8156bc50586dd4f",
    "src/engine/automation/main_trailing_research_handoff.py": "4c2d49eb51c2087bbf0853273275bac2bf7d85ac3cba40e0b46f1e770a0009fe",
    "src/engine/automation/main_trailing_source_assembler.py": "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
    "src/engine/automation/main_trailing_source_reuse.py": "c190554546468617b2963e2ba013473e992f4d4ad638a5f4aee2f71027bc58ef",
    "src/engine/automation/main_trailing_source_store.py": "19feaff3f7870392506c01e2712c195fa7f1f81c71b352e82fa055bd905d15c6",
    "src/engine/compress_db_backfilled_files.py": "3d1f34d4f8128e6e9b0b1aa9a3e0095bef1394314a731bd8a9c1eec8ea816f7c",
    "src/engine/infrastructure/validation_digest_session.py": "655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1",
    "src/engine/kiwoom_sniper_v2.py": "b7cec7cbec7082c9c98a8861638485432ee20346ce687dbd06d82196551548bb",
    "src/engine/kiwoom_websocket.py": "5016a58492f59a0728d9bbf979d76cc59a10de4681e92a5fcac21bf6c1cffde2",
    "src/engine/lifecycle/holding_research_cost.py": "3979cab1f18b2bd32933985d9e7c86068aa1284dc76dc278bbc171c0c4704911",
    "src/engine/lifecycle/holding_window_generation.py": "ee13b6cc48e1842c1710f6971703712e984ca636fe6f2378f068fb8fd5121092",
    "src/engine/lifecycle/research_json_stream.py": "f886a7510dbabda0db35cf264a9ea61aa7e50ddeb0a5cac407a2b479d7c4c944",
    "src/engine/lifecycle/snapshot_archive.py": "6046cf2f9ec83e74ee8f70985ecbd8a4f22c51bc2c703d72f5183f7b73a47b67",
    "src/engine/log_archive_service.py": "f084d07f81e84a2bc868ae39277af2800fa246475d0c11c734687c844d393ff2",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "a5e4d0f76287b6a1fa6a454e0cf11b66f67050ba359cf1797078f2dd1340945f",
    "src/engine/scalping/ai_decision_trace.py": "ea62bfe70f124e71a59b74cf0b885326217ceb019b00da9f8af45c37105ca17e",
    "src/engine/scalping/holding_vote_experiment.py": "79c76fda32ff00a5e2518109906cbcb23305ba15523e74e4f92876424027fdce",
    "src/engine/scalping/pre_submit_delay_observation.py": "c4d8765a72a398b045b924d96367f5b3a0876711265134515dd4bd4fcb4199f1",
    "src/engine/scalping/reversal_evaluation_context.py": "351efbbfae4c3a0a2f91d3c2edb9166d961d65dc44c680375f238a21b3045dcf",
    "src/engine/sniper_state_handlers.py": "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
    "src/utils/pipeline_event_logger.py": "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
}
REVIEWED_TRAILING_REUSE_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_TRAILING_REUSE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_reuse.py",
        "selector_sha256": REVIEWED_TRAILING_REUSE_HASHES[
            "src/engine/automation/main_trailing_source_reuse.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_TRAILING_REUSE_HASHES},
        "contract_extensions": {
            origin: {
                **{
                    path: REVIEWED_TRAILING_REUSE_HASHES.get(path, sha)
                    for path, sha in paths.items()
                },
                "src/engine/automation/main_trailing_source_reuse.py": REVIEWED_TRAILING_REUSE_HASHES[
                    "src/engine/automation/main_trailing_source_reuse.py"
                ],
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PARTIAL_CLOCK_DEPENDENCY_VARIANTS.items()
}
REVIEWED_TRAILING_REUSE_PAIRS = {
    "src/engine/../utils/pipeline_event_logger.py": (
        (
            "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
            "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
        ),
    ),
    "src/engine/ai/holding_exit_vote.py": (
        (
            "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "16960922bda613851599ad47870ac7c3820f04cc94440e395d9d29b0169988ce",
        ),
    ),
    "src/engine/ai/holding_vote_replay_source.py": (
        (
            "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "52a1e362c6ac8ad551428a840f96e100a5bb7ee679555ebe2933dfa2f5b95559",
        ),
        (
            "6aa1db742f4f2354c17ed9bd24cfb1bcfaace5e0130a8d0dceef84343ea6a428",
            "52a1e362c6ac8ad551428a840f96e100a5bb7ee679555ebe2933dfa2f5b95559",
        ),
    ),
    "src/engine/automation/main_trailing_all_scope_research.py": (
        (
            "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "a4433ef1560280d8cfc198bb95357414f01373ba55757c4197315a2b3d0f2dab",
        ),
        (
            "f704dcc16a4bb8434cb255168074a493a215feaac3b1c30372053c11c6babdcc",
            "a4433ef1560280d8cfc198bb95357414f01373ba55757c4197315a2b3d0f2dab",
        ),
    ),
    "src/engine/automation/main_trailing_completed_store.py": (),
    "src/engine/automation/main_trailing_partitioned_research.py": (
        (
            "093f392a0ef7afc060515b5173ca62270846fb886fcb48bec03a74cabf441a81",
            "142ef75169de9fc68664a7e556f0a4cbb2e79918b450a5c7a8156bc50586dd4f",
        ),
        (
            "90432e60f32bbc8dbc489655ea3f25a97511542f39c1fbb5f655e542495f9208",
            "142ef75169de9fc68664a7e556f0a4cbb2e79918b450a5c7a8156bc50586dd4f",
        ),
    ),
    "src/engine/automation/main_trailing_research_handoff.py": (
        (
            "23b05aac5bbf6bf20d4463ccdc4f9ffc290c759cfab269540d1afefbbea0a117",
            "4c2d49eb51c2087bbf0853273275bac2bf7d85ac3cba40e0b46f1e770a0009fe",
        ),
        (
            "7220a496df445299ce758f8d79eee0205fa51e1fdacc9440503f1854c9fda677",
            "4c2d49eb51c2087bbf0853273275bac2bf7d85ac3cba40e0b46f1e770a0009fe",
        ),
        (
            "f0e4cbe8ba222e361f9726fea04408dfe9b2dc2b40ac7db23106f4d543e2eda6",
            "4c2d49eb51c2087bbf0853273275bac2bf7d85ac3cba40e0b46f1e770a0009fe",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
        ),
        (
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
        ),
    ),
    "src/engine/automation/main_trailing_source_reuse.py": (),
    "src/engine/automation/main_trailing_source_store.py": (),
    "src/engine/compress_db_backfilled_files.py": (
        (
            "16a3fdffeeacd25a0a1a61c057da8ad9a5e5fe86f9faa823ff991108b960e7f2",
            "3d1f34d4f8128e6e9b0b1aa9a3e0095bef1394314a731bd8a9c1eec8ea816f7c",
        ),
    ),
    "src/engine/infrastructure/validation_digest_session.py": (
        (
            "bfdcbf093652783bea5d2c72bf10e1dc910b5d3cdca9c702279ee75a15ec77b9",
            "655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1",
        ),
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
            "b7cec7cbec7082c9c98a8861638485432ee20346ce687dbd06d82196551548bb",
        ),
        (
            "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "b7cec7cbec7082c9c98a8861638485432ee20346ce687dbd06d82196551548bb",
        ),
    ),
    "src/engine/kiwoom_websocket.py": (
        (
            "63293b9abbd511ade33dccca9598eba3e0e32e0eefa06c33a2ba5c411c67a130",
            "5016a58492f59a0728d9bbf979d76cc59a10de4681e92a5fcac21bf6c1cffde2",
        ),
        (
            "b760d5aa69b20f31060a00a5dc81670d29f1c7760c19a775499609d90e867363",
            "5016a58492f59a0728d9bbf979d76cc59a10de4681e92a5fcac21bf6c1cffde2",
        ),
    ),
    "src/engine/lifecycle/holding_research_cost.py": (
        (
            "12e76859310d617dc7cdb2c0f758f935f8d7c6619c76cdf02f92aefa92a0627a",
            "3979cab1f18b2bd32933985d9e7c86068aa1284dc76dc278bbc171c0c4704911",
        ),
        (
            "ef309953ea56261e38e1238ed2c61a4bcbd5e77f61677ee01fa30433bc077dd3",
            "3979cab1f18b2bd32933985d9e7c86068aa1284dc76dc278bbc171c0c4704911",
        ),
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        (
            "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "ee13b6cc48e1842c1710f6971703712e984ca636fe6f2378f068fb8fd5121092",
        ),
        (
            "925904f2505a15a0b179aeca4a8ecb6badac76130c50fe6d29973eb76b8cf2d1",
            "ee13b6cc48e1842c1710f6971703712e984ca636fe6f2378f068fb8fd5121092",
        ),
    ),
    "src/engine/lifecycle/research_json_stream.py": (
        (
            "fbca117c876a62659255914b5771772cdcbdb3e58a904e566a402959379f3df0",
            "f886a7510dbabda0db35cf264a9ea61aa7e50ddeb0a5cac407a2b479d7c4c944",
        ),
        (
            "ff07214148fce486e68e1db048469dd7a657553894cb3472960fea59c7ee09dc",
            "f886a7510dbabda0db35cf264a9ea61aa7e50ddeb0a5cac407a2b479d7c4c944",
        ),
    ),
    "src/engine/lifecycle/snapshot_archive.py": (
        (
            "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "6046cf2f9ec83e74ee8f70985ecbd8a4f22c51bc2c703d72f5183f7b73a47b67",
        ),
        (
            "f2a8eb56daf861d1ffb10bae945a9753e77ed5e0ed2c935cc1382b17c18f79c3",
            "6046cf2f9ec83e74ee8f70985ecbd8a4f22c51bc2c703d72f5183f7b73a47b67",
        ),
    ),
    "src/engine/log_archive_service.py": (
        (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "f084d07f81e84a2bc868ae39277af2800fa246475d0c11c734687c844d393ff2",
        ),
        (
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "f084d07f81e84a2bc868ae39277af2800fa246475d0c11c734687c844d393ff2",
        ),
        (
            "fd5cb478cb40b70ee2dd7fdcc5bc1ef18afa7cef1659e6be9eaaabab1084eca4",
            "f084d07f81e84a2bc868ae39277af2800fa246475d0c11c734687c844d393ff2",
        ),
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
            "a5e4d0f76287b6a1fa6a454e0cf11b66f67050ba359cf1797078f2dd1340945f",
        ),
        (
            "5a3861b05149893db38be6cc7c56a0f4cbf93911e0a209d31edf222b3b3943bf",
            "a5e4d0f76287b6a1fa6a454e0cf11b66f67050ba359cf1797078f2dd1340945f",
        ),
        (
            "60ab1c4f07c71928f33523b49e8a4143fb1d4e01583dabf3beda6290758f4e23",
            "a5e4d0f76287b6a1fa6a454e0cf11b66f67050ba359cf1797078f2dd1340945f",
        ),
    ),
    "src/engine/scalping/ai_decision_trace.py": (
        (
            "39ac65845ac18e6bbc9313e29175a31c0138254b8e323838552d361b08f5130c",
            "ea62bfe70f124e71a59b74cf0b885326217ceb019b00da9f8af45c37105ca17e",
        ),
        (
            "4ca36bfcf257cb8dc39738cff5e71b3da32f458e8e9febabc31f4acef1277bc4",
            "ea62bfe70f124e71a59b74cf0b885326217ceb019b00da9f8af45c37105ca17e",
        ),
    ),
    "src/engine/scalping/holding_vote_experiment.py": (
        (
            "0086eb212c3187c5b89e8680adacb28d96aad56d7f45e96788839f0824bdeaae",
            "79c76fda32ff00a5e2518109906cbcb23305ba15523e74e4f92876424027fdce",
        ),
        (
            "93633c0a9cea34837dd3bea2297dcb5305eb23651133e67d3788bc4fa2ad1007",
            "79c76fda32ff00a5e2518109906cbcb23305ba15523e74e4f92876424027fdce",
        ),
    ),
    "src/engine/scalping/pre_submit_delay_observation.py": (
        (
            "5128d73f6d45777c5671fd26a774dae5d4839203035607b5bb53a9bcc860e964",
            "c4d8765a72a398b045b924d96367f5b3a0876711265134515dd4bd4fcb4199f1",
        ),
        (
            "aff325d1d6f49496bb4548295cae57431980f7d28efb43156cffc61b44bfafa9",
            "c4d8765a72a398b045b924d96367f5b3a0876711265134515dd4bd4fcb4199f1",
        ),
    ),
    "src/engine/scalping/reversal_evaluation_context.py": (
        (
            "b5753ae20f5d8385f7ccf942131d591d5b4feb2dd1f7c278903c74f504201d72",
            "351efbbfae4c3a0a2f91d3c2edb9166d961d65dc44c680375f238a21b3045dcf",
        ),
        (
            "c3d732d937787fd881ebf8f47437f4164ba01582611bc332fe23fd784ed3fc43",
            "351efbbfae4c3a0a2f91d3c2edb9166d961d65dc44c680375f238a21b3045dcf",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
        ),
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
        ),
    ),
    "src/utils/pipeline_event_logger.py": (
        (
            "58dd5b4ba0ce91a248cebf8a608974caba13080226e139e779f512500b4b4c5f",
            "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
        ),
    ),
}

# Full native retry after a startup selector publication race. Preserve the
# preceding exact generation for verifying an already-running predecessor.
REVIEWED_STARTUP_RETRY_HASHES = {
    "src/engine/scalping/reversal_evaluation_context.py": "fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654"
}
REVIEWED_STARTUP_RETRY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/reversal_evaluation_context.py",
        "selector_sha256": REVIEWED_STARTUP_RETRY_HASHES[
            "src/engine/scalping/reversal_evaluation_context.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_STARTUP_RETRY_HASHES},
    }
    for key, value in REVIEWED_TRAILING_REUSE_DEPENDENCY_VARIANTS.items()
}
REVIEWED_STARTUP_RETRY_PAIRS = {
    "src/engine/scalping/reversal_evaluation_context.py": (
        (
            "351efbbfae4c3a0a2f91d3c2edb9166d961d65dc44c680375f238a21b3045dcf",
            "fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654",
        ),
    )
}

# Report-only history counters survive a zero-duration continuous segment.
# Preserve the preceding startup and index generations for native predecessor checks.
REVIEWED_HISTORY_SEGMENT_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18"
}
REVIEWED_HISTORY_SEGMENT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_HISTORY_SEGMENT_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_HISTORY_SEGMENT_HASHES},
        "contract_extensions": {
            origin: {
                path: REVIEWED_HISTORY_SEGMENT_HASHES.get(path, sha)
                for path, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STARTUP_RETRY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_HISTORY_SEGMENT_PAIRS = {
    name: tuple(
        (before, sha) for before, _ in REVIEWED_TRAILING_REUSE_PAIRS.get(name, ())
    )
    for name, sha in REVIEWED_HISTORY_SEGMENT_HASHES.items()
}


# Exact source-only historical exclusion disposition. Keep the prior 94-file
# generation for immutable predecessor validation; bind its additional native
# quantity publisher as part of the complete successor generation.
REVIEWED_QUANTITY_EXCLUSIONS_HASHES = {
    "src/engine/scalping/initial_quantity_monitor_projection.py": "d8e3ed265350afd2214dce5e06c7f3c8006ebc80b8d86435b705888edcff221f"
}
REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_monitor_projection.py",
        "selector_sha256": "d8e3ed265350afd2214dce5e06c7f3c8006ebc80b8d86435b705888edcff221f",
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_QUANTITY_EXCLUSIONS_HASHES,
        },
    }
    for key, value in REVIEWED_HISTORY_SEGMENT_DEPENDENCY_VARIANTS.items()
}


# Reviewed cleanup 336e0a79d: import relocation, startup summary and unreachable
# overnight removal. Preserve the full predecessor closure and bind the new
# direct owners as well. Historical variants remain independently verifiable.
REVIEWED_CLEANUP_HASHES = {
    "src/engine/scalping/reversal_auxiliary_next_session.py": "eacdffe20114a954e7111026b02ff9c8bdaeb03383e8effa2f78a45a5566e02f",
    "src/engine/infrastructure/startup_validation_code_context.py": "8dea691d28da5296669cf45504ce74eccd917240aae2579371cca1a88ef28261",
    "src/engine/ai_engine_openai.py": "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
    "src/engine/kiwoom_sniper_v2.py": "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
    "src/engine/sniper_condition_handlers.py": "c405cb33d19f9d9f857efd122f9175e1c0cc8f6614c53b574ab6aaa466bd7b6b",
    "src/engine/sniper_overnight_gatekeeper.py": "de9fac6b1dc43b7bc42db22a2e4fa699c2c17d1c12fff8da4738704c8fbc2292",
    "src/engine/sniper_state_handlers.py": "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
}
REVIEWED_CLEANUP_PAIRS = {
    "src/engine/ai_engine_openai.py": (
        (
            "b5c8b6e262678c5354ced1fd30ae4d20b974e50fbb01187b4ab2a9df61a010d7",
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
        ),
        (
            "194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584",
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
        ),
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
        ),
        (
            "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
        ),
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
        ),
    ),
}
REVIEWED_CLEANUP_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_CLEANUP_HASHES[trigger]): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_CLEANUP_HASHES},
        "contract_extensions": {
            key: {
                name: REVIEWED_CLEANUP_HASHES.get(name, sha)
                for name, sha in paths.items()
            }
            for key, paths in value["contract_extensions"].items()
        },
    }
    for (
        trigger,
        sha,
    ), value in REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS.items()
    if trigger == "src/engine/sniper_state_handlers.py"
    and sha == "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38"
}

# Reviewed AVG_DOWN input activation and Main SOR integration. Preserve the
# original policy digests and the predecessor dependency closure. The two added
# holding inputs are exact reviewed extensions, never fallback policy authority.
REVIEWED_AVG_DOWN_INPUT_HASHES = {
    "src/engine/ai/holding_exit_vote.py": "69f1a9a63a79d38e3a9986156800d883fab98b86a78ceb12a603040227cb2c81",
    "src/engine/automation/main_startup_validation.py": "190855a642ca713fe53257eae2268eeb5786990c474f2b63904ace41b66c9661",
    "src/engine/automation/main_trailing_source_store.py": "f052d476022f65f0b4742f7cc3c59cb647885a9224f5ba6791802616e546a9a7",
    "src/engine/automation/prepared_policy_code_handoff.py": "9ef09608077aa02c25bdd40d8bc33344bf0e10dbde18cae0fdcf434b0c6efaf8",
    "src/engine/infrastructure/startup_validation_code_context.py": "4d20ceaccb28ac3ab7e3521ded1603abb3587edb8b3ad828a5ae505d02da31c3",
    "src/engine/scalping/ai_market_snapshot.py": "e4a4ae29cca5d452b1bcfa4c54684e8d4bc8702224f6034231a4a4a12235881d",
    "src/engine/scalping/avg_down_replay_capture.py": "dbb163f2f23c678f4a2343e8501b405166bd18f30b94b0de64f98e76c0a2645a",
    "src/engine/scalping/holding_decision_context.py": "783f95ab9cd3ef2813151949cdf6aa2c2ab6ed3a1443ae60d6600d21dcd52898",
    "src/engine/scalping/holding_path_vote_policy.py": "f66fa049d9f15c51169015bd44c0464d4de540726d164d0c610e8fb9c51d8c85",
    "src/engine/scalping/holding_vote_experiment.py": "23d8ec40b586f6db69027c8fd5b4e949a3d0ee1ca102f45a064b0c874c517843",
    "src/engine/scalping/strategy_owner_replay.py": "7ea25642e08cb77f95840373dc8fb16fadcee37bb0aa2c03a9234212ac12b878",
    "src/engine/sniper_state_handlers.py": "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
    "src/trading/market/session_contract.py": "dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c",
    "src/engine/automation/main_stop_postclose.py": "d78ae70b6b125355bfd3d2c4ee7e511a4171b933219efedb80900afd6c3781c9",
}
REVIEWED_AVG_DOWN_INPUT_SOURCES = {
    "src/engine/ai/holding_exit_vote.py": (
        (
            "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "69f1a9a63a79d38e3a9986156800d883fab98b86a78ceb12a603040227cb2c81",
        ),
    ),
    "src/engine/scalping/ai_market_snapshot.py": (
        (
            "77f151a72094486b9b84e9a56fcba92aac6760648b58124a06250bf58dd6d650",
            "e4a4ae29cca5d452b1bcfa4c54684e8d4bc8702224f6034231a4a4a12235881d",
        ),
    ),
    "src/engine/scalping/avg_down_replay_capture.py": (
        (
            "67ff5887f46f24972ad5adb1d8051947a974697c38b2a16db5ed7635a34d3214",
            "dbb163f2f23c678f4a2343e8501b405166bd18f30b94b0de64f98e76c0a2645a",
        ),
    ),
    "src/engine/scalping/holding_decision_context.py": (
        (
            "e3590eebd7d40c295730f3579ec87ea57737d7ed5022ec32aea357c38bf57c44",
            "783f95ab9cd3ef2813151949cdf6aa2c2ab6ed3a1443ae60d6600d21dcd52898",
        ),
    ),
    "src/engine/scalping/holding_path_vote_policy.py": (
        (
            "bbac620a904ee015a9245a0d032dcbf3f615984b2c0c5e7c13dc904092dcc1aa",
            "f66fa049d9f15c51169015bd44c0464d4de540726d164d0c610e8fb9c51d8c85",
        ),
    ),
    "src/engine/scalping/holding_vote_experiment.py": (
        (
            "0086eb212c3187c5b89e8680adacb28d96aad56d7f45e96788839f0824bdeaae",
            "23d8ec40b586f6db69027c8fd5b4e949a3d0ee1ca102f45a064b0c874c517843",
        ),
        (
            "93633c0a9cea34837dd3bea2297dcb5305eb23651133e67d3788bc4fa2ad1007",
            "23d8ec40b586f6db69027c8fd5b4e949a3d0ee1ca102f45a064b0c874c517843",
        ),
    ),
    "src/engine/scalping/strategy_owner_replay.py": (
        (
            "bd080261d91243ab9f2ef2a69eeef07830edb3a9178be94ecd069912cc0343c9",
            "7ea25642e08cb77f95840373dc8fb16fadcee37bb0aa2c03a9234212ac12b878",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
        ),
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
        ),
    ),
    "src/trading/market/session_contract.py": (
        (
            "3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0",
            "dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c",
        ),
    ),
    "src/engine/automation/main_stop_postclose.py": (
        (
            "531f1498332196f0e54d17b76ed8d30295009a5e5ee9363ad9397613f0740ad2",
            "d78ae70b6b125355bfd3d2c4ee7e511a4171b933219efedb80900afd6c3781c9",
        ),
        (
            "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "d78ae70b6b125355bfd3d2c4ee7e511a4171b933219efedb80900afd6c3781c9",
        ),
    ),
}
REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_AVG_DOWN_INPUT_HASHES[trigger]): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_AVG_DOWN_INPUT_HASHES},
        "contract_extensions": {
            key: {
                **{
                    name: REVIEWED_AVG_DOWN_INPUT_HASHES.get(
                        os.path.normpath(name), sha
                    )
                    for name, sha in paths.items()
                },
                **(
                    {
                        name: REVIEWED_AVG_DOWN_INPUT_HASHES[name]
                        for name in (
                            "src/engine/scalping/holding_decision_context.py",
                            "src/engine/scalping/ai_market_snapshot.py",
                        )
                    }
                    if key[1]
                    == "6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112"
                    else {}
                ),
            }
            for key, paths in value["contract_extensions"].items()
        }
        | {
            (
                "8940ea4ad0d3b64d30f67f986a75715ee24c1d95",
                "c34bc30c734591c1c97c0ed770744c273e206de14dbd0b02382ef71a88265693",
            ): {
                name: REVIEWED_AVG_DOWN_INPUT_HASHES[name]
                for name in (
                    "src/engine/scalping/holding_decision_context.py",
                    "src/engine/scalping/ai_market_snapshot.py",
                )
            },
        },
    }
    for (trigger, sha), value in REVIEWED_CLEANUP_DEPENDENCY_VARIANTS.items()
}


# Reviewed completion-source contract and validation-before-publication repair.
# Select one complete dependency generation; every unrelated hash stays pinned.
REVIEWED_COMPLETION_CENSUS_HASHES = {
    "src/engine/log_archive_service.py": "3698af57301e2db4ba868bb75df878fc47441e16e4e831dfe4c90b31111a6cab",
    "src/engine/sniper_trade_review_report.py": "a7a7bda98e911626a62ffff472bcf263296e2bacac841f91341823298cb7a8eb",
}
REVIEWED_COMPLETION_CENSUS_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/log_archive_service.py",
        "selector_sha256": REVIEWED_COMPLETION_CENSUS_HASHES[
            "src/engine/log_archive_service.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_COMPLETION_CENSUS_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_COMPLETION_CENSUS_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS.items()
}
REVIEWED_COMPLETION_CENSUS_PAIRS = {
    "src/engine/log_archive_service.py": tuple(
        (origin, REVIEWED_COMPLETION_CENSUS_HASHES["src/engine/log_archive_service.py"])
        for origin in (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
        )
    ),
}

# Exact full-consumer successor; preserve the already-issued producer-only
# generation for native prepared-code ancestry verification.
REVIEWED_COMPLETION_CONSUMER_HASHES = {
    "src/engine/log_archive_service.py": "3698af57301e2db4ba868bb75df878fc47441e16e4e831dfe4c90b31111a6cab",
    "src/engine/sniper_trade_review_report.py": "de4dd6cfc135d5d6c53f757151f32753f13ff780caca285886dba2dc285890d8",
    "src/engine/strategy_position_performance_report.py": "af859017afe90f9865ec6ead86fd39a0255c36d3df23047e43c63b34e44a2c7a",
    "src/engine/holding_exit_observation_report.py": "bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3",
    "src/engine/lifecycle/main_stop_research_cost.py": "998f989d19979464bde492b14bd651d1bb7ff26abdfd6c5eaa454c2ebf994694",
    "src/engine/scalping/initial_quantity_source_cache.py": "aeabf97ec5bd69578e6e66fc4b2eb14945fbe7a34e59658e12fe1b9cf9732ecd",
}
REVIEWED_COMPLETION_CONSUMER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_trade_review_report.py",
        "selector_sha256": REVIEWED_COMPLETION_CONSUMER_HASHES[
            "src/engine/sniper_trade_review_report.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_COMPLETION_CONSUMER_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_COMPLETION_CONSUMER_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS.items()
}
REVIEWED_COMPLETION_CONSUMER_PAIRS = {
    "src/engine/log_archive_service.py": (
        (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "3698af57301e2db4ba868bb75df878fc47441e16e4e831dfe4c90b31111a6cab",
        ),
        (
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "3698af57301e2db4ba868bb75df878fc47441e16e4e831dfe4c90b31111a6cab",
        ),
    ),
    "src/engine/sniper_trade_review_report.py": (
        (
            "d3e838423aeeaba629be4902b2aac533caceef3145ad747bdc78ff2900c230d8",
            "de4dd6cfc135d5d6c53f757151f32753f13ff780caca285886dba2dc285890d8",
        ),
        (
            "8d07674031ac0ca0a08437c61490cd896d8810c30f57810ad53febb8cac0b57c",
            "de4dd6cfc135d5d6c53f757151f32753f13ff780caca285886dba2dc285890d8",
        ),
    ),
    "src/engine/strategy_position_performance_report.py": (
        (
            "4b7e718a1f8a2e9838095b618067729a94901cc41423e274a9ef07ee464d8bd4",
            "af859017afe90f9865ec6ead86fd39a0255c36d3df23047e43c63b34e44a2c7a",
        ),
        (
            "00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4",
            "af859017afe90f9865ec6ead86fd39a0255c36d3df23047e43c63b34e44a2c7a",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3",
        ),
    ),
    "src/engine/lifecycle/main_stop_research_cost.py": (
        (
            "0b76f9039325382ce8aa685e069b8783c333021ac1b9dc82f24f452b2b2768c7",
            "998f989d19979464bde492b14bd651d1bb7ff26abdfd6c5eaa454c2ebf994694",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "4dfa3c22640ee0f94fdac37633e7adbb0b6be4ecdaa14efe25ca04d840c799a7",
            "aeabf97ec5bd69578e6e66fc4b2eb14945fbe7a34e59658e12fe1b9cf9732ecd",
        ),
        (
            "910f1a50b7191cf47815b6707dae489847d25f1e45f1b40104a0c38d20eaa846",
            "aeabf97ec5bd69578e6e66fc4b2eb14945fbe7a34e59658e12fe1b9cf9732ecd",
        ),
    ),
}


# Prefix reuse now includes the exact producer code generation. The prior
# full-consumer generation remains native evidence for its issued receipts.
REVIEWED_PREFIX_PRODUCER_HASHES = {
    "src/engine/log_archive_service.py": "48243d6d40dc68e5d8023208b9c8c38be6d92c5326f8702a9a3d2060e1efcebb"
}
REVIEWED_PREFIX_PRODUCER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/log_archive_service.py",
        "selector_sha256": REVIEWED_PREFIX_PRODUCER_HASHES[
            "src/engine/log_archive_service.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_PREFIX_PRODUCER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREFIX_PRODUCER_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COMPLETION_CONSUMER_DEPENDENCY_VARIANTS.items()
}
REVIEWED_PREFIX_PRODUCER_PAIRS = {
    "src/engine/log_archive_service.py": tuple(
        (origin, REVIEWED_PREFIX_PRODUCER_HASHES["src/engine/log_archive_service.py"])
        for origin in (
            "a7b6b2fc09ba260ce2e9da11ed9ff9a9f1bf51085eb79c2184a27796b2a83280",
            "f0edcf09c4327ba2fc17e432e1ffe01c77185ee69cb0b66109d73fac408c02f3",
            "3698af57301e2db4ba868bb75df878fc47441e16e4e831dfe4c90b31111a6cab",
        )
    ),
}

# Original native fills and current late costs have independent generations.
# Exact reviewed report/research bytes; every issued predecessor stays intact.
REVIEWED_LATE_COST_HASHES = {
    "src/engine/automation/main_trailing_all_scope_research.py": "1385571ec3fea2b9ff5815f11d76c6132fd26a15633d8809fbb36c9c28781061",
    "src/engine/automation/main_trailing_partitioned_research.py": "f94e55e7be8bb9cb2f0b4b03af8ae740ceb07e3e51053bf085358c7b50ab6f28",
    "src/engine/automation/main_trailing_research_handoff.py": "87b07feb6284f09f8abb2c04bfe8ad15064b2aac9dc8975c92c31d394adb2edc",
    "src/engine/automation/main_trailing_source_assembler.py": "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
    "src/engine/automation/scalp_trailing_mechanical_policy_apply.py": "d5a8170e5d9f66ea16dede5b02135f35e508421173af3a22c3a517b9b7f0b6f3",
    "src/engine/holding_exit_observation_report.py": "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
    "src/engine/lifecycle/broker_cost_allocation.py": "e392d3e79ad63fe1502a7921aca590ce93c3134d9d3e4d488d42775dd20cf349",
    "src/engine/lifecycle/holding_window_generation.py": "73276f9a219d8a0406092be145c793616a33ebc7d4cf86383fde932ae45c5973",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
    "src/engine/scalping/initial_quantity_policy.py": "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
    "src/engine/scalping/initial_quantity_source_cache.py": "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
}
REVIEWED_LATE_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_source_cache.py",
        "selector_sha256": REVIEWED_LATE_COST_HASHES[
            "src/engine/scalping/initial_quantity_source_cache.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_LATE_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_LATE_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PREFIX_PRODUCER_DEPENDENCY_VARIANTS.items()
}
REVIEWED_LATE_COST_PAIRS = {
    "src/engine/automation/main_trailing_all_scope_research.py": (
        (
            "f704dcc16a4bb8434cb255168074a493a215feaac3b1c30372053c11c6babdcc",
            "1385571ec3fea2b9ff5815f11d76c6132fd26a15633d8809fbb36c9c28781061",
        ),
        (
            "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "1385571ec3fea2b9ff5815f11d76c6132fd26a15633d8809fbb36c9c28781061",
        ),
        (
            "a4433ef1560280d8cfc198bb95357414f01373ba55757c4197315a2b3d0f2dab",
            "1385571ec3fea2b9ff5815f11d76c6132fd26a15633d8809fbb36c9c28781061",
        ),
    ),
    "src/engine/automation/main_trailing_partitioned_research.py": (
        (
            "90432e60f32bbc8dbc489655ea3f25a97511542f39c1fbb5f655e542495f9208",
            "f94e55e7be8bb9cb2f0b4b03af8ae740ceb07e3e51053bf085358c7b50ab6f28",
        ),
        (
            "093f392a0ef7afc060515b5173ca62270846fb886fcb48bec03a74cabf441a81",
            "f94e55e7be8bb9cb2f0b4b03af8ae740ceb07e3e51053bf085358c7b50ab6f28",
        ),
        (
            "142ef75169de9fc68664a7e556f0a4cbb2e79918b450a5c7a8156bc50586dd4f",
            "f94e55e7be8bb9cb2f0b4b03af8ae740ceb07e3e51053bf085358c7b50ab6f28",
        ),
    ),
    "src/engine/automation/main_trailing_research_handoff.py": (
        (
            "7220a496df445299ce758f8d79eee0205fa51e1fdacc9440503f1854c9fda677",
            "87b07feb6284f09f8abb2c04bfe8ad15064b2aac9dc8975c92c31d394adb2edc",
        ),
        (
            "23b05aac5bbf6bf20d4463ccdc4f9ffc290c759cfab269540d1afefbbea0a117",
            "87b07feb6284f09f8abb2c04bfe8ad15064b2aac9dc8975c92c31d394adb2edc",
        ),
        (
            "4c2d49eb51c2087bbf0853273275bac2bf7d85ac3cba40e0b46f1e770a0009fe",
            "87b07feb6284f09f8abb2c04bfe8ad15064b2aac9dc8975c92c31d394adb2edc",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
        ),
        (
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
        ),
    ),
    "src/engine/automation/scalp_trailing_mechanical_policy_apply.py": (
        (
            "cf3cabe421126d38f5d5969ea3155bd5d0a27a49027484dceb2ab1ce6a02af6e",
            "d5a8170e5d9f66ea16dede5b02135f35e508421173af3a22c3a517b9b7f0b6f3",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
        ),
        (
            "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
            "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
        ),
        (
            "bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3",
            "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
        ),
    ),
    "src/engine/lifecycle/broker_cost_allocation.py": (
        (
            "f2ce924c4239f51e4d267e56c1ffae92978600b400796a935b6d30994e9f7783",
            "e392d3e79ad63fe1502a7921aca590ce93c3134d9d3e4d488d42775dd20cf349",
        ),
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        (
            "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "73276f9a219d8a0406092be145c793616a33ebc7d4cf86383fde932ae45c5973",
        ),
        (
            "ee13b6cc48e1842c1710f6971703712e984ca636fe6f2378f068fb8fd5121092",
            "73276f9a219d8a0406092be145c793616a33ebc7d4cf86383fde932ae45c5973",
        ),
    ),
    "src/engine/scalping/initial_quantity_monitor_projection.py": (
        (
            "128c119d988fb2865e4c4fbbaa7864fc28b037e5b50da0f85703879929345c9d",
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
        ),
        (
            "d8e3ed265350afd2214dce5e06c7f3c8006ebc80b8d86435b705888edcff221f",
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
        ),
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "dbd20ac53e9ebb59dbb6b465a214558eb838b8f012636eda73cb02f65c5304c6",
            "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
        ),
        (
            "2710cc18ab0289b1318cb53af8cd45bebcbd9ad9354d82ba2fa180ed3eb9fd90",
            "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
        ),
        (
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
            "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "4dfa3c22640ee0f94fdac37633e7adbb0b6be4ecdaa14efe25ca04d840c799a7",
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
        ),
        (
            "910f1a50b7191cf47815b6707dae489847d25f1e45f1b40104a0c38d20eaa846",
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
        ),
        (
            "b746d9c9d131ab2795953f3e2401f2fe367525dc0d7dc2c85051fdaac73af97c",
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
        ),
        (
            "aeabf97ec5bd69578e6e66fc4b2eb14945fbe7a34e59658e12fe1b9cf9732ecd",
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
        ),
    ),
}

# Report-only rejection census and invocation-local native source reuse.
# The issued late-cost generation remains an independent historical branch.
REVIEWED_POSTCLOSE_READER_HASHES = {
    "src/engine/automation/entry_cancel_wait_tuning.py": "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
    "src/engine/scalping/entry_split_order_plan.py": "c4a3938c0196d678bdaacc5911dde768d815d7f6d2ed31eabd9e44db87166ed2",
    "src/engine/scalping/initial_quantity_policy.py": "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
    "src/engine/lifecycle/snapshot_archive.py": "9d5ec9e5bfe87461341c440d573f90c2d44a5780b5206d3bd17bdb8d9fc618d8",
    "src/engine/automation/main_trailing_source_store.py": "e50e6e30840c030ad6823e0eebb5a4fa1ea8733518c66a79a4189a6426898266",
    "src/engine/automation/main_trailing_source_assembler.py": "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
}
REVIEWED_POSTCLOSE_READER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/entry_cancel_wait_tuning.py",
        "selector_sha256": REVIEWED_POSTCLOSE_READER_HASHES[
            "src/engine/automation/entry_cancel_wait_tuning.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_POSTCLOSE_READER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_POSTCLOSE_READER_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_LATE_COST_DEPENDENCY_VARIANTS.items()
}
REVIEWED_POSTCLOSE_READER_PAIRS = {
    "src/engine/automation/entry_cancel_wait_tuning.py": (
        (
            "a1f577f964a00ea156fbf29bd5b815bf11ac74172d78f3d025e81ef30c1bf27e",
            "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
        ),
    ),
    "src/engine/scalping/entry_split_order_plan.py": (
        (
            "23df522d2a729c24696e93e3f6d456223da042cec8f60424d99d970638dff838",
            "c4a3938c0196d678bdaacc5911dde768d815d7f6d2ed31eabd9e44db87166ed2",
        ),
        (
            "aa1e130239521229201759708c9ebf1e156a20ba1f88704c3607992043a65617",
            "c4a3938c0196d678bdaacc5911dde768d815d7f6d2ed31eabd9e44db87166ed2",
        ),
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "2710cc18ab0289b1318cb53af8cd45bebcbd9ad9354d82ba2fa180ed3eb9fd90",
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
        ),
        (
            "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
        ),
        (
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
        ),
        (
            "dbd20ac53e9ebb59dbb6b465a214558eb838b8f012636eda73cb02f65c5304c6",
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
        ),
    ),
    "src/engine/lifecycle/snapshot_archive.py": (
        (
            "6046cf2f9ec83e74ee8f70985ecbd8a4f22c51bc2c703d72f5183f7b73a47b67",
            "9d5ec9e5bfe87461341c440d573f90c2d44a5780b5206d3bd17bdb8d9fc618d8",
        ),
        (
            "9b1a0ac18db7fde52f609db45950b9fb631376f401fa565088a9831dd80ad42a",
            "9d5ec9e5bfe87461341c440d573f90c2d44a5780b5206d3bd17bdb8d9fc618d8",
        ),
    ),
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "f052d476022f65f0b4742f7cc3c59cb647885a9224f5ba6791802616e546a9a7",
            "e50e6e30840c030ad6823e0eebb5a4fa1ea8733518c66a79a4189a6426898266",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
        ),
        (
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
        ),
    ),
}

# Honor original archive logical authority without replacing an issued reader generation.
REVIEWED_ARCHIVE_AUTHORITY_HASHES = {
    "src/engine/automation/main_trailing_source_store.py": "5790bc3a11fef051c1e3dfdc1ff6e9c0f603c280509253ebd53c10227bd6998a"
}
REVIEWED_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_store.py",
        "selector_sha256": REVIEWED_ARCHIVE_AUTHORITY_HASHES[
            "src/engine/automation/main_trailing_source_store.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ARCHIVE_AUTHORITY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ARCHIVE_AUTHORITY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_POSTCLOSE_READER_DEPENDENCY_VARIANTS.items()
}
REVIEWED_ARCHIVE_AUTHORITY_PAIRS = {
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "e50e6e30840c030ad6823e0eebb5a4fa1ea8733518c66a79a4189a6426898266",
            "5790bc3a11fef051c1e3dfdc1ff6e9c0f603c280509253ebd53c10227bd6998a",
        ),
        (
            "f052d476022f65f0b4742f7cc3c59cb647885a9224f5ba6791802616e546a9a7",
            "5790bc3a11fef051c1e3dfdc1ff6e9c0f603c280509253ebd53c10227bd6998a",
        ),
    )
}

# Original v1 archive receipts require full CRC enrollment before indexed reuse.
REVIEWED_LEGACY_ARCHIVE_AUTHORITY_HASHES = {
    "src/engine/automation/main_trailing_source_store.py": "fea1b901d47c2ba32cdc7f66f97904738fbdc1affd089da44012bb80fdc39ec7"
}
REVIEWED_LEGACY_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_store.py",
        "selector_sha256": REVIEWED_LEGACY_ARCHIVE_AUTHORITY_HASHES[
            "src/engine/automation/main_trailing_source_store.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_LEGACY_ARCHIVE_AUTHORITY_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_LEGACY_ARCHIVE_AUTHORITY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_LEGACY_ARCHIVE_AUTHORITY_PAIRS = {
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "5790bc3a11fef051c1e3dfdc1ff6e9c0f603c280509253ebd53c10227bd6998a",
            "fea1b901d47c2ba32cdc7f66f97904738fbdc1affd089da44012bb80fdc39ec7",
        ),
        (
            "e50e6e30840c030ad6823e0eebb5a4fa1ea8733518c66a79a4189a6426898266",
            "fea1b901d47c2ba32cdc7f66f97904738fbdc1affd089da44012bb80fdc39ec7",
        ),
        (
            "f052d476022f65f0b4742f7cc3c59cb647885a9224f5ba6791802616e546a9a7",
            "fea1b901d47c2ba32cdc7f66f97904738fbdc1affd089da44012bb80fdc39ec7",
        ),
    )
}

# Shared data mounts preserve the original auxiliary source dependency paths.
# Keep the issued archive generation and select this complete successor only
# through the repaired source-handoff owner.
REVIEWED_AUXILIARY_DATA_ROOT_HASHES = {
    "src/engine/scalping/reversal_auxiliary_source_handoff.py": "36a89f137bd81f4453024241f68a70eec268520a0806e9ce59103bd0ae50b1d3"
}
REVIEWED_AUXILIARY_DATA_ROOT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/reversal_auxiliary_source_handoff.py",
        "selector_sha256": REVIEWED_AUXILIARY_DATA_ROOT_HASHES[
            "src/engine/scalping/reversal_auxiliary_source_handoff.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_AUXILIARY_DATA_ROOT_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_AUXILIARY_DATA_ROOT_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_LEGACY_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_AUXILIARY_DATA_ROOT_PAIRS = {
    "src/engine/scalping/reversal_auxiliary_source_handoff.py": tuple(
        (before, "36a89f137bd81f4453024241f68a70eec268520a0806e9ce59103bd0ae50b1d3")
        for before in (
            "f114eaa85987d72d2361a25e7d5aa2fa41ac5fcf6ad74992c0fe40658e038d82",
            "f5724a19f06ef4417226c801259e00378217b8e6ebd49355cad2d21e4ad15c0f",
        )
    )
}

# Enroll original completed projections once; consumers keep the source budget.
# Preserve each issued full generation and select this exact successor as a unit.
REVIEWED_COMPLETED_OFFLINE_HASHES = {
    "src/engine/automation/main_trailing_completed_store.py": "fc047ceddd40d963659fcba7f36f7d28bdbc74c3dfa799322f163fb4f3683a30",
    "src/engine/automation/main_trailing_source_store.py": "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
    "src/engine/automation/main_trailing_source_assembler.py": "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
    "src/engine/holding_exit_observation_report.py": "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
    "src/engine/lifecycle/research_json_stream.py": "1ea671f8ba5b5397257c2d1da513dee653b05379133073d1412ee4edf7a07a11",
}
REVIEWED_COMPLETED_OFFLINE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_completed_store.py",
        "selector_sha256": REVIEWED_COMPLETED_OFFLINE_HASHES[
            "src/engine/automation/main_trailing_completed_store.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_COMPLETED_OFFLINE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_COMPLETED_OFFLINE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AUXILIARY_DATA_ROOT_DEPENDENCY_VARIANTS.items()
}
REVIEWED_COMPLETED_OFFLINE_PAIRS = {
    "src/engine/automation/main_trailing_completed_store.py": (
        (
            "6cd944f303ba9851761ca0166bd757dd1f3210f0abeda3468510979142fd25da",
            "fc047ceddd40d963659fcba7f36f7d28bdbc74c3dfa799322f163fb4f3683a30",
        ),
    ),
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "19feaff3f7870392506c01e2712c195fa7f1f81c71b352e82fa055bd905d15c6",
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
        ),
        (
            "5790bc3a11fef051c1e3dfdc1ff6e9c0f603c280509253ebd53c10227bd6998a",
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
        ),
        (
            "e50e6e30840c030ad6823e0eebb5a4fa1ea8733518c66a79a4189a6426898266",
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
        ),
        (
            "f052d476022f65f0b4742f7cc3c59cb647885a9224f5ba6791802616e546a9a7",
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
        ),
        (
            "fea1b901d47c2ba32cdc7f66f97904738fbdc1affd089da44012bb80fdc39ec7",
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
        (
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f",
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
        ),
        (
            "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
        ),
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
        ),
        (
            "bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3",
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
        ),
        (
            "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
        ),
    ),
}

# Preserve original manifest-verified empty gzip cohorts in the predecessor.
REVIEWED_COMPLETED_EMPTY_HASHES = {
    "src/engine/automation/main_trailing_completed_store.py": "d8ab6595b4a803abb8d7440bb0a83617fc22faa4f93558c197323320a62e1a1c",
    "src/engine/lifecycle/holding_window_generation.py": "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
}
REVIEWED_COMPLETED_EMPTY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_completed_store.py",
        "selector_sha256": REVIEWED_COMPLETED_EMPTY_HASHES[
            "src/engine/automation/main_trailing_completed_store.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_COMPLETED_EMPTY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_COMPLETED_EMPTY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COMPLETED_OFFLINE_DEPENDENCY_VARIANTS.items()
}
REVIEWED_COMPLETED_EMPTY_PAIRS = {
    "src/engine/automation/main_trailing_completed_store.py": (
        (
            "6cd944f303ba9851761ca0166bd757dd1f3210f0abeda3468510979142fd25da",
            "d8ab6595b4a803abb8d7440bb0a83617fc22faa4f93558c197323320a62e1a1c",
        ),
        (
            "fc047ceddd40d963659fcba7f36f7d28bdbc74c3dfa799322f163fb4f3683a30",
            "d8ab6595b4a803abb8d7440bb0a83617fc22faa4f93558c197323320a62e1a1c",
        ),
    ),
    "src/engine/lifecycle/holding_window_generation.py": (
        (
            "52c641abbec603cd419cda1f42121e461cff7487888888df6294b573a52e62ac",
            "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
        ),
        (
            "73276f9a219d8a0406092be145c793616a33ebc7d4cf86383fde932ae45c5973",
            "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
        ),
        (
            "925904f2505a15a0b179aeca4a8ecb6badac76130c50fe6d29973eb76b8cf2d1",
            "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
        ),
        (
            "b31337f09b51d7d1ad1b06b24f92eda3bc2b19b0f160166e25d603708940926c",
            "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
        ),
        (
            "ee13b6cc48e1842c1710f6971703712e984ca636fe6f2378f068fb8fd5121092",
            "c21d4793499158dcb7a9af25f59e5e49c0cfde49234f77669788746645ac3875",
        ),
    ),
}

# Native empty sidecars retain their own census/identity proof and reader.
REVIEWED_NATIVE_EMPTY_HASHES = {
    "src/engine/automation/main_trailing_completed_store.py": "2fc12700ccf64fa03667a0a859e13dc40515e932cc68da23ed9b3d962bdfdd5a"
}
REVIEWED_NATIVE_EMPTY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_completed_store.py",
        "selector_sha256": REVIEWED_NATIVE_EMPTY_HASHES[
            "src/engine/automation/main_trailing_completed_store.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_NATIVE_EMPTY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_NATIVE_EMPTY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COMPLETED_EMPTY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_NATIVE_EMPTY_PAIRS = {
    "src/engine/automation/main_trailing_completed_store.py": (
        (
            "6cd944f303ba9851761ca0166bd757dd1f3210f0abeda3468510979142fd25da",
            "2fc12700ccf64fa03667a0a859e13dc40515e932cc68da23ed9b3d962bdfdd5a",
        ),
        (
            "d8ab6595b4a803abb8d7440bb0a83617fc22faa4f93558c197323320a62e1a1c",
            "2fc12700ccf64fa03667a0a859e13dc40515e932cc68da23ed9b3d962bdfdd5a",
        ),
        (
            "fc047ceddd40d963659fcba7f36f7d28bdbc74c3dfa799322f163fb4f3683a30",
            "2fc12700ccf64fa03667a0a859e13dc40515e932cc68da23ed9b3d962bdfdd5a",
        ),
    )
}

# Bounded source reads reserve admitted chunks within the existing shared budget.
REVIEWED_ASSEMBLER_BUDGET_HASHES = {
    "src/engine/automation/main_trailing_source_assembler.py": "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
    "src/engine/lifecycle/research_storage.py": "18c0644ea2a6805b9027b2bce4bc7a1b89dbc5e10925d104b38a05a9423b4c35",
}
REVIEWED_ASSEMBLER_BUDGET_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_assembler.py",
        "selector_sha256": REVIEWED_ASSEMBLER_BUDGET_HASHES[
            "src/engine/automation/main_trailing_source_assembler.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ASSEMBLER_BUDGET_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ASSEMBLER_BUDGET_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_NATIVE_EMPTY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_ASSEMBLER_BUDGET_PAIRS = {
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "39449970d0024236ccaaed2eb996b8b1222f9ec804450071c090dd6eb4bd2955",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
        (
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
        ),
    ),
    "src/engine/lifecycle/research_storage.py": (
        (
            "bc936e55d483e9e58995924b139cd13f423ce911e60a50c6b63859855f711f3e",
            "18c0644ea2a6805b9027b2bce4bc7a1b89dbc5e10925d104b38a05a9423b4c35",
        ),
        (
            "fa93d4ac728999184e3d238d9050cb51898b9f62780e80929786385421b719af",
            "18c0644ea2a6805b9027b2bce4bc7a1b89dbc5e10925d104b38a05a9423b4c35",
        ),
    ),
}

# Calendar diagnostics bind physical bytes separately from logical archives.
REVIEWED_CALENDAR_PHYSICAL_HASHES = {
    "src/engine/automation/main_trailing_source_assembler.py": "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b"
}
REVIEWED_CALENDAR_PHYSICAL_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_assembler.py",
        "selector_sha256": REVIEWED_CALENDAR_PHYSICAL_HASHES[
            "src/engine/automation/main_trailing_source_assembler.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_CALENDAR_PHYSICAL_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_CALENDAR_PHYSICAL_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ASSEMBLER_BUDGET_DEPENDENCY_VARIANTS.items()
}
REVIEWED_CALENDAR_PHYSICAL_PAIRS = {
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "242285e71a822a7e77c0d0fcc75dfb3109b0ae7e8c0c861244f982eef6bd55c2",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "39449970d0024236ccaaed2eb996b8b1222f9ec804450071c090dd6eb4bd2955",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "500b678cdebef30499e2f990ef7061b0de3b331348bef62a3c9961aec036b75e",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "552eee99e36db1fd314a6b92e6533201cc3181993bb4c7bba08666c1a165d0bc",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "a44afcfac3661e43038d7848eb4e512a5c6bc74bfbfa2a9024e93941ce3cee0b",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "aee4636b6f5c5bad90a9f79d29c3d8cb8ebf93a0bf6613e377b2a2619781eedd",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "ea7039a171b5a3d07883b0549ba763100900cfdec7cb6c14172e0fb887f6b804",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
        (
            "f61e20d7bfba4b8b743dca601b2ff81255752602b5093d6e4df56d076b5abcf1",
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
        ),
    )
}

# Share one bounded native position across all independent stop consumers.
REVIEWED_STOP_SHARED_POSITION_HASHES = {
    "src/engine/automation/main_stop_postclose.py": "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
    "src/engine/automation/main_stop_source_index.py": "7c91f86956a2e4f5fbab57f05517ce3f50cd7c322dca54bd429e60e3f35ea45b",
}
REVIEWED_STOP_SHARED_POSITION_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_stop_postclose.py",
        "selector_sha256": REVIEWED_STOP_SHARED_POSITION_HASHES[
            "src/engine/automation/main_stop_postclose.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_STOP_SHARED_POSITION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_STOP_SHARED_POSITION_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CALENDAR_PHYSICAL_DEPENDENCY_VARIANTS.items()
}
REVIEWED_STOP_SHARED_POSITION_PAIRS = {
    "src/engine/automation/main_stop_postclose.py": (
        (
            "0a33ccf900e7d512ff03ee62923efa95842ea87caeb2987fbd1b479aa18f8258",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "360573dc170d91617cbaec7f1c8713b769c403b22e52449e11434019360a6224",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "531f1498332196f0e54d17b76ed8d30295009a5e5ee9363ad9397613f0740ad2",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "68628fd7c9758946344c5841b90d8073929665d2b61eba40041c74fabc843255",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "72334470389eed899eed84da5fb3d157bd8ae6078e2d38bfb10b0bc96b79ba6f",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "98cbaef223ee161a0fef7547161ffd07f09741842a8675ac1d3c1b787d689772",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "c3aa703f54661aeae94143fb36afd2d2ac7a4337c1ba346062c21ca2be12a9cc",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "cce1f797bd17f5ddde0aa5eec68cdb285c224e198fea7bb184d03a444ff32c05",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "d78ae70b6b125355bfd3d2c4ee7e511a4171b933219efedb80900afd6c3781c9",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "e9ab07117a0200610e19f4b24ea0000579203628a887e16387b24189b8734a13",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
        (
            "efb6eefeeca91b6a91891dffee06cfff996f47095ef70aa637d9afb0f0613a7d",
            "b170f3537578b817944ad839b93f2eaa23abd577ecb6d41bfefa870e36ba00a7",
        ),
    ),
    "src/engine/automation/main_stop_source_index.py": (
        (
            "791fd757311aa8c0a96b2373165a52a560b026492992e46e9fe386996eb605ff",
            "7c91f86956a2e4f5fbab57f05517ce3f50cd7c322dca54bd429e60e3f35ea45b",
        ),
        (
            "802a8f3878f5d9d2fd299c79a57f9b84db6bf1de52017f0e995958b65145381d",
            "7c91f86956a2e4f5fbab57f05517ce3f50cd7c322dca54bd429e60e3f35ea45b",
        ),
        (
            "89155d656e6c28a6eaa045d206a68897f04d1825fdb339a818053579f049b559",
            "7c91f86956a2e4f5fbab57f05517ce3f50cd7c322dca54bd429e60e3f35ea45b",
        ),
        (
            "ddaab50afeee7a47c4a49565f27dc699532aabf8197e5276eb0d57cf974dfdce",
            "7c91f86956a2e4f5fbab57f05517ce3f50cd7c322dca54bd429e60e3f35ea45b",
        ),
    ),
}

# Consume sorted native references without repositioning the gzip text decoder.
REVIEWED_STOP_FORWARD_STREAM_HASHES = {
    "src/engine/automation/main_stop_source_index.py": "a3f7a3d8c29308845e74015208ad02642df906c199d8ed60edeadc75680a7fde"
}
REVIEWED_STOP_FORWARD_STREAM_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_stop_source_index.py",
        "selector_sha256": REVIEWED_STOP_FORWARD_STREAM_HASHES[
            "src/engine/automation/main_stop_source_index.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_STOP_FORWARD_STREAM_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_STOP_FORWARD_STREAM_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STOP_SHARED_POSITION_DEPENDENCY_VARIANTS.items()
}
REVIEWED_STOP_FORWARD_STREAM_PAIRS = {
    name: tuple(
        (before, after)
        for before in sorted(
            {pair[0] for pair in REVIEWED_STOP_SHARED_POSITION_PAIRS[name]}
            | {REVIEWED_STOP_SHARED_POSITION_HASHES[name]}
        )
    )
    for name, after in REVIEWED_STOP_FORWARD_STREAM_HASHES.items()
}

# The stop consumer validates each indexed vote with its native generation owner.
REVIEWED_STOP_INDEXED_VOTE_HASHES = {
    "src/engine/automation/main_stop_postclose.py": "616a22f236d89de67e18001dbb3564aca6ed5b87e1b26ade3a119a711e1ab057"
}
REVIEWED_STOP_INDEXED_VOTE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_stop_postclose.py",
        "selector_sha256": REVIEWED_STOP_INDEXED_VOTE_HASHES[
            "src/engine/automation/main_stop_postclose.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_STOP_INDEXED_VOTE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_STOP_INDEXED_VOTE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STOP_FORWARD_STREAM_DEPENDENCY_VARIANTS.items()
}
REVIEWED_STOP_INDEXED_VOTE_PAIRS = {
    name: tuple(
        (before, after)
        for before in sorted(
            {pair[0] for pair in REVIEWED_STOP_SHARED_POSITION_PAIRS[name]}
            | {REVIEWED_STOP_SHARED_POSITION_HASHES[name]}
        )
    )
    for name, after in REVIEWED_STOP_INDEXED_VOTE_HASHES.items()
}

# One complete report-only pre-entry observer generation. Preserve every
# historical generation; no runtime entry-clock or policy behavior changes.
REVIEWED_PRE_ENTRY_OBSERVER_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "bed604f22ae510af223e3363ef2b482bcb4a8ce9fa51d8f9574a1fbf8fc7a37c"
}
REVIEWED_PRE_ENTRY_OBSERVER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_PRE_ENTRY_OBSERVER_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_PRE_ENTRY_OBSERVER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PRE_ENTRY_OBSERVER_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STOP_INDEXED_VOTE_DEPENDENCY_VARIANTS.items()
}
REVIEWED_PRE_ENTRY_OBSERVER_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
            "bed604f22ae510af223e3363ef2b482bcb4a8ce9fa51d8f9574a1fbf8fc7a37c",
        ),
        (
            "60ab1c4f07c71928f33523b49e8a4143fb1d4e01583dabf3beda6290758f4e23",
            "bed604f22ae510af223e3363ef2b482bcb4a8ce9fa51d8f9574a1fbf8fc7a37c",
        ),
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "bed604f22ae510af223e3363ef2b482bcb4a8ce9fa51d8f9574a1fbf8fc7a37c",
        ),
    )
}

# Native claim/lock journals are synchronization metadata, not vote inputs.
REVIEWED_VOTE_METADATA_HASHES = {
    "src/engine/automation/main_stop_postclose.py": "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b"
}
REVIEWED_VOTE_METADATA_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_stop_postclose.py",
        "selector_sha256": REVIEWED_VOTE_METADATA_HASHES[
            "src/engine/automation/main_stop_postclose.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_VOTE_METADATA_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_VOTE_METADATA_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRE_ENTRY_OBSERVER_DEPENDENCY_VARIANTS.items()
}
REVIEWED_VOTE_METADATA_PAIRS = {
    "src/engine/automation/main_stop_postclose.py": (
        (
            "531f1498332196f0e54d17b76ed8d30295009a5e5ee9363ad9397613f0740ad2",
            "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
        ),
        (
            "616a22f236d89de67e18001dbb3564aca6ed5b87e1b26ade3a119a711e1ab057",
            "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
        ),
        (
            "c020c831fcc3e33776d2c19154fc5cd3892e4bb98f8b19db7c9eeab83b847ab5",
            "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
        ),
    )
}

# Broker receipt ACK and exact fractional BUY identity; no order guard changes.
REVIEWED_BROKER_CUSTODY_HASHES = {
    "src/engine/ai/holding_exit_vote.py": "d8c9de0ae5270c0e40f8494941def50c69d52fbab887b5c38c6b1fd73129514c",
    "src/engine/monitoring/policy_generation_contract.py": "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
    "src/engine/sniper_execution_receipts.py": "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
    "src/engine/sniper_trade_review_report.py": "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
}
REVIEWED_BROKER_CUSTODY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_execution_receipts.py",
        "selector_sha256": REVIEWED_BROKER_CUSTODY_HASHES[
            "src/engine/sniper_execution_receipts.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_BROKER_CUSTODY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_BROKER_CUSTODY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_VOTE_METADATA_DEPENDENCY_VARIANTS.items()
}
REVIEWED_BROKER_CUSTODY_PAIRS = {
    "src/engine/ai/holding_exit_vote.py": (
        (
            "69f1a9a63a79d38e3a9986156800d883fab98b86a78ceb12a603040227cb2c81",
            "d8c9de0ae5270c0e40f8494941def50c69d52fbab887b5c38c6b1fd73129514c",
        ),
        (
            "9d516e9dd068613765944d7ab78d65fe561905046c38d45c0d0a835078d98a7b",
            "d8c9de0ae5270c0e40f8494941def50c69d52fbab887b5c38c6b1fd73129514c",
        ),
    ),
    "src/engine/monitoring/policy_generation_contract.py": (
        (
            "5f41ee2c9f8a3df2ac5f00b1d972673505266b598303ea787db533336eb79290",
            "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
        ),
        (
            "abdbc156884a627671b95965d0985103ab720561a4b4ebfdf092b509116b563f",
            "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
        ),
    ),
    "src/engine/sniper_execution_receipts.py": (
        (
            "179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05",
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
        ),
        (
            "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
        ),
        (
            "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
        ),
    ),
    "src/engine/sniper_trade_review_report.py": (
        (
            "8d07674031ac0ca0a08437c61490cd896d8810c30f57810ad53febb8cac0b57c",
            "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
        ),
        (
            "d3e838423aeeaba629be4902b2aac533caceef3145ad747bdc78ff2900c230d8",
            "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
        ),
        (
            "de4dd6cfc135d5d6c53f757151f32753f13ff780caca285886dba2dc285890d8",
            "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
        ),
    ),
}

# Native frozen-source reuse and receipt census; prior generations stay sealed.
REVIEWED_FROZEN_INPUT_HASHES = {
    "src/engine/automation/main_trailing_source_assembler.py": "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
    "src/engine/automation/main_trailing_source_reuse.py": "b2542e5924e87107b5d3319f7e9787d09b3b6bddf85639a6d5f305e4a3c83944",
    "src/engine/scalping/holding_profit_exit_semantics.py": "586d26b7c6a9bd7041477f490c1f897f3d305d7dd07b2d56af3e368221af29de",
    "src/engine/sniper_trade_review_report.py": "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
}
REVIEWED_FROZEN_INPUT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_reuse.py",
        "selector_sha256": REVIEWED_FROZEN_INPUT_HASHES[
            "src/engine/automation/main_trailing_source_reuse.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_FROZEN_INPUT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_FROZEN_INPUT_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_BROKER_CUSTODY_DEPENDENCY_VARIANTS.items()
}
REVIEWED_FROZEN_INPUT_PAIRS = {
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
        ),
        (
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
            "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
        ),
    ),
    "src/engine/automation/main_trailing_source_reuse.py": (
        (
            "c190554546468617b2963e2ba013473e992f4d4ad638a5f4aee2f71027bc58ef",
            "b2542e5924e87107b5d3319f7e9787d09b3b6bddf85639a6d5f305e4a3c83944",
        ),
    ),
    "src/engine/scalping/holding_profit_exit_semantics.py": (
        (
            "7512700df7e7d3bf705ec3e5d866bf9b916e564d60312fa3918f950c34431b78",
            "586d26b7c6a9bd7041477f490c1f897f3d305d7dd07b2d56af3e368221af29de",
        ),
    ),
    "src/engine/sniper_trade_review_report.py": (
        (
            "d3e838423aeeaba629be4902b2aac533caceef3145ad747bdc78ff2900c230d8",
            "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
        ),
        (
            "8d07674031ac0ca0a08437c61490cd896d8810c30f57810ad53febb8cac0b57c",
            "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
        ),
        (
            "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
            "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
        ),
    ),
}

# Preserved source-reader generation from0255cb05f; no generic hash bypass.
REVIEWED_SOURCE_READER_HASHES = {
    "src/engine/automation/main_startup_validation.py": "c39f9d5b8a68c297304c95b36a8ff7415fd413f3493e5584eb227adecc6ce84c",
    "src/engine/automation/next_preopen_readiness.py": "c7ba75db4fedb705bdbfc4b7c2bdd39ac527b44b111d33c9639e911adaded88e",
    "src/engine/error_detectors/artifact_freshness.py": "47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4",
    "src/engine/infrastructure/validation_digest_session.py": "40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056",
    "src/engine/lifecycle/research_json_stream.py": "53bd6a0cec6435ff0cfb399ad75fc9edd0b479463c06dea77bc5cae5e59db4b6",
    "src/engine/log_archive_service.py": "18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af",
    "src/engine/monitoring/rising_missed_intraday_feedback.py": "902ec3543434043e3ee0808bdd724c119a370c43747939ed935af0df4bdb0799",
    "src/engine/monitoring/sentinel_compact_store.py": "3bb5572bb36683f43151fb6c4c5bcfa3bd7403b6bfa412661c556d5e0fc84b30",
    "src/engine/pipeline_event_summary.py": "f3051e000b6edbd349a58e37f7880f5db10ae62dde9dec7f32edaa4eea6ebe3b",
    "src/engine/scalping/ai_action_outcome_calibration.py": "18c661a624b4db88ac0ee5963ff3667a258434662d9ddfca9bea8ab6cc7f50aa",
    "src/engine/scalping/compact_auxiliary_paired_replay.py": "792619031c87b993dd32fcff8b9821fbfbc464641ff1ea246c6871db97e26d67",
    "src/engine/scalping/continuous_reversal_operating_postclose.py": "23b5b1a03b3c4ad1fe5c261ed3a65917fa424d94c2e02ede18191d20b2b95f58",
    "src/engine/scalping/continuous_reversal_postclose.py": "d294d3fab9ef36e29b0b15007b0d22c47e1572f3b36de25d72802873f2568dda",
    "src/engine/scalping/continuous_reversal_source.py": "96f1edc13538616832ec4270064afcc9a6bacab8274903cd57b2838573a1155d",
    "src/engine/scalping/postclose_entry_validation.py": "ff34fd56d765e8e598cbb3f9306ebf962b144699bb6a2ec58eeee698a0754540",
    "src/engine/scalping/reversal_cumulative_postclose.py": "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
    "src/engine/sniper_performance_tuning_report.py": "64a6f84c470d3f8a221a509fdf4a71152b521a49b4b5a49a0023c3214c93fbe2",
    "src/utils/jsonl_io.py": "c8e3058acdf08d411bfd19edee9cdfe3871bc0b004106038f449320727ab7fb1",
}

REVIEWED_SOURCE_READER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/lifecycle/research_json_stream.py",
        "selector_sha256": REVIEWED_SOURCE_READER_HASHES[
            "src/engine/lifecycle/research_json_stream.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_SOURCE_READER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SOURCE_READER_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_BROKER_CUSTODY_DEPENDENCY_VARIANTS.items()
}

REVIEWED_SOURCE_READER_PAIRS = {
    "src/engine/error_detectors/artifact_freshness.py": (
        (
            "bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a",
            "47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4",
        ),
    ),
    "src/engine/infrastructure/validation_digest_session.py": (
        (
            "655b6f32ed1f14cb7c00e7c85b4b2f3917d55e00cfdefc905160a039d585a4f1",
            "40497e9bcb5d325bb0623631cd2149a0b2090c996bc54e3300b650f201a0e056",
        ),
    ),
    "src/engine/lifecycle/research_json_stream.py": (
        (
            "1ea671f8ba5b5397257c2d1da513dee653b05379133073d1412ee4edf7a07a11",
            "53bd6a0cec6435ff0cfb399ad75fc9edd0b479463c06dea77bc5cae5e59db4b6",
        ),
    ),
    "src/engine/log_archive_service.py": (
        (
            "48243d6d40dc68e5d8023208b9c8c38be6d92c5326f8702a9a3d2060e1efcebb",
            "18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af",
        ),
    ),
    "src/engine/monitoring/rising_missed_intraday_feedback.py": (
        (
            "814aaadd29b76ad0b8843d3607fcb12bb086efa8b20714a6f427209e24d204d1",
            "902ec3543434043e3ee0808bdd724c119a370c43747939ed935af0df4bdb0799",
        ),
    ),
    "src/engine/monitoring/sentinel_compact_store.py": (
        (
            "cde3555c1a8fd1f45a21e2fcbf54f3d6829bf2354b76dc54aed18874b415430d",
            "3bb5572bb36683f43151fb6c4c5bcfa3bd7403b6bfa412661c556d5e0fc84b30",
        ),
    ),
    "src/engine/pipeline_event_summary.py": (
        (
            "fc39f13b5b026c628345268953daec046cf1277f88b9f3b1bcef4833f34e99af",
            "f3051e000b6edbd349a58e37f7880f5db10ae62dde9dec7f32edaa4eea6ebe3b",
        ),
    ),
    "src/engine/scalping/ai_action_outcome_calibration.py": (
        (
            "26b7b67e5efcf5ed9d4904ac2c715cb1e1e87d76a8b63acc0b6049bff91c03c2",
            "18c661a624b4db88ac0ee5963ff3667a258434662d9ddfca9bea8ab6cc7f50aa",
        ),
    ),
    "src/engine/scalping/compact_auxiliary_paired_replay.py": (
        (
            "94a8ab07b0380259aba0a649719c1639cba6345bec4a4023136a417a4a467b10",
            "792619031c87b993dd32fcff8b9821fbfbc464641ff1ea246c6871db97e26d67",
        ),
    ),
    "src/engine/scalping/continuous_reversal_operating_postclose.py": (
        (
            "88c6185c43171dec9ff28d2dfff621e21303f1e94489c5d8fe6755791755ec81",
            "23b5b1a03b3c4ad1fe5c261ed3a65917fa424d94c2e02ede18191d20b2b95f58",
        ),
    ),
    "src/engine/scalping/continuous_reversal_postclose.py": (
        (
            "94adb3c969f3053414e6e825878e4afbec83def90c8b5dc0bb6808fac8892edd",
            "d294d3fab9ef36e29b0b15007b0d22c47e1572f3b36de25d72802873f2568dda",
        ),
    ),
    "src/engine/scalping/continuous_reversal_source.py": (
        (
            "401ff28d4f2b20db778768aa10486bffdac01466480e7429a428d3fa14705b02",
            "96f1edc13538616832ec4270064afcc9a6bacab8274903cd57b2838573a1155d",
        ),
    ),
    "src/engine/scalping/postclose_entry_validation.py": (
        (
            "c8fbcdac97c33b2b06e301b15f6dbe4d42fb31824cbeef547a25de7d70aa1189",
            "ff34fd56d765e8e598cbb3f9306ebf962b144699bb6a2ec58eeee698a0754540",
        ),
    ),
    "src/engine/scalping/reversal_cumulative_postclose.py": (
        (
            "708ee7428c494f67a7407e5093771f8ddf45ba67227073bea05ff5d87a172493",
            "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
        ),
    ),
    "src/engine/sniper_performance_tuning_report.py": (
        (
            "7ca2bb38af56e0a985c47e89bee7064efb7da1f87243d27691b3294389e0ac0a",
            "64a6f84c470d3f8a221a509fdf4a71152b521a49b4b5a49a0023c3214c93fbe2",
        ),
    ),
    "src/utils/jsonl_io.py": (
        (
            "b0173c0cd27eefd75a73b9f1c2b956378256a7476341496cf248a77e9984f418",
            "c8e3058acdf08d411bfd19edee9cdfe3871bc0b004106038f449320727ab7fb1",
        ),
    ),
}

# Combined0255 source readers, frozen census and actual P5 preserved closure.
# Select one complete reviewed generation before any incumbent drain.
REVIEWED_SOURCE_INTEGRATION_HASHES = {
    **REVIEWED_FROZEN_INPUT_HASHES,
    **{
        "src/engine/automation/main_startup_validation.py": "399ee38f0d22991d9761e5d301f8bc6af15b53fe2a8ba582cbc0435bd62daa67",
        "src/engine/infrastructure/startup_validation_code_context.py": "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
    },
}
REVIEWED_SOURCE_INTEGRATION_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_SOURCE_INTEGRATION_HASHES[
            "src/engine/infrastructure/startup_validation_code_context.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_SOURCE_INTEGRATION_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SOURCE_INTEGRATION_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SOURCE_READER_DEPENDENCY_VARIANTS.items()
}
# The observer successor only completes bounded incident classification; its
# exact bytes preserve current/unknown failures and the source-quality alert.
REVIEWED_SOURCE_INTEGRATION_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "e9905d8614a2b8c8751b723eaa8ba53507e2b67e0909c53c393c92b366fb68b9",
        ),
    ),
    "src/engine/automation/main_startup_validation.py": (
        (
            "190855a642ca713fe53257eae2268eeb5786990c474f2b63904ace41b66c9661",
            "399ee38f0d22991d9761e5d301f8bc6af15b53fe2a8ba582cbc0435bd62daa67",
        ),
        (
            "c39f9d5b8a68c297304c95b36a8ff7415fd413f3493e5584eb227adecc6ce84c",
            "399ee38f0d22991d9761e5d301f8bc6af15b53fe2a8ba582cbc0435bd62daa67",
        ),
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        (
            "4d20ceaccb28ac3ab7e3521ded1603abb3587edb8b3ad828a5ae505d02da31c3",
            "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
        ),
    ),
}

# Exact report-only original-gap evidence successor. Preserve all issued profiles.
REVIEWED_ORIGINAL_GAP_HASHES = {
    "src/engine/scalping/holding_profit_exit_semantics.py": "e76d509fa67cb46100d1fffd1b272fbc3355b3c729604a348e22f653f8b0d269"
}
REVIEWED_ORIGINAL_GAP_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/holding_profit_exit_semantics.py",
        "selector_sha256": REVIEWED_ORIGINAL_GAP_HASHES[
            "src/engine/scalping/holding_profit_exit_semantics.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ORIGINAL_GAP_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ORIGINAL_GAP_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SOURCE_INTEGRATION_DEPENDENCY_VARIANTS.items()
}
REVIEWED_SOURCE_INTEGRATION_PAIRS[
    "src/engine/scalping/holding_profit_exit_semantics.py"
] = tuple(
    (
        old,
        REVIEWED_ORIGINAL_GAP_HASHES[
            "src/engine/scalping/holding_profit_exit_semantics.py"
        ],
    )
    for old in (
        "7512700df7e7d3bf705ec3e5d866bf9b916e564d60312fa3918f950c34431b78",
        "586d26b7c6a9bd7041477f490c1f897f3d305d7dd07b2d56af3e368221af29de",
    )
)

# Select a complete successor, retaining every issued original-gap profile.
REVIEWED_INCIDENT_ORDER_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_SOURCE_INTEGRATION_PAIRS[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ][0][1],
        "dependencies": {
            **value["dependencies"],
            "src/engine/monitoring/submission_bottleneck_monitor.py": REVIEWED_SOURCE_INTEGRATION_PAIRS[
                "src/engine/monitoring/submission_bottleneck_monitor.py"
            ][
                0
            ][
                1
            ],
        },
    }
    for key, value in REVIEWED_ORIGINAL_GAP_DEPENDENCY_VARIANTS.items()
}

# The shared product predicate and its two dispatch consumers form one exact
# successor. Historical policies retain their original dependency profiles.
REVIEWED_PRODUCT_INTAKE_HASHES = {
    "src/utils/kiwoom_utils.py": "a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f",
    "src/scanners/scalping_scanner.py": "3280979b86c4bb10231b7886f591aba239c453b3e37d1ba79b8c2fdb1d4f477f",
    "src/scanners/zero_base_discovery_queue.py": "9bbcaa6181f9a3f46d9c6c3328dc857e774d5fd7800f2e297bae5d3ea17cb7c8",
}
REVIEWED_PRODUCT_INTAKE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/utils/kiwoom_utils.py",
        "selector_sha256": REVIEWED_PRODUCT_INTAKE_HASHES["src/utils/kiwoom_utils.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_PRODUCT_INTAKE_HASHES},
    }
    for key, value in REVIEWED_INCIDENT_ORDER_DEPENDENCY_VARIANTS.items()
}

# SQL connection lifecycle and its diagnostic consumer are one complete
# successor. Issued product/observer profiles remain byte-bound independently.
REVIEWED_SQLITE_LIFECYCLE_HASHES = {
    "src/engine/automation/main_trailing_source_store.py": "a27ce958c053023e920ac23e6369126bdc7d77eb2d73fd713cc5c109e212d593",
    "src/engine/infrastructure/validation_digest_session.py": "87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da",
    "src/engine/error_detector.py": "c4d2e89d6e257d4c9cd7d819a2592fd4e31a73fb3806662ab97911542c471f56",
}
REVIEWED_SQLITE_LIFECYCLE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_store.py",
        "selector_sha256": REVIEWED_SQLITE_LIFECYCLE_HASHES[
            "src/engine/automation/main_trailing_source_store.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_SQLITE_LIFECYCLE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SQLITE_LIFECYCLE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRODUCT_INTAKE_DEPENDENCY_VARIANTS.items()
}

# Reviewed retired-helper removal and report-parser consolidation. Bind the
# complete predecessor generation; historical handoffs retain their own hashes.
# Evidence: docs/checklists/2026-10-20-stage2-todo-checklist.md (CodeRefactorRetiredReview1020).
REVIEWED_RETIRED_REVIEW_HASHES = {
    "src/engine/sniper_overnight_gatekeeper.py": "0342a74e37f17540ad89329e0fe8d5ae78b5c71144c82947971ced995a9b9f54",
    "src/engine/scalp_entry_adm_runtime.py": "4c17ed099fa378545ffad45a89a0cc3996022ab00400217df1333e6d23ebd3ca",
    "src/engine/holding_exit_matrix_runtime.py": "b3386f73fc5b6eb3b0e438c59cb6c2874ead1163011ecd93e53a15f83b7127bc",
    "src/engine/automation/dual_candidate_review.py": "29642a08a59e4f08cca765934fd2d5fd27dd8e12f763bb216cba6e363bde3914",
    "src/engine/automation/producer_gap_discovery.py": "c66f911a67f75524148d0608a13b7b451d71917d9da5016bea5627a85eb9a6bd",
    "src/engine/automation/stage_hook_workorder_discovery.py": "d6079fd11abdcca5f69950e41f15ca49c26f014446004358f30e89316844df80",
}
REVIEWED_RETIRED_REVIEW_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_overnight_gatekeeper.py",
        "selector_sha256": REVIEWED_RETIRED_REVIEW_HASHES[
            "src/engine/sniper_overnight_gatekeeper.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_RETIRED_REVIEW_HASHES},
    }
    for key, value in REVIEWED_PRODUCT_INTAKE_DEPENDENCY_VARIANTS.items()
}

# The integrated cleanup/SQLite generation retains both independently issued
# profiles. Match both selectors before selecting the complete merged contract.
REVIEWED_CLEAN_SQLITE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "additional_selector_path": "src/engine/sniper_overnight_gatekeeper.py",
        "additional_selector_sha256": REVIEWED_RETIRED_REVIEW_HASHES[
            "src/engine/sniper_overnight_gatekeeper.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_RETIRED_REVIEW_HASHES},
    }
    for key, value in REVIEWED_SQLITE_LIFECYCLE_DEPENDENCY_VARIANTS.items()
}

# Reviewed approved delay-v4 evidence plus retired PYRAMID helper removal.
# Keep the issued cleanup/SQLite profiles; one complete final trigger owns all
# producer/consumer bytes, including startup and pre-drain report currentness.
REVIEWED_DELAY_CLEANUP_HASHES = {
    "src/engine/automation/main_trailing_source_store.py": "aca2d7dda4c8eda53f6634a73b133090e73c511cc62973584f31633245edd850",
    "src/engine/automation/pre_submit_delay_partitioned_research.py": "cbc0a519c2126948f7c68982c86bae7678c54db65c687ed960563cf76053e6e3",
    "src/engine/automation/pre_submit_delay_research_review.py": "159b04fa4b5486e43feba9ca2dee73b7e1f9052926f729cb6169ff0ff89ad2ac",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "3e22aacfc10f43a86e4e242793eb30b44bb2f622d55236debb6e8a0dfdfc2158",
    "src/engine/scalping/pre_submit_delay_initial_policy.py": "918c266dea445d4b9f949b6ae76755c724df8fc525760812a0cab33b70de8b1c",
    "src/engine/scalping/pre_submit_delay_tuning.py": "6d2335731199417edce383e773b5737b110f4401297fefce75fc578dd7ce6fd2",
    "src/engine/scalping/reversal_auxiliary_registry.py": "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
    "src/engine/sniper_state_handlers.py": "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
    "src/bot_main.py": "f8c2f1626d60502234c002bb75f99fb6e092c620ad2ae6ae87eac6db76da1f0c",
    "src/engine/automation/ordered_intraday_deploy.py": "9b16f12badd137f866cd77b09e356ef75e70ce40fa1a1455c16581fea98fbea0",
}
REVIEWED_DELAY_CLEANUP_PAIRS = {
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "3e7893cab9a61cf3ff9e08242a9786d2d8f24cc69dd42c7f9943bd90bcf116ae",
            "aca2d7dda4c8eda53f6634a73b133090e73c511cc62973584f31633245edd850",
        ),
        (
            "a27ce958c053023e920ac23e6369126bdc7d77eb2d73fd713cc5c109e212d593",
            "aca2d7dda4c8eda53f6634a73b133090e73c511cc62973584f31633245edd850",
        ),
    ),
    "src/engine/automation/pre_submit_delay_partitioned_research.py": (
        (
            "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
            "cbc0a519c2126948f7c68982c86bae7678c54db65c687ed960563cf76053e6e3",
        ),
        (
            "1f92ea9be98b4a9d0cce66d4105959b21eb03b5d060c501d628b9cef2cc73d65",
            "cbc0a519c2126948f7c68982c86bae7678c54db65c687ed960563cf76053e6e3",
        ),
    ),
    "src/engine/automation/pre_submit_delay_research_review.py": (
        (
            "6cf9e50d915da95f0cd469b2a7d36ede3754cba6c237f69ab0fdfcf565f968d6",
            "159b04fa4b5486e43feba9ca2dee73b7e1f9052926f729cb6169ff0ff89ad2ac",
        ),
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "3e22aacfc10f43a86e4e242793eb30b44bb2f622d55236debb6e8a0dfdfc2158",
        ),
        (
            "082d6e1af5276405fc493d2be739818ad7d9d55e5026a113029f66eaec0b4b2e",
            "3e22aacfc10f43a86e4e242793eb30b44bb2f622d55236debb6e8a0dfdfc2158",
        ),
        (
            "e9905d8614a2b8c8751b723eaa8ba53507e2b67e0909c53c393c92b366fb68b9",
            "3e22aacfc10f43a86e4e242793eb30b44bb2f622d55236debb6e8a0dfdfc2158",
        ),
    ),
    "src/engine/scalping/pre_submit_delay_initial_policy.py": (
        (
            "0853914ebbc643de4301b87209c9db106662bd60485146b0d16e495b77c0cd33",
            "918c266dea445d4b9f949b6ae76755c724df8fc525760812a0cab33b70de8b1c",
        ),
        (
            "9bf1914b5445ad687d2480352cb01d6ca3ab742709175a3ba7181d1747499edc",
            "918c266dea445d4b9f949b6ae76755c724df8fc525760812a0cab33b70de8b1c",
        ),
    ),
    "src/engine/scalping/pre_submit_delay_tuning.py": (
        (
            "c5fdf030c87f4faf94a70ecf1d2c4c40a753b4da6069a58ed105f5e43cb76605",
            "6d2335731199417edce383e773b5737b110f4401297fefce75fc578dd7ce6fd2",
        ),
        (
            "c2fb791a41e35c326ca874562c332fac0e7ea16cda0066fc82f34679cd93ef1a",
            "6d2335731199417edce383e773b5737b110f4401297fefce75fc578dd7ce6fd2",
        ),
    ),
    "src/engine/scalping/reversal_auxiliary_registry.py": (
        (
            "5702bd5b558ca0e61c52eb4c3679c4f57d6bc877629ea9635ad6f0143fe413da",
            "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
        ),
        (
            "a9ca6ebc7b924fcb8de2dc4b141d99500aacc5f3700fe566b3fea190b24cbd31",
            "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
        ),
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
        ),
    ),
    "src/bot_main.py": (
        (
            "d98fbcddf8f3d2735385fcb92f1d5d43a631bc1b7ab11e2d5c7311c838ae969a",
            "f8c2f1626d60502234c002bb75f99fb6e092c620ad2ae6ae87eac6db76da1f0c",
        ),
        (
            "a2e8ec8578bb6b52cc91348584a8c4627fdc06412dc505a71c2c9ebf8f6bd526",
            "f8c2f1626d60502234c002bb75f99fb6e092c620ad2ae6ae87eac6db76da1f0c",
        ),
    ),
    "src/engine/automation/ordered_intraday_deploy.py": (
        (
            "4345d7b8ea95b13b7c7862bc54c24b9add92e6da79806190308bfb17b15ba3b9",
            "9b16f12badd137f866cd77b09e356ef75e70ce40fa1a1455c16581fea98fbea0",
        ),
        (
            "48b9376c7683466e5d0e195ac971c93d1ed1cd442e9968eddacc2031e38e75a9",
            "9b16f12badd137f866cd77b09e356ef75e70ce40fa1a1455c16581fea98fbea0",
        ),
    ),
}
REVIEWED_DELAY_CLEANUP_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_DELAY_CLEANUP_HASHES.get(trigger, sha)): {
        **value,
        "selector_path": "src/engine/sniper_state_handlers.py",
        "selector_sha256": REVIEWED_DELAY_CLEANUP_HASHES[
            "src/engine/sniper_state_handlers.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_DELAY_CLEANUP_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_DELAY_CLEANUP_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_CLEAN_SQLITE_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_DELAY_CLEANUP_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]

# Reviewed local completion latency and role-only model configuration. Preserve
# every issued dependency generation; one exact group prevents mixed rollbacks.
# Evidence: SubmissionMonitorSyncLineage1019, review section 2026-10-20.
REVIEWED_ROLE_LATENCY_HASHES = {
    "src/engine/ai/hot_path_ai_dispatcher.py": "a7688b6d206035d66cd61303868ed20f9da3f334997b3e64fc1e2c8c7634330b",
    "src/engine/ai_engine_openai.py": "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
    "src/engine/infrastructure/snapshot_copy.py": "6e40a74825ad11fdc84afde95d5080549d9b284644108919aa35adee7fc10e41",
    "src/engine/kiwoom_sniper_v2.py": "44133e57f1c20521b80cfa5fa1e7dadb7c89b010ab461cce3959fd1ba6fd4997",
    "src/engine/lifecycle/avg_down_policy_replay.py": "26ec5374924617f9beef1bda42a7b2433c583abbae73407da360e4d866ed35cd",
    "src/engine/scalping/ai_decision_trace.py": "dfbb14a03971bcfa1f8a0b4c1f3b712d45e7da7fa7259cac125db7f5bb8747a0",
    "src/engine/scalping/avg_down_replay_capture.py": "fb26fb1d9a2d834d5a626fb81e6a7bf97ab88042386630f9b7ed2a0237b1c49a",
    "src/engine/scalping/entry_context_intraday_probe.py": "d5594fc0d9384cec15441c81f83be03bfdbf7b38fdd6de9e2ed8f7a02eea0c6f",
    "src/engine/scalping/opening_rotation.py": "405246b7429792a1a7bb1dc9fd12e35f2c1a9211de65208ecae4ac6f567e2e5d",
    "src/engine/scalping/scanner_async_eval.py": "9fb2ac9ff75f620f008fb38a6611e5f08c6984d552c475e3314fa6ad6f3fefdf",
    "src/engine/swing/bottom_rebound_policy_auto_loop.py": "d674258f0fa3dad667bceec870c024177117973a7955d167004d60650f665a04",
    "src/utils/constants.py": "91b7840994ca13114176ced7cbc0ed23f9ecf53aad5dd9497956b9c991990252",
}
REVIEWED_ROLE_LATENCY_PAIRS = {
    "src/engine/ai/hot_path_ai_dispatcher.py": (
        (
            "bec51a2d3e23baf4277066e57fcde81368aa6d53cb923470e58757bb8102d229",
            "a7688b6d206035d66cd61303868ed20f9da3f334997b3e64fc1e2c8c7634330b",
        ),
    ),
    "src/engine/ai_engine_openai.py": (
        (
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
        ),
    ),
    "src/engine/infrastructure/snapshot_copy.py": (
        (
            "1299ee9fecd33f8a2c7eca4762fbe5e26a0a3414f7c0c91f8b3e199f7e9489c0",
            "6e40a74825ad11fdc84afde95d5080549d9b284644108919aa35adee7fc10e41",
        ),
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
            "44133e57f1c20521b80cfa5fa1e7dadb7c89b010ab461cce3959fd1ba6fd4997",
        ),
    ),
    "src/engine/lifecycle/avg_down_policy_replay.py": (
        (
            "1340fc7a7afda1cfb6a46acf6be6f73318901098aab06fbff07044d86a4c8dc5",
            "26ec5374924617f9beef1bda42a7b2433c583abbae73407da360e4d866ed35cd",
        ),
    ),
    "src/engine/scalping/ai_decision_trace.py": (
        (
            "ea62bfe70f124e71a59b74cf0b885326217ceb019b00da9f8af45c37105ca17e",
            "dfbb14a03971bcfa1f8a0b4c1f3b712d45e7da7fa7259cac125db7f5bb8747a0",
        ),
    ),
    "src/engine/scalping/avg_down_replay_capture.py": (
        (
            "dbb163f2f23c678f4a2343e8501b405166bd18f30b94b0de64f98e76c0a2645a",
            "fb26fb1d9a2d834d5a626fb81e6a7bf97ab88042386630f9b7ed2a0237b1c49a",
        ),
    ),
    "src/engine/scalping/entry_context_intraday_probe.py": (
        (
            "b6c9fc8a0a96ce6055a8dffb64884e802aaea94bc58e987473d7b8ea43f3ebd3",
            "d5594fc0d9384cec15441c81f83be03bfdbf7b38fdd6de9e2ed8f7a02eea0c6f",
        ),
    ),
    "src/engine/scalping/opening_rotation.py": (
        (
            "5f571f69ae8f999b7ccdf376132572a029abdf8ecbad7447872e54a8baebf58c",
            "405246b7429792a1a7bb1dc9fd12e35f2c1a9211de65208ecae4ac6f567e2e5d",
        ),
    ),
    "src/engine/scalping/scanner_async_eval.py": (
        (
            "bfd354bbfbc371e912e873a3cbb40fd1ec2b9f5a78427602f214cfb0543b1d21",
            "9fb2ac9ff75f620f008fb38a6611e5f08c6984d552c475e3314fa6ad6f3fefdf",
        ),
    ),
    "src/engine/swing/bottom_rebound_policy_auto_loop.py": (
        (
            "cfa0e7fb2de886845bdae5cc2f85c40886cce8d6f04e8eaa84b7c45f8df9d9ed",
            "d674258f0fa3dad667bceec870c024177117973a7955d167004d60650f665a04",
        ),
    ),
    "src/utils/constants.py": (
        (
            "72021194611922de3e7c4399770fa98b488035753b24a9fce62f12115bb1c0c6",
            "91b7840994ca13114176ced7cbc0ed23f9ecf53aad5dd9497956b9c991990252",
        ),
    ),
}
REVIEWED_ROLE_LATENCY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/ai_engine_openai.py",
        "selector_sha256": REVIEWED_ROLE_LATENCY_HASHES[
            "src/engine/ai_engine_openai.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ROLE_LATENCY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ROLE_LATENCY_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_DELAY_CLEANUP_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_ROLE_LATENCY_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]

# The no-notification observer reserves publication time only. Preserve every
# issued predecessor profile and bind the complete reviewed successor inputs.
REVIEWED_STARTUP_BUDGET_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1",
}
REVIEWED_STARTUP_BUDGET_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1",
        ),
    ),
}
REVIEWED_STARTUP_BUDGET_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_STARTUP_BUDGET_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_STARTUP_BUDGET_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_STARTUP_BUDGET_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ROLE_LATENCY_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_STARTUP_BUDGET_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]

# One exact generation for controlled diagnostic shutdown, retaining every
# issued predecessor and the complete startup-budget dependency closure.
REVIEWED_DELAY_SHUTDOWN_HASHES = {
    "src/engine/kiwoom_sniper_v2.py": "522bc4a71a1375144db798b2e451fcee03a44e80d57323c7996fa365bf20c71c",
    "src/engine/scalping/pre_submit_delay_observation.py": "99d7b8d5e57ad886433747cee55f8f12c9a71d539577d94adff03543a8ff724d",
    "src/utils/pipeline_event_logger.py": "fde49c9a27dfc5c858d765353a0a898ac45728d57ecfa0526c4a6df4fef4c99e",
}
REVIEWED_DELAY_SHUTDOWN_PAIRS = {
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
            REVIEWED_DELAY_SHUTDOWN_HASHES["src/engine/kiwoom_sniper_v2.py"],
        ),
    ),
    "src/engine/scalping/pre_submit_delay_observation.py": (
        (
            "c4d8765a72a398b045b924d96367f5b3a0876711265134515dd4bd4fcb4199f1",
            REVIEWED_DELAY_SHUTDOWN_HASHES[
                "src/engine/scalping/pre_submit_delay_observation.py"
            ],
        ),
    ),
    "src/utils/pipeline_event_logger.py": (
        (
            "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
            REVIEWED_DELAY_SHUTDOWN_HASHES["src/utils/pipeline_event_logger.py"],
        ),
    ),
}
REVIEWED_DELAY_SHUTDOWN_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_DELAY_SHUTDOWN_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/kiwoom_sniper_v2.py",
        "selector_sha256": REVIEWED_DELAY_SHUTDOWN_HASHES[
            "src/engine/kiwoom_sniper_v2.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_DELAY_SHUTDOWN_HASHES.get(os.path.normpath(name), digest)
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_DELAY_SHUTDOWN_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_DELAY_SHUTDOWN_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_STARTUP_BUDGET_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_DELAY_SHUTDOWN_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Exact routed-data issuer reader; every issued shutdown generation stays valid.
REVIEWED_ROUTED_REUSE_HASHES = {
    "src/engine/automation/main_trailing_source_reuse.py": "272f0753cce9fc43324063a2d690394e844630f6eab8da7dace87596620ac0ab",
}
REVIEWED_ROUTED_REUSE_PAIRS = {
    "src/engine/automation/main_trailing_source_reuse.py": (
        (
            "c190554546468617b2963e2ba013473e992f4d4ad638a5f4aee2f71027bc58ef",
            REVIEWED_ROUTED_REUSE_HASHES[
                "src/engine/automation/main_trailing_source_reuse.py"
            ],
        ),
    ),
}
REVIEWED_ROUTED_REUSE_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_ROUTED_REUSE_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_reuse.py",
        "selector_sha256": REVIEWED_ROUTED_REUSE_HASHES[
            "src/engine/automation/main_trailing_source_reuse.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_ROUTED_REUSE_HASHES.get(os.path.normpath(name), digest)
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_ROUTED_REUSE_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_ROUTED_REUSE_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_DELAY_SHUTDOWN_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_ROUTED_REUSE_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Preserve native source connection epochs through the ordered restart.
REVIEWED_SOURCE_EPOCH_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "d67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90"
}
REVIEWED_SOURCE_EPOCH_PAIRS = {
    "src/engine/automation/ordered_intraday_deploy.py": (
        (
            "4345d7b8ea95b13b7c7862bc54c24b9add92e6da79806190308bfb17b15ba3b9",
            "d67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90",
        ),
    )
}
REVIEWED_SOURCE_EPOCH_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_SOURCE_EPOCH_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/automation/ordered_intraday_deploy.py",
        "selector_sha256": "d67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90",
        "dependencies": {
            **{
                name: REVIEWED_SOURCE_EPOCH_HASHES.get(os.path.normpath(name), digest)
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_SOURCE_EPOCH_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_SOURCE_EPOCH_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_ROUTED_REUSE_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_SOURCE_EPOCH_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Exact diagnostic close-time reader with the complete issued source epoch.
REVIEWED_CLOSED_OBSERVER_HASHES = {
    "src/engine/error_detectors/artifact_freshness.py": "7d75cb5f90844d42206b4e79714898442e15b7edc84649cb73fc97f7407e4376",
}
REVIEWED_CLOSED_OBSERVER_PAIRS = {
    "src/engine/error_detectors/artifact_freshness.py": tuple(
        (
            before,
            REVIEWED_CLOSED_OBSERVER_HASHES[
                "src/engine/error_detectors/artifact_freshness.py"
            ],
        )
        for before in (
            "bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a",
            "47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4",
        )
    ),
}
REVIEWED_CLOSED_OBSERVER_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_CLOSED_OBSERVER_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/error_detectors/artifact_freshness.py",
        "selector_sha256": REVIEWED_CLOSED_OBSERVER_HASHES[
            "src/engine/error_detectors/artifact_freshness.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_CLOSED_OBSERVER_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_CLOSED_OBSERVER_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_CLOSED_OBSERVER_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_SOURCE_EPOCH_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_CLOSED_OBSERVER_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Exact postclose reader, archive and native stopped-origin restart repair.
# Each observed member requires this entire reviewed source generation.
REVIEWED_POSTCLOSE_REPAIR_HASHES = {
    "deploy/run_threshold_cycle_postclose.sh": "e56ebd50f596b142083df248f301f8bce8a7d55ca67dbeb646224e5fb17dd9c5",
    "src/engine/automation/main_startup_validation.py": "af3f290c4e0ff97216e7c2351c06b0314967d87c9cc0c54176b5850a94e65c5b",
    "src/engine/automation/main_stop_postclose.py": "ad0eb4c9eea9b260fb63bed150ff8882671ae126500d005dc00af5f3361dd3ae",
    "src/engine/automation/main_stop_source_projection.py": "307192aac2897b8999dab43ff5c0183166df29d3a0d796882dc7308263f49006",
    "src/engine/automation/ordered_intraday_deploy.py": "2b25345a2cc0711a42a2a39898961c157dfb927c0b1eb4929b74fe3c624af626",
    "src/engine/automation/prepared_policy_code_handoff.py": "00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c",
    "src/engine/error_detectors/artifact_freshness.py": "f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e",
    "src/engine/infrastructure/startup_validation_code_context.py": "01c1d63084444119e0de2589099f20e758758d3699d0ffb59a43a3f76e5fab8c",
    "src/engine/lifecycle/snapshot_archive.py": "5194c082454e6c734cc4ef553ad78b32c11082fb504c33ffcd49242704735cb4",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "28e2d8b4e06be95c5f91b36298cfe8015f0f2474419964c60f1db4fcc267a21f",
    "src/engine/scalping/reversal_code_handoff.py": "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
}
REVIEWED_POSTCLOSE_REPAIR_PAIRS = {
    "deploy/run_threshold_cycle_postclose.sh": (
        (
            "594cd0a6613cbcd5c642ba818a8468fcafbeb4474a7cbd08e1b013ad0556911c",
            "e56ebd50f596b142083df248f301f8bce8a7d55ca67dbeb646224e5fb17dd9c5",
        ),
    ),
    "src/engine/automation/main_startup_validation.py": (
        (
            "190855a642ca713fe53257eae2268eeb5786990c474f2b63904ace41b66c9661",
            "af3f290c4e0ff97216e7c2351c06b0314967d87c9cc0c54176b5850a94e65c5b",
        ),
    ),
    "src/engine/automation/main_stop_postclose.py": (
        (
            "616a22f236d89de67e18001dbb3564aca6ed5b87e1b26ade3a119a711e1ab057",
            "ad0eb4c9eea9b260fb63bed150ff8882671ae126500d005dc00af5f3361dd3ae",
        ),
    ),
    "src/engine/automation/main_stop_source_projection.py": (
        (
            "d02e54b9f3a1233b4c2c7e0462916e3e8b789c3dd6afe0b6e35a4230856250cb",
            "307192aac2897b8999dab43ff5c0183166df29d3a0d796882dc7308263f49006",
        ),
    ),
    "src/engine/automation/ordered_intraday_deploy.py": (
        (
            "4345d7b8ea95b13b7c7862bc54c24b9add92e6da79806190308bfb17b15ba3b9",
            "2b25345a2cc0711a42a2a39898961c157dfb927c0b1eb4929b74fe3c624af626",
        ),
    ),
    "src/engine/automation/prepared_policy_code_handoff.py": (
        (
            "9ef09608077aa02c25bdd40d8bc33344bf0e10dbde18cae0fdcf434b0c6efaf8",
            "00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c",
        ),
    ),
    "src/engine/error_detectors/artifact_freshness.py": (
        (
            "bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a",
            "f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e",
        ),
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        (
            "4d20ceaccb28ac3ab7e3521ded1603abb3587edb8b3ad828a5ae505d02da31c3",
            "01c1d63084444119e0de2589099f20e758758d3699d0ffb59a43a3f76e5fab8c",
        ),
    ),
    "src/engine/lifecycle/snapshot_archive.py": (
        (
            "9d5ec9e5bfe87461341c440d573f90c2d44a5780b5206d3bd17bdb8d9fc618d8",
            "5194c082454e6c734cc4ef553ad78b32c11082fb504c33ffcd49242704735cb4",
        ),
    ),
    "src/engine/scalping/initial_quantity_monitor_projection.py": (
        (
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
            "28e2d8b4e06be95c5f91b36298cfe8015f0f2474419964c60f1db4fcc267a21f",
        ),
    ),
    "src/engine/scalping/reversal_code_handoff.py": (
        (
            "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
            "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
        ),
    ),
}
REVIEWED_POSTCLOSE_REPAIR_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_POSTCLOSE_REPAIR_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/error_detectors/artifact_freshness.py",
        "selector_sha256": REVIEWED_POSTCLOSE_REPAIR_HASHES[
            "src/engine/error_detectors/artifact_freshness.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_POSTCLOSE_REPAIR_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_POSTCLOSE_REPAIR_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_POSTCLOSE_REPAIR_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_CLOSED_OBSERVER_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_POSTCLOSE_REPAIR_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Source-only logical pipeline receipt successor. Preserve the previous
# postclose group and require the complete exact producer/cache/proof delta.
REVIEWED_LOGICAL_PIPELINE_HASHES = {
    "src/engine/scalping/initial_quantity_monitor_projection.py": "8dce560b2434f30912b39330c42932debfb4671d3b3689c10226ddcd18d083c4",
    "src/engine/scalping/initial_quantity_policy.py": "4567eed7de944395133eb6ebc975c823cf3840e6abe9424877455130feb55c87",
    "src/engine/scalping/initial_quantity_source_cache.py": "353795e63675a34743f1bdf0823f684cbdcdd472cdf12790dc17896e1aa107db",
}
REVIEWED_LOGICAL_PIPELINE_PAIRS = {
    "src/engine/scalping/initial_quantity_monitor_projection.py": (
        (
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
            "8dce560b2434f30912b39330c42932debfb4671d3b3689c10226ddcd18d083c4",
        ),
        (
            "28e2d8b4e06be95c5f91b36298cfe8015f0f2474419964c60f1db4fcc267a21f",
            "8dce560b2434f30912b39330c42932debfb4671d3b3689c10226ddcd18d083c4",
        ),
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
            "4567eed7de944395133eb6ebc975c823cf3840e6abe9424877455130feb55c87",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
            "353795e63675a34743f1bdf0823f684cbdcdd472cdf12790dc17896e1aa107db",
        ),
    ),
}
# Bind the direct prepared-bootstrap P5 repair in this unissued successor.
REVIEWED_LOGICAL_PIPELINE_HASHES["src/engine/automation/main_startup_validation.py"] = (
    "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54"
)
REVIEWED_LOGICAL_PIPELINE_PAIRS[
    "src/engine/automation/main_startup_validation.py"
] = tuple(
    (old, "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54")
    for old, _ in REVIEWED_POSTCLOSE_REPAIR_PAIRS[
        "src/engine/automation/main_startup_validation.py"
    ]
) + (
    (
        "af3f290c4e0ff97216e7c2351c06b0314967d87c9cc0c54176b5850a94e65c5b",
        "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54",
    ),
)
REVIEWED_LOGICAL_PIPELINE_HASHES[
    "src/engine/infrastructure/startup_validation_code_context.py"
] = "8a5d817a90a9176ca5383fab0477583fe0d3d8ceef5e42c19010f4b4fea270bf"
REVIEWED_LOGICAL_PIPELINE_PAIRS[
    "src/engine/infrastructure/startup_validation_code_context.py"
] = tuple(
    (old, "8a5d817a90a9176ca5383fab0477583fe0d3d8ceef5e42c19010f4b4fea270bf")
    for old, _ in REVIEWED_POSTCLOSE_REPAIR_PAIRS[
        "src/engine/infrastructure/startup_validation_code_context.py"
    ]
) + (
    (
        "01c1d63084444119e0de2589099f20e758758d3699d0ffb59a43a3f76e5fab8c",
        "8a5d817a90a9176ca5383fab0477583fe0d3d8ceef5e42c19010f4b4fea270bf",
    ),
)
# Exact actual selected source20 producer before the closed-reader repair.
REVIEWED_LOGICAL_PIPELINE_PAIRS["src/engine/automation/main_stop_postclose.py"] = (
    (
        "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
        "ad0eb4c9eea9b260fb63bed150ff8882671ae126500d005dc00af5f3361dd3ae",
    ),
)
# Native legacy gzip comparison retains issued research bytes and economics.
REVIEWED_LOGICAL_PIPELINE_HASHES[
    "src/engine/scalping/initial_quantity_refresh_evaluation.py"
] = "6b052913a8a88b6780257bbfef0de9bae5c961039608e1cfa1ed25ab0412053f"
REVIEWED_LOGICAL_PIPELINE_PAIRS[
    "src/engine/scalping/initial_quantity_refresh_evaluation.py"
] = (
    (
        "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
        "6b052913a8a88b6780257bbfef0de9bae5c961039608e1cfa1ed25ab0412053f",
    ),
)
# A regenerated holding source must use current native publication semantics.
REVIEWED_LOGICAL_PIPELINE_HASHES["src/engine/runtime_approval_summary.py"] = (
    "a79d492129b3222a25711d1f1086b37c2714f50c3920b2973e74f518a97ef43d"
)
REVIEWED_LOGICAL_PIPELINE_PAIRS["src/engine/runtime_approval_summary.py"] = (
    (
        "91dbb00d92f0aeb51de17f92dc0bea31591f1d41ad3bcab24579c8cb3c1dd14d",
        "a79d492129b3222a25711d1f1086b37c2714f50c3920b2973e74f518a97ef43d",
    ),
)
REVIEWED_LOGICAL_PIPELINE_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_LOGICAL_PIPELINE_HASHES.get(os.path.normpath(trigger), sha)): {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_policy.py",
        "selector_sha256": REVIEWED_LOGICAL_PIPELINE_HASHES[
            "src/engine/scalping/initial_quantity_policy.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_LOGICAL_PIPELINE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_LOGICAL_PIPELINE_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_LOGICAL_PIPELINE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_POSTCLOSE_REPAIR_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_LOGICAL_PIPELINE_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]

# Exact immutable historical-diagnostic successor. Native archived policy/PID
# validation affects report re-audit only; runtime policy gates stay strict.
REVIEWED_HISTORICAL_RESOLUTION_HASHES = {
    "src/engine/scalping/micro_reversion/storage_maintenance.py": "61282651dcdf8bda3a4311855c3e7d10b500f1f8ac3fbaef2d5a66b5f4bcc514",
    "src/engine/compress_db_backfilled_files.py": "501159d87c7901b2a9edb6e7cd8a04d99ef6c15aae12577f9344078cf76ace3f",
    "src/engine/automation/main_trailing_source_store.py": "e9f596c589348c1090c54eb971ede6497f20d2ccb1a0fb45340b05797fd1e2b8",
    "src/engine/scalping/holding_profit_exit_semantics.py": "c3c2d58e97c99f24e37001622874ec294b4e8424e3dc22052495f35ec564b93a",
    "src/engine/holding_exit_sentinel.py": "a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb",
    "src/engine/error_detectors/artifact_freshness.py": "5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "81a69a5f6a4d512ab7578b196fcddcf08d56ceb791ee8d2d1d3a9bdfdb926327",
}
REVIEWED_HISTORICAL_RESOLUTION_PAIRS = {
    "src/engine/scalping/micro_reversion/storage_maintenance.py": (
        (
            "881d8a0d6e90dd73b753f73d28d3f8f1004edfc0ededf0928bfee8ef1397f098",
            "61282651dcdf8bda3a4311855c3e7d10b500f1f8ac3fbaef2d5a66b5f4bcc514",
        ),
    ),
    "src/engine/compress_db_backfilled_files.py": (
        (
            "3d1f34d4f8128e6e9b0b1aa9a3e0095bef1394314a731bd8a9c1eec8ea816f7c",
            "501159d87c7901b2a9edb6e7cd8a04d99ef6c15aae12577f9344078cf76ace3f",
        ),
    ),
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "aca2d7dda4c8eda53f6634a73b133090e73c511cc62973584f31633245edd850",
            "e9f596c589348c1090c54eb971ede6497f20d2ccb1a0fb45340b05797fd1e2b8",
        ),
    ),
    "src/engine/scalping/holding_profit_exit_semantics.py": (
        (
            "586d26b7c6a9bd7041477f490c1f897f3d305d7dd07b2d56af3e368221af29de",
            "c3c2d58e97c99f24e37001622874ec294b4e8424e3dc22052495f35ec564b93a",
        ),
        (
            "7512700df7e7d3bf705ec3e5d866bf9b916e564d60312fa3918f950c34431b78",
            "c3c2d58e97c99f24e37001622874ec294b4e8424e3dc22052495f35ec564b93a",
        ),
        (
            "e76d509fa67cb46100d1fffd1b272fbc3355b3c729604a348e22f653f8b0d269",
            "c3c2d58e97c99f24e37001622874ec294b4e8424e3dc22052495f35ec564b93a",
        ),
    ),
    "src/engine/holding_exit_sentinel.py": (
        (
            "5bc00325005b6d4346dc896c21741cec0e61fcd9904c6c947ae7774ce5e031e4",
            "a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb",
        ),
    ),
    "src/engine/error_detectors/artifact_freshness.py": (
        (
            "47897e387407c5d6472735463107d8e0ce7697aededa723c724973e4efc173a4",
            "5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6",
        ),
        (
            "bc6c903c8a9ea08026103101bcefcaf8e18ea5a4e707408787bc26a15ebd150a",
            "5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6",
        ),
        (
            "f8955d1d5f8fc807d0f1772e6a21ac682ff800b6668a00d551a1f4a8fd25983e",
            "5badbc45d86f2426ce060c7420f2f1f428dd262a2d9c2ea14f41454c89d2d1b6",
        ),
    ),
    "src/engine/scalping/initial_quantity_monitor_projection.py": tuple(
        (before, "81a69a5f6a4d512ab7578b196fcddcf08d56ceb791ee8d2d1d3a9bdfdb926327")
        for before in (
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
            "28e2d8b4e06be95c5f91b36298cfe8015f0f2474419964c60f1db4fcc267a21f",
            "8dce560b2434f30912b39330c42932debfb4671d3b3689c10226ddcd18d083c4",
        )
    ),
}
REVIEWED_HISTORICAL_RESOLUTION_DEPENDENCY_VARIANTS = {
    (
        trigger,
        REVIEWED_HISTORICAL_RESOLUTION_HASHES.get(os.path.normpath(trigger), sha),
    ): {
        **value,
        "selector_path": "src/engine/scalping/holding_profit_exit_semantics.py",
        "selector_sha256": REVIEWED_HISTORICAL_RESOLUTION_HASHES[
            "src/engine/scalping/holding_profit_exit_semantics.py"
        ],
        "dependencies": {
            **{
                name: REVIEWED_HISTORICAL_RESOLUTION_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in value["dependencies"].items()
            },
            **REVIEWED_HISTORICAL_RESOLUTION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_HISTORICAL_RESOLUTION_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_LOGICAL_PIPELINE_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _trigger_sha,
), _variant in REVIEWED_HISTORICAL_RESOLUTION_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_trigger_sha] = _variant[
        "dependencies"
    ]


# Exact finalization suffix and pending historical notification successor.
# Preserve the issued historical-resolution profile for predecessor receipts.
REVIEWED_FINALIZATION_HEALTH_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "d3a344923d590f55cdd08ed14c3eba67de149c8e5fef1c89a28fba7d00a68cd7",
    "src/engine/automation/postclose_finalization_generation.py": "e4454cb3da9c7542177cb49f30579970978717538baae4fd3bab9dfbdf269b63",
    "deploy/run_postclose_finalization.sh": "f0256308c44cad1f30d3f1f2bea43192f797c72aa93c3970d9ec65ef8c712fe9",
    "src/engine/scalping/entry_machine_source_recovery.py": "43fd0b6edf45ce92a9ff07364683385804445296608c63455ad5f9b9c57cba55",
    "src/engine/monitoring/entry_attempt_identity.py": "5bd57a8d235e360ba5a9ea953256164722c267931e7d8caf55816c3a819b7d63",
    "src/engine/buy_funnel_sentinel.py": "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1",
    "src/engine/monitoring/sentinel_source_window.py": "876d89e26f8fbf819417357d5065bbc213c1e41e479f1b0f4c8f4ec8dc3a7572",
    "src/engine/sentinel_event_cache.py": "7367cf13033fc3ed8134b504d65da53fa6921098b9640b2b9a619b85ae6367c3",
    "src/engine/monitoring/sentinel_summary_contract.py": "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
    "src/engine/automation/ordered_intraday_deploy.py": "85671b2217e554dd573d23fe8616ce177726bcfdd771bc3893a37dae2b19f9b6",
}
REVIEWED_FINALIZATION_HEALTH_PAIRS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "d3a344923d590f55cdd08ed14c3eba67de149c8e5fef1c89a28fba7d00a68cd7",
        ),
        (
            "9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1",
            "d3a344923d590f55cdd08ed14c3eba67de149c8e5fef1c89a28fba7d00a68cd7",
        ),
    ),
    "src/engine/automation/postclose_finalization_generation.py": (
        (
            "d4d4d0819c4a1845baf10bcaf7935137aa9d925544a374a8c47ead6259f51e43",
            "e4454cb3da9c7542177cb49f30579970978717538baae4fd3bab9dfbdf269b63",
        ),
        (
            "1ac7c5d9a4269f73a9a9f82656d22a277689813b32c94b3a526e0b37452d3041",
            "e4454cb3da9c7542177cb49f30579970978717538baae4fd3bab9dfbdf269b63",
        ),
    ),
    "deploy/run_postclose_finalization.sh": (
        (
            "719a2f90670011ae9d8411609fe9f0ea51c70a47656a9028768a00745d227766",
            "f0256308c44cad1f30d3f1f2bea43192f797c72aa93c3970d9ec65ef8c712fe9",
        ),
    ),
    "src/engine/scalping/entry_machine_source_recovery.py": (
        (
            "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "43fd0b6edf45ce92a9ff07364683385804445296608c63455ad5f9b9c57cba55",
        ),
    ),
    "src/engine/monitoring/entry_attempt_identity.py": (
        (
            "a18c0b96de81dcb17f6717703f5e5ebc46c29a579e7e85f257c5d6f0251d7f5e",
            "5bd57a8d235e360ba5a9ea953256164722c267931e7d8caf55816c3a819b7d63",
        ),
    ),
    "src/engine/buy_funnel_sentinel.py": (
        (
            "6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993",
            "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1",
        ),
    ),
    "src/engine/monitoring/sentinel_source_window.py": (
        (
            "927073bc71d5c4dab4fa903924d31ccd57aa3f4bedf52ec3166103ec9f080f71",
            "876d89e26f8fbf819417357d5065bbc213c1e41e479f1b0f4c8f4ec8dc3a7572",
        ),
    ),
    "src/engine/sentinel_event_cache.py": (
        (
            "3254bb5044b610330e27ec59d6fd3fe59c58b780013887a82871301f0cb72e9a",
            "7367cf13033fc3ed8134b504d65da53fa6921098b9640b2b9a619b85ae6367c3",
        ),
    ),
    "src/engine/monitoring/sentinel_summary_contract.py": (
        (
            "63966b549566771cc7bff12ea742fc0017bfc37c0c00ac648d6dfd63bfdc06d9",
            "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
        ),
        (
            "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
            "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
        ),
    ),
    "src/engine/automation/ordered_intraday_deploy.py": (
        (
            "4345d7b8ea95b13b7c7862bc54c24b9add92e6da79806190308bfb17b15ba3b9",
            "85671b2217e554dd573d23fe8616ce177726bcfdd771bc3893a37dae2b19f9b6",
        ),
        (
            "2b25345a2cc0711a42a2a39898961c157dfb927c0b1eb4929b74fe3c624af626",
            "85671b2217e554dd573d23fe8616ce177726bcfdd771bc3893a37dae2b19f9b6",
        ),
    ),
}
REVIEWED_FINALIZATION_HEALTH_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_FINALIZATION_HEALTH_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_FINALIZATION_HEALTH_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_FINALIZATION_HEALTH_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_HISTORICAL_RESOLUTION_DEPENDENCY_VARIANTS.items()
}


# Exact native invalidation observation successor; original policy/FSM guards stay pinned.
# Earlier issued profiles remain readable. A partial producer/consumer update is invalid.
REVIEWED_NATIVE_INVALIDATION_HASHES = {
    "src/engine/monitoring/runtime_performance.py": "626ae4d2db569edce63082aab86965872b57f0ec9daacca767ec4e83f84e36be",
    "src/engine/scalping/reversal_source_diagnostics.py": "ad9fc4f2eeac858435cae48f9707275eabce46c8f48fee38e40029ea4a843c93",
    "src/engine/scalping/entry_machine_source_recovery.py": "a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5",
    "src/engine/ai_engine_openai.py": "4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162",
    "src/engine/scalping/zero_base_probe.py": "c8e671c81375910971a7b8f75d1e2d6162a3411906cfbd3a3a2e076c99837fc7",
    "src/scanners/scalping_scanner.py": "ea6188939ecc11462923d4746d27d38042aadd06f4dcd02d14cea7b2e5f8123b",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
}
REVIEWED_NATIVE_INVALIDATION_PAIRS = {
    "src/engine/monitoring/runtime_performance.py": (
        (
            "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
            "626ae4d2db569edce63082aab86965872b57f0ec9daacca767ec4e83f84e36be",
        ),
    ),
    "src/engine/scalping/reversal_source_diagnostics.py": (
        (
            "bf7dd538048888ce9793ccdf39a6c5c4a463c9e3379f4c3c5c1a09173f543eb8",
            "ad9fc4f2eeac858435cae48f9707275eabce46c8f48fee38e40029ea4a843c93",
        ),
    ),
    "src/engine/scalping/entry_machine_source_recovery.py": (
        (
            "43fd0b6edf45ce92a9ff07364683385804445296608c63455ad5f9b9c57cba55",
            "a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5",
        ),
        (
            "89845a56178c7b2a7322317a5f0c3f9ea2344b0514efc7241d0c5a846acea712",
            "a78c70c5c49169ccb57069df7a524a540a33b615617a49195ddbc343ff9602a5",
        ),
    ),
    "src/engine/ai_engine_openai.py": (
        (
            "703bc5e36bf23a02caf78a3fa8f9251e202979048e4ed1cd64aafed57e732d07",
            "4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162",
        ),
        (
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
            "4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162",
        ),
    ),
    "src/engine/scalping/zero_base_probe.py": (
        (
            "214e80199cc4f9d56699aba376e24d325d0396abd7662a2f9ae5f788da66fc20",
            "c8e671c81375910971a7b8f75d1e2d6162a3411906cfbd3a3a2e076c99837fc7",
        ),
        (
            "c91d31899343d4381a30edaa82046a65ace8cb6a55f33c03cd5851d9cd1e689f",
            "c8e671c81375910971a7b8f75d1e2d6162a3411906cfbd3a3a2e076c99837fc7",
        ),
    ),
    "src/scanners/scalping_scanner.py": (
        (
            "0473ce423dbae36455bc50bf94549b991b904a86f5f9c00acc20f4766cc48c75",
            "ea6188939ecc11462923d4746d27d38042aadd06f4dcd02d14cea7b2e5f8123b",
        ),
        (
            "3280979b86c4bb10231b7886f591aba239c453b3e37d1ba79b8c2fdb1d4f477f",
            "ea6188939ecc11462923d4746d27d38042aadd06f4dcd02d14cea7b2e5f8123b",
        ),
    ),
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        (
            "9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1",
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
        ),
        (
            "b2ed455255bc7659d2959a5c6012fe052206de588f1932d57dde2e376d2fad18",
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
        ),
        (
            "d3a344923d590f55cdd08ed14c3eba67de149c8e5fef1c89a28fba7d00a68cd7",
            "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
        ),
    ),
}
REVIEWED_NATIVE_INVALIDATION_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_NATIVE_INVALIDATION_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_NATIVE_INVALIDATION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_NATIVE_INVALIDATION_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_FINALIZATION_HEALTH_DEPENDENCY_VARIANTS.items()
}


# Exact revived fixed-watch wait producer and current capability reader.
REVIEWED_FIXED_WAIT_HASHES = {
    "src/engine/sniper_state_handlers.py": "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
    "src/engine/monitoring/policy_generation_code_handoff.py": "a398aec3dba6e1f5ece0d53955565f49f9673423c9a215d9c394defa3b62ed9d",
}
REVIEWED_FIXED_WAIT_PAIRS = {
    "src/engine/sniper_state_handlers.py": (
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
        ),
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        (
            "905dd6a05df9f19fac25292a3a1e7fe579281e4aeabd84d4965855f9fef928b1",
            "a398aec3dba6e1f5ece0d53955565f49f9673423c9a215d9c394defa3b62ed9d",
        ),
        (
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "a398aec3dba6e1f5ece0d53955565f49f9673423c9a215d9c394defa3b62ed9d",
        ),
        (
            "78b3d4a55b89ccd784bc2120d7caf0cc47b65656ca75d4cb3bcd20e2edc6ac1a",
            "a398aec3dba6e1f5ece0d53955565f49f9673423c9a215d9c394defa3b62ed9d",
        ),
    ),
}
REVIEWED_FIXED_WAIT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_state_handlers.py",
        "selector_sha256": REVIEWED_FIXED_WAIT_HASHES[
            "src/engine/sniper_state_handlers.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_FIXED_WAIT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_FIXED_WAIT_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_NATIVE_INVALIDATION_DEPENDENCY_VARIANTS.items()
}


# Exact native receipt handoff and bounded owned inventory recovery.
REVIEWED_ENTRY_RECEIPT_HASHES = {
    "src/engine/sniper_state_handlers.py": "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
    "src/engine/sniper_execution_receipts.py": "26b75b658f2fbb8f0411fed3d03a5a1f26923a2ad6d0610fa550aaf9a0ad4b51",
    "src/engine/sniper_sync.py": "95d5aab3d869cc3c49b8b4d416812603f767468e050277b11e3da89b4601b103",
    "src/engine/monitoring/policy_generation_code_handoff.py": "af5457739037ba9d29d39764dcdbd22bbe2377ae807792c30736f9d02f91b09f",
}
REVIEWED_ENTRY_RECEIPT_PAIRS = {
    "src/engine/sniper_state_handlers.py": (
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
        ),
        (
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
        ),
    ),
    "src/engine/sniper_execution_receipts.py": (
        (
            "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
            "26b75b658f2fbb8f0411fed3d03a5a1f26923a2ad6d0610fa550aaf9a0ad4b51",
        ),
        (
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
            "26b75b658f2fbb8f0411fed3d03a5a1f26923a2ad6d0610fa550aaf9a0ad4b51",
        ),
    ),
    "src/engine/sniper_sync.py": (
        (
            "baed080aaa9dd6708f1999ed4a811a758df2bb683449a773e5418303affd4f34",
            "95d5aab3d869cc3c49b8b4d416812603f767468e050277b11e3da89b4601b103",
        ),
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        (
            "905dd6a05df9f19fac25292a3a1e7fe579281e4aeabd84d4965855f9fef928b1",
            "af5457739037ba9d29d39764dcdbd22bbe2377ae807792c30736f9d02f91b09f",
        ),
        (
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "af5457739037ba9d29d39764dcdbd22bbe2377ae807792c30736f9d02f91b09f",
        ),
        (
            "78b3d4a55b89ccd784bc2120d7caf0cc47b65656ca75d4cb3bcd20e2edc6ac1a",
            "af5457739037ba9d29d39764dcdbd22bbe2377ae807792c30736f9d02f91b09f",
        ),
        (
            "a398aec3dba6e1f5ece0d53955565f49f9673423c9a215d9c394defa3b62ed9d",
            "af5457739037ba9d29d39764dcdbd22bbe2377ae807792c30736f9d02f91b09f",
        ),
    ),
}
REVIEWED_ENTRY_RECEIPT_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_execution_receipts.py",
        "selector_sha256": REVIEWED_ENTRY_RECEIPT_HASHES[
            "src/engine/sniper_execution_receipts.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_RECEIPT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_RECEIPT_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_FIXED_WAIT_DEPENDENCY_VARIANTS.items()
}


# Preserve the deployed receipt profile; require its exact durable-identity successor.
REVIEWED_BUY_IDENTITY_HASHES = {
    "src/engine/monitoring/policy_generation_code_handoff.py": "86b6ea98d0af89360c350f24dc9771441c9332c22354059ae7d5dc1a7b2ac3e4",
    "src/engine/sniper_sync.py": "2a2cdc2f144bbe2abd7649b4c4b9f4a6ff50ae751ab3e978699c2da49a06199d",
}
REVIEWED_BUY_IDENTITY_PAIRS = {
    name: tuple(
        dict.fromkeys(
            (old, current)
            for old in [
                *(pair[0] for pair in REVIEWED_ENTRY_RECEIPT_PAIRS[name]),
                REVIEWED_ENTRY_RECEIPT_HASHES[name],
            ]
        )
    )
    for name, current in REVIEWED_BUY_IDENTITY_HASHES.items()
}
REVIEWED_BUY_IDENTITY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/sniper_sync.py",
        "selector_sha256": REVIEWED_BUY_IDENTITY_HASHES["src/engine/sniper_sync.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_BUY_IDENTITY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_BUY_IDENTITY_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_RECEIPT_DEPENDENCY_VARIANTS.items()
}


# Exact cooperative collector-close generation; retain every issued predecessor.
REVIEWED_COLLECTOR_CLOSE_HASHES = {
    "src/bot_main.py": "468b479d71b728715f4638614f50d4c1fa9f6f6d32416a21200a395392866302",
    "src/engine/automation/ordered_intraday_deploy.py": "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
    "src/engine/infrastructure/restart_requests.py": "b94b2c81039bd6299c5b2062da89dfba38fb70a3d9ca4ee875dd92b7a2a1c7b9",
    "src/engine/kiwoom_sniper_v2.py": "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
    "src/engine/kiwoom_websocket.py": "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
    "src/engine/scalping/continuous_reversal_source.py": "fb3d91a378457c244a805a49183572f74f3c4541cb3efdca4aa9f3c1a52df082",
    "src/engine/scalping/micro_reversion/canary_monitor.py": "1a767cc4e34ac8add1ec4318e305317f6faa35c469951dd422b45ec814258891",
    "src/engine/scalping/micro_reversion/forward_collector.py": "975d0b0061398a488244c80e869336a4aaac14e37d653b57c8115b83382e465e",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "189b61810654f59055c0dcf863c8e3e1bf17fc308f624b4feac09808676d7e7c",
}
REVIEWED_COLLECTOR_CLOSE_PAIRS = {
    "src/bot_main.py": (
        (
            "a2e8ec8578bb6b52cc91348584a8c4627fdc06412dc505a71c2c9ebf8f6bd526",
            "468b479d71b728715f4638614f50d4c1fa9f6f6d32416a21200a395392866302",
        ),
        (
            "d98fbcddf8f3d2735385fcb92f1d5d43a631bc1b7ab11e2d5c7311c838ae969a",
            "468b479d71b728715f4638614f50d4c1fa9f6f6d32416a21200a395392866302",
        ),
        (
            "f8c2f1626d60502234c002bb75f99fb6e092c620ad2ae6ae87eac6db76da1f0c",
            "468b479d71b728715f4638614f50d4c1fa9f6f6d32416a21200a395392866302",
        ),
    ),
    "src/engine/automation/ordered_intraday_deploy.py": (
        (
            "2b25345a2cc0711a42a2a39898961c157dfb927c0b1eb4929b74fe3c624af626",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
        (
            "4345d7b8ea95b13b7c7862bc54c24b9add92e6da79806190308bfb17b15ba3b9",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
        (
            "48b9376c7683466e5d0e195ac971c93d1ed1cd442e9968eddacc2031e38e75a9",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
        (
            "85671b2217e554dd573d23fe8616ce177726bcfdd771bc3893a37dae2b19f9b6",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
        (
            "9b16f12badd137f866cd77b09e356ef75e70ce40fa1a1455c16581fea98fbea0",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
        (
            "d67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90",
            "8026643f4f2de6ff94f39e4e5f2ad9bbfd5dae11740a603b7e6725dcb1ccd80d",
        ),
    ),
    "src/engine/infrastructure/restart_requests.py": (
        (
            "1f0152ce292b77d466fc04be58da263e194e5c7e9ab344de2ab13de97a0954b0",
            "b94b2c81039bd6299c5b2062da89dfba38fb70a3d9ca4ee875dd92b7a2a1c7b9",
        ),
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "2498fb498de2d796fd9abc695caad99ccc61b914c2999a640d88f3f5c96f8dac",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "3b35fc7133fc87cf5b23ae6f03c3272b9b78b61840f3bc1c6f0e84db5ba8def4",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "44133e57f1c20521b80cfa5fa1e7dadb7c89b010ab461cce3959fd1ba6fd4997",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "4454e6051c47ef959f0b8201526901fe5bd2dfff3b25aaa5593605cf7f53cd33",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "45a139a2ed413afb888cd244ae73d60d5f312b503a8e1c54cc1ce599b048d279",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "4cbd06363b1156761fd748c51ac9fbb4f54e69b64771f9f86e6770bba5ce177c",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "51280b79c7eee85279c9d649c76888cb03954f73c18c1e0ba41a863c4ea8a0a1",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "522bc4a71a1375144db798b2e451fcee03a44e80d57323c7996fa365bf20c71c",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "b7cec7cbec7082c9c98a8861638485432ee20346ce687dbd06d82196551548bb",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "d19c471856511889cf9728a3fee7f13c4bcdfce29566dbea80ae5b581d9e8777",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
        (
            "e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e",
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
        ),
    ),
    "src/engine/kiwoom_websocket.py": (
        (
            "5016a58492f59a0728d9bbf979d76cc59a10de4681e92a5fcac21bf6c1cffde2",
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
        ),
        (
            "63293b9abbd511ade33dccca9598eba3e0e32e0eefa06c33a2ba5c411c67a130",
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
        ),
        (
            "9aca69dc06a8fffee8999d8c8c2cdece1760e9fdb21e3c8eddf8cda87a6da9e2",
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
        ),
        (
            "b760d5aa69b20f31060a00a5dc81670d29f1c7760c19a775499609d90e867363",
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
        ),
        (
            "e60b5435694e74fc9afa65101b4b407af4da365d07dbac0b38263c66bf8e8921",
            "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3",
        ),
    ),
    "src/engine/scalping/continuous_reversal_source.py": (
        (
            "401ff28d4f2b20db778768aa10486bffdac01466480e7429a428d3fa14705b02",
            "fb3d91a378457c244a805a49183572f74f3c4541cb3efdca4aa9f3c1a52df082",
        ),
        (
            "96f1edc13538616832ec4270064afcc9a6bacab8274903cd57b2838573a1155d",
            "fb3d91a378457c244a805a49183572f74f3c4541cb3efdca4aa9f3c1a52df082",
        ),
    ),
    "src/engine/scalping/micro_reversion/canary_monitor.py": (
        (
            "d1d6bec4b4ee96988345b87c8c1d8b8384b813693bf66a13fa98b50592245db0",
            "1a767cc4e34ac8add1ec4318e305317f6faa35c469951dd422b45ec814258891",
        ),
    ),
    "src/engine/scalping/micro_reversion/forward_collector.py": (
        (
            "e4bbf5c481058e0a8eb31927347340154265d20d59c1d3c711faebaf4e8a3af6",
            "975d0b0061398a488244c80e869336a4aaac14e37d653b57c8115b83382e465e",
        ),
    ),
    "src/engine/scalping/micro_reversion/observer_source_quality.py": (
        (
            "a7959ab7ad37e4b9d70f5448803424e0a8c05a368d138dc4a14571b0c372b410",
            "189b61810654f59055c0dcf863c8e3e1bf17fc308f624b4feac09808676d7e7c",
        ),
    ),
}
REVIEWED_COLLECTOR_CLOSE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/micro_reversion/forward_collector.py",
        "selector_sha256": REVIEWED_COLLECTOR_CLOSE_HASHES[
            "src/engine/scalping/micro_reversion/forward_collector.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_COLLECTOR_CLOSE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_COLLECTOR_CLOSE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_BUY_IDENTITY_DEPENDENCY_VARIANTS.items()
}


# First transition consumes the already sealed native market-close epoch.
# Preserve the earlier cooperative successor as an issued compatibility reader.
REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES = {
    **REVIEWED_COLLECTOR_CLOSE_HASHES,
    "src/engine/automation/ordered_intraday_deploy.py": "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
}
REVIEWED_COLLECTOR_FIRST_TRANSITION_PAIRS = {
    name: tuple(
        dict.fromkeys(
            (old, current)
            for old in [
                *(pair[0] for pair in REVIEWED_COLLECTOR_CLOSE_PAIRS[name]),
                REVIEWED_COLLECTOR_CLOSE_HASHES[name],
            ]
        )
    )
    for name, current in REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES.items()
}
REVIEWED_COLLECTOR_FIRST_TRANSITION_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/automation/ordered_intraday_deploy.py",
        "selector_sha256": REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES[
            "src/engine/automation/ordered_intraday_deploy.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COLLECTOR_CLOSE_DEPENDENCY_VARIANTS.items()
}


# Exact delay cohort successor. Existing issued-policy selection stays unchanged;
# only a separately generated, native-bound policy may join identical parents.
REVIEWED_DELAY_MACHINE_PARENT_HASHES = {
    "src/engine/automation/pre_submit_delay_partitioned_research.py": "481cf3053929d89e4679dd33be92cc5c93f7c0118e62d86fc814cd324ef00507",
    "src/engine/automation/pre_submit_delay_research_review.py": "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
    "src/engine/automation/pre_submit_delay_situation_projection.py": "572758cce22a8ba5ac6159ad9b670c3ac45d1112c30fc31907f8eb0d02ca7454",
}
REVIEWED_DELAY_MACHINE_PARENT_PAIRS = {
    "src/engine/automation/pre_submit_delay_partitioned_research.py": (
        (
            "df3407a49b012152ee894db86b5052a681ccf6122db5c459cf743747e8f95ba6",
            "481cf3053929d89e4679dd33be92cc5c93f7c0118e62d86fc814cd324ef00507",
        ),
        (
            "cbc0a519c2126948f7c68982c86bae7678c54db65c687ed960563cf76053e6e3",
            "481cf3053929d89e4679dd33be92cc5c93f7c0118e62d86fc814cd324ef00507",
        ),
    ),
    "src/engine/automation/pre_submit_delay_research_review.py": (
        (
            "6cf9e50d915da95f0cd469b2a7d36ede3754cba6c237f69ab0fdfcf565f968d6",
            "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
        ),
        (
            "159b04fa4b5486e43feba9ca2dee73b7e1f9052926f729cb6169ff0ff89ad2ac",
            "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
        ),
    ),
    "src/engine/automation/pre_submit_delay_situation_projection.py": (
        (
            "c77e565c1f29b64551e690f0e0901226c73baba2c53a61b6c49239be76c39f28",
            "572758cce22a8ba5ac6159ad9b670c3ac45d1112c30fc31907f8eb0d02ca7454",
        ),
    ),
}
# Quantity capture and offline context projection repair; trading rules are
# unchanged. Pin one reviewed successor while preserving issued generations.
REVIEWED_QUANTITY_CAPTURE_HASHES = {
    "src/engine/automation/main_trailing_source_reuse.py": "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
    "src/engine/automation/main_trailing_completed_store.py": "a5ebc1ab43334b5d8b3d418c6f16406187258fb6caffc868a5da23efa9d76f0f",
    "src/engine/monitoring/policy_generation_code_handoff.py": "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
    "src/engine/lifecycle/research_json_stream.py": "8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201",
    "src/engine/scalping/initial_quantity_cap_observation.py": "b812ebdb125283b7f2e80e840edfb8f84fbd2160b73428bd5ae319c1f3c38560",
    "src/engine/scalping/initial_quantity_policy.py": "c9496cee9ce0305a75fd0e1c2df93370e18ea4792b61b3d47d8de9937aaef4d4",
    "src/engine/scalping/initial_quantity_source_cache.py": "f76427a4e0c75e5062149daff971362962acdc22c599bac957a5dfd3f4c04a70",
    "src/engine/sniper_state_handlers.py": "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
    "src/utils/pipeline_event_logger.py": "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
}
REVIEWED_QUANTITY_CAPTURE_PAIRS = {
    "src/engine/automation/main_trailing_source_reuse.py": (
        (
            "272f0753cce9fc43324063a2d690394e844630f6eab8da7dace87596620ac0ab",
            "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
        ),
        (
            "c190554546468617b2963e2ba013473e992f4d4ad638a5f4aee2f71027bc58ef",
            "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
        ),
    ),
    "src/engine/automation/main_trailing_completed_store.py": (
        (
            "2fc12700ccf64fa03667a0a859e13dc40515e932cc68da23ed9b3d962bdfdd5a",
            "a5ebc1ab43334b5d8b3d418c6f16406187258fb6caffc868a5da23efa9d76f0f",
        ),
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        (
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
        ),
        (
            "86b6ea98d0af89360c350f24dc9771441c9332c22354059ae7d5dc1a7b2ac3e4",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
        ),
        (
            "905dd6a05df9f19fac25292a3a1e7fe579281e4aeabd84d4965855f9fef928b1",
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
        ),
    ),
    "src/engine/lifecycle/research_json_stream.py": (
        (
            "1ea671f8ba5b5397257c2d1da513dee653b05379133073d1412ee4edf7a07a11",
            "8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201",
        ),
        (
            "53bd6a0cec6435ff0cfb399ad75fc9edd0b479463c06dea77bc5cae5e59db4b6",
            "8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201",
        ),
    ),
    "src/engine/scalping/initial_quantity_cap_observation.py": (
        (
            "11d5fe453033bfdc158d64f423f2d299443401b6782955440d643079ad864667",
            "b812ebdb125283b7f2e80e840edfb8f84fbd2160b73428bd5ae319c1f3c38560",
        ),
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
            "c9496cee9ce0305a75fd0e1c2df93370e18ea4792b61b3d47d8de9937aaef4d4",
        ),
        (
            "4567eed7de944395133eb6ebc975c823cf3840e6abe9424877455130feb55c87",
            "c9496cee9ce0305a75fd0e1c2df93370e18ea4792b61b3d47d8de9937aaef4d4",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
            "f76427a4e0c75e5062149daff971362962acdc22c599bac957a5dfd3f4c04a70",
        ),
        (
            "353795e63675a34743f1bdf0823f684cbdcdd472cdf12790dc17896e1aa107db",
            "f76427a4e0c75e5062149daff971362962acdc22c599bac957a5dfd3f4c04a70",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
        ),
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
        ),
        (
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
        ),
    ),
    "src/utils/pipeline_event_logger.py": (
        (
            "02d713d72647ce18e49c13f40843415611260a4fd5ba6be34712d6bfb9b83416",
            "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
        ),
        (
            "fde49c9a27dfc5c858d765353a0a898ac45728d57ecfa0526c4a6df4fef4c99e",
            "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
        ),
    ),
}
REVIEWED_QUANTITY_CAPTURE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_cap_observation.py",
        "selector_sha256": REVIEWED_QUANTITY_CAPTURE_HASHES[
            "src/engine/scalping/initial_quantity_cap_observation.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_QUANTITY_CAPTURE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_QUANTITY_CAPTURE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COLLECTOR_FIRST_TRANSITION_DEPENDENCY_VARIANTS.items()
}


# Prepared research stages keep the incumbent reference and bind one exact reader.
# Evidence: existing quantity producer/consumer review, 2026-10-21.
REVIEWED_QUANTITY_STAGE_HASHES = {
    "src/engine/scalping/initial_quantity_policy.py": "9b18c05ff050cb8d182b03296ee71f30b8efa867341ba47b04a2f06dc55f87c7",
    "src/engine/error_detectors/artifact_freshness.py": "edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6",
}
REVIEWED_QUANTITY_STAGE_PAIRS = {
    name: tuple(
        (before, REVIEWED_QUANTITY_STAGE_HASHES[name])
        for before in dict.fromkeys(
            [
                value
                for pair in REVIEWED_QUANTITY_CAPTURE_PAIRS.get(name, ())
                for value in pair
            ]
        )
    )
    for name in REVIEWED_QUANTITY_STAGE_HASHES
}
REVIEWED_QUANTITY_STAGE_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/initial_quantity_policy.py",
        "selector_sha256": REVIEWED_QUANTITY_STAGE_HASHES[
            "src/engine/scalping/initial_quantity_policy.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_QUANTITY_STAGE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_QUANTITY_STAGE_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_QUANTITY_CAPTURE_DEPENDENCY_VARIANTS.items()
}


# Exact nonfixed metadata and work-conserving scheduling successor.
# Historical profiles remain independently verifiable; no policy values change.
REVIEWED_NONFIXED_CAPACITY_HASHES = {
    "src/scanners/zero_base_discovery_queue.py": "46422619816d9ccffd272a0bd63a80f2265c61000c574bc21e51c7c1e455eda6",
    "src/scanners/zero_base_discovery_runtime.py": "dc058e9520482506a7659ae9cbefe1e7ce2a3ac0f2dde0b8b053742aec0535f4",
    "src/scanners/zero_base_discovery_source.py": "7cb5b73e5501feea78cafbff43ef21e671c267daeec0768ee692f64c2e4b199b",
    "src/utils/kiwoom_utils.py": "00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f",
}
REVIEWED_NONFIXED_CAPACITY_PAIRS = {
    "src/scanners/zero_base_discovery_queue.py": (
        (
            "9bbcaa6181f9a3f46d9c6c3328dc857e774d5fd7800f2e297bae5d3ea17cb7c8",
            "46422619816d9ccffd272a0bd63a80f2265c61000c574bc21e51c7c1e455eda6",
        ),
    ),
    "src/scanners/zero_base_discovery_runtime.py": (
        (
            "47347d90b4dad70233a55bca9dc282da20b14b3be4fda4090291ce1d7e66bb57",
            "dc058e9520482506a7659ae9cbefe1e7ce2a3ac0f2dde0b8b053742aec0535f4",
        ),
    ),
    "src/scanners/zero_base_discovery_source.py": (
        (
            "9d0f424e9a82cc2c29e08797c6fc9172875adeeabc94f429e0ded10df4da0cbc",
            "7cb5b73e5501feea78cafbff43ef21e671c267daeec0768ee692f64c2e4b199b",
        ),
    ),
    "src/utils/kiwoom_utils.py": (
        (
            "a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f",
            "00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f",
        ),
    ),
}
REVIEWED_NONFIXED_CAPACITY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/scanners/zero_base_discovery_queue.py",
        "selector_sha256": REVIEWED_NONFIXED_CAPACITY_HASHES[
            "src/scanners/zero_base_discovery_queue.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_NONFIXED_CAPACITY_HASHES,
            **{
                "src/engine/scalping/micro_reversion/economic_reference_owner.py": "ec0cbe43c548e77e2ccf81284a08bbc7faf16aa505ff16bf09b80aa9868b688b",
                "src/engine/scalping/micro_reversion/symbol_master.py": "f1bef46a5213a18eed07a1b81a390a6523f3baa84b72d6dea8602ed2e1e71dd4",
                "src/utils/jsonl_io.py": "c8e3058acdf08d411bfd19edee9cdfe3871bc0b004106038f449320727ab7fb1",
            },
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_NONFIXED_CAPACITY_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_QUANTITY_STAGE_DEPENDENCY_VARIANTS.items()
}


# Normal-exit source capture and holding-input repair; preserve issued generations.
# Existing stop/holding review, 2026-10-21. No trading thresholds change.
REVIEWED_HOLDING_INPUT_HASHES = {
    "src/database/db_manager.py": "263871b31390d03e14b3881c4edd09bb74f7fce42f142bd19afb5b0778d49ff8",
    "src/engine/kiwoom_sniper_v2.py": "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
    "src/engine/scalping/avg_down_rebound.py": "8248104e54c002e41a846c1b318adc8b86445934538256746e7404b72cc15e1f",
    "src/engine/scalping/holding_decision_context.py": "5d7577896850988b6419996a76db24344f7a612c59ecac339331ca2e841607d2",
    "src/engine/scalping/main_stop_quantity_source.py": "736226f72aabb1f7a1fe134d746e1f79139ae5ce3da52d83d49abb1d37483f36",
    "src/engine/scalping/main_stop_runtime_source.py": "6d097264784b2f7a1601c534a27d13c0647dee227bfa5e12bedb2a9471cd2344",
    "src/engine/sniper_state_handlers.py": "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
}
REVIEWED_HOLDING_INPUT_PAIRS = {
    "src/database/db_manager.py": (
        (
            "6577bc9847a7decace8ad701f2ea628e6f49e687e30296aa0c4c977212b82672",
            "263871b31390d03e14b3881c4edd09bb74f7fce42f142bd19afb5b0778d49ff8",
        ),
    ),
    "src/engine/kiwoom_sniper_v2.py": (
        (
            "2498fb498de2d796fd9abc695caad99ccc61b914c2999a640d88f3f5c96f8dac",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "3b35fc7133fc87cf5b23ae6f03c3272b9b78b61840f3bc1c6f0e84db5ba8def4",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "44133e57f1c20521b80cfa5fa1e7dadb7c89b010ab461cce3959fd1ba6fd4997",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "4454e6051c47ef959f0b8201526901fe5bd2dfff3b25aaa5593605cf7f53cd33",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "45a139a2ed413afb888cd244ae73d60d5f312b503a8e1c54cc1ce599b048d279",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "4cbd06363b1156761fd748c51ac9fbb4f54e69b64771f9f86e6770bba5ce177c",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "51280b79c7eee85279c9d649c76888cb03954f73c18c1e0ba41a863c4ea8a0a1",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "522bc4a71a1375144db798b2e451fcee03a44e80d57323c7996fa365bf20c71c",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "647f24d8805d0d9d6c1489df272b258706c7314111121e8660c01ee72930e713",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "6f1abc2ad7c532d693b832fb041ff519874ce141b52d2f1c724b445467440c0e",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "96319c0071dfce04980af151ff9e22b91352a704281bb727c8e68d604ee6aa20",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "ab335b38a3aff9362bd17a29fde787b425a4478f60e0d328c7b60553800cc21e",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "ac1bcb15d252715133c256970dabc03985522f4a2a6fced0ead54b75309481e8",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "b7cec7cbec7082c9c98a8861638485432ee20346ce687dbd06d82196551548bb",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "bb8cc6f224428a073f60826f8aa70e97d4b68b0383c907d681b8be5473a2d7c6",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "d19c471856511889cf9728a3fee7f13c4bcdfce29566dbea80ae5b581d9e8777",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "d3740c011a60c9a6214e2744e8a57da1767ea5608ccf6586c714df68d941e8da",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
        (
            "e1f43d4d08a0606db678c59f5755b94fbb976ef4ce55ece812ecc00e97c8973e",
            "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
        ),
    ),
    "src/engine/scalping/avg_down_rebound.py": (
        (
            "56475ad935418ebb1d335e750b4a0e6fcd5c7478eb6eeae6979511cfdf8ff4af",
            "8248104e54c002e41a846c1b318adc8b86445934538256746e7404b72cc15e1f",
        ),
    ),
    "src/engine/scalping/holding_decision_context.py": (
        (
            "783f95ab9cd3ef2813151949cdf6aa2c2ab6ed3a1443ae60d6600d21dcd52898",
            "5d7577896850988b6419996a76db24344f7a612c59ecac339331ca2e841607d2",
        ),
    ),
    "src/engine/scalping/main_stop_quantity_source.py": (
        (
            "dd49bd2d6543adfa0e653974e31c37be7aed752b6e279a58e33ceca846ea240e",
            "736226f72aabb1f7a1fe134d746e1f79139ae5ce3da52d83d49abb1d37483f36",
        ),
    ),
    "src/engine/scalping/main_stop_runtime_source.py": (
        (
            "fb32767aee777ed660ec0db018b5419e6f12f09a5644882425f79a954bd32978",
            "6d097264784b2f7a1601c534a27d13c0647dee227bfa5e12bedb2a9471cd2344",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
        (
            "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
        ),
    ),
}
REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES = {
    **REVIEWED_HOLDING_INPUT_HASHES,
    **{
        "src/engine/automation/pre_submit_delay_partitioned_research.py": "481cf3053929d89e4679dd33be92cc5c93f7c0118e62d86fc814cd324ef00507",
        "src/engine/automation/pre_submit_delay_research_review.py": "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
        "src/utils/pipeline_event_logger.py": "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
    },
}
REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_HOLDING_INPUT_HASHES.get(trigger, sha)): {
        **value,
        "selector_path": "src/engine/scalping/main_stop_runtime_source.py",
        "selector_sha256": REVIEWED_HOLDING_INPUT_HASHES[
            "src/engine/scalping/main_stop_runtime_source.py"
        ],
        "dependencies": {
            **{
                os.path.normpath(name): REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in value["dependencies"].items()
            },
            **REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_NONFIXED_CAPACITY_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _holding_input_sha,
), _variant in REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_holding_input_sha] = _variant[
        "dependencies"
    ]


# Post-sell source registration consumes the exact native route vocabulary.
# Unknown physical fill venue stays unresolved; issued source readers remain.
REVIEWED_POST_SELL_SOURCE_HASHES = {
    "src/engine/sniper_post_sell_feedback.py": "03026d2b252fa18fc5c36aaa9e1df7c9f3a0ae43ad2debc541882a78e8a9c275",
    "src/engine/sniper_state_handlers.py": "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
}
REVIEWED_POST_SELL_SOURCE_PAIRS = {
    "src/engine/sniper_post_sell_feedback.py": (
        (
            "8fcbf7de95acc2e5ba3121be0f20ece3bbefc7bd22fb57cc4cebe938115fc2d9",
            "03026d2b252fa18fc5c36aaa9e1df7c9f3a0ae43ad2debc541882a78e8a9c275",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
        (
            "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
        ),
    ),
}
REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_POST_SELL_SOURCE_HASHES.get(trigger, sha)): {
        **value,
        "selector_path": "src/engine/sniper_post_sell_feedback.py",
        "selector_sha256": REVIEWED_POST_SELL_SOURCE_HASHES[
            "src/engine/sniper_post_sell_feedback.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_POST_SELL_SOURCE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_POST_SELL_SOURCE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _post_sell_source_sha,
), _variant in REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_post_sell_source_sha] = _variant[
        "dependencies"
    ]


# Dated operator KRX/SOR defaults preserve raw exchange, quote and economic proof.
# All importing producers/readers are one exact dependency generation.
REVIEWED_OPERATOR_MARKET_HASHES = {
    "src/engine/automation/main_trailing_all_scope_research.py": "53d7acf04f8bcb37240a1a6572f8e0db2c8ac5e40029010f66e5419ce6d3aa89",
    "src/engine/holding_exit_observation_report.py": "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
    "src/engine/kiwoom_orders.py": "32e93c49a880e1f3a393ec0367cf1339dbc3ef00c689c821b45b159872c423d9",
    "src/engine/scalping/ai_action_outcome_calibration.py": "b239020a8231bc8e4d92f5fd8a21af1359c441336823b26e5ac52150459a904c",
    "src/engine/scalping/initial_quantity_policy.py": "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
    "src/engine/scalping/initial_quantity_source_cache.py": "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
    "src/engine/sniper_execution_receipts.py": "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
    "src/engine/sniper_post_sell_feedback.py": "fae77491c422f776a48a99da5d855b76e934bdd244055e4cdc44372c8016b41b",
    "src/engine/sniper_state_handlers.py": "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
    "src/engine/sniper_trade_review_report.py": "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
    "src/trading/market/execution_venue.py": "a794c64a1787fd892837c665e5a495f4043a1bc7371cbdc1604466528bb2fe9a",
}
REVIEWED_OPERATOR_MARKET_PAIRS = {
    "src/engine/automation/main_trailing_all_scope_research.py": (
        (
            "1385571ec3fea2b9ff5815f11d76c6132fd26a15633d8809fbb36c9c28781061",
            "53d7acf04f8bcb37240a1a6572f8e0db2c8ac5e40029010f66e5419ce6d3aa89",
        ),
        (
            "a4433ef1560280d8cfc198bb95357414f01373ba55757c4197315a2b3d0f2dab",
            "53d7acf04f8bcb37240a1a6572f8e0db2c8ac5e40029010f66e5419ce6d3aa89",
        ),
        (
            "a51359c9c0864e055c4c71cb240760f11ca7de265530aa22ac378a70c30af01b",
            "53d7acf04f8bcb37240a1a6572f8e0db2c8ac5e40029010f66e5419ce6d3aa89",
        ),
        (
            "f704dcc16a4bb8434cb255168074a493a215feaac3b1c30372053c11c6babdcc",
            "53d7acf04f8bcb37240a1a6572f8e0db2c8ac5e40029010f66e5419ce6d3aa89",
        ),
    ),
    "src/engine/holding_exit_observation_report.py": (
        (
            "108fcdffa626abec4e90b263c12780e78c7f77e222b950e2407b0b00d462fa4f",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
        (
            "538cc6b7a2cdc91871af06896ee1328de11ebad441f343e7c6b693ad29b8f255",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
        (
            "6ffbcceecdecfa73346047d2ec6f2019ccd1ab296959819c63c4acac7c421ec9",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
        (
            "8baa7a8788877aa872afeec62f199db2a095d420ff1d87d84fdd50e4b1b2c7db",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
        (
            "bd366b341b5515a0d7dcc2b4da47cf71320a0d703b617057037044d52b8c06e3",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
        (
            "fb676ef08389cfbf7d46a0b532d0bd6f3c81949d6b6a64a2c45c17ccf3a839b5",
            "bde5c4156f9b748e957b8b1fa38d12ce24f5b23777a7343fbe31aedbeeb6e75a",
        ),
    ),
    "src/engine/kiwoom_orders.py": (
        (
            "3d31672f0dfab9080cfca4623aa280c1e2f850db43435241c5d0b8b669ce5702",
            "32e93c49a880e1f3a393ec0367cf1339dbc3ef00c689c821b45b159872c423d9",
        ),
    ),
    "src/engine/scalping/ai_action_outcome_calibration.py": (
        (
            "18c661a624b4db88ac0ee5963ff3667a258434662d9ddfca9bea8ab6cc7f50aa",
            "b239020a8231bc8e4d92f5fd8a21af1359c441336823b26e5ac52150459a904c",
        ),
        (
            "26b7b67e5efcf5ed9d4904ac2c715cb1e1e87d76a8b63acc0b6049bff91c03c2",
            "b239020a8231bc8e4d92f5fd8a21af1359c441336823b26e5ac52150459a904c",
        ),
    ),
    "src/engine/scalping/initial_quantity_policy.py": (
        (
            "2710cc18ab0289b1318cb53af8cd45bebcbd9ad9354d82ba2fa180ed3eb9fd90",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "366541bd4f1dd717c75fa5ae9ae4297aafe5950e1d7f0a72afd050b57252d68d",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "4567eed7de944395133eb6ebc975c823cf3840e6abe9424877455130feb55c87",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "6c4e28dc699c2d0b5c12be791c3bf64b721a78a9cb344a3b5f42f79fcf89ed51",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "99656408f2e1dd095686f4ce3b8cdea8364baaf98b62664e53104186c3db62f4",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "9b18c05ff050cb8d182b03296ee71f30b8efa867341ba47b04a2f06dc55f87c7",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "a6e57b600500e10b20ebf1ca2ac097a2433fbd5f8696e28f8ec1ef97601b627a",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "c9496cee9ce0305a75fd0e1c2df93370e18ea4792b61b3d47d8de9937aaef4d4",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
        (
            "dbd20ac53e9ebb59dbb6b465a214558eb838b8f012636eda73cb02f65c5304c6",
            "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
        ),
    ),
    "src/engine/scalping/initial_quantity_refresh_evaluation.py": (
        (
            "5311174d8495ed9560ff6421027700ff7acf89bd43315ba1c63484bb50bfb3e9",
            "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
        ),
        (
            "6b052913a8a88b6780257bbfef0de9bae5c961039608e1cfa1ed25ab0412053f",
            "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
        ),
        (
            "779a0d679ec1b7e1704ad368d8896d166a545e358438fda8e2f51ef0dde800fa",
            "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
        ),
        (
            "798f15352dc47787bc3d3bd571f45fbed2911cdaafbdcab5487998745442bbe4",
            "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
        ),
        (
            "921bac7fcf49a127f1a9f7e1f15d3641b4d8eab39fb054c506e68219f5cc8f43",
            "41b4737da689b2802bc33b0b17cba65938fb173c53a5dd76f4af1a5d49db5afc",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "353795e63675a34743f1bdf0823f684cbdcdd472cdf12790dc17896e1aa107db",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "4dfa3c22640ee0f94fdac37633e7adbb0b6be4ecdaa14efe25ca04d840c799a7",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "910f1a50b7191cf47815b6707dae489847d25f1e45f1b40104a0c38d20eaa846",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "aeabf97ec5bd69578e6e66fc4b2eb14945fbe7a34e59658e12fe1b9cf9732ecd",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "b746d9c9d131ab2795953f3e2401f2fe367525dc0d7dc2c85051fdaac73af97c",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
        (
            "f76427a4e0c75e5062149daff971362962acdc22c599bac957a5dfd3f4c04a70",
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
        ),
    ),
    "src/engine/sniper_execution_receipts.py": (
        (
            "179948c3eb4a0bd7bab6d121ae6d90a0817b82dbef557dea72a25db62c0b8e05",
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
        ),
        (
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
        ),
        (
            "26b75b658f2fbb8f0411fed3d03a5a1f26923a2ad6d0610fa550aaf9a0ad4b51",
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
        ),
        (
            "978dcd47d83709b245dfe8e2983b450d6559f39c9716fe47cce5a475b1eee4b6",
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
        ),
        (
            "a169bb2c9d48b0ce289488985e7df6c6a8d83df9fc9257b63ef4bbf0e2fbbe80",
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
        ),
    ),
    "src/engine/sniper_post_sell_feedback.py": (
        (
            "03026d2b252fa18fc5c36aaa9e1df7c9f3a0ae43ad2debc541882a78e8a9c275",
            "fae77491c422f776a48a99da5d855b76e934bdd244055e4cdc44372c8016b41b",
        ),
        (
            "8fcbf7de95acc2e5ba3121be0f20ece3bbefc7bd22fb57cc4cebe938115fc2d9",
            "fae77491c422f776a48a99da5d855b76e934bdd244055e4cdc44372c8016b41b",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "02be17b70de8acfa2bc2750c25b2292117e4b5b6c1680a95b1d3e0e65b245d19",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "5900377f71e90559ca111bf60448fa60375464af10693e1b5dd16158078c8eaf",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "669b6109e36f81e9dee263d1c3e31011d55fd612d5641713c6ee109a827a9425",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "7c24ee7d6fbd307be13e1d64e1c4995fa06a06f098b7c0144f54984b624a1c5d",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "885af7dd480a520e98502bcd6729586b4d21016de8254a4a7d9e299389f09ed4",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "8cc435544ceeda76309b9051179af20022f100c8b1bad48356636fb51b9f101c",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "9bf2d5b2a3fc5461beaaaf0ca4190e3bf8e4a12d4465d333a495b746f00f98b8",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "c47a60dccf7266e27880b94cb9bccf3b2c23c6c513ede76cce33bce212abfd55",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "ee62c7703fe10c8c602ad13b351ffc5ab1976af5f0d0709e8f09f082a8a81d38",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
        (
            "f79445872ae7b091f494d9e0ee7880b0476f20cd009492803261e44bd70f3c42",
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
        ),
    ),
    "src/engine/sniper_trade_review_report.py": (
        (
            "8d07674031ac0ca0a08437c61490cd896d8810c30f57810ad53febb8cac0b57c",
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
        ),
        (
            "af3f2273dc66d0da041bc64c8b5d79dc553558d369714d586609f0f6cbbd90f0",
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
        ),
        (
            "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
        ),
        (
            "d3e838423aeeaba629be4902b2aac533caceef3145ad747bdc78ff2900c230d8",
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
        ),
        (
            "de4dd6cfc135d5d6c53f757151f32753f13ff780caca285886dba2dc285890d8",
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
        ),
    ),
    "src/trading/market/execution_venue.py": (
        (
            "50b13de6e49aae4e861c29cc66a6508ada2cc33176ba94b67a815dfc2fb819af",
            "a794c64a1787fd892837c665e5a495f4043a1bc7371cbdc1604466528bb2fe9a",
        ),
    ),
}
REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS = {
    (trigger, REVIEWED_OPERATOR_MARKET_HASHES.get(trigger, sha)): {
        **value,
        "selector_path": "src/trading/market/execution_venue.py",
        "selector_sha256": REVIEWED_OPERATOR_MARKET_HASHES[
            "src/trading/market/execution_venue.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_OPERATOR_MARKET_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_OPERATOR_MARKET_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for (trigger, sha), value in REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS.items()
}
for (
    _trigger,
    _operator_market_sha,
), _variant in REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS.items():
    REVIEWED_HOLDING_RESEARCH_DEPENDENCIES[_trigger][_operator_market_sha] = _variant[
        "dependencies"
    ]

REVIEWED_P5_ANCESTRY_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
    "src/engine/scalping/micro_reversion/observer_source_quality.py": "9f87eb48e36b9a0d19ac97289f0fc667d9217da75a8270d60377fb2a351cce66",
}
REVIEWED_P5_ANCESTRY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_P5_ANCESTRY_HASHES[
            "src/engine/infrastructure/startup_validation_code_context.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_P5_ANCESTRY_HASHES},
    }
    for key, value in REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS.items()
}


# Reviewed archive/source/TTL recovery extends one complete P5 generation.
# Preserve every issued predecessor; unknown or mixed bytes still fail closed.
# Review: docs/audits/postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_POSTCLOSE_RECOVERY_HASHES = {
    "src/engine/ai/holding_vote_replay_source.py": "cd40fbcbfabcd43430b0817bf284e7745c1cf4a1cbb4fee62e238a2d1de51653",
    "src/engine/automation/main_stop_postclose.py": "873679d1d6169c84d7480953c23db66d9ed3af8e44e60fe4ae74e0588645b40e",
    "src/engine/automation/main_trailing_source_assembler.py": "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
    "src/engine/infrastructure/validation_digest_session.py": "5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86",
    "src/engine/error_detectors/artifact_freshness.py": "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
    "deploy/run_threshold_cycle_postclose.sh": "c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470",
    "src/engine/automation/postclose_finalization_generation.py": "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
}
REVIEWED_POSTCLOSE_RECOVERY_PAIRS = {
    "src/engine/ai/holding_vote_replay_source.py": (
        (
            "51a90688f175c9fc242367811e4aab8c2509d1287e8b92d3cdf340badc68421a",
            "cd40fbcbfabcd43430b0817bf284e7745c1cf4a1cbb4fee62e238a2d1de51653",
        ),
        (
            "52a1e362c6ac8ad551428a840f96e100a5bb7ee679555ebe2933dfa2f5b95559",
            "cd40fbcbfabcd43430b0817bf284e7745c1cf4a1cbb4fee62e238a2d1de51653",
        ),
        (
            "6aa1db742f4f2354c17ed9bd24cfb1bcfaace5e0130a8d0dceef84343ea6a428",
            "cd40fbcbfabcd43430b0817bf284e7745c1cf4a1cbb4fee62e238a2d1de51653",
        ),
    ),
    "src/engine/automation/main_trailing_source_assembler.py": (
        (
            "4ad0ea7a311c1ee6745f6bec364c92582fd3b2f7b591291970692fa28295951b",
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
        ),
        (
            "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
        ),
        (
            "e64c9943e0894558ded208637e4f2ef87565fa469745b299cc872ecd1d4c3bfa",
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
        ),
        (
            "edf4f62628db48829848fb12b6d5d3446c9c82d49223e3676e4d4dac18fe4b25",
            "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
        ),
    ),
    "deploy/run_threshold_cycle_postclose.sh": (
        (
            "594cd0a6613cbcd5c642ba818a8468fcafbeb4474a7cbd08e1b013ad0556911c",
            "c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470",
        ),
        (
            "e56ebd50f596b142083df248f301f8bce8a7d55ca67dbeb646224e5fb17dd9c5",
            "c5e60200a9cf27839204a8fd7d46733f0c10c1a4a0ddeef5bfae35f683b29470",
        ),
    ),
    "src/engine/automation/main_stop_postclose.py": (
        (
            "616a22f236d89de67e18001dbb3564aca6ed5b87e1b26ade3a119a711e1ab057",
            "873679d1d6169c84d7480953c23db66d9ed3af8e44e60fe4ae74e0588645b40e",
        ),
        (
            "ad0eb4c9eea9b260fb63bed150ff8882671ae126500d005dc00af5f3361dd3ae",
            "873679d1d6169c84d7480953c23db66d9ed3af8e44e60fe4ae74e0588645b40e",
        ),
        (
            "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
            "873679d1d6169c84d7480953c23db66d9ed3af8e44e60fe4ae74e0588645b40e",
        ),
    ),
    "src/engine/automation/postclose_finalization_generation.py": (
        (
            "1ac7c5d9a4269f73a9a9f82656d22a277689813b32c94b3a526e0b37452d3041",
            "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
        ),
        (
            "d4d4d0819c4a1845baf10bcaf7935137aa9d925544a374a8c47ead6259f51e43",
            "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
        ),
        (
            "e4454cb3da9c7542177cb49f30579970978717538baae4fd3bab9dfbdf269b63",
            "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
        ),
    ),
    "src/engine/infrastructure/validation_digest_session.py": (
        (
            "87ea421cd28cd81d06fabecbfeed4c03d041b771f31dba6057857283a53828da",
            "5a8fc66dc1cb1626de559efb024e2ee30afa9e68bce83fd6c31be2456f677d86",
        ),
    ),
    "src/engine/error_detectors/artifact_freshness.py": (
        (
            "edd034fef32d08c01ea52e3a0022a5ac185d45bde9ff66ab190fdbc4fd7221e6",
            "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
        ),
    ),
}
REVIEWED_POSTCLOSE_RECOVERY_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/ai/holding_vote_replay_source.py",
        "selector_sha256": REVIEWED_POSTCLOSE_RECOVERY_HASHES[
            "src/engine/ai/holding_vote_replay_source.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_POSTCLOSE_RECOVERY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_POSTCLOSE_RECOVERY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_P5_ANCESTRY_DEPENDENCY_VARIANTS.items()
}


# Reviewed 10/22 entry source/receipt and quantity-cost integration. Each new
# member requires the complete predecessor plus the exact integrated sources.
# Review: postclose-root-cause-recovery-review-2026-10-19.md.
REVIEWED_ENTRY_COST_HASHES = {
    "src/engine/ai_engine_openai.py": "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
    "src/engine/automation/main_startup_validation.py": "f1ee443e585a5373ffcd16f5c041fd87cc5961de0dbc8de63c3bb1e80fe15c54",
    "src/engine/automation/main_stop_postclose.py": "8c50fca4270514425cdd533f605845307c3fdf27b0336dddd93cde61dd88ec8c",
    "src/engine/automation/main_trailing_source_store.py": "9605fcdc48f11e3c92a1ddaa7846a2f5d725e6d9518d658095235e3c435fb520",
    "src/engine/automation/next_preopen_readiness.py": "2e34f2a99ec94609674d7cf267763d651e5b3d4d3e030b8267dd282f325d5c69",
    "src/engine/automation/policy_generation_fixture_validation.py": "28ec0362fddac74b6a1ad9230b4729879faccdf1e67ab9245e27eae5c4b45331",
    "src/engine/buy_funnel_sentinel.py": "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7",
    "src/engine/infrastructure/startup_validation_code_context.py": "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
    "src/engine/lifecycle/broker_cost_allocation.py": "404a1fb1f49683eba1e0443b74758cda11fd8b62452e49f229808b7e5769afae",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "4fac0132c2281f278270b6d6c2bc171b4ff413f57b3075e9493173ab5cb144bc",
    "src/engine/lifecycle/main_stop_research_cost.py": "8f88c3c701971f909d275b4dde629173c7aed0e966698237a355114349c08ad8",
    "src/engine/monitoring/entry_attempt_identity.py": "a80693ad2bdc2c8e9aef234fbbeff8d65d05d81ac7b8310d89019069ec28ca90",
    "src/engine/monitoring/policy_generation_code_handoff.py": "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
    "src/engine/monitoring/policy_generation_contract.py": "394c8710936e2d4cd30ed5b90bcceb130a1ab442aaa34df701cf9068e0029394",
    "src/engine/monitoring/sentinel_summary_contract.py": "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "ef78c5ae7aa9dd7eab7e7ce3575329943713750fc70b248f6e992766511fd114",
    "src/engine/scalping/initial_quantity_source_cache.py": "d891c6da643136f14a28c17f0747e0123c17535777e924e68a381d219b2265eb",
    "src/engine/sniper_execution_receipts.py": "f7210ea376fcd04d19e1592d72d0bc4a8261b799422e6161e511a338052eebb1",
    "src/engine/sniper_state_handlers.py": "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
    "src/engine/sniper_sync.py": "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
    "src/engine/sniper_trade_review_report.py": "3f08c6ad233609367839f48a9bdea3493fc09188c14077d8a19043f9c0b56390",
}
REVIEWED_ENTRY_COST_PAIRS = {
    "src/engine/ai_engine_openai.py": (
        (
            "4a70967c006a6dba29d06ba8409d346b782d7e2fe09656e1fbfc9807f17cc162",
            "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
        ),
        (
            "bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185",
            "3463333df619b52d896ea02779647fa48adf6ae29a45713de80cf31c213806c7",
        ),
    ),
    "src/engine/automation/main_startup_validation.py": (
        (
            "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54",
            "f1ee443e585a5373ffcd16f5c041fd87cc5961de0dbc8de63c3bb1e80fe15c54",
        ),
        (
            "399ee38f0d22991d9761e5d301f8bc6af15b53fe2a8ba582cbc0435bd62daa67",
            "f1ee443e585a5373ffcd16f5c041fd87cc5961de0dbc8de63c3bb1e80fe15c54",
        ),
    ),
    "src/engine/automation/main_stop_postclose.py": (
        (
            "873679d1d6169c84d7480953c23db66d9ed3af8e44e60fe4ae74e0588645b40e",
            "8c50fca4270514425cdd533f605845307c3fdf27b0336dddd93cde61dd88ec8c",
        ),
        (
            "d20e955fdbc79529efd72d10957cf329acc0d0447c54f798ebfd59ecb87a978b",
            "8c50fca4270514425cdd533f605845307c3fdf27b0336dddd93cde61dd88ec8c",
        ),
    ),
    "src/engine/automation/main_trailing_source_store.py": (
        (
            "e9f596c589348c1090c54eb971ede6497f20d2ccb1a0fb45340b05797fd1e2b8",
            "9605fcdc48f11e3c92a1ddaa7846a2f5d725e6d9518d658095235e3c435fb520",
        ),
        (
            "aca2d7dda4c8eda53f6634a73b133090e73c511cc62973584f31633245edd850",
            "9605fcdc48f11e3c92a1ddaa7846a2f5d725e6d9518d658095235e3c435fb520",
        ),
    ),
    "src/engine/automation/next_preopen_readiness.py": (
        (
            "c7ba75db4fedb705bdbfc4b7c2bdd39ac527b44b111d33c9639e911adaded88e",
            "2e34f2a99ec94609674d7cf267763d651e5b3d4d3e030b8267dd282f325d5c69",
        ),
    ),
    "src/engine/automation/policy_generation_fixture_validation.py": (
        (
            "88e251b6268e1814ad2e1ff6882381edb5c733973de72ad1b377ec3335cde058",
            "28ec0362fddac74b6a1ad9230b4729879faccdf1e67ab9245e27eae5c4b45331",
        ),
        (
            "64d9ceffad22ca5e4875fcbfd497ab450a908e427c190af5f4f109ffec6daf83",
            "28ec0362fddac74b6a1ad9230b4729879faccdf1e67ab9245e27eae5c4b45331",
        ),
    ),
    "src/engine/buy_funnel_sentinel.py": (
        (
            "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1",
            "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7",
        ),
        (
            "6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993",
            "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7",
        ),
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        (
            "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
            "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
        ),
        (
            "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
            "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
        ),
    ),
    "src/engine/lifecycle/broker_cost_allocation.py": (
        (
            "e392d3e79ad63fe1502a7921aca590ce93c3134d9d3e4d488d42775dd20cf349",
            "404a1fb1f49683eba1e0443b74758cda11fd8b62452e49f229808b7e5769afae",
        ),
    ),
    "src/engine/lifecycle/broker_cost_reconciliation.py": (
        (
            "db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5",
            "4fac0132c2281f278270b6d6c2bc171b4ff413f57b3075e9493173ab5cb144bc",
        ),
    ),
    "src/engine/lifecycle/main_stop_research_cost.py": (
        (
            "998f989d19979464bde492b14bd651d1bb7ff26abdfd6c5eaa454c2ebf994694",
            "8f88c3c701971f909d275b4dde629173c7aed0e966698237a355114349c08ad8",
        ),
    ),
    "src/engine/monitoring/entry_attempt_identity.py": (
        (
            "5bd57a8d235e360ba5a9ea953256164722c267931e7d8caf55816c3a819b7d63",
            "a80693ad2bdc2c8e9aef234fbbeff8d65d05d81ac7b8310d89019069ec28ca90",
        ),
        (
            "a18c0b96de81dcb17f6717703f5e5ebc46c29a579e7e85f257c5d6f0251d7f5e",
            "a80693ad2bdc2c8e9aef234fbbeff8d65d05d81ac7b8310d89019069ec28ca90",
        ),
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        (
            "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
            "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
        ),
        (
            "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
            "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
        ),
    ),
    "src/engine/monitoring/policy_generation_contract.py": (
        (
            "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
            "394c8710936e2d4cd30ed5b90bcceb130a1ab442aaa34df701cf9068e0029394",
        ),
    ),
    "src/engine/monitoring/sentinel_summary_contract.py": (
        (
            "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
            "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
        ),
        (
            "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
            "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
        ),
    ),
    "src/engine/scalping/initial_quantity_monitor_projection.py": (
        (
            "81a69a5f6a4d512ab7578b196fcddcf08d56ceb791ee8d2d1d3a9bdfdb926327",
            "ef78c5ae7aa9dd7eab7e7ce3575329943713750fc70b248f6e992766511fd114",
        ),
        (
            "252ca991d7729e4b86393831ca2b6c7345a4a255d0e9c8d5d39c1bbf77a13947",
            "ef78c5ae7aa9dd7eab7e7ce3575329943713750fc70b248f6e992766511fd114",
        ),
    ),
    "src/engine/scalping/initial_quantity_source_cache.py": (
        (
            "5e2724f3532cd7a8f467d7fbf04cd562444f9de7e46fcea5e83180e4bc68fa53",
            "d891c6da643136f14a28c17f0747e0123c17535777e924e68a381d219b2265eb",
        ),
        (
            "77a7b57d5f752c760332fc6fd46a4fb121d4c0042ceb464a689fae1dc23c5704",
            "d891c6da643136f14a28c17f0747e0123c17535777e924e68a381d219b2265eb",
        ),
    ),
    "src/engine/sniper_execution_receipts.py": (
        (
            "e015955435a78f9558999c6347b49c10beb7bf48582fc6b28cc102a2ee4807e1",
            "f7210ea376fcd04d19e1592d72d0bc4a8261b799422e6161e511a338052eebb1",
        ),
        (
            "20d1f9b5403440f10571199bd33e1ba103aa611512e6b7d5151fbe07acd94620",
            "f7210ea376fcd04d19e1592d72d0bc4a8261b799422e6161e511a338052eebb1",
        ),
    ),
    "src/engine/sniper_state_handlers.py": (
        (
            "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
        ),
        (
            "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
            "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
        ),
    ),
    "src/engine/sniper_sync.py": (
        (
            "2a2cdc2f144bbe2abd7649b4c4b9f4a6ff50ae751ab3e978699c2da49a06199d",
            "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
        ),
        (
            "baed080aaa9dd6708f1999ed4a811a758df2bb683449a773e5418303affd4f34",
            "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
        ),
    ),
    "src/engine/sniper_trade_review_report.py": (
        (
            "65c57137cffbc8e02f349ef16964e9fe2f6d27ce30573b37a9d6bbd502c5023b",
            "3f08c6ad233609367839f48a9bdea3493fc09188c14077d8a19043f9c0b56390",
        ),
        (
            "afbd53084fbf25dfa6f91c865d74b0327b02a38d9b3b3d7957c7a60a78874a1b",
            "3f08c6ad233609367839f48a9bdea3493fc09188c14077d8a19043f9c0b56390",
        ),
    ),
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_ENTRY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/sniper_sync.py",
        "selector_sha256": REVIEWED_ENTRY_COST_HASHES["src/engine/sniper_sync.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_POSTCLOSE_RECOVERY_DEPENDENCY_VARIANTS.items()
}


# Preserve the actually consumed first integration generation independently.
REVIEWED_ENTRY_COST_PRE_STARTUP_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_STARTUP_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **{
        "src/engine/automation/ordered_intraday_deploy.py": "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
        "src/engine/monitoring/sentinel_summary_contract.py": "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
        "src/engine/sniper_state_handlers.py": "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
        "src/engine/sniper_sync.py": "ec7e5585faceca2bd2d0c75a56751df085125a6580fc662794db053723d5a9f8",
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        "src/engine/automation/ordered_intraday_deploy.py": (
            (
                "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            ),
        ),
        "src/engine/monitoring/sentinel_summary_contract.py": (
            (
                "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
                "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
            ),
            (
                "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
                "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
            ),
            (
                "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
                "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
            ),
            (
                "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
                "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
            ),
            (
                "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
                "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
            ),
        ),
        "src/engine/sniper_state_handlers.py": (
            (
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            ),
            (
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            ),
            (
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
            (
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
            (
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
        ),
        "src/engine/sniper_sync.py": (
            (
                "2a2cdc2f144bbe2abd7649b4c4b9f4a6ff50ae751ab3e978699c2da49a06199d",
                "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
            ),
            (
                "baed080aaa9dd6708f1999ed4a811a758df2bb683449a773e5418303affd4f34",
                "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
            ),
            (
                "2a2cdc2f144bbe2abd7649b4c4b9f4a6ff50ae751ab3e978699c2da49a06199d",
                "ec7e5585faceca2bd2d0c75a56751df085125a6580fc662794db053723d5a9f8",
            ),
            (
                "baed080aaa9dd6708f1999ed4a811a758df2bb683449a773e5418303affd4f34",
                "ec7e5585faceca2bd2d0c75a56751df085125a6580fc662794db053723d5a9f8",
            ),
            (
                "bdd9eb54314dde790f84a2d8a79655e1eb8d6267f382d5e5f95fdd2c79efc7cb",
                "ec7e5585faceca2bd2d0c75a56751df085125a6580fc662794db053723d5a9f8",
            ),
        ),
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_ENTRY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "selector_sha256": REVIEWED_ENTRY_COST_HASHES["src/engine/sniper_sync.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_STARTUP_VARIANTS.items()
}


# Preserve the native consumed70fc generation before the diagnostic closure.
REVIEWED_ENTRY_COST_PRE_SHUTDOWN_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_SHUTDOWN_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **{
        "src/engine/error_detectors/artifact_freshness.py": "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
        "src/engine/error_detector.py": "738601adc71f9c3ccddbfa8e290709eba44492bb743ffa6043264e04bc7b0a62",
        "src/engine/automation/entry_cancel_wait_tuning.py": "38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa",
        "src/engine/kiwoom_sniper_v2.py": "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
        "src/engine/monitoring/policy_generation_code_handoff.py": "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
        "src/engine/monitoring/policy_generation_contract.py": "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
        "src/engine/monitoring/policy_generation_validation.py": "bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238",
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        "src/engine/error_detectors/artifact_freshness.py": (
            (
                "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
                "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
            ),
        ),
        "src/engine/error_detector.py": (
            (
                "c4d2e89d6e257d4c9cd7d819a2592fd4e31a73fb3806662ab97911542c471f56",
                "738601adc71f9c3ccddbfa8e290709eba44492bb743ffa6043264e04bc7b0a62",
            ),
        ),
        "src/engine/automation/entry_cancel_wait_tuning.py": (
            (
                "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
                "38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa",
            ),
        ),
        "src/engine/kiwoom_sniper_v2.py": (
            (
                "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
                "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
            ),
        ),
        "src/engine/monitoring/policy_generation_code_handoff.py": (
            (
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            ),
            (
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            ),
            (
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
            (
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
            (
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
        ),
        "src/engine/monitoring/policy_generation_contract.py": (
            (
                "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
                "394c8710936e2d4cd30ed5b90bcceb130a1ab442aaa34df701cf9068e0029394",
            ),
            (
                "8e71ab5797bf950f0bb8161304e23b5b3788a3e252c2a1eb4316b095ec5f52be",
                "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
            ),
            (
                "394c8710936e2d4cd30ed5b90bcceb130a1ab442aaa34df701cf9068e0029394",
                "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
            ),
        ),
        "src/engine/monitoring/policy_generation_validation.py": (
            (
                "f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc",
                "bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238",
            ),
        ),
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_ENTRY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_SHUTDOWN_VARIANTS.items()
}


# Bind the reviewed selection observer and offline native-label owner together.
# Preserve the consumed b1519 generation for predecessor and historical readers.
REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_ENTRY_COST_NATIVE_LABEL_HASHES = {
    "src/engine/automation/main_market_weakness_research.py": "c7fc0eacb9ec937d28c507a4b7586d1d71425a3719a08c1d8ada65e0404071f9",
    "src/engine/monitoring/policy_generation_code_handoff.py": "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
    "src/engine/monitoring/runtime_performance.py": "3414c2eee58fc8c5547b11ad6786f1775b20d4cfb6e9b0ce78ed16e17a34e5d4",
    "src/engine/scalping/continuous_reversal_source.py": "0c8e4d4a0ab08c2bb54e115d8071fa5f2b732e99414043b75e2d51b9da914ba0",
    "src/engine/sniper_state_handlers.py": "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_ENTRY_COST_NATIVE_LABEL_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        "src/engine/automation/main_market_weakness_research.py": (
            (
                "375f13bd830a42de09cb9fae28879ab69459f76013e47dd4365207d28d976309",
                "c7fc0eacb9ec937d28c507a4b7586d1d71425a3719a08c1d8ada65e0404071f9",
            ),
        ),
        "src/engine/monitoring/policy_generation_code_handoff.py": (
            (
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            ),
            (
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
            ),
            (
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
            (
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
            (
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
            ),
            (
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            ),
            (
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
                "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            ),
            (
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
                "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            ),
            (
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            ),
        ),
        "src/engine/monitoring/runtime_performance.py": (
            (
                "626ae4d2db569edce63082aab86965872b57f0ec9daacca767ec4e83f84e36be",
                "3414c2eee58fc8c5547b11ad6786f1775b20d4cfb6e9b0ce78ed16e17a34e5d4",
            ),
        ),
        "src/engine/scalping/continuous_reversal_source.py": (
            (
                "fb3d91a378457c244a805a49183572f74f3c4541cb3efdca4aa9f3c1a52df082",
                "0c8e4d4a0ab08c2bb54e115d8071fa5f2b732e99414043b75e2d51b9da914ba0",
            ),
        ),
        "src/engine/sniper_state_handlers.py": (
            (
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            ),
            (
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
            ),
            (
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
            (
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
            (
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ),
            (
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            ),
            (
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
                "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            ),
            (
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            ),
            (
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
                "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
            ),
        ),
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_ENTRY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_VARIANTS.items()
}


# Coordinate the native producer before drain; keep the issued selection generation.
REVIEWED_ENTRY_COST_PRE_COORDINATION_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_COORDINATION_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_COORDINATION_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
    "src/engine/scalping/reversal_code_handoff.py": "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_COORDINATION_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        "src/engine/automation/ordered_intraday_deploy.py": (
            (
                "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            ),
            (
                "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            ),
            (
                "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
                "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            ),
        ),
        "src/engine/scalping/reversal_code_handoff.py": (
            (
                "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
                "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
            ),
        ),
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_ENTRY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_ENTRY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ENTRY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_COORDINATION_VARIANTS.items()
}


# The read-only prepared-intraday closure has its own complete reviewed profile.
REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_VARIANTS = (
    REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
)
REVIEWED_PREPARED_VALIDATION_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212"
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PREPARED_VALIDATION_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    "src/engine/infrastructure/startup_validation_code_context.py": (
        (
            "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
            "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
        ),
        (
            "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
            "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
        ),
    ),
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_PREPARED_VALIDATION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREPARED_VALIDATION_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_VARIANTS.items()
}


# Keep the issued prepared-validation generation while repairing its manifest binding.
REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_VARIANTS = (
    REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
)
REVIEWED_PREPARED_REPAIR_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
    "src/engine/scalping/reversal_code_handoff.py": "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
    "src/engine/infrastructure/startup_validation_code_context.py": "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PREPARED_REPAIR_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + pairs
        for name, pairs in {
            "src/engine/automation/ordered_intraday_deploy.py": (
                (
                    "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
                    "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
                ),
                (
                    "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                    "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
                ),
                (
                    "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
                    "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
                ),
            ),
            "src/engine/scalping/reversal_code_handoff.py": (
                (
                    "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
                    "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
                ),
                (
                    "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
                    "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
                ),
            ),
            "src/engine/infrastructure/startup_validation_code_context.py": (
                (
                    "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
                    "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
                ),
                (
                    "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
                    "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
                ),
                (
                    "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
                    "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
                ),
            ),
        }.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PREPARED_REPAIR_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREPARED_REPAIR_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_VARIANTS.items()
}


# Preserve the manifest repair; bind the Main preparation consumer explicitly.
REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_VARIANTS = (
    REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
)
REVIEWED_MAIN_PREPARATION_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
    "src/engine/infrastructure/startup_validation_code_context.py": "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_MAIN_PREPARATION_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + pairs
        for name, pairs in {
            "src/engine/automation/ordered_intraday_deploy.py": (
                (
                    "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
                    "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                ),
                (
                    "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                    "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                ),
                (
                    "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
                    "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                ),
                (
                    "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
                    "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                ),
            ),
            "src/engine/infrastructure/startup_validation_code_context.py": (
                (
                    "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
                    "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
                ),
                (
                    "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
                    "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
                ),
                (
                    "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
                    "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
                ),
                (
                    "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
                    "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
                ),
            ),
        }.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_MAIN_PREPARATION_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_MAIN_PREPARATION_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_VARIANTS.items()
}


# Preserve the issued Main-preparation profile through its exact start recovery.
REVIEWED_ENTRY_COST_PRE_PREPARED_START_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_PREPARED_START_VARIANTS = (
    REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
)
REVIEWED_PREPARED_START_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756"
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PREPARED_START_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    "src/engine/automation/ordered_intraday_deploy.py": REVIEWED_ENTRY_COST_PAIRS[
        "src/engine/automation/ordered_intraday_deploy.py"
    ]
    + (
        (
            "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
        ),
        (
            "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
        ),
        (
            "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
        ),
        (
            "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
        ),
        (
            "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
            "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
        ),
    ),
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PREPARED_START_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREPARED_START_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PREPARED_START_VARIANTS.items()
}


# Bind the FIRST cancellation reader and rejected-probe reference producer as
# one exact group; retain the already consumed e9ee generation separately.
REVIEWED_ENTRY_COST_PRE_FIRST_TURN_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_FIRST_TURN_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_FIRST_TURN_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
    "src/engine/scalping/zero_base_probe.py": "104746b1f9a2144bc6c6955c022e9ad925cba688300e715392554ec2c81e097c",
}
REVIEWED_FIRST_TURN_ORIGINS = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": (
        "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
    ),
    "src/engine/scalping/zero_base_probe.py": (
        "c8e671c81375910971a7b8f75d1e2d6162a3411906cfbd3a3a2e076c99837fc7",
    ),
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_FIRST_TURN_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (old, current)
            for old in sorted(
                {pair[0] for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())}
                | set(REVIEWED_FIRST_TURN_ORIGINS[name])
            )
        )
        for name, current in REVIEWED_FIRST_TURN_HASHES.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_FIRST_TURN_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_FIRST_TURN_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_FIRST_TURN_VARIANTS.items()
}


# Keep the consumed FIRST generation while consolidating native expiry health.
REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_EXPIRY_HEALTH_HASHES = {
    "src/engine/monitoring/submission_bottleneck_monitor.py": "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e"
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_EXPIRY_HEALTH_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS[name]
        + tuple(
            (old, current)
            for old in sorted(
                {pair[0] for pair in REVIEWED_ENTRY_COST_PAIRS[name]}
                | {REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_HASHES[name]}
            )
        )
        for name, current in REVIEWED_EXPIRY_HEALTH_HASHES.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_EXPIRY_HEALTH_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_EXPIRY_HEALTH_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_VARIANTS.items()
}


# Signed volume-surge metadata uses the existing signed parser. Preserve the
# consumed native-expiry profile; bind exact adapter bytes without policy changes.
REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_SIGNED_SURGE_HASHES = {
    "src/utils/kiwoom_utils.py": "498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323"
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_SIGNED_SURGE_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    "src/utils/kiwoom_utils.py": REVIEWED_ENTRY_COST_PAIRS.get(
        "src/utils/kiwoom_utils.py", ()
    )
    + (
        (
            "00b0fffbf665ac0d598fa53bc02ad4b0a927943846ed9de94fb7449ec05a9a0f",
            "498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323",
        ),
    ),
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_SIGNED_SURGE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SIGNED_SURGE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_VARIANTS.items()
}


# Pre-adjudication rejection uses the existing source-invalid capture and
# downstream primary provenance. Keep the actually consumed fc51 generation.
REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    "src/engine/scalping/ai_decision_trace.py": REVIEWED_ROLE_LATENCY_HASHES[
        "src/engine/scalping/ai_decision_trace.py"
    ],
    "src/engine/automation/main_trailing_source_reuse.py": "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
    "src/engine/automation/main_trailing_source_assembler.py": "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "4fac0132c2281f278270b6d6c2bc171b4ff413f57b3075e9493173ab5cb144bc",
    "src/engine/lifecycle/holding_research_cost.py": "3979cab1f18b2bd32933985d9e7c86068aa1284dc76dc278bbc171c0c4704911",
    "src/engine/scalping/reversal_source_diagnostics.py": "ad9fc4f2eeac858435cae48f9707275eabce46c8f48fee38e40029ea4a843c93",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
    "src/engine/automation/main_trailing_source_store.py": "9605fcdc48f11e3c92a1ddaa7846a2f5d725e6d9518d658095235e3c435fb520",
}
REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_PREASSESSMENT_HASHES = {
    "src/engine/ai_engine_openai.py": "9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56",
    "src/engine/scalping/ai_decision_trace.py": "ad480ce1fb75ce2ec9217e4623e5de31dfd83e9ff62520934ab0317da60e973b",
    "src/engine/infrastructure/startup_validation_code_context.py": "be396153e7574f9cbf2d8a90145a373bbdc576adb116553896a9184093bcec47",
    "src/engine/automation/main_trailing_source_reuse.py": "4c38cd9add7e87e7a50529f1a0ad379dde4b786fb8405bf02ee1c7e117a280ec",
    "src/engine/automation/main_trailing_source_assembler.py": "d76ee7b7c79ea1d420f4432f9026690b3155f7e815f0dbf1fec66016b51d8e26",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "e448a6d71b3ac419591ecc679d8fc180f0c021efc4146131236282eb4cc0485b",
    "src/engine/lifecycle/holding_research_cost.py": "cb4f4c3fb7a9b49dd8f113dd03b9d34cd1e8dd84304220415308ebeb0fb4f4c7",
    "src/engine/scalping/reversal_source_diagnostics.py": "bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
    "src/engine/automation/main_trailing_source_store.py": "afe1370cd010ee50a1cefc6e0f3bed5febdd4e401ce6183dbbb3eaf3546ccf66",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PREASSESSMENT_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (old, current)
            for old in sorted(
                {pair[0] for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())}
                | {REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_HASHES[name]}
            )
        )
        for name, current in REVIEWED_PREASSESSMENT_HASHES.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_PREASSESSMENT_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PREASSESSMENT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREASSESSMENT_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_VARIANTS.items()
}


# Prepared-stage repair: native P5 failures keep their immutable original
# report; effective auxiliary registry research remains report-only.
REVIEWED_ENTRY_COST_PRE_PRESTART_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_PRESTART_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_PRESTART_INTEGRATION_HASHES = {
    "src/engine/automation/ordered_intraday_deploy.py": "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
    "src/engine/automation/main_market_weakness_research.py": "e78122825224eee72bb3301fd2df7c22230645c5b88103fd32009a186316909b",
    "src/engine/automation/main_startup_validation.py": "fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c",
    "src/engine/infrastructure/startup_validation_code_context.py": "b999b1fb1e2ff40dc112cfd88a97ac0e2ecb62975fcbd95ac0c78a1899ad3ea2",
    "src/engine/scalping/reversal_code_handoff.py": "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PRESTART_INTEGRATION_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (old, current)
            for old in sorted(
                {pair[0] for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())}
                | {REVIEWED_ENTRY_COST_PRE_PRESTART_HASHES[name]}
            )
        )
        for name, current in REVIEWED_PRESTART_INTEGRATION_HASHES.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_PRESTART_INTEGRATION_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_PRESTART_INTEGRATION_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_PRESTART_INTEGRATION_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PRESTART_VARIANTS.items()
}


# Native prepared-code issuance belongs to the ordered producer. Preserve the
# actually consumed predecessor as a complete immutable dependency generation.
REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    "src/engine/automation/postclose_summary_handoff.py": "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
}
REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_VARIANTS = {
    key: {
        **value,
        "dependencies": {
            **value["dependencies"],
            "src/engine/automation/postclose_summary_handoff.py": "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
        },
    }
    for key, value in REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS.items()
}
REVIEWED_PREPARED_OWNER_HASHES = {
    "deploy/run_threshold_cycle_postclose.sh": "dde8ede993e00f022654534a93c9b54c9b38227b9c151bde6288b8782d096067",
    "src/engine/automation/ordered_intraday_deploy.py": "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
    "src/engine/automation/prepared_policy_code_handoff.py": "5bf1ed07810e5beeba889493c83bdd5b8eaa913b1710fc534c8a20246e1422e3",
    "src/engine/infrastructure/runtime_release_router.py": "ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962",
    "src/engine/automation/entry_cancel_wait_tuning.py": "bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e",
    "src/engine/lifecycle/broker_cost_source.py": "4ee127feb84ac4d0cea4eaed80a7813308f434983bba3d99f9e359fb07c6cad4",
    "src/engine/lifecycle/broker_cost_reconciliation.py": "3d0baf2c711f47a23c453ca78587f849391906a31d6fa1866968408b645be34f",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "c0ac0738df35657d770b4c7a1a7c0490a0ab4bc8756aa1c19215ad2661dead8b",
    "src/engine/automation/main_trailing_source_reuse.py": "88faf62cd0e01d4b32f5f36ca96b37fdf3a4bd2432e0adcab8ca1c9d8cfd8ac5",
    "src/engine/automation/main_trailing_source_assembler.py": "947171df074a8074ebb3d9bcca5710a2b001ccc00a211c58d99113ab5317e77b",
    "src/engine/lifecycle/holding_research_cost.py": "25ba4b953775e2248a6d83cacb256a50af5b639472c18c4ab759c88413610016",
    "src/engine/scalping/ai_action_outcome_calibration.py": "a300563f9c78eb6365a24eb1c2afa67872aaf2fc287ac7d4c8aad69907bb5aed",
    "src/engine/scalping/continuous_reversal_operating_postclose.py": "2fc75be21c110341ac4596f08f8a3bcdb42adfd4e3ba8322f601337b84ab8441",
    "src/engine/scalping/continuous_reversal_policy_v6.py": "b2be4fe8fe3080bc8e7de9a42c76a8d00985c6ad257a8b1da052fa6a3a108bf2",
    "src/engine/automation/main_market_weakness_research.py": "9e704cce559ff4d7cc714feece733ca64380b440a7c3490a219170412656bce8",
    "src/engine/infrastructure/startup_validation_code_context.py": "5f6b4ccc8c4ea74d5b4012dd02b4607c437587402fdbb325752fe53fc0080947",
    "src/engine/scalping/reversal_code_handoff.py": "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
    "src/engine/scalping/reversal_auxiliary_tuning.py": "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
    "src/engine/automation/postclose_finalization_generation.py": "ba7533068261dadc984418175d3dcb5e7bba70110e359de4aba488a52cc8c0e3",
    "src/engine/error_detectors/artifact_freshness.py": "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
    "src/engine/automation/postclose_summary_handoff.py": "f45c0222962988a0b210e405dbc9cb70c1338538e83d9a3fcbc8796ff0ab3df2",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_PREPARED_OWNER_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (old, current)
            for old in sorted(
                {pair[0] for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())}
                | {
                    REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_HASHES.get(
                        name,
                        {
                            "src/engine/infrastructure/runtime_release_router.py": "58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308",
                            "src/engine/scalping/continuous_reversal_policy_v6.py": "eca7f2f2a46d2b4e8f1739e53e6c59d19fd70951c1e2fd786dd8c712201f2460",
                            "src/engine/lifecycle/broker_cost_source.py": "62a88c219868754055c8754a43fb5976c453aa70c81422fd97e410a8ae995c86",
                            "src/engine/automation/postclose_finalization_generation.py": "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
                            "src/engine/error_detectors/artifact_freshness.py": "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
                            "src/engine/automation/postclose_summary_handoff.py": "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
                        }.get(
                            name,
                            "00d78a00a10ad6c3d4cdc68083b659a6e5d4b0230ff38b87d7c2d52648f47a0c",
                        ),
                    )
                }
            )
        )
        for name, current in REVIEWED_PREPARED_OWNER_HASHES.items()
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    "src/engine/infrastructure/startup_validation_code_context.py": REVIEWED_ENTRY_COST_PAIRS[
        "src/engine/infrastructure/startup_validation_code_context.py"
    ]
    + (
        (
            "741f502aeb6c210fa59a7e1b5a5d5e0264fc1d3cc045a7717a8e403016e8ba3e",
            "5f6b4ccc8c4ea74d5b4012dd02b4607c437587402fdbb325752fe53fc0080947",
        ),
    ),
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_PREPARED_OWNER_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PREPARED_OWNER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PREPARED_OWNER_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_VARIANTS.items()
}


# Keep the complete selected91 generation valid when reading its native
# predecessor. Only this exact finalizer owner selects that old profile.
REVIEWED_PRE_FINALIZATION_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    "src/engine/automation/postclose_finalization_generation.py": "add8eaa8de08300a3da458e880ecf24884da4d0467b2ab0c6da0eb09c8349fa7",
    "src/engine/error_detectors/artifact_freshness.py": "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
    "src/engine/automation/postclose_summary_handoff.py": "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
    "src/engine/infrastructure/startup_validation_code_context.py": "741f502aeb6c210fa59a7e1b5a5d5e0264fc1d3cc045a7717a8e403016e8ba3e",
}
REVIEWED_PRE_FINALIZATION_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PRE_FINALIZATION_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PRE_FINALIZATION_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS.items()
}


# Native PREOPEN consumed this complete generation without an intraday handoff.
REVIEWED_NATIVE_PREOPEN_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    "src/engine/automation/postclose_finalization_generation.py": "ddc559621e47b8069a4f46b44746e659884e08a3a875dbe03564dde6bbc84513",
    "src/engine/error_detectors/artifact_freshness.py": "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
    "src/engine/automation/postclose_summary_handoff.py": "f3b4559530defabadbdd1e0efcfb6112069ae98c001cc17ab49a2ba6e8676a06",
    "src/engine/infrastructure/startup_validation_code_context.py": "741f502aeb6c210fa59a7e1b5a5d5e0264fc1d3cc045a7717a8e403016e8ba3e",
}
REVIEWED_NATIVE_PREOPEN_VARIANTS = {
    key: {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_NATIVE_PREOPEN_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_NATIVE_PREOPEN_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS.items()
}


# Exact sentinel scope/972 integration. Preserve the complete consumed9a8
# profile; selecting any new member requires the entire reviewed successor.
# Review: postclose-root-cause-recovery-review-2026-10-19.md,2026-10-23.
REVIEWED_ENTRY_COST_PRE_SENTINEL_SCOPE_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_PRE_SENTINEL_SCOPE_VARIANTS = (
    REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
)
REVIEWED_SENTINEL_SCOPE_HASHES = {
    "src/engine/automation/main_market_weakness_research.py": "ad97af89ce2480978e7c5286b05af8d9cb30dd81fad8d62152f7258eb646912b",
    "src/engine/automation/main_trailing_source_assembler.py": "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
    "src/engine/automation/main_trailing_source_reuse.py": "bdbfff175232f9595b5180bd64b1f288f659e8964d4f7306311d7c45f3c940ba",
    "src/engine/automation/ordered_intraday_deploy.py": "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
    "src/engine/buy_funnel_sentinel.py": "40b489fff0e1b82edbf36b734424ca7826dbc2c4c8a3b27ee9069c9381e7df2a",
    "src/engine/holding_exit_sentinel.py": "7ae845b51d16bf425337e4758d1f83047f1f4e1c3479d39875523f0e2748012a",
    "src/engine/infrastructure/startup_validation_code_context.py": "355a1eb29a8e7584872f7446cd7b78af4375a72c8d53fe482f2023afab311e59",
    "src/engine/kiwoom_sniper_v2.py": "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
    "src/engine/kiwoom_websocket.py": "ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377",
    "src/engine/monitoring/sentinel_event_scope.py": "5a06206336713a85bbf28e479ae39482cd77549ee9296b9a92b90ef7f61aa559",
    "src/engine/monitoring/sentinel_summary_contract.py": "182f6372e025989b47825e6b9a54b6450e837dd6be772740298d567a965015eb",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
    "src/engine/scalping/market_weakness_research.py": "a98076e2d27f17fc50b25335d9b79b4019d828c4d4b8ade2aa985911af1d5677",
    "src/engine/scalping/pre_submit_delay_observation.py": "225bf41983835e7ab53febd50d0cb42d13ce5b296322887a519a53e24281e8ff",
    "src/engine/sniper_state_handlers.py": "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_SENTINEL_SCOPE_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, REVIEWED_SENTINEL_SCOPE_HASHES[name]) for old in origins)
        for name, origins in {
            "src/engine/buy_funnel_sentinel.py": [
                "4918513346f28c8908b0fe18085663ef662ba2dc03349b4b7822ff1656b908d1",
                "6c41ee5823caa738bdc40c6da07e8b5fe4714976a9efc7668e90dac33a325993",
                "b1836d21a079e7164d3c04629b1bb83e5f9475dda917c34b97802c2e2e3a95b7",
            ],
            "src/engine/holding_exit_sentinel.py": [
                "a02066a6f6538f7b4f855c5cc93ed3b5b4e661f4516c6191cd4859542cc5afdb"
            ],
            "src/engine/kiwoom_sniper_v2.py": [
                "f0289f079fc3f193efe02a0ff3ee7542da5dc3b1689292277372ba526bc4eba7",
                "f88f16a8747ba64edc7594e5936dcf6d7e636fd07d852932635204c44384d4a8",
            ],
            "src/engine/kiwoom_websocket.py": [
                "215a0e3d6388df5938a4d70e8e5afad689fa8087280a3a53b81619a2295e35e3"
            ],
            "src/engine/monitoring/sentinel_event_scope.py": [],
            "src/engine/monitoring/sentinel_summary_contract.py": [
                "06fb351581ad704aae6374589f6b4db288c802dc030e3dcde036ac217c5b8a80",
                "15a789219cfaca8ec81f611b01a1d15456f64c40201e26ef8bb320f607dc8a3c",
                "28e0a5f8a32283c0f9503e1bae045ac2f9129c8bb00a291d3da40c22a9e9d565",
                "c4c20df27d61239aa45d0f2447c5cda85edc2bcb4fff508230cedf14f28a2117",
            ],
            "src/engine/monitoring/submission_bottleneck_monitor.py": [
                "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
                "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
                "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
                "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
            ],
            "src/engine/scalping/pre_submit_delay_observation.py": [
                "99d7b8d5e57ad886433747cee55f8f12c9a71d539577d94adff03543a8ff724d"
            ],
            "src/engine/sniper_state_handlers.py": [
                "2e69e440301dbc3bf4ec7020abc29b4a37b0dfd5dd624480378c7eab491c45d9",
                "8a0c18d2c097b063a8349907f39e6057d43b7ad9ef173e5f6c4e1be48f8b21f9",
                "bd2c589431b0f507b2bbbba31cfc700a22dcab07b914313dc101add2cc9c9686",
                "eaca4d2d23d2764c42e3f7cc2f73d04db0b29bb8115cabac4f10cf48e89d57aa",
                "edfd4af04194182dff2a3ced3952dbfc5dc989d85906409c0172fabadb381419",
            ],
        }.items()
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, REVIEWED_SENTINEL_SCOPE_HASHES[name]) for old in before)
        for name, before in {
            "src/engine/automation/main_trailing_source_assembler.py": [
                "947171df074a8074ebb3d9bcca5710a2b001ccc00a211c58d99113ab5317e77b",
                "af2d5343723e53093eb2fcc8debcf70b7d13c964b448ff10a094d61971ad4d29",
                "d76ee7b7c79ea1d420f4432f9026690b3155f7e815f0dbf1fec66016b51d8e26",
            ],
            "src/engine/automation/main_trailing_source_reuse.py": [
                "4c38cd9add7e87e7a50529f1a0ad379dde4b786fb8405bf02ee1c7e117a280ec",
                "88faf62cd0e01d4b32f5f36ca96b37fdf3a4bd2432e0adcab8ca1c9d8cfd8ac5",
                "acf252905da4704ff54a3adffdd74ecf7c6b9ab056b52b6719fab8be91866b97",
            ],
        }.items()
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, REVIEWED_SENTINEL_SCOPE_HASHES[name]) for old in before)
        for name, before in {
            "src/engine/automation/main_market_weakness_research.py": [
                "375f13bd830a42de09cb9fae28879ab69459f76013e47dd4365207d28d976309",
                "9e704cce559ff4d7cc714feece733ca64380b440a7c3490a219170412656bce8",
                "c7fc0eacb9ec937d28c507a4b7586d1d71425a3719a08c1d8ada65e0404071f9",
                "e78122825224eee72bb3301fd2df7c22230645c5b88103fd32009a186316909b",
            ],
            "src/engine/scalping/market_weakness_research.py": [
                "8e124bee20aadb75fc399b752973434f9ccd0df7c1de675ca5b70af2aa8ab59c"
            ],
        }.items()
    },
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, REVIEWED_SENTINEL_SCOPE_HASHES[name]) for old in before)
        for name, before in {
            "src/engine/automation/ordered_intraday_deploy.py": [
                "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
                "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
                "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
                "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
                "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
                "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
            ]
        }.items()
    },
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_SENTINEL_SCOPE_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_SENTINEL_SCOPE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SENTINEL_SCOPE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_PRE_SENTINEL_SCOPE_VARIANTS.items()
}


# Preserve the actually consumed2b7 profile. The index-only health successor
# must supply every reviewed scope dependency; partial/mixed sets remain invalid.
REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_HASHES = REVIEWED_ENTRY_COST_HASHES
REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_VARIANTS = REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
REVIEWED_DEPLOYED_SENTINEL_SCOPE_HASHES = REVIEWED_SENTINEL_SCOPE_HASHES
REVIEWED_SENTINEL_SCOPE_HASHES = {
    **REVIEWED_SENTINEL_SCOPE_HASHES,
    "src/engine/monitoring/submission_bottleneck_monitor.py": "808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57",
    "src/engine/infrastructure/startup_validation_code_context.py": "eebb9048c5500a5c184c7dcca4810db89ec266722611fa07e4f4c90f66aad1cf",
}
REVIEWED_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_SENTINEL_SCOPE_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    name: (
        pairs
        + tuple(
            (old, REVIEWED_SENTINEL_SCOPE_HASHES[name])
            for old in dict.fromkeys(
                [
                    *(
                        old
                        for old, target in pairs
                        if target == REVIEWED_DEPLOYED_SENTINEL_SCOPE_HASHES.get(name)
                    ),
                    REVIEWED_DEPLOYED_SENTINEL_SCOPE_HASHES[name],
                ]
            )
        )
        if name
        in (
            "src/engine/monitoring/submission_bottleneck_monitor.py",
            "src/engine/infrastructure/startup_validation_code_context.py",
        )
        else pairs
    )
    for name, pairs in REVIEWED_ENTRY_COST_PAIRS.items()
}
REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_SENTINEL_SCOPE_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_SENTINEL_SCOPE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SENTINEL_SCOPE_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_VARIANTS.items()
}

# Observer IO/P5/b67, logical-archive and research retention form one reviewed profile.
# Preserve actually consumed historical profiles; the shared IO owner has no wrapper.
REVIEWED_OBSERVER_IO_HASHES = {
    "src/engine/automation/entry_cancel_wait_tuning.py": "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
    "src/engine/automation/ordered_intraday_deploy.py": "7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026",
    "src/engine/error_detectors/artifact_freshness.py": "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
    "src/engine/infrastructure/startup_validation_code_context.py": "ee715b40b27ddd814128f7c49945d2dfbba08e65cf6c7c23c4a8cbd73594b171",
    "src/engine/lifecycle/research_storage.py": "448514a835975dd28266a985492ff3c352a566b71e18426214498b1f9fd1bf13",
    "src/engine/monitoring/observer_artifact_io.py": "4653b9d9785e129b403b28d4c96c99bba3251dec986779bc8c4d182e5c862cc7",
    "src/engine/monitoring/policy_generation_code_handoff.py": "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902",
    "src/engine/scalping/mechanistic_entry_runtime_policy.py": "2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08",
}
REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES = {
    **REVIEWED_ENTRY_COST_HASHES,
    **REVIEWED_OBSERVER_IO_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, REVIEWED_OBSERVER_IO_HASHES[name]) for old in origins)
        for name, origins in {
            "src/engine/automation/entry_cancel_wait_tuning.py": [
                "38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa",
                "bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e",
                "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
            ],
            "src/engine/automation/ordered_intraday_deploy.py": [
                "404b870046364da476c4df9abb0007312123ea4b4331459f67da6d3c53e183e6",
                "4358273a4a70f58de9dd0bf960e2b146cfd1b5c389a3643cae5b8dda7ffc5756",
                "64e4e2a29ed8fcc47a2e2eaca4fde8a1f492964db98973f1aba37c4ed199ca21",
                "92d30c0ec38266d9fe1cc7abd144c71b7d0227b88fb42d4beb384096bbeb31ab",
                "a6cdc6bebdf22f47a6736d0b7201fd988ad69ffacfe81ee5b40d77bbae5218ed",
                "afa9ca5839c59670f4c38f6898089cd8c743157b87ead058e393d5f78d4e07ab",
                "d56d407f1515ee8a8bfd307f469b175b794f490120aec2b2fe2f98165d5488af",
                "e01bfae9c239223c409da878d2e45a66bccbe6c5b37684f9951badfb4d12c5ae",
                "fcc7c6935434dc1b2e03598bec6fb721997b23cd4c39b6776fa1dfc2afa46423",
            ],
            "src/engine/error_detectors/artifact_freshness.py": [
                "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
                "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
                "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
            ],
            "src/engine/infrastructure/startup_validation_code_context.py": [
                "355a1eb29a8e7584872f7446cd7b78af4375a72c8d53fe482f2023afab311e59",
                "eebb9048c5500a5c184c7dcca4810db89ec266722611fa07e4f4c90f66aad1cf",
            ],
            "src/engine/lifecycle/research_storage.py": [
                "18c0644ea2a6805b9027b2bce4bc7a1b89dbc5e10925d104b38a05a9423b4c35"
            ],
            "src/engine/monitoring/policy_generation_code_handoff.py": [
                "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
                "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
                "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
                "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
                "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
            ],
            "src/engine/monitoring/submission_bottleneck_monitor.py": [
                "00e5a75bdbf7fa812145212820094baa7e04638d5a9c18d4e8011b3b7165abae",
                "0cacfa688b336befe533f2010b3bfaea40d5d2fe778e4ca48d7347071114527e",
                "6e1588b8e5709563f15cdea0705babe7357fed62a27061365ec5ac2425fc2085",
                "808deb51627b4ed17561f168ad2cad808f0181aaac7a754377493912e71d9e57",
                "9c51124b5c07b8ae9039e2e70d1f36da0e3b542136dd24d2ff66ccab642b4ccb",
                "a5a8b7be30b63d0e7990a5761a60a6e0225a563272b15a24c8ccf9fc013f21d8",
            ],
            "src/engine/scalping/mechanistic_entry_runtime_policy.py": [
                "215ac04e8c50c5d18777617b262c7a73b77c2d4d134c26c6f4c88a31dc162867"
            ],
        }.items()
    },
}
REVIEWED_OBSERVER_IO_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_OBSERVER_IO_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_OBSERVER_IO_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_OBSERVER_IO_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS.items()
}

# Keep the actually consumed observer profile intact for Main preparation.
# Any submit-repair member selects one complete reviewed successor, never a mix.
REVIEWED_PRE_SUBMIT_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "52a87252121e687de0674cfea5ef565cb183032b0962e8fbee90a7d656b59fe5",
    "src/engine/monitoring/policy_generation_code_handoff.py": "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
    "src/engine/monitoring/runtime_performance.py": "ad937198678bef9cc5ef62e6aa41d9b980a0427d456608a94a1317b4fcd3cb39",
    "src/engine/scalping/reversal_evaluation_context.py": "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
    "src/engine/sniper_state_handlers.py": "56a0613b596418c0ade581aabedef12d38371ff7d4d2af9fffea2cc00665dd20",
    "src/trading/entry/physical_send_guard.py": "1d5d6f7feb0fba4062d770db52dc74d0a8fca8dbdd10b48e0485c9ec80865c27",
}
REVIEWED_PRE_SUBMIT_ENTRY_COST_HASHES = {
    **REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES,
    **REVIEWED_PRE_SUBMIT_HASHES,
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (old, current)
            for old in dict.fromkeys(
                [
                    *(
                        origin
                        for origin, target in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                        if target == REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES.get(name)
                    ),
                    REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES.get(name, previous[name]),
                ]
            )
        )
        for name, current in REVIEWED_PRE_SUBMIT_HASHES.items()
        for previous in [
            {
                "src/engine/infrastructure/startup_validation_code_context.py": "ee715b40b27ddd814128f7c49945d2dfbba08e65cf6c7c23c4a8cbd73594b171",
                "src/engine/monitoring/policy_generation_code_handoff.py": "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
                "src/engine/monitoring/runtime_performance.py": "3414c2eee58fc8c5547b11ad6786f1775b20d4cfb6e9b0ce78ed16e17a34e5d4",
                "src/engine/scalping/reversal_evaluation_context.py": "fb5d1ffb46da13d69390c84c3d2e83de03842bebb3978d3a22bbf6fb6bb4d654",
                "src/engine/sniper_state_handlers.py": "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
                "src/trading/entry/physical_send_guard.py": "73b332cc40d021cd1b62b00cf140b8ee2abdca19007fd161d4b17ab57056e946",
            }
        ]
    },
}
REVIEWED_PRE_SUBMIT_DEPENDENCY_VARIANTS = {
    (key[0], REVIEWED_PRE_SUBMIT_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_PRE_SUBMIT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PRE_SUBMIT_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_OBSERVER_IO_DEPENDENCY_VARIANTS.items()
}

# Exact native BUY cost consumer; preserve the already consumed observer profile.
REVIEWED_NATIVE_BUY_COST_HASHES = {
    "src/engine/automation/main_startup_validation.py": "e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64",
    "src/engine/automation/policy_generation_fixture_validation.py": "65a54013574589331515057cba2c28abca8d794aebec133bb7f51395a0ab555c",
    "src/engine/automation/tuning_performance_control_tower.py": "3f47b1381a43e0ef5f44fe99ebc8774e8666fabe3e81578694fbdf2772762f8d",
    "src/engine/infrastructure/startup_validation_code_context.py": "94d6a8f4d3e5266523512f77fc05b706c0d26b0a28bf3bebb86dc2e863853337",
    "src/engine/infrastructure/startup_validation_isolation.py": "42715b0545c044c2ccee975c6109f42195092adc3595a0e16c2535957ec283cb",
    "src/engine/kiwoom_websocket.py": "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
    "src/engine/lifecycle/broker_cost_allocation.py": "021f0a60d6569d0fe02dd619333b7af2f8bcfa0858601b30d93f2847be1c11c9",
    "src/engine/monitoring/policy_generation_code_handoff.py": "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
    "src/engine/runtime_approval_summary.py": "cabe6bfd2bcde43ff81988905dc2149e48c809e80f535b03d28b0338bc11b1fe",
    "src/engine/scalping/holding_path_vote_policy.py": "6aaf70d617961fee9a8aa18a3db19efd54cedcefc9a51aa1bce02ed91abd430e",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "87f78306653fc9f51d890a3531752301589782639b1832ad38a24f7c29c4215d",
    "src/engine/scalping/initial_quantity_policy.py": "0dc2ed9f75960006ec08e4f5eb7606dc1ee5b501ebcaf3507e0af6f8c8d12dca",
    "src/engine/sniper_state_handlers.py": "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
    "src/scanners/scalping_scanner.py": "e3b93e6526caab14d4870bc2550c7efdbb841d86b65abc9cd1f36b8d7c21f90c",
    "src/scanners/zero_base_discovery_runtime.py": "b27a13a0e24a3b07b3161defb97271a73bcc4d214ce2ff419d10d09bc46ce606",
    "src/utils/pipeline_event_logger.py": "67fa82fe4f022123a529f13efa14a0b13a20ef1975210c45b2a5deae3b675b3d",
}
REVIEWED_NATIVE_BUY_COST_PROFILE = {
    **REVIEWED_PRE_SUBMIT_ENTRY_COST_HASHES,
    **REVIEWED_NATIVE_BUY_COST_HASHES,
}
REVIEWED_NATIVE_BUY_COST_VARIANTS = {
    (key[0], REVIEWED_NATIVE_BUY_COST_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_NATIVE_BUY_COST_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_NATIVE_BUY_COST_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRE_SUBMIT_DEPENDENCY_VARIANTS.items()
}
REVIEWED_NATIVE_BUY_ORIGINAL_HASHES = {
    "src/engine/automation/main_startup_validation.py": "fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c",
    "src/engine/automation/policy_generation_fixture_validation.py": "28ec0362fddac74b6a1ad9230b4729879faccdf1e67ab9245e27eae5c4b45331",
    "src/engine/automation/tuning_performance_control_tower.py": "9172370837eed5724bc16fcd483cdaaa9ea2144a92f06ba55d10df91369569b1",
    "src/engine/infrastructure/startup_validation_code_context.py": "ee715b40b27ddd814128f7c49945d2dfbba08e65cf6c7c23c4a8cbd73594b171",
    "src/engine/infrastructure/startup_validation_isolation.py": "475bbdf7f45d7979e7cb687fe8a68a86e4d4c3e42fe54deb90d8bc049801f7ae",
    "src/engine/kiwoom_websocket.py": "ef70d8fc0fd74416fc1e7a9c27dca68663a1f057b7e2b14041b255a66a9af377",
    "src/engine/lifecycle/broker_cost_allocation.py": "404a1fb1f49683eba1e0443b74758cda11fd8b62452e49f229808b7e5769afae",
    "src/engine/monitoring/policy_generation_code_handoff.py": "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
    "src/engine/runtime_approval_summary.py": "a79d492129b3222a25711d1f1086b37c2714f50c3920b2973e74f518a97ef43d",
    "src/engine/scalping/holding_path_vote_policy.py": "f66fa049d9f15c51169015bd44c0464d4de540726d164d0c610e8fb9c51d8c85",
    "src/engine/scalping/initial_quantity_monitor_projection.py": "c0ac0738df35657d770b4c7a1a7c0490a0ab4bc8756aa1c19215ad2661dead8b",
    "src/engine/scalping/initial_quantity_policy.py": "f8e29defaefb8128834b22e19404c75037686d5e107961f3f173996895eebbdd",
    "src/engine/sniper_state_handlers.py": "b3b2965f65f33e5e5bf52fd960757d6bdbe6b5a63e6844bd95f5dc1d5353ea1d",
    "src/scanners/scalping_scanner.py": "ea6188939ecc11462923d4746d27d38042aadd06f4dcd02d14cea7b2e5f8123b",
    "src/scanners/zero_base_discovery_runtime.py": "dc058e9520482506a7659ae9cbefe1e7ce2a3ac0f2dde0b8b053742aec0535f4",
    "src/utils/pipeline_event_logger.py": "2e1c150e1b7d21adcb6fa586a15c1e018cdf2e6a2aab13daa067f414d9b4e6d3",
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES.get(
                    name, REVIEWED_NATIVE_BUY_ORIGINAL_HASHES[name]
                )
            }
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_NATIVE_BUY_COST_HASHES.items()
    },
}


# Reviewed continuous holding observation producer and terminal consumer.
# Preserve the actually consumed 9e820 profile above as an independent generation.
REVIEWED_HOLDING_STREAM_HASHES = {
    "src/engine/automation/main_trailing_source_assembler.py": "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
    "src/engine/automation/pre_submit_delay_research_review.py": "79fd3246300d7636c2e8d0c4ba33cbd2d26cf6cbc9a431b1d87f02e0725076d0",
    "src/engine/infrastructure/startup_validation_code_context.py": "5a881b096932962604f6aab3a995378d0246ea30e7cb3c17e3ef7e3b93b2288d",
    "src/engine/kiwoom_sniper_v2.py": "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
    "src/engine/lifecycle/research_json_stream.py": "cfaf531c495730a6ae2f159601153749f8dc53ab297576250e03de61decf796b",
    "src/engine/monitoring/policy_generation_code_handoff.py": "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
    "src/engine/scalping/holding_decision_context.py": "afbcc348707d87032e8dcdc01c2c84c7712fa69e8cbe387342c3708fdd09e49b",
    "src/engine/scalping/trailing_threshold_policy.py": "ff2211f487c9475494e711f26cb1dae0ba11b90b40f6e6790e10c74483a3260b",
    "src/engine/scalping/universal_trailing_replay.py": "2de2182dcf57d4d3f850b57e6583ad3a48eba4618ebf254525970a2da668850a",
    "src/engine/sniper_execution_receipts.py": "83e2d110d5219698c3caf502fe96beb3f24018399706b574076902f63c36647f",
    "src/engine/sniper_state_handlers.py": "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
    "src/utils/pipeline_event_logger.py": "402e7391e0083ee87fdcaa248e9a46aaabd960d8b967a3df419d67b8b735b624",
}
REVIEWED_HOLDING_STREAM_PREVIOUS = {
    "src/engine/automation/main_trailing_source_assembler.py": "b951b49987a039de6b9746f40ae9f3190facb4c42dd28265a1585d02c52ef413",
    "src/engine/automation/pre_submit_delay_research_review.py": "7dc2c312ce3fe14d5f3343d668e22d90f083a214e5ed25144f446e26f6dec8d3",
    "src/engine/infrastructure/startup_validation_code_context.py": "94d6a8f4d3e5266523512f77fc05b706c0d26b0a28bf3bebb86dc2e863853337",
    "src/engine/kiwoom_sniper_v2.py": "02ecf7b4a55042fbcd2a7b4f59bf8602bed6020730f0a8bb326b41d5d6418866",
    "src/engine/lifecycle/research_json_stream.py": "8fd211dc5409ee6a5bdd619bef772255c07687e921b075d473f50f70303a6201",
    "src/engine/monitoring/policy_generation_code_handoff.py": "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
    "src/engine/scalping/holding_decision_context.py": "5d7577896850988b6419996a76db24344f7a612c59ecac339331ca2e841607d2",
    "src/engine/scalping/trailing_threshold_policy.py": "ce1171456cba2374a001ea31d1cda60a4ee2593e4a5c7fca6426c6ed37b4ef1a",
    "src/engine/scalping/universal_trailing_replay.py": "70055c43944d7dac085826c416fd6fffb42bd0a38bde96e928c5ed5b550a4b4f",
    "src/engine/sniper_execution_receipts.py": "f7210ea376fcd04d19e1592d72d0bc4a8261b799422e6161e511a338052eebb1",
    "src/engine/sniper_state_handlers.py": "6a8c1ad86951d2720a91175cda4565d6202e9ff63b0b220b6613166760c84f66",
    "src/utils/pipeline_event_logger.py": "67fa82fe4f022123a529f13efa14a0b13a20ef1975210c45b2a5deae3b675b3d",
}
REVIEWED_HOLDING_STREAM_PROFILE = {
    **REVIEWED_NATIVE_BUY_COST_PROFILE,
    **REVIEWED_HOLDING_STREAM_HASHES,
}
REVIEWED_HOLDING_STREAM_VARIANTS = {
    (key[0], REVIEWED_HOLDING_STREAM_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_HOLDING_STREAM_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_HOLDING_STREAM_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_NATIVE_BUY_COST_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_HOLDING_STREAM_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_HOLDING_STREAM_HASHES.items()
    },
}


# Original issued-policy origins, bound to the complete reviewed successor.
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + pairs
        for name, pairs in {
            "src/engine/automation/main_trailing_source_assembler.py": (
                (
                    "921fcb2621dfd444e029fe6ddd8bd9c1d933c4fbbc0f4dda2ec0b3ae97939fa8",
                    "1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52",
                ),
            ),
            "src/engine/automation/pre_submit_delay_research_review.py": (
                (
                    "159b04fa4b5486e43feba9ca2dee73b7e1f9052926f729cb6169ff0ff89ad2ac",
                    "79fd3246300d7636c2e8d0c4ba33cbd2d26cf6cbc9a431b1d87f02e0725076d0",
                ),
            ),
            "src/engine/infrastructure/startup_validation_code_context.py": (
                (
                    "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
                    "5a881b096932962604f6aab3a995378d0246ea30e7cb3c17e3ef7e3b93b2288d",
                ),
            ),
            "src/engine/kiwoom_sniper_v2.py": (
                (
                    "522bc4a71a1375144db798b2e451fcee03a44e80d57323c7996fa365bf20c71c",
                    "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
                ),
            ),
            "src/engine/lifecycle/research_json_stream.py": (
                (
                    "53bd6a0cec6435ff0cfb399ad75fc9edd0b479463c06dea77bc5cae5e59db4b6",
                    "cfaf531c495730a6ae2f159601153749f8dc53ab297576250e03de61decf796b",
                ),
            ),
            "src/engine/scalping/holding_decision_context.py": (
                (
                    "783f95ab9cd3ef2813151949cdf6aa2c2ab6ed3a1443ae60d6600d21dcd52898",
                    "afbcc348707d87032e8dcdc01c2c84c7712fa69e8cbe387342c3708fdd09e49b",
                ),
            ),
            "src/utils/pipeline_event_logger.py": (
                (
                    "fde49c9a27dfc5c858d765353a0a898ac45728d57ecfa0526c4a6df4fef4c99e",
                    "402e7391e0083ee87fdcaa248e9a46aaabd960d8b967a3df419d67b8b735b624",
                ),
            ),
        }.items()
    },
}


# Compose the existing native-invalidation and submit-timing reviews for the
# issued 726179 origin. No unreviewed intermediate or runtime hash is accepted.
REVIEWED_ENTRY_COST_PAIRS["src/engine/monitoring/runtime_performance.py"] += (
    (
        "80089ba158ce24d79df5f37de8d521321bc2a40f988d5f394e354db637cce78d",
        "ad937198678bef9cc5ef62e6aa41d9b980a0427d456608a94a1317b4fcd3cb39",
    ),
)


# Exact two-edge reviews for issued 726179 policy ancestry. The complete
# generation profile remains mandatory; unconnected origins remain rejected.
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + pairs
        for name, pairs in {
            "src/engine/automation/main_trailing_source_reuse.py": (
                (
                    "272f0753cce9fc43324063a2d690394e844630f6eab8da7dace87596620ac0ab",
                    "bdbfff175232f9595b5180bd64b1f288f659e8964d4f7306311d7c45f3c940ba",
                ),
            ),
            "src/engine/automation/ordered_intraday_deploy.py": (
                (
                    "d67e4f0b2c1ae0d7a88de0cffaeb8f76cb114e4b34c55dfb5575b0e464a17d90",
                    "7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026",
                ),
            ),
            "src/engine/automation/postclose_finalization_generation.py": (
                (
                    "1ac7c5d9a4269f73a9a9f82656d22a277689813b32c94b3a526e0b37452d3041",
                    "ba7533068261dadc984418175d3dcb5e7bba70110e359de4aba488a52cc8c0e3",
                ),
            ),
            "src/engine/automation/prepared_policy_code_handoff.py": (
                (
                    "9ef09608077aa02c25bdd40d8bc33344bf0e10dbde18cae0fdcf434b0c6efaf8",
                    "5bf1ed07810e5beeba889493c83bdd5b8eaa913b1710fc534c8a20246e1422e3",
                ),
            ),
            "src/engine/holding_exit_sentinel.py": (
                (
                    "5bc00325005b6d4346dc896c21741cec0e61fcd9904c6c947ae7774ce5e031e4",
                    "7ae845b51d16bf425337e4758d1f83047f1f4e1c3479d39875523f0e2748012a",
                ),
            ),
            "src/engine/kiwoom_websocket.py": (
                (
                    "5016a58492f59a0728d9bbf979d76cc59a10de4681e92a5fcac21bf6c1cffde2",
                    "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
                ),
            ),
            "src/engine/monitoring/submission_bottleneck_monitor.py": (
                (
                    "9b6066255a77a38bd869bfcf2e3aacd4814bf7742f306428d04ed1f1741908d1",
                    "f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902",
                ),
            ),
            "src/engine/runtime_approval_summary.py": (
                (
                    "91dbb00d92f0aeb51de17f92dc0bea31591f1d41ad3bcab24579c8cb3c1dd14d",
                    "cabe6bfd2bcde43ff81988905dc2149e48c809e80f535b03d28b0338bc11b1fe",
                ),
            ),
            "src/engine/scalping/continuous_reversal_source.py": (
                (
                    "96f1edc13538616832ec4270064afcc9a6bacab8274903cd57b2838573a1155d",
                    "0c8e4d4a0ab08c2bb54e115d8071fa5f2b732e99414043b75e2d51b9da914ba0",
                ),
            ),
            "src/engine/scalping/initial_quantity_policy.py": (
                (
                    "806875b857f58895a39ec116ed0a3b619539f7d782fc1996581c1af84c201a34",
                    "0dc2ed9f75960006ec08e4f5eb7606dc1ee5b501ebcaf3507e0af6f8c8d12dca",
                ),
            ),
            "src/engine/scalping/reversal_code_handoff.py": (
                (
                    "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
                    "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
                ),
            ),
            "src/engine/scalping/reversal_source_diagnostics.py": (
                (
                    "bf7dd538048888ce9793ccdf39a6c5c4a463c9e3379f4c3c5c1a09173f543eb8",
                    "bd5e37ae27b48464ea62f07b949979d3d5b112352f6e0e400c16e8f4fbc3cbee",
                ),
            ),
            "src/engine/scalping/zero_base_probe.py": (
                (
                    "c91d31899343d4381a30edaa82046a65ace8cb6a55f33c03cd5851d9cd1e689f",
                    "104746b1f9a2144bc6c6955c022e9ad925cba688300e715392554ec2c81e097c",
                ),
            ),
            "src/scanners/scalping_scanner.py": (
                (
                    "3280979b86c4bb10231b7886f591aba239c453b3e37d1ba79b8c2fdb1d4f477f",
                    "e3b93e6526caab14d4870bc2550c7efdbb841d86b65abc9cd1f36b8d7c21f90c",
                ),
            ),
            "src/scanners/zero_base_discovery_runtime.py": (
                (
                    "47347d90b4dad70233a55bca9dc282da20b14b3be4fda4090291ce1d7e66bb57",
                    "b27a13a0e24a3b07b3161defb97271a73bcc4d214ce2ff419d10d09bc46ce606",
                ),
            ),
            "src/utils/kiwoom_utils.py": (
                (
                    "a21607460d8bc4817b80499414a796bf4ac8a3e8af10846c2682e1daa12e152f",
                    "498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323",
                ),
            ),
        }.items()
    },
}


# Exact reviewed offline REST outcome integration; retain the issued stream profile.
REVIEWED_MACHINE_REST_HISTORY_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "0ca493e04eecc4031d75de2d3dfcc076fca47fbc6fb874843f29ab51ff7adebe",
    "src/engine/scalping/continuous_reversal.py": "7c1d8a3f8f093ec3fde3d8deda7c411ddb3230bb3115086a28b5f811204879cc",
    "src/engine/scalping/continuous_reversal_branch_postclose.py": "cf39f092eae8557ed031c82e4e24cfc32cc31279e60eb9069ae789e2500c43f8",
    "src/engine/scalping/continuous_reversal_operating_postclose.py": "60b420adf69789175491963858bad6ad26d38399d00294010de2079612e6b194",
    "src/engine/scalping/continuous_reversal_path_postclose.py": "7c8530c2419ca0465ec530c2cdde6125b4984326babd1ff2bbff05e32f150f5b",
    "src/engine/scalping/continuous_reversal_postclose.py": "212965dc89048c663bad5083d0f3a9fb21fb315825359a9a347428c20926d69c",
    "src/engine/scalping/continuous_reversal_registered_postclose.py": "65f2cd48607abfae735836d5f4c5f60bad9d8866e0d4386b1c8e22756516899d",
    "src/engine/scalping/reversal_cumulative_postclose.py": "990d9dd982e2fe6976fe070588e39e6a2aa46830344e3ea449ce77c93c4b68fc",
    "src/trading/market/completed_history.py": "381740faff9ca4c00ff6f117a076f444f9762985d1fb13a8d0e5b3581ff75ed5",
}
REVIEWED_MACHINE_REST_HISTORY_PREVIOUS = {
    "src/engine/infrastructure/startup_validation_code_context.py": "5a881b096932962604f6aab3a995378d0246ea30e7cb3c17e3ef7e3b93b2288d",
    "src/engine/scalping/continuous_reversal.py": "17b73fbd524814faa53895148364758716aac406ca41761768cb69d430178030",
    "src/engine/scalping/continuous_reversal_branch_postclose.py": "7525d0c8bb68b9eb57d4bdc29462b33d5f35bc6b62f48b41d9a2e0a2c58b4c4c",
    "src/engine/scalping/continuous_reversal_operating_postclose.py": "2fc75be21c110341ac4596f08f8a3bcdb42adfd4e3ba8322f601337b84ab8441",
    "src/engine/scalping/continuous_reversal_path_postclose.py": "ce4f350b3e372e6287d86ed8e070f8eb4679282964ab2a64b6b626c364269af2",
    "src/engine/scalping/continuous_reversal_postclose.py": "d294d3fab9ef36e29b0b15007b0d22c47e1572f3b36de25d72802873f2568dda",
    "src/engine/scalping/continuous_reversal_registered_postclose.py": "e725b5d63af61268760ebdbf760d150f38f5d19790261d6f978f803a48f86b29",
    "src/engine/scalping/reversal_cumulative_postclose.py": "6adcd6526ca315d53e60d4817cda3cfec1b8ed8db30d624a1c212d6005dbba87",
    "src/trading/market/completed_history.py": "dec2b7afcb5fdaab16980d046a124ddac384515b7e3400249d73acaacaf348e7",
}
REVIEWED_MACHINE_REST_HISTORY_PROFILE = {
    **REVIEWED_HOLDING_STREAM_PROFILE,
    **REVIEWED_MACHINE_REST_HISTORY_HASHES,
}
REVIEWED_MACHINE_REST_HISTORY_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/scalping/continuous_reversal_postclose.py",
        "selector_sha256": REVIEWED_MACHINE_REST_HISTORY_HASHES[
            "src/engine/scalping/continuous_reversal_postclose.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_MACHINE_REST_HISTORY_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_MACHINE_REST_HISTORY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_HOLDING_STREAM_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_MACHINE_REST_HISTORY_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_MACHINE_REST_HISTORY_HASHES.items()
    },
}


# Reviewed report-only auxiliary fixture succession. Retain the consumed REST profile.
REVIEWED_AUXILIARY_CAPABILITY_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "8ef7d406ba2b9af7504321f14114e4eea6a31c963d56048a26745f2a62cfd0de",
    "src/engine/monitoring/policy_generation_code_handoff.py": "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
}
REVIEWED_AUXILIARY_CAPABILITY_PREVIOUS = {
    "src/engine/infrastructure/startup_validation_code_context.py": "0ca493e04eecc4031d75de2d3dfcc076fca47fbc6fb874843f29ab51ff7adebe",
    "src/engine/monitoring/policy_generation_code_handoff.py": "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
}
REVIEWED_AUXILIARY_CAPABILITY_PROFILE = {
    **REVIEWED_MACHINE_REST_HISTORY_PROFILE,
    **REVIEWED_AUXILIARY_CAPABILITY_HASHES,
}
REVIEWED_AUXILIARY_CAPABILITY_VARIANTS = {
    key: {
        **value,
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_AUXILIARY_CAPABILITY_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_AUXILIARY_CAPABILITY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_MACHINE_REST_HISTORY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_AUXILIARY_CAPABILITY_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_AUXILIARY_CAPABILITY_HASHES.items()
    },
}


# Exact numeric/replay successor; the source-flush integration; consumed auxiliary/REST/holding profiles stay intact.
REVIEWED_NUMERIC_REPLAY_HASHES = {
    "src/engine/ai_engine_openai.py": "278da9793f4415c1609f17532e68a82cb4a6e6c6d7a70f0bc4975354f3f2a4a2",
    "src/engine/automation/ordered_intraday_deploy.py": "d14017560b8664ea2b1fe39a6c146840807c875178764e014683da4713e8bc9b",
    "src/engine/infrastructure/startup_validation_code_context.py": "e81848fa4e85f082005b905ff5e71390dc2bfec114be3ef9fd550bea2c4dceba",
    "src/engine/kiwoom_sniper_v2.py": "51b75d2cd21cc8a66c9fc5bcda6119c102d0f2256b6f569ea5e05194e15f1ce4",
    "src/engine/lifecycle/avg_down_policy_replay.py": "7e11c813a94653b142f2682946b78a9bda3fd700c9300f4112e7209771787096",
    "src/engine/log_archive_service.py": "1a3f94cc9e50ab7768cd7b7fb2953a3c0787a15f5b99e7a9f40231a41f8b81f2",
    "src/engine/monitoring/policy_generation_code_handoff.py": "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
    "src/engine/monitoring/policy_generation_contract.py": "9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9",
    "src/engine/monitoring/runtime_performance.py": "a0223bb985173ed7029ff26cabf1db76d45db690fff22bbf0cf336640a1a4ada",
    "src/engine/scalping/entry_candle_context.py": "1acd9a0b1c5fee0cb25835b6a249381e766aff3d54a0481e257466327c1d6f5f",
    "src/engine/scalping/mechanistic_entry_runtime_policy.py": "439eff9acb93d3ecd5513d137ee03bdb9c33fd9fde60dcdbb7638058f2dc9951",
    "src/engine/scalping/micro_reversion/path_journal.py": "91308bcba1d7162cdedcd47918b50400bc5a8e1f8afee66aa50b8f975b5672d1",
    "src/engine/scalping/reversal_evaluation_context.py": "fe093211bb7677bc6568e31dbc1d8c425ef15482163eacd24844d041856868c2",
    "src/engine/sniper_scale_in.py": "4a60e43a414c26b2e4f8d809b45bb339c2d8c04c16ca229fa8c334868c29a506",
    "src/engine/sniper_state_handlers.py": "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
    "src/utils/numeric.py": "2da99f1423eefd7ac55e0c30c8d62d4b9f175944b7017aae46bc21ae23e02273",
}
REVIEWED_NUMERIC_REPLAY_PREVIOUS = {
    "src/engine/ai_engine_openai.py": "9f9a3561db4dd3247ef14a47e3346f41453c98c0bf42b5ef7ff0be4a2a5b5e56",
    "src/engine/automation/ordered_intraday_deploy.py": "7f52b1d056bf13f16791c4d5d41e8ca4ba4a9715a77176403c1dff97e95d0026",
    "src/engine/infrastructure/startup_validation_code_context.py": "8ef7d406ba2b9af7504321f14114e4eea6a31c963d56048a26745f2a62cfd0de",
    "src/engine/kiwoom_sniper_v2.py": "bbbe478a566caa33fe2fcf8889d3e9c05dd15409e10f70eb97caaef76595e365",
    "src/engine/lifecycle/avg_down_policy_replay.py": "26ec5374924617f9beef1bda42a7b2433c583abbae73407da360e4d866ed35cd",
    "src/engine/log_archive_service.py": "18e912bb93cf937548077466fc4fd510c13fff73823e2b1c2510a19481e980af",
    "src/engine/monitoring/policy_generation_code_handoff.py": "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
    "src/engine/monitoring/policy_generation_contract.py": "ff28f004a26a287394d45c4bebfe14a22a144369e8354ea23df0a0c25f7b0028",
    "src/engine/monitoring/runtime_performance.py": "ad937198678bef9cc5ef62e6aa41d9b980a0427d456608a94a1317b4fcd3cb39",
    "src/engine/scalping/entry_candle_context.py": "754f9ddcdead55df23259ba21cef5f324023831bf1eaa06e44b5275efa0c48b1",
    "src/engine/scalping/mechanistic_entry_runtime_policy.py": "2b8653cc8f30209992c2ac34690846e3d5d7607114b95560aafbf1445d509c08",
    "src/engine/scalping/micro_reversion/path_journal.py": "5d8e09413c104fc7392bca32c0804ee4d0142a61ecfb2674cf207089dc943dd6",
    "src/engine/scalping/reversal_evaluation_context.py": "7a20e1c32f0a4b54ebb25ae8970939184cbe9cef2e590adf68fb2791561e2458",
    "src/engine/sniper_scale_in.py": "11d6a2313c16d28e257cb0fc0cd4e2a44b7e6c2d29eb8c692509735bfdb08be3",
    "src/engine/sniper_state_handlers.py": "0fe0c01839a6186b0ef45aa8112075d13220ebc64f299656164aa007a84b1541",
}
REVIEWED_NUMERIC_REPLAY_PROFILE = {
    **REVIEWED_AUXILIARY_CAPABILITY_PROFILE,
    **REVIEWED_NUMERIC_REPLAY_HASHES,
}
REVIEWED_NUMERIC_REPLAY_VARIANTS = {
    (key[0], REVIEWED_NUMERIC_REPLAY_HASHES.get(key[0], key[1])): {
        **value,
        "dependencies": {**value["dependencies"], **REVIEWED_NUMERIC_REPLAY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_NUMERIC_REPLAY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AUXILIARY_CAPABILITY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_NUMERIC_REPLAY_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_NUMERIC_REPLAY_HASHES.items()
        if name in REVIEWED_NUMERIC_REPLAY_PREVIOUS
    },
}


# Exact reviewed listing/SOR successor; retain the complete consumed REST profile.
REVIEWED_AFTERMARKET_LISTING_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "c2ad2370a32236543bdc70991274a83a109ed48ccd24d1eac4a7206f987034f5",
    "src/engine/kiwoom_orders.py": "8b256c9e5802ad9afdf3b8806ce77420c3b425b107bb4aa6abedcd2e73f6ccbc",
    "src/engine/monitoring/policy_generation_code_handoff.py": "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
    "src/engine/sniper_state_handlers.py": "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
    "src/trading/market/aftermarket_eligibility.py": "63d81fe30f23cca232304c84a3f4e0c4e9e23a2f447c74d6b356798471417d4a",
    "src/trading/market/session_contract.py": "52a9574a5e12b2437a727607c1f6fea93480861e1abb37076e9bb39ea920398c",
    "src/utils/kiwoom_utils.py": "ef692b544c8ac01c90ab56413aa236935bb5740b7edfe27cf5c30217948c0e95",
}
REVIEWED_AFTERMARKET_LISTING_PREVIOUS = {
    "src/engine/infrastructure/startup_validation_code_context.py": "e81848fa4e85f082005b905ff5e71390dc2bfec114be3ef9fd550bea2c4dceba",
    "src/engine/kiwoom_orders.py": "32e93c49a880e1f3a393ec0367cf1339dbc3ef00c689c821b45b159872c423d9",
    "src/engine/monitoring/policy_generation_code_handoff.py": "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
    "src/engine/sniper_state_handlers.py": "ea59d6365ae1707af457535650937c49977997d9bc516bb8cc141f07da6eea86",
    "src/trading/market/aftermarket_eligibility.py": "f28f3dd45c2d9b1aee2dcb64898d8cbecb85798bb812b058741d7f011fb45a2b",
    "src/trading/market/session_contract.py": "dfd0ff3b2a28d8d6581a44762e5b618ae807fdc1c45d7f8cd3128b76be83573c",
    "src/utils/kiwoom_utils.py": "498cfc4bc4ce9b1cbe13f0b70967da7f2dbb113c6d70563924b03c98d371b323",
}
REVIEWED_AFTERMARKET_LISTING_PROFILE = {
    **REVIEWED_NUMERIC_REPLAY_PROFILE,
    **REVIEWED_AFTERMARKET_LISTING_HASHES,
}
REVIEWED_AFTERMARKET_LISTING_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/trading/market/aftermarket_eligibility.py",
        "selector_sha256": REVIEWED_AFTERMARKET_LISTING_HASHES[
            "src/trading/market/aftermarket_eligibility.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_AFTERMARKET_LISTING_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_AFTERMARKET_LISTING_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_NUMERIC_REPLAY_VARIANTS.items()
}
# Trigger keys also bind the new reviewed consumer bytes, using the same full
# dependency/contract generation; individual predecessor mixtures still fail.
for (_trigger, _old_sha), _variant in tuple(
    REVIEWED_AFTERMARKET_LISTING_VARIANTS.items()
):
    if _trigger in REVIEWED_AFTERMARKET_LISTING_HASHES:
        REVIEWED_AFTERMARKET_LISTING_VARIANTS[
            (_trigger, REVIEWED_AFTERMARKET_LISTING_HASHES[_trigger])
        ] = _variant
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_AFTERMARKET_LISTING_PREVIOUS[name]}
            | {
                origin
                for origin, successor in REVIEWED_OPERATOR_MARKET_PAIRS.get(name, ())
                if successor == REVIEWED_AFTERMARKET_LISTING_PREVIOUS[name]
            }
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_AFTERMARKET_LISTING_HASHES.items()
    },
}


# Report-only legacy preflight lineage successor; preserve the consumed listing generation.
REVIEWED_SCANNER_PREFLIGHT_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "21fdf9d9229c558edc70361412735a1be36b483e7eb841665a1d5659c45f7387",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "038d0b162dfd801d10fc23a27f06d062b0f917ec306c942314ee89c6779d3dda",
}
REVIEWED_SCANNER_PREFLIGHT_PREVIOUS = {
    "src/engine/infrastructure/startup_validation_code_context.py": "c2ad2370a32236543bdc70991274a83a109ed48ccd24d1eac4a7206f987034f5",
    "src/engine/monitoring/submission_bottleneck_monitor.py": "f8d68d78e8423db51d4a2f8786c786ea1a53def58f43cb3019d6d79a58dc5902",
}
REVIEWED_SCANNER_PREFLIGHT_PROFILE = {
    **REVIEWED_AFTERMARKET_LISTING_PROFILE,
    **REVIEWED_SCANNER_PREFLIGHT_HASHES,
}
REVIEWED_SCANNER_PREFLIGHT_VARIANTS = {
    key: {
        **value,
        "selector_path": "src/engine/monitoring/submission_bottleneck_monitor.py",
        "selector_sha256": REVIEWED_SCANNER_PREFLIGHT_HASHES[
            "src/engine/monitoring/submission_bottleneck_monitor.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_SCANNER_PREFLIGHT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_SCANNER_PREFLIGHT_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AFTERMARKET_LISTING_VARIANTS.items()
}
for (_trigger, _old_sha), _variant in tuple(
    REVIEWED_SCANNER_PREFLIGHT_VARIANTS.items()
):
    if _trigger in REVIEWED_SCANNER_PREFLIGHT_HASHES:
        REVIEWED_SCANNER_PREFLIGHT_VARIANTS[
            (_trigger, REVIEWED_SCANNER_PREFLIGHT_HASHES[_trigger])
        ] = _variant
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_SCANNER_PREFLIGHT_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_SCANNER_PREFLIGHT_HASHES.items()
    },
}


# Exact closed-scanner diagnostic successor; consumed preflight remains intact.
REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "5b1f9610fd8eda6353e8911cf558beb9d40f764cbd11472ddb883454d3355d6e",
    "src/engine/error_detectors/artifact_freshness.py": "a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27",
    "deploy/run_threshold_cycle_postclose.sh": "ce9cf7c699628ec67466c79890b135c9cea46f268381192c722e6259fd86bfac",
}
REVIEWED_CLOSED_SCANNER_PREVIOUS_PROFILE = {
    **REVIEWED_SCANNER_PREFLIGHT_PROFILE,
    **REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES,
}
REVIEWED_CLOSED_SCANNER_PREVIOUS_VARIANTS = {
    (key[0], REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/error_detectors/artifact_freshness.py",
        "selector_sha256": REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES[
            "src/engine/error_detectors/artifact_freshness.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SCANNER_PREFLIGHT_VARIANTS.items()
}

REVIEWED_CLOSED_SCANNER_HASHES = {
    **REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES,
    "src/engine/infrastructure/startup_validation_code_context.py": "5890164cb152c1f408347ea5703b699b5c8ec8cdf225819314c52bbc76776681",
    "src/engine/error_detectors/artifact_freshness.py": "6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa",
    "src/engine/scalping/reversal_code_handoff.py": "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
}
REVIEWED_CLOSED_SCANNER_PROFILE = {
    **REVIEWED_SCANNER_PREFLIGHT_PROFILE,
    **REVIEWED_CLOSED_SCANNER_HASHES,
}
REVIEWED_CLOSED_SCANNER_VARIANTS = {
    (key[0], REVIEWED_CLOSED_SCANNER_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/error_detectors/artifact_freshness.py",
        "selector_sha256": REVIEWED_CLOSED_SCANNER_HASHES[
            "src/engine/error_detectors/artifact_freshness.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_CLOSED_SCANNER_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_CLOSED_SCANNER_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SCANNER_PREFLIGHT_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                REVIEWED_SCANNER_PREFLIGHT_PROFILE[name],
                REVIEWED_CLOSED_SCANNER_PREVIOUS_PROFILE[name],
            }
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_CLOSED_SCANNER_HASHES.items()
    },
}


# Complete reviewed postclose source-repair successor, including weekend custody.
# Historical generations remain exact; partial/mixed successors are rejected.
REVIEWED_POSTCLOSE_SOURCE_PREVIOUS = {
    "src/engine/automation/entry_cancel_wait_tuning.py": "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
    "src/engine/kiwoom_websocket.py": "ddc6bab2dfd4adb2d253a420e66eac6bd33c1877b18070023f75c489f9c40730",
    "src/engine/monitoring/rising_missed_intraday_feedback.py": "902ec3543434043e3ee0808bdd724c119a370c43747939ed935af0df4bdb0799",
    "src/engine/observation_source_quality_audit.py": "dd307c98964273da61188a6832fab3de0b402c5cdd97bf69f063721b096c4ed6",
    "src/engine/scalping/ai_action_outcome_calibration.py": "a300563f9c78eb6365a24eb1c2afa67872aaf2fc287ac7d4c8aad69907bb5aed",
    "src/engine/scalping/compact_auxiliary_paired_replay.py": "792619031c87b993dd32fcff8b9821fbfbc464641ff1ea246c6871db97e26d67",
    "src/engine/scalping/micro_reversion/canary_monitor.py": "1a767cc4e34ac8add1ec4318e305317f6faa35c469951dd422b45ec814258891",
    "src/engine/scalping/micro_reversion/contracts.py": "ef867b3cfd8c447dd63985af31102dba35b162fd80eeac601b66bc2b7e99d96a",
    "src/engine/scalping/micro_reversion/forward_collector.py": "975d0b0061398a488244c80e869336a4aaac14e37d653b57c8115b83382e465e",
    "src/engine/scalping/reversal_auxiliary_tuning.py": "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
    "src/engine/scalping/reversal_cumulative_postclose.py": "990d9dd982e2fe6976fe070588e39e6a2aa46830344e3ea449ce77c93c4b68fc",
    "src/engine/sniper_post_sell_feedback.py": "fae77491c422f776a48a99da5d855b76e934bdd244055e4cdc44372c8016b41b",
    "src/engine/sniper_state_handlers.py": "b620eff5df4d7d71fc9a8cace747a260b0aad5b1be358e5ef32e2b1deab591f9",
    "src/engine/scalping/reversal_code_handoff.py": "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
    "src/engine/monitoring/policy_generation_code_handoff.py": "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
    "src/engine/infrastructure/startup_validation_code_context.py": "5890164cb152c1f408347ea5703b699b5c8ec8cdf225819314c52bbc76776681",
}
REVIEWED_POSTCLOSE_SOURCE_HASHES = {
    "src/engine/automation/entry_cancel_wait_tuning.py": "860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe",
    "src/engine/kiwoom_websocket.py": "cc5af2d47bcb6d18a64917fcf286e7cad909be5c056e49afedcc9827ea80e637",
    "src/engine/monitoring/rising_missed_intraday_feedback.py": "6c0665007b1274780f6f13e2b5921368b09ca455b4318107704957767f506942",
    "src/engine/observation_source_quality_audit.py": "9004c2adbcf818b956c9ab9f6194c2583ae254ae80f46c0d49a3b09caa32e073",
    "src/engine/scalping/ai_action_outcome_calibration.py": "c570880da2ac0a96fdab41a07aea9ddc8bdf9740d9ba542d364e8b5a4e469486",
    "src/engine/scalping/compact_auxiliary_paired_replay.py": "b9095cf665e68a16817839f1e77df79334a3aa385095703ba616ad69d8106cff",
    "src/engine/scalping/micro_reversion/canary_monitor.py": "ccf52d1c9dfb17af4d43eca012fdceed9bfdfab4e7989e21f765711449c63223",
    "src/engine/scalping/micro_reversion/contracts.py": "670fb3aafc56d9d93057be31bb867d6cc1d50ce01f6c656f00049ebe76020d32",
    "src/engine/scalping/micro_reversion/forward_collector.py": "0922b5db75dc895532ec63f185f2527d09d2e13c788a4b27f84c5369573504fe",
    "src/engine/scalping/reversal_auxiliary_tuning.py": "252aeca80423c1f9881ef6a26dc8baa1c18dad18be8c446cbc7c990b5e3f058a",
    "src/engine/scalping/reversal_cumulative_postclose.py": "f24f1cd9dba38de51a7e3193b506cb8b0e02a8b53fbc94348bf432140782e1f9",
    "src/engine/sniper_post_sell_feedback.py": "7f1b662ce5b135f8d0d1ca14a3b4d584c8b9823360b79bc1864ce5e0dbbf38af",
    "src/engine/sniper_state_handlers.py": "f10df239b1d974d817eed5eb7f99be8f744070643ae3e32f98930434662be95d",
    "src/engine/scalping/reversal_code_handoff.py": "a54226c0232b8a12f049940bc810d5fd6161b9fc7b9154ce66063de3f55b34ec",
    "src/engine/monitoring/policy_generation_code_handoff.py": "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
    "src/engine/infrastructure/startup_validation_code_context.py": "13d85428ca0657171a7e01e9d5ada28e0ef1bd42db630d851072748963fc1ca5",
}
REVIEWED_POSTCLOSE_SOURCE_PROFILE = {
    **REVIEWED_CLOSED_SCANNER_PROFILE,
    **REVIEWED_POSTCLOSE_SOURCE_HASHES,
}
REVIEWED_POSTCLOSE_SOURCE_VARIANTS = {
    (key[0], REVIEWED_POSTCLOSE_SOURCE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/scalping/reversal_code_handoff.py",
        "selector_sha256": REVIEWED_POSTCLOSE_SOURCE_HASHES[
            "src/engine/scalping/reversal_code_handoff.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_POSTCLOSE_SOURCE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_POSTCLOSE_SOURCE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CLOSED_SCANNER_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_POSTCLOSE_SOURCE_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_POSTCLOSE_SOURCE_HASHES.items()
    },
}

# Reviewed frozen auxiliary definition/request readers. Physical source hashes
# remain current; frozen contract fields and registry identities are preserved.
REVIEWED_AUXILIARY_FORMAT_PREVIOUS = {
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "9cc4e362967b0294c0ee43b92cb4ced24f8d40946257567d6becf72253940bce",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "ac517cab3a60a6a224cbabe1ef3b162edf9dfa1992b6ebfa0b4fafbf9e34428a",
    "src/engine/scalping/reversal_auxiliary_registry.py": "80d91c4cd7758621236403d2f4ae4596317d9fa10a8624a616c3699775aedea0",
    "src/engine/scalping/reversal_auxiliary_wire.py": "6f3de130bc8ca5670a4588c8c274399f79b68408ed3312523bdbbe7e0018d578",
    "src/engine/monitoring/policy_generation_contract.py": "9542537f06fc603ffe04b9cb6a1f01ea9689749d0b06becaeda8f0a4c19b20c9",
    "src/engine/monitoring/policy_generation_code_handoff.py": "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
    "src/engine/infrastructure/startup_validation_code_context.py": "13d85428ca0657171a7e01e9d5ada28e0ef1bd42db630d851072748963fc1ca5",
}
REVIEWED_AUXILIARY_FORMAT_HASHES = {
    "src/engine/scalping/reversal_auxiliary_compatibility.py": "77f8d67a5bc89fabab76438d92cad8d719e607c6b5321d56d1e3003ec41aca34",
    "src/engine/scalping/reversal_auxiliary_production_input.py": "324b2d6e41bafaf0eddb1b65069de8f140325bb84e4e3aa42941e397d75d3464",
    "src/engine/scalping/reversal_auxiliary_registry.py": "8699770d1c0d5a51d1b48521dba270cde65ba8d65429f0a3f7c6be3a5105d651",
    "src/engine/scalping/reversal_auxiliary_wire.py": "7751d8cbeb4d1fdfe8411aefee2b0adaf25079abb8ebdf5800222b4fe7c42600",
    "src/engine/monitoring/policy_generation_contract.py": "afb9e016f2772721a249566d51f02b5de0ae20c642446c0909194f21413914e4",
    "src/engine/monitoring/policy_generation_code_handoff.py": "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
    "src/engine/infrastructure/startup_validation_code_context.py": "a54c23586d077630db8bdbe7b012719bbae411dfdf5f33ebae7bfa559a76f3bc",
}
REVIEWED_AUXILIARY_FORMAT_PROFILE = {
    **REVIEWED_POSTCLOSE_SOURCE_PROFILE,
    **REVIEWED_AUXILIARY_FORMAT_HASHES,
}
REVIEWED_AUXILIARY_FORMAT_VARIANTS = {
    (key[0], REVIEWED_AUXILIARY_FORMAT_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/scalping/reversal_auxiliary_compatibility.py",
        "selector_sha256": REVIEWED_AUXILIARY_FORMAT_HASHES[
            "src/engine/scalping/reversal_auxiliary_compatibility.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_AUXILIARY_FORMAT_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_AUXILIARY_FORMAT_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_POSTCLOSE_SOURCE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {REVIEWED_AUXILIARY_FORMAT_PREVIOUS[name]}
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_AUXILIARY_FORMAT_HASHES.items()
    },
}

# Reviewed source/publication and stopped cold preparation workflow. Original
# profiles remain available; all current dependencies are exact Git bytes.
REVIEWED_STOPPED_POSTCLOSE_PREVIOUS = {
    "src/engine/scalping/continuous_reversal_policy.py": "82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b",
    "src/engine/automation/main_startup_validation.py": "14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7",
    "src/engine/automation/next_preopen_readiness.py": "ea29654d0456212dc462275e1474b84f023a3784991e4cff9aabc1da1583b6dd",
    "src/engine/automation/runtime_policy_bootstrap.py": "f852c630ead01b4895eaac2d66b3717907f4a1a99657bb327331ee2b3f2fd883",
    "src/engine/scalping/reversal_auxiliary_tuning.py": "252aeca80423c1f9881ef6a26dc8baa1c18dad18be8c446cbc7c990b5e3f058a",
    "src/engine/scalping/reversal_code_handoff.py": "a54226c0232b8a12f049940bc810d5fd6161b9fc7b9154ce66063de3f55b34ec",
    "src/engine/infrastructure/startup_validation_code_context.py": "a54c23586d077630db8bdbe7b012719bbae411dfdf5f33ebae7bfa559a76f3bc",
}
REVIEWED_STOPPED_POSTCLOSE_HASHES = {
    "src/engine/scalping/continuous_reversal_policy.py": "7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744",
    "src/engine/automation/main_startup_validation.py": "e35cfba631fa0409b87cbe35c87ea2a55464a4479ff1c975156a033e363fa604",
    "src/engine/automation/next_preopen_readiness.py": "a391fd0e9c500cb7ca222f9e6bfd2984a3891b242033f9f9edc99095246b1eff",
    "src/engine/automation/runtime_policy_bootstrap.py": "1d353dac40e7bbace49e6860dffe50965244ac35defb37468970419a76a156e0",
    "src/engine/scalping/reversal_auxiliary_tuning.py": "265a06e3b26c59f616e2819a58dbd27935a4190a7eeea95aaaba6e3e2b1c7992",
    "src/engine/scalping/reversal_code_handoff.py": "b1fdf211b0318caaddeda2ccfdb63710c839c61edb89030633143bdf730396b7",
    "src/engine/infrastructure/startup_validation_code_context.py": "17e301896dcb28e112dee5497559ab33d9ac39c7a02c00f6851b507908fec8e8",
}
REVIEWED_STOPPED_POSTCLOSE_ORIGINS = {
    "src/engine/scalping/continuous_reversal_policy.py": (
        "2c83f7afad5355cda14ef76eb82793ffb1cb982d4e158d260aa71d3c4f1c6cbd",
        "7ec28cd206daf422f275f440b4f98b37ee9878eed3de0c098f908d1813fcb744",
        "82788b5b7832ee26641b80d646269b9568245fea4e480ec79fbaf4400da3238b",
    ),
    "src/engine/automation/main_startup_validation.py": (
        "14209ae80827e4583c236ff8a3426d9a173ec290015046fdc076bb5d18214fd7",
        "b6bd145a6b7b1508a81667d35932dc802b3f1c4123df75ddf991738daea34d54",
        "e71cc4965ab6749c2579a3fe3e864624502fe98269d07c1e362618691fa7ab64",
        "fcf33f73c9b4831339c3215732c5364c9cd11f30147273c30c172fa3f611fd0c",
    ),
    "src/engine/automation/next_preopen_readiness.py": (
        "2e34f2a99ec94609674d7cf267763d651e5b3d4d3e030b8267dd282f325d5c69",
        "ea29654d0456212dc462275e1474b84f023a3784991e4cff9aabc1da1583b6dd",
    ),
    "src/engine/automation/runtime_policy_bootstrap.py": (
        "c7fc85190018ece3a859ba5d569596285a3bb1b21c40a79ab166ee0b2d22f433",
        "f852c630ead01b4895eaac2d66b3717907f4a1a99657bb327331ee2b3f2fd883",
    ),
    "src/engine/scalping/reversal_auxiliary_tuning.py": (
        "0e8f31ed349a6ef17f5f588f8b4bf4180b2f819ab85077a1d51641662611a40a",
        "252aeca80423c1f9881ef6a26dc8baa1c18dad18be8c446cbc7c990b5e3f058a",
        "a8ac3de954b2d6e89e3a46bb49501edc0d35df47621900a1d22b6d8492672412",
        "fe5d737f446e95028a6d5135cfa0f7c76f7047ea108aa89c737d7e5283f64e34",
    ),
    "src/engine/scalping/reversal_code_handoff.py": (
        "16776a22b99bff4054ba99914cd8f7c96e87f6ca9fb1ac041e6a8191723b929d",
        "54b9c0efc38700a0cb8722694cdf84b9df8aa478a28f529b2b618f5532559b5a",
        "65fb740d0ddc41cfb8b5c7e0319ed442287cc0c14fd62ef1514c8378a820948c",
        "6c5b8f3013e055ef54774c1e89be66fda93988aa5792e775bb82bac86636cbf0",
        "852d31cba14cfcb68cfb73603de07b30643969c5e476ddca6dde1f2d3a6fc589",
        "8681d10376f4228bbe5b9d1d012d3510e8abd89470036077c3c0bc69fad63471",
        "a54226c0232b8a12f049940bc810d5fd6161b9fc7b9154ce66063de3f55b34ec",
        "ab61f882f4c8bbaddc0576a5765f4f102e38fd824b44a25341ffc78d647741b5",
        "b77b63fa5afe9b3dff59266cecce73f92880b5256b12c32343a70aeddba63aa9",
        "c5c6edd558c15bd1067e018d2fa84e4670cd213183baa376cf223e1376ba0238",
        "de1ac1086dcaac8d0d5737cc5b0d49374342e19ecd69d698aa43cb2133e3a124",
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        "a54c23586d077630db8bdbe7b012719bbae411dfdf5f33ebae7bfa559a76f3bc",
    ),
}
REVIEWED_STOPPED_POSTCLOSE_PROFILE = {
    **REVIEWED_AUXILIARY_FORMAT_PROFILE,
    **REVIEWED_STOPPED_POSTCLOSE_HASHES,
}
REVIEWED_STOPPED_POSTCLOSE_VARIANTS = {
    (key[0], REVIEWED_STOPPED_POSTCLOSE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/automation/main_startup_validation.py",
        "selector_sha256": REVIEWED_STOPPED_POSTCLOSE_HASHES[
            "src/engine/automation/main_startup_validation.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_STOPPED_POSTCLOSE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_STOPPED_POSTCLOSE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AUXILIARY_FORMAT_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in set(REVIEWED_STOPPED_POSTCLOSE_ORIGINS[name])
            | {old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair}
        )
        for name, current in REVIEWED_STOPPED_POSTCLOSE_HASHES.items()
    },
}

# Separate actual bootstrap producer from selected runtime in a reviewed workflow.
REVIEWED_PRODUCER_IDENTITY_HASHES = {
    "src/engine/automation/runtime_policy_bootstrap.py": "8df8fa94ae94370b483ab816d3c35a51464f15f193458429f252379d536f01e4",
    "src/engine/infrastructure/startup_validation_code_context.py": "15dc6609382751359651f7d744fa616207cf024abe45a5ae4c1fe167134c8b42",
}
REVIEWED_PRODUCER_IDENTITY_PROFILE = {
    **REVIEWED_STOPPED_POSTCLOSE_PROFILE,
    **REVIEWED_PRODUCER_IDENTITY_HASHES,
}
REVIEWED_PRODUCER_IDENTITY_VARIANTS = {
    (key[0], REVIEWED_PRODUCER_IDENTITY_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/automation/runtime_policy_bootstrap.py",
        "selector_sha256": REVIEWED_PRODUCER_IDENTITY_HASHES[
            "src/engine/automation/runtime_policy_bootstrap.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_PRODUCER_IDENTITY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_PRODUCER_IDENTITY_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STOPPED_POSTCLOSE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair
            }
            | {REVIEWED_STOPPED_POSTCLOSE_HASHES[name]}
        )
        for name, current in REVIEWED_PRODUCER_IDENTITY_HASHES.items()
    },
}

# Exact native compressed-report receipt succession; prior profiles retained.
REVIEWED_ARCHIVE_PROJECTION_HASHES = {
    "src/engine/monitoring/policy_generation_validation.py": "caa1f2fcfebceece4910b1594ba4f0507a7e098bbc9912e1e728aeb00e29129a",
    "src/engine/monitoring/policy_generation_code_handoff.py": "d54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b",
    "src/engine/infrastructure/startup_validation_code_context.py": "fb11b341ae539ba32b02871ea69f3e94a1e9b0ea5a295e4de4bc29f57df66e33",
}
REVIEWED_ARCHIVE_PROJECTION_ORIGINS = {
    "src/engine/monitoring/policy_generation_validation.py": (
        "bc67ecca967ae10c638ae92da1ecde21852ebe492c7d205ed0fe3181e6c26238",
        "d925da0cfe6de3d3622cf5433db13ceba31757e1b1b685453fb0f2220ea77ad0",
        "f7dd92bfce26c5d53e5e722ad8ca37a59b29f9d058d6689c7388eb7dc188ecfc",
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
        "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
        "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
        "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
        "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
        "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
        "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
        "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
        "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
        "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
        "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
        "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
        "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        "0ca493e04eecc4031d75de2d3dfcc076fca47fbc6fb874843f29ab51ff7adebe",
        "13d85428ca0657171a7e01e9d5ada28e0ef1bd42db630d851072748963fc1ca5",
        "15dc6609382751359651f7d744fa616207cf024abe45a5ae4c1fe167134c8b42",
        "17e301896dcb28e112dee5497559ab33d9ac39c7a02c00f6851b507908fec8e8",
        "21fdf9d9229c558edc70361412735a1be36b483e7eb841665a1d5659c45f7387",
        "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
        "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
        "355a1eb29a8e7584872f7446cd7b78af4375a72c8d53fe482f2023afab311e59",
        "52a87252121e687de0674cfea5ef565cb183032b0962e8fbee90a7d656b59fe5",
        "5890164cb152c1f408347ea5703b699b5c8ec8cdf225819314c52bbc76776681",
        "5a881b096932962604f6aab3a995378d0246ea30e7cb3c17e3ef7e3b93b2288d",
        "5b1f9610fd8eda6353e8911cf558beb9d40f764cbd11472ddb883454d3355d6e",
        "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
        "5f6b4ccc8c4ea74d5b4012dd02b4607c437587402fdbb325752fe53fc0080947",
        "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
        "741f502aeb6c210fa59a7e1b5a5d5e0264fc1d3cc045a7717a8e403016e8ba3e",
        "8ef7d406ba2b9af7504321f14114e4eea6a31c963d56048a26745f2a62cfd0de",
        "94d6a8f4d3e5266523512f77fc05b706c0d26b0a28bf3bebb86dc2e863853337",
        "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
        "a54c23586d077630db8bdbe7b012719bbae411dfdf5f33ebae7bfa559a76f3bc",
        "b999b1fb1e2ff40dc112cfd88a97ac0e2ecb62975fcbd95ac0c78a1899ad3ea2",
        "be396153e7574f9cbf2d8a90145a373bbdc576adb116553896a9184093bcec47",
        "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
        "c2ad2370a32236543bdc70991274a83a109ed48ccd24d1eac4a7206f987034f5",
        "e81848fa4e85f082005b905ff5e71390dc2bfec114be3ef9fd550bea2c4dceba",
        "ee715b40b27ddd814128f7c49945d2dfbba08e65cf6c7c23c4a8cbd73594b171",
        "eebb9048c5500a5c184c7dcca4810db89ec266722611fa07e4f4c90f66aad1cf",
    ),
}
REVIEWED_ARCHIVE_PROJECTION_PROFILE = {
    **REVIEWED_PRODUCER_IDENTITY_PROFILE,
    **REVIEWED_ARCHIVE_PROJECTION_HASHES,
}
REVIEWED_ARCHIVE_PROJECTION_VARIANTS = {
    (key[0], REVIEWED_ARCHIVE_PROJECTION_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/monitoring/policy_generation_validation.py",
        "selector_sha256": REVIEWED_ARCHIVE_PROJECTION_HASHES[
            "src/engine/monitoring/policy_generation_validation.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_ARCHIVE_PROJECTION_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_ARCHIVE_PROJECTION_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PRODUCER_IDENTITY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current) for origin in REVIEWED_ARCHIVE_PROJECTION_ORIGINS[name]
        )
        for name, current in REVIEWED_ARCHIVE_PROJECTION_HASHES.items()
    },
}

# Exact cancel-cache capability repair; archive and earlier profiles retained.
REVIEWED_CANCEL_CACHE_HASHES = {
    "src/engine/automation/entry_cancel_wait_tuning.py": "7cb52595d1c470f89588b339b83558b990136073ba25e6917bd61e133f5f52b5",
    "src/engine/monitoring/policy_generation_code_handoff.py": "bb62913faa6170362beffc417f974fbb07cca808754112dde0669cd889d1e99f",
    "src/engine/infrastructure/startup_validation_code_context.py": "53737d9fb89696fcfa2a5ff7ca0035be1cb7db838e63c1235395248acb7fe712",
}
REVIEWED_CANCEL_CACHE_ORIGINS = {
    "src/engine/automation/entry_cancel_wait_tuning.py": (
        "38ba95d3965f11f4d31bee05c5a0e4ba28dd2fc7e05505104b491dbf390cd0fa",
        "49c1f36ca4082714705e0e558fa6a931cba7f394fb7f1dca83090884db86dfb4",
        "860304462737c66646146b84f04c5b930664d144442d12ef223e23f7d0b943fe",
        "bdfaaeaac7768f703d181314be45afaf2ecfc983001a6364a60a41ae54882c4e",
        "d557fef76bf6c35ff583c5c52fa23bd3c19039efe14fc48f81db90036edb61aa",
        "e3d227354e85ec9d2dc19cb96e533d1b9f4cb54c5cd2338f7c671eae84a91582",
    ),
    "src/engine/monitoring/policy_generation_code_handoff.py": (
        "056582f3a61d683220910a86107018d5fea3467f5181a7a837498cf94df6d4c2",
        "1a572a81032cd49121e24e2e4925d91d922d9697a65c65db0f473873b656c5cc",
        "1dff8c3fcc6dba15fdc720a36c5070a81805d5124433140b8158f3f50c62b98e",
        "28feb05ecb68ddb0413e45043e92f0d30805a0b4b5b708c894bbdbe12a286411",
        "41ebbc34a2fd015a0cd76ae525c1e6e859edbaa6dc4e4e88e4cc76a44a7a9bef",
        "47db04eba70a27e3fbb5c4078e828be38920859efbf4224e3049582776ff6d5f",
        "4c23315cdd2585bab300b493aae73e8204ab5aa38279b70196b6c34a8779421b",
        "4db24d4d542b8cc6142c1b85e0839bfce6a7116aaae5f49e2b0d90e4174e3d62",
        "58f427eee221104aef727ec4dcadb4ad5ec8021c262b6e3c104941ed851fcf6e",
        "62872a82eda5eae04541329a65dc062b4f99150360dfb24b7eeb8888214f0c25",
        "64c1d33b10b5e3999f12825dbcb850ad7520c7c117d8542e6da6e127234192dc",
        "858f6f949015f1c27d0185a0183df7a331f7fda971830408a5cdf53d16b39b5a",
        "af16ae40eed72ce51960ce6141f3b800e476007f3026cfd2dcd7455226b32fdc",
        "b14d8aaf06d7414bcbe6bdb87ddfc685f2c3765db15f8a5f50d93f3e5eeaf444",
        "b188d34dea921cf21f602ce83ef7d6c8af0527b8e874b208e92394f2d904759d",
        "b65c616d024460c825d73472311ddf995282069cd58dfdec9241447d4285d841",
        "b9bb89e9ea3c3835e2cb45dc7687b91e38156d208adf1dfc7554869038e50a0e",
        "ceb7e9d6031da3e0f77fd0285897e760bec25b3c26f82f85e7b272537e4cbfee",
        "d54110a7b981997f50e496a37a92c8a04f711278ccd9a50d194519ac35baed3b",
        "e9b1ef85c2cae6c3bec70a6697a36d767584abee1c6fe621530865ef5146a9eb",
    ),
    "src/engine/infrastructure/startup_validation_code_context.py": (
        "0ca493e04eecc4031d75de2d3dfcc076fca47fbc6fb874843f29ab51ff7adebe",
        "13d85428ca0657171a7e01e9d5ada28e0ef1bd42db630d851072748963fc1ca5",
        "15dc6609382751359651f7d744fa616207cf024abe45a5ae4c1fe167134c8b42",
        "17e301896dcb28e112dee5497559ab33d9ac39c7a02c00f6851b507908fec8e8",
        "21fdf9d9229c558edc70361412735a1be36b483e7eb841665a1d5659c45f7387",
        "27cc959c3a18217d2e312a7a04b4c7160ab2a55bbc0ee6dbd4eb56c684138212",
        "2c0b95c995c3f4db749dd40a7522a2e78a59c79ad244869a57b0295a8b7b2f0b",
        "355a1eb29a8e7584872f7446cd7b78af4375a72c8d53fe482f2023afab311e59",
        "52a87252121e687de0674cfea5ef565cb183032b0962e8fbee90a7d656b59fe5",
        "5890164cb152c1f408347ea5703b699b5c8ec8cdf225819314c52bbc76776681",
        "5a881b096932962604f6aab3a995378d0246ea30e7cb3c17e3ef7e3b93b2288d",
        "5b1f9610fd8eda6353e8911cf558beb9d40f764cbd11472ddb883454d3355d6e",
        "5e78314e2105d6a8c645bda55aed36036db797ef447dc5085c87dd3cf91d8bed",
        "5f6b4ccc8c4ea74d5b4012dd02b4607c437587402fdbb325752fe53fc0080947",
        "6366e821e8af94ff9b9ce582593a5c317f608b93a826e8d1951d8214e0b4922c",
        "741f502aeb6c210fa59a7e1b5a5d5e0264fc1d3cc045a7717a8e403016e8ba3e",
        "8ef7d406ba2b9af7504321f14114e4eea6a31c963d56048a26745f2a62cfd0de",
        "94d6a8f4d3e5266523512f77fc05b706c0d26b0a28bf3bebb86dc2e863853337",
        "a3d24175cc87b1e0d67963191bc34e1910595e7fd5e967707543ed0f45b747be",
        "a54c23586d077630db8bdbe7b012719bbae411dfdf5f33ebae7bfa559a76f3bc",
        "b999b1fb1e2ff40dc112cfd88a97ac0e2ecb62975fcbd95ac0c78a1899ad3ea2",
        "be396153e7574f9cbf2d8a90145a373bbdc576adb116553896a9184093bcec47",
        "c25b9e60f3773337412f1ccd28146aea2e9788980bc17f17802077352eb579fb",
        "c2ad2370a32236543bdc70991274a83a109ed48ccd24d1eac4a7206f987034f5",
        "e81848fa4e85f082005b905ff5e71390dc2bfec114be3ef9fd550bea2c4dceba",
        "ee715b40b27ddd814128f7c49945d2dfbba08e65cf6c7c23c4a8cbd73594b171",
        "eebb9048c5500a5c184c7dcca4810db89ec266722611fa07e4f4c90f66aad1cf",
        "fb11b341ae539ba32b02871ea69f3e94a1e9b0ea5a295e4de4bc29f57df66e33",
    ),
}
REVIEWED_CANCEL_CACHE_PROFILE = {
    **REVIEWED_ARCHIVE_PROJECTION_PROFILE,
    **REVIEWED_CANCEL_CACHE_HASHES,
}
REVIEWED_CANCEL_CACHE_VARIANTS = {
    (key[0], REVIEWED_CANCEL_CACHE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/automation/entry_cancel_wait_tuning.py",
        "selector_sha256": REVIEWED_CANCEL_CACHE_HASHES[
            "src/engine/automation/entry_cancel_wait_tuning.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_CANCEL_CACHE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_CANCEL_CACHE_HASHES.get(os.path.normpath(name), sha)
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ARCHIVE_PROJECTION_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((origin, current) for origin in REVIEWED_CANCEL_CACHE_ORIGINS[name])
        for name, current in REVIEWED_CANCEL_CACHE_HASHES.items()
    },
}

# Exact source-only formatting succession. The review manifest preserves the
# committed predecessor and deterministic formatter output; it never rewrites
# a policy contract or grants runtime authority. The verifier itself remains
# bound directly to the candidate Git tree (it is not projected).
_FORMATTING_REVIEW_ROOT = Path(__file__).resolve().parents[3]
_FORMATTING_REVIEW_PATH = (
    "docs/audit-reports/2026-10-24-source-formatting-consumer-review.json.txt"
)
_FORMATTING_REVIEW_SHA256 = (
    "451ce5de8152f1e8c07b3a33844ee5e7fe010315a8a62a78f613964978b3ebdd"
)
_FORMATTING_BASE = "78bfac3d7804d4c5d6da1f6345f8fbdc28241976"


def _formatting_review():
    raw = (_FORMATTING_REVIEW_ROOT / _FORMATTING_REVIEW_PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != _FORMATTING_REVIEW_SHA256:
        raise ValueError("entry_consumer_formatting_review_invalid")
    return json.loads(raw)["sources"]


def reviewed_formatting_predecessor(name, digest, *, review=None):
    """Resolve only a pinned physical successor; unknown bytes stay unknown."""
    row = (review if review is not None else _formatting_review()).get(name)
    if row and digest == row["after_sha256"]:
        return row["before_sha256"]
    return digest


@lru_cache(maxsize=128)
def _formatting_original(name, expected):
    # Git objects are immutable; the expected original digest is part of the
    # cache key. Candidate files and the pinned review are still read afresh.
    original = subprocess.check_output(
        [
            "git",
            "-C",
            str(_FORMATTING_REVIEW_ROOT),
            "show",
            _FORMATTING_BASE + ":" + name,
        ],
        stderr=subprocess.DEVNULL,
        timeout=10,
    )
    if hashlib.sha256(original).hexdigest() != expected:
        raise ValueError("entry_consumer_formatting_origin_invalid")
    return original


def reviewed_formatting_source(name, raw, *, review=None):
    """Historical comparison bytes, never the physical runtime code digest."""
    row = (review if review is not None else _formatting_review()).get(name)
    if not row or hashlib.sha256(raw).hexdigest() != row["after_sha256"]:
        return raw
    return _formatting_original(name, row["before_sha256"])


# Native cold workflow code origin in P5; selected runtime and parents stay distinct.
REVIEWED_WORKFLOW_INVENTORY_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "919d6b976c987484799875102266280c595b478ac51e31e49e00c2c13e9905dd",
}
REVIEWED_WORKFLOW_INVENTORY_PROFILE = {
    **REVIEWED_CANCEL_CACHE_PROFILE,
    **REVIEWED_WORKFLOW_INVENTORY_HASHES,
}
REVIEWED_WORKFLOW_INVENTORY_VARIANTS = {
    (key[0], REVIEWED_WORKFLOW_INVENTORY_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_WORKFLOW_INVENTORY_HASHES[
            "src/engine/infrastructure/startup_validation_code_context.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_WORKFLOW_INVENTORY_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_WORKFLOW_INVENTORY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CANCEL_CACHE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair
            }
            | {REVIEWED_CANCEL_CACHE_HASHES[name]}
        )
        for name, current in REVIEWED_WORKFLOW_INVENTORY_HASHES.items()
    },
}


# Keep large native predecessor sources out of the bounded generic header path.
REVIEWED_COLD_SOURCE_BOUNDARY_HASHES = {
    "src/engine/infrastructure/startup_validation_code_context.py": "4f7d53950d2c54046b68a1863309d87ba2d17f865511c199ac616aab96ae4fbf",
}
REVIEWED_COLD_SOURCE_BOUNDARY_PROFILE = {
    **REVIEWED_WORKFLOW_INVENTORY_PROFILE,
    **REVIEWED_COLD_SOURCE_BOUNDARY_HASHES,
}
REVIEWED_COLD_SOURCE_BOUNDARY_VARIANTS = {
    (key[0], REVIEWED_COLD_SOURCE_BOUNDARY_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_COLD_SOURCE_BOUNDARY_HASHES[
            "src/engine/infrastructure/startup_validation_code_context.py"
        ],
        "dependencies": {
            **value["dependencies"],
            **REVIEWED_COLD_SOURCE_BOUNDARY_HASHES,
        },
        "contract_extensions": {
            origin: {
                name: REVIEWED_COLD_SOURCE_BOUNDARY_HASHES.get(
                    os.path.normpath(name), sha
                )
                for name, sha in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_WORKFLOW_INVENTORY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair
            }
            | {REVIEWED_WORKFLOW_INVENTORY_HASHES[name]}
        )
        for name, current in REVIEWED_COLD_SOURCE_BOUNDARY_HASHES.items()
    },
}


# Frozen contract identity repair; prior complete generations stay readable.
REVIEWED_AUXILIARY_ENVELOPE_HASHES = {
    "src/engine/scalping/reversal_auxiliary_registry.py": "e0ef036e8451e3ca867fbe274ff26fa747f281907cbee2470183b307350a5b77",
    "src/engine/monitoring/policy_generation_code_handoff.py": "02609b635fdb49576cd9596e25fa3c697ce557aa4cd856a27e090be045f1ea04",
    "src/engine/infrastructure/startup_validation_code_context.py": "0206c0105ef369957816a2383f72edc89e4e0f5a145868e7db837b37e6ca687d",
}
REVIEWED_AUXILIARY_ENVELOPE_PROFILE = {
    **REVIEWED_COLD_SOURCE_BOUNDARY_PROFILE,
    **REVIEWED_AUXILIARY_ENVELOPE_HASHES,
}
REVIEWED_AUXILIARY_ENVELOPE_VARIANTS = {
    (key[0], REVIEWED_AUXILIARY_ENVELOPE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/scalping/reversal_auxiliary_registry.py",
        "selector_sha256": REVIEWED_AUXILIARY_ENVELOPE_HASHES[
            "src/engine/scalping/reversal_auxiliary_registry.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_AUXILIARY_ENVELOPE_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_AUXILIARY_ENVELOPE_HASHES.get(
                    os.path.normpath(name), digest
                )
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_COLD_SOURCE_BOUNDARY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple(
            (origin, current)
            for origin in {
                old for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for old in pair
            }
            | {REVIEWED_COLD_SOURCE_BOUNDARY_PROFILE[name]}
        )
        for name, current in REVIEWED_AUXILIARY_ENVELOPE_HASHES.items()
    },
}


# Reviewed migration configuration; keep issued profiles and exact mixed-code rejection.
REVIEWED_MIGRATION_HASHES = {
    "src/utils/constants.py": "6fad50da635c7c4b694afb1d59205d9f901f15d197db2156f489e4829750e8bb",
    "src/engine/error_detectors/artifact_freshness.py": "8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665",
    "src/engine/infrastructure/runtime_release_router.py": "a02d89fca5ff58c1d257989dceb44dd6d4a9520552fbf4ad8e274c8522f1515d",
    "src/engine/infrastructure/startup_validation_code_context.py": "360d3d9f2d086135f9b6aa21689e70b2b93a8b662f4e15bd86f5a64f784fc38f",
}
REVIEWED_MIGRATION_ORIGINS = {
    "src/utils/constants.py": [
        "91b7840994ca13114176ced7cbc0ed23f9ecf53aad5dd9497956b9c991990252",
        "a7fd2722df4e74270e87ee9489c1e696f540f43a996fcc034e5265ec5b67946e",
    ],
    "src/engine/error_detectors/artifact_freshness.py": [
        "09c1d34cc554ef68060125590e84545e75a335add5ed2b87043b4a6a6b2eafb9",
        "3a58f8ac3220ea8d64247cf17a756d2658c7815cd3d57744303f80bc40d34dcc",
        "6f853e28cf95b2f6513ad6650350c6574ddeeb5b99f5d2d2d5756d34ebf14ed9",
        "6f9cf859a4adf8e27b6465d38cf4eb536b16631381e94af199ecf84554ca7ffa",
        "756a1fa9a36e7350a97d274b22047dffd8bedcdccd4bd4e3c7bb034efdcceba2",
        "a6b9f2882bac4ae90f8a972a3cfbd56e111d78dd3bacead8cb5f32c41a949e27",
        "f64db72754c88c8bab262e275fe3ab68440b32656a5b74ab9c4f0f0044b94ebf",
    ],
    "src/engine/infrastructure/runtime_release_router.py": [
        "02e83a628b50041e5d5938697ef4b1e4a8bddde2b301b7564cc6644f465f8e63",
        "58daee5eebdc8f02bf4fc86477929b0a05cc14438c5251c7e52d12b4d2a7f308",
        "ab16b27904d4d9b2b680a27219844d76bb692bc257385b23e4abed5abe93d962",
    ],
    "src/engine/infrastructure/startup_validation_code_context.py": [
        "0206c0105ef369957816a2383f72edc89e4e0f5a145868e7db837b37e6ca687d"
    ],
}
REVIEWED_MIGRATION_PROFILE = {
    **REVIEWED_AUXILIARY_ENVELOPE_PROFILE,
    **REVIEWED_MIGRATION_HASHES,
}
REVIEWED_MIGRATION_VARIANTS = {
    (key[0], REVIEWED_MIGRATION_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/utils/constants.py",
        "selector_sha256": REVIEWED_MIGRATION_HASHES["src/utils/constants.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_MIGRATION_HASHES},
        "contract_extensions": {
            origin: {
                name: REVIEWED_MIGRATION_HASHES.get(os.path.normpath(name), digest)
                for name, digest in paths.items()
            }
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_AUXILIARY_ENVELOPE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {
    **REVIEWED_ENTRY_COST_PAIRS,
    **{
        name: REVIEWED_ENTRY_COST_PAIRS.get(name, ())
        + tuple((old, current) for old in REVIEWED_MIGRATION_ORIGINS[name])
        for name, current in REVIEWED_MIGRATION_HASHES.items()
    },
}


# Explicit next-session activation date; retain original immutable profiles.
REVIEWED_ACTIVATION_DATE_HASHES = {'src/engine/scalping/reversal_code_handoff.py': 'e1da1e26b3f8bcfff6e3182cf20889cf083ceee6987748571edcbd8c606f3bed', 'src/engine/infrastructure/startup_validation_code_context.py': 'b11cd38efcbb7486c2532598669925490b5bb205e597bc51dd1299f2523d1ece', 'src/engine/monitoring/submission_bottleneck_monitor.py': '9b4327a28d01fe07d0b61359ffb908e5ac3932a7fefb4231f83f4afb3205a08c'}
REVIEWED_ACTIVATION_DATE_PROFILE = {**REVIEWED_MIGRATION_PROFILE, **REVIEWED_ACTIVATION_DATE_HASHES}
REVIEWED_ACTIVATION_DATE_VARIANTS = {
    (key[0], REVIEWED_ACTIVATION_DATE_HASHES.get(key[0], key[1])): {
        **value, "selector_path": "src/engine/scalping/reversal_code_handoff.py",
        "selector_sha256": REVIEWED_ACTIVATION_DATE_HASHES["src/engine/scalping/reversal_code_handoff.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_ACTIVATION_DATE_HASHES},
        "contract_extensions": {origin: {name: REVIEWED_ACTIVATION_DATE_HASHES.get(os.path.normpath(name), sha)
            for name, sha in paths.items()} for origin, paths in value["contract_extensions"].items()},
    } for key, value in REVIEWED_MIGRATION_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple((old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for value in pair}
        | {REVIEWED_MIGRATION_PROFILE[name]})
    for name, current in REVIEWED_ACTIVATION_DATE_HASHES.items()
}}

# Preserve the actually selected observer/activation generation above.
REVIEWED_REGISTRY_REPLAY_HASHES = {'src/engine/scalping/initial_quantity_policy.py': 'a60fc47c9467e0da033f8371ebdb66627e632d6b1bcd00b9a915b333fc11fd2f', 'src/engine/scalping/initial_quantity_refresh_evaluation.py': '5a143af8a348ef30c19848ccdf696659be69831dec840bb8f4233087b1ff82f8', 'src/engine/automation/postclose_summary_handoff.py': 'aeb5c0e1c259425c17de08af1dab323f2101d8147e1c7cd3c53731bcf78f024d', 'src/engine/automation/ordered_intraday_deploy.py': '7b10c5d127bd45ad4e82e90c4a504ca39dfd64f23a6d487c9be7880cc682beb5', 'src/engine/infrastructure/startup_validation_code_context.py': 'adb7ac1312370d7639072412f0869aadbe53f7c644a58bab0a2ddac6d8ddc95c', 'src/engine/scalping/reversal_code_handoff.py': '945d695b08b5f8a6bb06ef723f5a9dc8226469e49c66e03eb79dca3a70e429f4', 'src/engine/automation/runtime_policy_bootstrap.py': 'ab3e75ecf03a69bdb4787b358c06026e32963e945cf2e867aa70193bc5f32de0', 'src/engine/runtime_approval_summary.py': '8de2430637152fbc72c60d7f246273492754bcb922109e0f3d1afa88165e7d3a'}
REVIEWED_REGISTRY_REPLAY_ORIGINS = {'src/engine/scalping/initial_quantity_policy.py': 'ab293d183811ca8740e94046dfc54f6011ccf24ebca9803d1420da29c7ef95bf', 'src/engine/scalping/initial_quantity_refresh_evaluation.py': 'cf4a6f44ae65f44fb273649845b65bdfb2ae7e1863be9d3790935ce95a9289b8', 'src/engine/automation/postclose_summary_handoff.py': '12fef0e06265f23c6f60f2f6de2a0c67cf75922d2c54e00af49bfda7e23fc8f3', 'src/engine/automation/ordered_intraday_deploy.py': '47a9283d556dcc394c49ccfb6a249a00a50823fc1a1b78c2015ade233aa07cc8', 'src/engine/infrastructure/startup_validation_code_context.py': 'b11cd38efcbb7486c2532598669925490b5bb205e597bc51dd1299f2523d1ece', 'src/engine/scalping/reversal_code_handoff.py': 'e1da1e26b3f8bcfff6e3182cf20889cf083ceee6987748571edcbd8c606f3bed', 'src/engine/automation/runtime_policy_bootstrap.py': '8df8fa94ae94370b483ab816d3c35a51464f15f193458429f252379d536f01e4', 'src/engine/runtime_approval_summary.py': 'ba8e192796659314dc1ea5d371fe72413135937f55655fd270b2bcb8b2266075'}
REVIEWED_REGISTRY_REPLAY_PROFILE = {**REVIEWED_ACTIVATION_DATE_PROFILE, **REVIEWED_REGISTRY_REPLAY_HASHES}
REVIEWED_REGISTRY_REPLAY_VARIANTS = {
    (key[0], REVIEWED_REGISTRY_REPLAY_HASHES.get(key[0], key[1])): {
        **value, "selector_path": "src/engine/scalping/initial_quantity_refresh_evaluation.py",
        "selector_sha256": REVIEWED_REGISTRY_REPLAY_HASHES["src/engine/scalping/initial_quantity_refresh_evaluation.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_REGISTRY_REPLAY_HASHES},
        "contract_extensions": {origin: {name: REVIEWED_REGISTRY_REPLAY_HASHES.get(os.path.normpath(name), sha)
            for name, sha in paths.items()} for origin, paths in value["contract_extensions"].items()},
    } for key, value in REVIEWED_ACTIVATION_DATE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple((old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for value in pair}
        | {REVIEWED_REGISTRY_REPLAY_ORIGINS[name]})
    for name, current in REVIEWED_REGISTRY_REPLAY_HASHES.items()
}}


# Preserve the consumed registry/activation profile; fixture reader is separate.
REVIEWED_PREPARED_FIXTURE_HASHES = {'src/engine/monitoring/policy_generation_code_handoff.py': '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', 'src/engine/infrastructure/startup_validation_code_context.py': '14c9e87d9cd40276f6cfde243f319624cbece0b7838659e9f69c7f254a6ee6ec'}
REVIEWED_PREPARED_FIXTURE_PROFILE = {**REVIEWED_REGISTRY_REPLAY_PROFILE, **REVIEWED_PREPARED_FIXTURE_HASHES}
REVIEWED_PREPARED_FIXTURE_VARIANTS = {
    (key[0], REVIEWED_PREPARED_FIXTURE_HASHES.get(key[0], key[1])): {
        **value, "selector_path": "src/engine/monitoring/policy_generation_code_handoff.py",
        "selector_sha256": REVIEWED_PREPARED_FIXTURE_HASHES["src/engine/monitoring/policy_generation_code_handoff.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_PREPARED_FIXTURE_HASHES},
        "contract_extensions": {origin: {name: REVIEWED_PREPARED_FIXTURE_HASHES.get(os.path.normpath(name), sha)
            for name, sha in paths.items()} for origin, paths in value["contract_extensions"].items()},
    } for key, value in REVIEWED_REGISTRY_REPLAY_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple((old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ()) for value in pair}
        | {REVIEWED_REGISTRY_REPLAY_PROFILE[name]})
    for name, current in REVIEWED_PREPARED_FIXTURE_HASHES.items()
}}


# Exact reviewed submit-deadline and probe-terminal integration. Preserve
# the consumed fixture profile; mixed or unknown successor bytes still fail.
REVIEWED_SUBMIT_PROBE_HASHES = {'src/engine/scalping/zero_base_probe.py': '7df54ed102940afeb63b478d8d532c3a9604d1f6c6ade34780cd509b2be424ae', 'src/engine/scalping/mechanistic_entry_runtime_policy.py': '7d19b7409abfbb75ece84f1c877cd9e8ae58631fa770ce4956f90964742d46b7', 'src/engine/sniper_state_handlers.py': 'e441b1ad823d53e94aa10537e0645a5661d1612a4800ce6e54c7cf6b476fb259', 'src/engine/monitoring/entry_attempt_identity.py': '10132ab4e6d77b41a5c86408f85d8ece4350bc7a5c3e316a238fa35d291e02f4', 'src/engine/monitoring/runtime_performance.py': 'e001ea31ffe885cd3ef2d9883d1eae99cb444e3a65e53b11e9d6dd28d6bdede1', 'src/engine/infrastructure/startup_validation_code_context.py': 'ebafd87b937ad53627408d31d4a2f40c12e2e1800e6f775eb808f3fc289c82a5', 'src/engine/automation/next_preopen_readiness.py': 'b21095ca45f5844d1b2f6cf0cf0f312f44736e42cdf1a519eb65e7d39c0821f2'}
REVIEWED_SUBMIT_PROBE_PROFILE = {
    **REVIEWED_PREPARED_FIXTURE_PROFILE, **REVIEWED_SUBMIT_PROBE_HASHES
}
REVIEWED_SUBMIT_PROBE_VARIANTS = {
    (key[0], REVIEWED_SUBMIT_PROBE_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/scalping/mechanistic_entry_runtime_policy.py",
        "selector_sha256": REVIEWED_SUBMIT_PROBE_HASHES[
            "src/engine/scalping/mechanistic_entry_runtime_policy.py"
        ],
        "dependencies": {**value["dependencies"], **REVIEWED_SUBMIT_PROBE_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_SUBMIT_PROBE_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_PREPARED_FIXTURE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_PREPARED_FIXTURE_PROFILE[name]}
    )
    for name, current in REVIEWED_SUBMIT_PROBE_HASHES.items()
}}


# Exact reviewed health/snapshot generation; retain the actual consumed
# submit/probe profile. No runtime decision or source-validity guard changed.
REVIEWED_HEALTH_SNAPSHOT_HASHES = {'src/engine/error_detectors/artifact_freshness.py': '0c3d6bfd413cf5e3a49e0d748d7d2366e2a60a75cb107514a6a69cbaf20db677', 'src/engine/monitoring/policy_generation_code_handoff.py': '93f96eb1ee42111142201a257155616a246cd9d7b8bbbabe5560a24892c82120', 'src/engine/log_archive_service.py': '7b530c05f6e5cf4498f332a6b7df10641126dbb4da5165af314d1f2507f73348', 'src/engine/sniper_trade_review_report.py': '188e761ec9373f0bf4f8890b620b6f7071b7ec925bf7455dcc4eeb8b11aee4ac', 'src/engine/sniper_performance_tuning_report.py': 'c6a00cba271c0b4af88f6bf6973e73b110dd7eba12ac9ddbf534ea1a3c5129af', 'src/engine/infrastructure/startup_validation_code_context.py': 'bb8c4efdaa7b8f9d43e2de53099a558a18c4c6855a1b85cfab36db7f52b7867e'}
REVIEWED_HEALTH_SNAPSHOT_ORIGINS = {'src/engine/error_detectors/artifact_freshness.py': '8dae2dc097b769214195f17c3b666fb6e43c2c2f25ea7c3a0311b723355bc665', 'src/engine/monitoring/policy_generation_code_handoff.py': '0389b444ff6b4b2b44ed368baca7f08b073331fbaede3cdbe4ae782b977f2111', 'src/engine/log_archive_service.py': '08b7c8d890bd5d2857a428776195d1168fa4cba5dff7ee7d587e7466527114c3', 'src/engine/sniper_trade_review_report.py': '612d19f9108f6355a43188e1209b82078e3a6da7ce97323f18854d486065d53f', 'src/engine/sniper_performance_tuning_report.py': '64d66e04f7cae07a6c80ad48e7348ab77262be6f3ec8ad8ec3df1b2018dc0dd1', 'src/engine/infrastructure/startup_validation_code_context.py': 'ebafd87b937ad53627408d31d4a2f40c12e2e1800e6f775eb808f3fc289c82a5'}
REVIEWED_HEALTH_SNAPSHOT_PROFILE = {
    **REVIEWED_SUBMIT_PROBE_PROFILE, **REVIEWED_HEALTH_SNAPSHOT_HASHES
}
REVIEWED_HEALTH_SNAPSHOT_VARIANTS = {
    (key[0], REVIEWED_HEALTH_SNAPSHOT_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/log_archive_service.py",
        "selector_sha256": REVIEWED_HEALTH_SNAPSHOT_HASHES["src/engine/log_archive_service.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_HEALTH_SNAPSHOT_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_HEALTH_SNAPSHOT_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_SUBMIT_PROBE_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_HEALTH_SNAPSHOT_ORIGINS[name]}
    )
    for name, current in REVIEWED_HEALTH_SNAPSHOT_HASHES.items()
}}


# Diagnostic-only cumulative hold invalidation. Native trading and guards are
# unchanged; all complete profile and predecessor checks still apply.
REVIEWED_CUMULATIVE_HOLD_HASHES = {'src/engine/monitoring/runtime_performance.py': 'c23788f10acaaf0e554a42f187042ea3f37ea74d9b1d969ac95f7fdd4c9ca104', 'src/engine/infrastructure/startup_validation_code_context.py': 'bc93b384147d5905d6b44e9407a3ddfd3433e915e2c8cbbacbee8bcbedeb32a6'}
REVIEWED_CUMULATIVE_HOLD_PROFILE = {
    **REVIEWED_HEALTH_SNAPSHOT_PROFILE, **REVIEWED_CUMULATIVE_HOLD_HASHES
}
REVIEWED_CUMULATIVE_HOLD_VARIANTS = {
    (key[0], REVIEWED_CUMULATIVE_HOLD_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/monitoring/runtime_performance.py",
        "selector_sha256": REVIEWED_CUMULATIVE_HOLD_HASHES["src/engine/monitoring/runtime_performance.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_CUMULATIVE_HOLD_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_CUMULATIVE_HOLD_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_HEALTH_SNAPSHOT_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_HEALTH_SNAPSHOT_PROFILE[name]}
    )
    for name, current in REVIEWED_CUMULATIVE_HOLD_HASHES.items()
}}


# Report-only normal postclose loader classification. Preserve every issued
# profile and bind the complete reviewed successor and independent reader.
REVIEWED_CLOSED_LOADER_HASHES = {'src/engine/error_detectors/artifact_freshness.py': 'adbd91229c1a84cf5bcacf8f6c7ef6e55f9636fefc37b182a9802f4aa1755bd3', 'src/engine/infrastructure/startup_validation_code_context.py': 'b1ee0ff0463b848d59d9eb676182373ff475d0868ce5dce2d3f7a6975294a7ae'}
REVIEWED_CLOSED_LOADER_PROFILE = {
    **REVIEWED_CUMULATIVE_HOLD_PROFILE, **REVIEWED_CLOSED_LOADER_HASHES
}
REVIEWED_CLOSED_LOADER_VARIANTS = {
    (key[0], REVIEWED_CLOSED_LOADER_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/error_detectors/artifact_freshness.py",
        "selector_sha256": REVIEWED_CLOSED_LOADER_HASHES["src/engine/error_detectors/artifact_freshness.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_CLOSED_LOADER_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_CLOSED_LOADER_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CUMULATIVE_HOLD_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_CUMULATIVE_HOLD_PROFILE[name]}
    )
    for name, current in REVIEWED_CLOSED_LOADER_HASHES.items()
}}


# Exact isolated native indexed-source closure, retaining all prior profiles.
REVIEWED_STOP_INDEX_HASHES = {'src/engine/automation/main_trailing_source_assembler.py': '26fa3a2f2658f7d5081bb0d16d0d8ef27c19e8ab54da9f0e14074c82c3c096d5', 'src/engine/infrastructure/startup_validation_code_context.py': 'd760b6207bd253be85b9d543cbc052bb911e4a4fb2902ce70599791d31c87792'}
REVIEWED_STOP_INDEX_PROFILE = {
    **REVIEWED_CLOSED_LOADER_PROFILE, **REVIEWED_STOP_INDEX_HASHES
}
REVIEWED_STOP_INDEX_VARIANTS = {
    (key[0], REVIEWED_STOP_INDEX_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/automation/main_trailing_source_assembler.py",
        "selector_sha256": REVIEWED_STOP_INDEX_HASHES["src/engine/automation/main_trailing_source_assembler.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_STOP_INDEX_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_STOP_INDEX_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_CLOSED_LOADER_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_CLOSED_LOADER_PROFILE[name]}
    )
    for name, current in REVIEWED_STOP_INDEX_HASHES.items()
}}


# Isolated-only indexed I/O; production research fingerprints are unchanged.
REVIEWED_ISOLATED_INDEX_HASHES = {'src/engine/automation/main_trailing_source_assembler.py': '1aa864f4fd5db4f3ef4d14b6983617c9ac41cc208e792497cf34134b4e99bc52', 'src/engine/infrastructure/startup_validation_code_context.py': '1932ef04fe121b341d64ad58675675b354444dab3915168b9458f2103914db15'}
REVIEWED_ISOLATED_INDEX_PROFILE = {
    **REVIEWED_STOP_INDEX_PROFILE, **REVIEWED_ISOLATED_INDEX_HASHES
}
REVIEWED_ISOLATED_INDEX_VARIANTS = {
    (key[0], REVIEWED_ISOLATED_INDEX_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_ISOLATED_INDEX_HASHES["src/engine/infrastructure/startup_validation_code_context.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_ISOLATED_INDEX_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_ISOLATED_INDEX_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_STOP_INDEX_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_STOP_INDEX_PROFILE[name]}
    )
    for name, current in REVIEWED_ISOLATED_INDEX_HASHES.items()
}}


# Complete reviewed report-absence recovery profile, retaining issued origins.
REVIEWED_SUFFIX_REPORT_HASHES = {'src/engine/automation/postclose_finalization_generation.py': '0d70b7d26a768416c20b7345f47ac45155feda44469d3241930e48fa2f0e4c41', 'src/engine/infrastructure/startup_validation_code_context.py': '65c598fa42854b22eaa223b78f4ab93a6d95916af5b64b20d6bb95199f8d33a6'}
REVIEWED_SUFFIX_REPORT_PROFILE = {
    **REVIEWED_ISOLATED_INDEX_PROFILE, **REVIEWED_SUFFIX_REPORT_HASHES
}
REVIEWED_SUFFIX_REPORT_VARIANTS = {
    (key[0], REVIEWED_SUFFIX_REPORT_HASHES.get(key[0], key[1])): {
        **value,
        "selector_path": "src/engine/infrastructure/startup_validation_code_context.py",
        "selector_sha256": REVIEWED_SUFFIX_REPORT_HASHES["src/engine/infrastructure/startup_validation_code_context.py"],
        "dependencies": {**value["dependencies"], **REVIEWED_SUFFIX_REPORT_HASHES},
        "contract_extensions": {
            origin: {name: REVIEWED_SUFFIX_REPORT_HASHES.get(os.path.normpath(name), sha)
                     for name, sha in paths.items()}
            for origin, paths in value["contract_extensions"].items()
        },
    }
    for key, value in REVIEWED_ISOLATED_INDEX_VARIANTS.items()
}
REVIEWED_ENTRY_COST_PAIRS = {**REVIEWED_ENTRY_COST_PAIRS, **{
    name: REVIEWED_ENTRY_COST_PAIRS.get(name, ()) + tuple(
        (old, current)
        for old in {value for pair in REVIEWED_ENTRY_COST_PAIRS.get(name, ())
                    for value in pair} | {REVIEWED_ISOLATED_INDEX_PROFILE[name]}
    )
    for name, current in REVIEWED_SUFFIX_REPORT_HASHES.items()
}}


def _verify_entry_code_delta(root, commit, origin, paths, expected):
    """Read-only code projection shared by pre-stop and selected handoff checks."""
    import ast

    root = Path(root)
    formatting_review = _formatting_review()
    physical_candidates = {}
    committed_sources = {}
    projections = {}
    allowed = {
        # Report-only lifecycle classification; delay qualification/selection
        # and every other monitor function remain byte/AST bound.
        "src/engine/monitoring/submission_bottleneck_monitor.py": {
            "_reversal_lifecycle_diagnostic",
            "observation_health_projection",
        },
        "src/engine/ai_engine_openai.py": {"_final_entry_machine_inputs"},
        "src/engine/sniper_state_handlers.py": {
            "_resolve_watching_state_change_refresh",
            "_get_live_entry_arm",
        },
        "src/engine/scalping/pre_submit_delay_tuning.py": {
            "_verify_runtime_code_contract",
            "prepare_runtime_policy",
        },
        "src/engine/automation/runtime_policy_bootstrap.py": {
            "_pre_submit_delay_handoff"
        },
        "src/engine/scalping/holding_vote_experiment.py": {"_code_paths", "code_sha"},
        "src/engine/scalping/holding_path_vote_policy.py": {
            "validate_successor",
            "verify_source_handoff",
        },
    }

    def repository_name(name):
        # Contract inventories retain their original keys, including ../utils.
        # Git object paths require a canonical repository-relative spelling.
        normalized = os.path.normpath(name)
        if (
            os.path.isabs(normalized)
            or normalized == ".."
            or normalized.startswith("../")
        ):
            raise ValueError("entry_consumer_code_path_outside_release")
        return normalized

    def revision_raw(revision, name):
        normalized = repository_name(name)
        key = (revision, normalized)
        if key not in committed_sources:
            try:
                committed_sources[key] = subprocess.check_output(
                    ["git", "-C", str(root), "show", revision + ":" + normalized],
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise ValueError("entry_consumer_code_source_missing") from exc
        return committed_sources[key]

    def format_projection(name, raw):
        key = (repository_name(name), hashlib.sha256(raw).hexdigest())
        if key not in projections:
            projections[key] = reviewed_formatting_source(
                key[0], raw, review=formatting_review
            )
        return projections[key]

    def candidate_bytes(name, *, optional=False):
        normalized = repository_name(name)
        path = root
        for part in Path(normalized).parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("entry_consumer_code_source_symlink:" + name)
        if not path.is_file():
            if optional and not path.exists():
                return None
            raise ValueError("entry_consumer_code_source_missing:" + name)
        raw = path.read_bytes()
        physical_candidates[normalized] = raw
        compared = format_projection(name, raw)
        # Comparing historical bytes must never hide an uncommitted physical
        # successor (including a committed predecessor replaced by its format).
        if compared != raw and raw != revision_raw(commit, name):
            raise ValueError("entry_consumer_dirty_release")
        return compared

    def revision_bytes(revision, name):
        return format_projection(name, revision_raw(revision, name))

    own_name = "src/engine/automation/intraday_release_handoff.py"
    if candidate_bytes(own_name) != revision_bytes(commit, own_name):
        raise ValueError("entry_consumer_dirty_verifier")
    original_hashes, changed, runtime_hashes = {}, [], {}
    extensions = REVIEWED_DELAY_CONTRACT_EXTENSIONS.get((origin, expected), {})
    dependencies_by_trigger = {}
    # A selector reverted alone must not downgrade the other cleanup files to
    # an older dependency profile. Detect the reviewed group before selection;
    # its first observed member requires the complete exact group below.
    cleanup_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_RETIRED_REVIEW_HASHES.items()
    )
    role_latency_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_ROLE_LATENCY_HASHES.items()
    )
    delay_shutdown_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_DELAY_SHUTDOWN_HASHES.items()
    )
    routed_reuse_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_ROUTED_REUSE_HASHES.items()
    )
    source_epoch_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_SOURCE_EPOCH_HASHES.items()
    )
    closed_observer_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_CLOSED_OBSERVER_HASHES.items()
    )
    postclose_repair_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_POSTCLOSE_REPAIR_HASHES.items()
    )
    logical_pipeline_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_LOGICAL_PIPELINE_HASHES.items()
    )
    historical_resolution_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_HISTORICAL_RESOLUTION_HASHES.items()
    )
    finalization_health_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_FINALIZATION_HEALTH_HASHES.items()
    )
    quantity_stage_present = (
        root / "src/engine/scalping/initial_quantity_policy.py"
    ).is_file() and (
        hashlib.sha256(
            candidate_bytes("src/engine/scalping/initial_quantity_policy.py")
        ).hexdigest()
        == REVIEWED_QUANTITY_STAGE_HASHES[
            "src/engine/scalping/initial_quantity_policy.py"
        ]
    )
    quantity_capture_present = (
        root / "src/engine/scalping/initial_quantity_cap_observation.py"
    ).is_file() and (
        hashlib.sha256(
            candidate_bytes("src/engine/scalping/initial_quantity_cap_observation.py")
        ).hexdigest()
        == REVIEWED_QUANTITY_CAPTURE_HASHES[
            "src/engine/scalping/initial_quantity_cap_observation.py"
        ]
    )
    first_transition_present = (
        root / "src/engine/automation/ordered_intraday_deploy.py"
    ).is_file() and (
        hashlib.sha256(
            candidate_bytes("src/engine/automation/ordered_intraday_deploy.py")
        ).hexdigest()
        == REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES[
            "src/engine/automation/ordered_intraday_deploy.py"
        ]
    )
    collector_close_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_COLLECTOR_CLOSE_HASHES.items()
    )
    buy_identity_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_BUY_IDENTITY_HASHES.items()
    )
    entry_receipt_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_ENTRY_RECEIPT_HASHES.items()
    )
    fixed_wait_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_FIXED_WAIT_HASHES.items()
    )
    native_invalidation_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_NATIVE_INVALIDATION_HASHES.items()
    )
    delay_machine_parent_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_DELAY_MACHINE_PARENT_HASHES.items()
    )
    holding_input_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_HOLDING_INPUT_HASHES.items()
    )
    nonfixed_capacity_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_NONFIXED_CAPACITY_HASHES.items()
    )
    operator_market_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_OPERATOR_MARKET_HASHES.items()
    )
    p5_ancestry_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_P5_ANCESTRY_HASHES.items()
    )
    postclose_recovery_selector = "src/engine/ai/holding_vote_replay_source.py"
    postclose_recovery_present = (
        root / postclose_recovery_selector
    ).is_file() and hashlib.sha256(
        candidate_bytes(postclose_recovery_selector)
    ).hexdigest() == REVIEWED_POSTCLOSE_RECOVERY_HASHES[
        postclose_recovery_selector
    ]
    post_sell_source_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_POST_SELL_SOURCE_HASHES.items()
    )
    native_label_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_ENTRY_COST_NATIVE_LABEL_HASHES.items()
    )
    coordination_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_COORDINATION_HASHES.items()
    )
    prepared_validation_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PREPARED_VALIDATION_HASHES.items()
    )
    prepared_repair_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PREPARED_REPAIR_HASHES.items()
    )
    main_preparation_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_MAIN_PREPARATION_HASHES.items()
    )
    prepared_start_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PREPARED_START_HASHES.items()
    )
    first_turn_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_FIRST_TURN_HASHES.items()
    )
    expiry_health_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_EXPIRY_HEALTH_HASHES.items()
    )
    signed_surge_present = all(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_SIGNED_SURGE_HASHES.items()
    )
    prestart_integration_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PRESTART_INTEGRATION_HASHES.items()
    )
    preassessment_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PREASSESSMENT_HASHES.items()
    )
    prepared_owner_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PREPARED_OWNER_HASHES.items()
    )
    finalization_owner = "src/engine/automation/postclose_finalization_generation.py"
    consumed_finalization = (root / finalization_owner).is_file() and hashlib.sha256(
        candidate_bytes(finalization_owner)
    ).hexdigest() == REVIEWED_PRE_FINALIZATION_HASHES[finalization_owner]
    native_preopen = (root / finalization_owner).is_file() and hashlib.sha256(
        candidate_bytes(finalization_owner)
    ).hexdigest() == REVIEWED_NATIVE_PREOPEN_HASHES[finalization_owner]
    sentinel_scope_present = (
        root / "src/engine/monitoring/sentinel_event_scope.py"
    ).exists() or any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_SENTINEL_SCOPE_HASHES.items()
    )
    deployed_sentinel = all(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == digest
        for name, digest in REVIEWED_DEPLOYED_SENTINEL_SCOPE_HASHES.items()
    )
    observer_io_present = (
        root / "src/engine/monitoring/observer_artifact_io.py"
    ).exists()
    pre_submit_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_PRE_SUBMIT_HASHES.items()
        if name
        not in {
            "src/engine/infrastructure/startup_validation_code_context.py",
            "src/engine/monitoring/policy_generation_code_handoff.py",
        }
    )
    native_buy_cost = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_NATIVE_BUY_COST_HASHES.items()
    )
    holding_stream = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_HOLDING_STREAM_HASHES.items()
        if sha != REVIEWED_HOLDING_STREAM_PREVIOUS[name]
    )
    machine_rest_history = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_MACHINE_REST_HISTORY_HASHES.items()
    )
    auxiliary_capability = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_AUXILIARY_CAPABILITY_HASHES.items()
    )
    numeric_replay = (root / "src/utils/numeric.py").exists() or any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_NUMERIC_REPLAY_HASHES.items()
        if name
        not in {
            "src/engine/infrastructure/startup_validation_code_context.py",
            "src/engine/automation/ordered_intraday_deploy.py",
        }
    )
    aftermarket_listing = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_AFTERMARKET_LISTING_HASHES.items()
    )
    scanner_preflight = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_SCANNER_PREFLIGHT_HASHES.items()
    )
    detector_name = "src/engine/error_detectors/artifact_freshness.py"
    # Discovery cannot enlarge an unrelated historical source inventory.
    # Reuse the native reader so aliases in any path component and present
    # non-files still fail. Declared/profile sources remain mandatory below.
    detector_bytes = candidate_bytes(detector_name, optional=True)
    detector_sha = (
        hashlib.sha256(detector_bytes).hexdigest()
        if detector_bytes is not None
        else None
    )
    closed_scanner = detector_sha == REVIEWED_CLOSED_SCANNER_HASHES[detector_name]
    previous_closed_scanner = (
        detector_sha == REVIEWED_CLOSED_SCANNER_PREVIOUS_HASHES[detector_name]
    )
    prepared_hashes = (
        REVIEWED_CLOSED_SCANNER_PROFILE
        if closed_scanner
        else (
            REVIEWED_CLOSED_SCANNER_PREVIOUS_PROFILE
            if previous_closed_scanner
            else (
                REVIEWED_SCANNER_PREFLIGHT_PROFILE
                if scanner_preflight
                else (
                    REVIEWED_AFTERMARKET_LISTING_PROFILE
                    if aftermarket_listing
                    else (
                        REVIEWED_NUMERIC_REPLAY_PROFILE
                        if numeric_replay
                        else (
                            REVIEWED_AUXILIARY_CAPABILITY_PROFILE
                            if auxiliary_capability
                            else (
                                REVIEWED_MACHINE_REST_HISTORY_PROFILE
                                if machine_rest_history
                                else (
                                    REVIEWED_HOLDING_STREAM_PROFILE
                                    if holding_stream
                                    else (
                                        REVIEWED_NATIVE_BUY_COST_PROFILE
                                        if native_buy_cost
                                        else (
                                            REVIEWED_PRE_SUBMIT_ENTRY_COST_HASHES
                                            if pre_submit_present
                                            else (
                                                REVIEWED_OBSERVER_IO_ENTRY_COST_HASHES
                                                if observer_io_present
                                                else (
                                                    REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_HASHES
                                                    if deployed_sentinel
                                                    else (
                                                        REVIEWED_ENTRY_COST_HASHES
                                                        if sentinel_scope_present
                                                        else (
                                                            REVIEWED_PRE_FINALIZATION_HASHES
                                                            if consumed_finalization
                                                            else (
                                                                REVIEWED_NATIVE_PREOPEN_HASHES
                                                                if native_preopen
                                                                else REVIEWED_ENTRY_COST_PRE_SENTINEL_SCOPE_HASHES
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    prepared_variants = (
        REVIEWED_CLOSED_SCANNER_VARIANTS
        if closed_scanner
        else (
            REVIEWED_CLOSED_SCANNER_PREVIOUS_VARIANTS
            if previous_closed_scanner
            else (
                REVIEWED_SCANNER_PREFLIGHT_VARIANTS
                if scanner_preflight
                else (
                    REVIEWED_AFTERMARKET_LISTING_VARIANTS
                    if aftermarket_listing
                    else (
                        REVIEWED_NUMERIC_REPLAY_VARIANTS
                        if numeric_replay
                        else (
                            REVIEWED_AUXILIARY_CAPABILITY_VARIANTS
                            if auxiliary_capability
                            else (
                                REVIEWED_MACHINE_REST_HISTORY_VARIANTS
                                if machine_rest_history
                                else (
                                    REVIEWED_HOLDING_STREAM_VARIANTS
                                    if holding_stream
                                    else (
                                        REVIEWED_NATIVE_BUY_COST_VARIANTS
                                        if native_buy_cost
                                        else (
                                            REVIEWED_PRE_SUBMIT_DEPENDENCY_VARIANTS
                                            if pre_submit_present
                                            else (
                                                REVIEWED_OBSERVER_IO_DEPENDENCY_VARIANTS
                                                if observer_io_present
                                                else (
                                                    REVIEWED_ENTRY_COST_DEPLOYED_SENTINEL_VARIANTS
                                                    if deployed_sentinel
                                                    else (
                                                        REVIEWED_ENTRY_COST_DEPENDENCY_VARIANTS
                                                        if sentinel_scope_present
                                                        else (
                                                            REVIEWED_PRE_FINALIZATION_VARIANTS
                                                            if consumed_finalization
                                                            else (
                                                                REVIEWED_NATIVE_PREOPEN_VARIANTS
                                                                if native_preopen
                                                                else REVIEWED_ENTRY_COST_PRE_SENTINEL_SCOPE_VARIANTS
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    successor_name = "src/engine/scalping/reversal_code_handoff.py"
    successor = candidate_bytes(successor_name, optional=True)
    if (
        successor is not None
        and hashlib.sha256(successor).hexdigest()
        == REVIEWED_POSTCLOSE_SOURCE_HASHES[successor_name]
    ):
        prepared_hashes = REVIEWED_POSTCLOSE_SOURCE_PROFILE
        prepared_variants = REVIEWED_POSTCLOSE_SOURCE_VARIANTS
    auxiliary_name = "src/engine/scalping/reversal_auxiliary_compatibility.py"
    auxiliary_successor = candidate_bytes(auxiliary_name, optional=True)
    if (
        auxiliary_successor is not None
        and hashlib.sha256(auxiliary_successor).hexdigest()
        == REVIEWED_AUXILIARY_FORMAT_HASHES[auxiliary_name]
    ):
        prepared_hashes = REVIEWED_AUXILIARY_FORMAT_PROFILE
        prepared_variants = REVIEWED_AUXILIARY_FORMAT_VARIANTS
    cold_name = "src/engine/automation/main_startup_validation.py"
    cold_successor = candidate_bytes(cold_name, optional=True)
    if (
        cold_successor is not None
        and hashlib.sha256(cold_successor).hexdigest()
        == REVIEWED_STOPPED_POSTCLOSE_HASHES[cold_name]
    ):
        prepared_hashes = REVIEWED_STOPPED_POSTCLOSE_PROFILE
        prepared_variants = REVIEWED_STOPPED_POSTCLOSE_VARIANTS
    producer_name = "src/engine/automation/runtime_policy_bootstrap.py"
    producer_successor = candidate_bytes(producer_name, optional=True)
    if (
        producer_successor is not None
        and hashlib.sha256(producer_successor).hexdigest()
        == REVIEWED_PRODUCER_IDENTITY_HASHES[producer_name]
    ):
        prepared_hashes = REVIEWED_PRODUCER_IDENTITY_PROFILE
        prepared_variants = REVIEWED_PRODUCER_IDENTITY_VARIANTS
    archive_name = "src/engine/monitoring/policy_generation_validation.py"
    archive_successor = candidate_bytes(archive_name, optional=True)
    if (
        archive_successor is not None
        and hashlib.sha256(archive_successor).hexdigest()
        == REVIEWED_ARCHIVE_PROJECTION_HASHES[archive_name]
    ):
        prepared_hashes = REVIEWED_ARCHIVE_PROJECTION_PROFILE
        prepared_variants = REVIEWED_ARCHIVE_PROJECTION_VARIANTS
    cancel_cache_name = "src/engine/automation/entry_cancel_wait_tuning.py"
    cancel_cache_successor = candidate_bytes(cancel_cache_name, optional=True)
    if (
        cancel_cache_successor is not None
        and hashlib.sha256(cancel_cache_successor).hexdigest()
        == REVIEWED_CANCEL_CACHE_HASHES[cancel_cache_name]
    ):
        prepared_hashes = REVIEWED_CANCEL_CACHE_PROFILE
        prepared_variants = REVIEWED_CANCEL_CACHE_VARIANTS
    workflow_name = "src/engine/infrastructure/startup_validation_code_context.py"
    workflow_successor = candidate_bytes(workflow_name, optional=True)
    if (
        workflow_successor is not None
        and hashlib.sha256(workflow_successor).hexdigest()
        == REVIEWED_WORKFLOW_INVENTORY_HASHES[workflow_name]
    ):
        prepared_hashes = REVIEWED_WORKFLOW_INVENTORY_PROFILE
        prepared_variants = REVIEWED_WORKFLOW_INVENTORY_VARIANTS
    if (
        workflow_successor is not None
        and hashlib.sha256(workflow_successor).hexdigest()
        == REVIEWED_COLD_SOURCE_BOUNDARY_HASHES[workflow_name]
    ):
        prepared_hashes = REVIEWED_COLD_SOURCE_BOUNDARY_PROFILE
        prepared_variants = REVIEWED_COLD_SOURCE_BOUNDARY_VARIANTS
    envelope_name = 'src/engine/scalping/reversal_auxiliary_registry.py'
    envelope_successor = candidate_bytes(envelope_name, optional=True)
    if (
        envelope_successor is not None
        and hashlib.sha256(envelope_successor).hexdigest()
        == REVIEWED_AUXILIARY_ENVELOPE_HASHES[envelope_name]
    ):
        prepared_hashes = REVIEWED_AUXILIARY_ENVELOPE_PROFILE
        prepared_variants = REVIEWED_AUXILIARY_ENVELOPE_VARIANTS
    migration_name = "src/utils/constants.py"
    migration_source = candidate_bytes(migration_name, optional=True)
    if (
        migration_source is not None
        and hashlib.sha256(migration_source).hexdigest()
        == REVIEWED_MIGRATION_HASHES[migration_name]
    ):
        prepared_hashes = REVIEWED_MIGRATION_PROFILE
        prepared_variants = REVIEWED_MIGRATION_VARIANTS
    activation_name = "src/engine/scalping/reversal_code_handoff.py"
    activation_source = candidate_bytes(activation_name, optional=True)
    if (activation_source is not None and hashlib.sha256(activation_source).hexdigest()
            == REVIEWED_ACTIVATION_DATE_HASHES[activation_name]):
        prepared_hashes = REVIEWED_ACTIVATION_DATE_PROFILE
        prepared_variants = REVIEWED_ACTIVATION_DATE_VARIANTS
    registry_name = "src/engine/scalping/initial_quantity_refresh_evaluation.py"
    registry_source = candidate_bytes(registry_name, optional=True)
    if (registry_source is not None and hashlib.sha256(registry_source).hexdigest()
            == REVIEWED_REGISTRY_REPLAY_HASHES[registry_name]):
        prepared_hashes = REVIEWED_REGISTRY_REPLAY_PROFILE
        prepared_variants = REVIEWED_REGISTRY_REPLAY_VARIANTS
    fixture_name = "src/engine/monitoring/policy_generation_code_handoff.py"
    fixture_source = candidate_bytes(fixture_name, optional=True)
    if (fixture_source is not None and hashlib.sha256(fixture_source).hexdigest()
            == REVIEWED_PREPARED_FIXTURE_HASHES[fixture_name]):
        prepared_hashes = REVIEWED_PREPARED_FIXTURE_PROFILE
        prepared_variants = REVIEWED_PREPARED_FIXTURE_VARIANTS
    if any(
        (source := candidate_bytes(name, optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == sha
        for name, sha in REVIEWED_SUBMIT_PROBE_HASHES.items()
    ):
        prepared_hashes = REVIEWED_SUBMIT_PROBE_PROFILE
        prepared_variants = REVIEWED_SUBMIT_PROBE_VARIANTS
    if any(
        (source := candidate_bytes(name, optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == sha
        for name, sha in REVIEWED_HEALTH_SNAPSHOT_HASHES.items()
    ):
        prepared_hashes = REVIEWED_HEALTH_SNAPSHOT_PROFILE
        prepared_variants = REVIEWED_HEALTH_SNAPSHOT_VARIANTS
    if any(
        (source := candidate_bytes(name, optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == sha
        for name, sha in REVIEWED_CUMULATIVE_HOLD_HASHES.items()
    ):
        prepared_hashes = REVIEWED_CUMULATIVE_HOLD_PROFILE
        prepared_variants = REVIEWED_CUMULATIVE_HOLD_VARIANTS
    if any(
        (source := candidate_bytes(name, optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == sha
        for name, sha in REVIEWED_CLOSED_LOADER_HASHES.items()
    ):
        prepared_hashes = REVIEWED_CLOSED_LOADER_PROFILE
        prepared_variants = REVIEWED_CLOSED_LOADER_VARIANTS
    if any(
        (source := candidate_bytes(name, optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == sha
        for name, sha in REVIEWED_STOP_INDEX_HASHES.items()
    ):
        prepared_hashes = REVIEWED_STOP_INDEX_PROFILE
        prepared_variants = REVIEWED_STOP_INDEX_VARIANTS
    if (
        (source := candidate_bytes("src/engine/infrastructure/startup_validation_code_context.py", optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == REVIEWED_ISOLATED_INDEX_HASHES["src/engine/infrastructure/startup_validation_code_context.py"]
    ):
        prepared_hashes = REVIEWED_ISOLATED_INDEX_PROFILE
        prepared_variants = REVIEWED_ISOLATED_INDEX_VARIANTS
    if (
        (source := candidate_bytes("src/engine/infrastructure/startup_validation_code_context.py", optional=True)) is not None
        and hashlib.sha256(source).hexdigest() == REVIEWED_SUFFIX_REPORT_HASHES["src/engine/infrastructure/startup_validation_code_context.py"]
    ):
        prepared_hashes = REVIEWED_SUFFIX_REPORT_PROFILE
        prepared_variants = REVIEWED_SUFFIX_REPORT_VARIANTS
    entry_cost_hashes = (
        prepared_hashes
        if prepared_owner_present
        else (
            REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_HASHES
            if prestart_integration_present
            else (
                REVIEWED_ENTRY_COST_PRE_PRESTART_HASHES
                if preassessment_present
                else (
                    REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_HASHES
                    if signed_surge_present
                    else (
                        REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_HASHES
                        if expiry_health_present
                        else (
                            REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_HASHES
                            if first_turn_present
                            else (
                                REVIEWED_ENTRY_COST_PRE_FIRST_TURN_HASHES
                                if prepared_start_present
                                else (
                                    REVIEWED_ENTRY_COST_PRE_PREPARED_START_HASHES
                                    if main_preparation_present
                                    else (
                                        REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_HASHES
                                        if prepared_repair_present
                                        else (
                                            REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_HASHES
                                            if prepared_validation_present
                                            else (
                                                REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_HASHES
                                                if coordination_present
                                                else (
                                                    REVIEWED_ENTRY_COST_PRE_COORDINATION_HASHES
                                                    if native_label_present
                                                    else REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_HASHES
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    entry_cost_variants = (
        prepared_variants
        if prepared_owner_present
        else (
            REVIEWED_ENTRY_COST_PRE_PREPARED_OWNER_VARIANTS
            if prestart_integration_present
            else (
                REVIEWED_ENTRY_COST_PRE_PRESTART_VARIANTS
                if preassessment_present
                else (
                    REVIEWED_ENTRY_COST_PRE_PREASSESSMENT_VARIANTS
                    if signed_surge_present
                    else (
                        REVIEWED_ENTRY_COST_PRE_SIGNED_SURGE_VARIANTS
                        if expiry_health_present
                        else (
                            REVIEWED_ENTRY_COST_PRE_EXPIRY_HEALTH_VARIANTS
                            if first_turn_present
                            else (
                                REVIEWED_ENTRY_COST_PRE_FIRST_TURN_VARIANTS
                                if prepared_start_present
                                else (
                                    REVIEWED_ENTRY_COST_PRE_PREPARED_START_VARIANTS
                                    if main_preparation_present
                                    else (
                                        REVIEWED_ENTRY_COST_PRE_MAIN_PREPARATION_VARIANTS
                                        if prepared_repair_present
                                        else (
                                            REVIEWED_ENTRY_COST_PRE_PREPARED_REPAIR_VARIANTS
                                            if prepared_validation_present
                                            else (
                                                REVIEWED_ENTRY_COST_PRE_PREPARED_VALIDATION_VARIANTS
                                                if coordination_present
                                                else (
                                                    REVIEWED_ENTRY_COST_PRE_COORDINATION_VARIANTS
                                                    if native_label_present
                                                    else (
                                                        REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_VARIANTS
                                                        if any(
                                                            (root / name).is_file()
                                                            and hashlib.sha256(
                                                                candidate_bytes(name)
                                                            ).hexdigest()
                                                            == sha
                                                            for name, sha in REVIEWED_ENTRY_COST_PRE_NATIVE_LABEL_HASHES.items()
                                                            if REVIEWED_ENTRY_COST_PRE_SHUTDOWN_HASHES.get(
                                                                name
                                                            )
                                                            != sha
                                                        )
                                                        else (
                                                            REVIEWED_ENTRY_COST_PRE_SHUTDOWN_VARIANTS
                                                            if any(
                                                                (root / name).is_file()
                                                                and hashlib.sha256(
                                                                    candidate_bytes(
                                                                        name
                                                                    )
                                                                ).hexdigest()
                                                                == sha
                                                                for name, sha in REVIEWED_ENTRY_COST_PRE_SHUTDOWN_HASHES.items()
                                                                if REVIEWED_ENTRY_COST_PRE_STARTUP_HASHES.get(
                                                                    name
                                                                )
                                                                != sha
                                                            )
                                                            else REVIEWED_ENTRY_COST_PRE_STARTUP_VARIANTS
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    entry_cost_present = any(
        (root / name).is_file()
        and hashlib.sha256(candidate_bytes(name)).hexdigest() == sha
        for name, sha in REVIEWED_ENTRY_COST_HASHES.items()
    )
    contract_names = {repository_name(name) for name in paths.values()}
    for trigger, generations in REVIEWED_HOLDING_RESEARCH_DEPENDENCIES.items():
        if trigger not in contract_names:
            continue
        trigger_sha = hashlib.sha256(candidate_bytes(trigger)).hexdigest()
        dependencies = generations.get(trigger_sha, {})
        # New exact selectors precede their historical parent. The first match
        # selects one complete generation, never per-file SHA alternatives.
        for variants in (
            entry_cost_variants,
            REVIEWED_POSTCLOSE_RECOVERY_DEPENDENCY_VARIANTS,
            REVIEWED_P5_ANCESTRY_DEPENDENCY_VARIANTS,
            REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS,
            REVIEWED_POST_SELL_SOURCE_DEPENDENCY_VARIANTS,
            REVIEWED_HOLDING_INPUT_DEPENDENCY_VARIANTS,
            REVIEWED_NONFIXED_CAPACITY_DEPENDENCY_VARIANTS,
            REVIEWED_QUANTITY_STAGE_DEPENDENCY_VARIANTS,
            REVIEWED_QUANTITY_CAPTURE_DEPENDENCY_VARIANTS,
            REVIEWED_COLLECTOR_FIRST_TRANSITION_DEPENDENCY_VARIANTS,
            REVIEWED_COLLECTOR_CLOSE_DEPENDENCY_VARIANTS,
            REVIEWED_BUY_IDENTITY_DEPENDENCY_VARIANTS,
            REVIEWED_ENTRY_RECEIPT_DEPENDENCY_VARIANTS,
            REVIEWED_FIXED_WAIT_DEPENDENCY_VARIANTS,
            REVIEWED_NATIVE_INVALIDATION_DEPENDENCY_VARIANTS,
            REVIEWED_FINALIZATION_HEALTH_DEPENDENCY_VARIANTS,
            REVIEWED_HISTORICAL_RESOLUTION_DEPENDENCY_VARIANTS,
            REVIEWED_LOGICAL_PIPELINE_DEPENDENCY_VARIANTS,
            REVIEWED_POSTCLOSE_REPAIR_DEPENDENCY_VARIANTS,
            REVIEWED_CLOSED_OBSERVER_DEPENDENCY_VARIANTS,
            REVIEWED_SOURCE_EPOCH_DEPENDENCY_VARIANTS,
            REVIEWED_ROUTED_REUSE_DEPENDENCY_VARIANTS,
            REVIEWED_DELAY_SHUTDOWN_DEPENDENCY_VARIANTS,
            REVIEWED_STARTUP_BUDGET_DEPENDENCY_VARIANTS,
            REVIEWED_ROLE_LATENCY_DEPENDENCY_VARIANTS,
            REVIEWED_DELAY_CLEANUP_DEPENDENCY_VARIANTS,
            REVIEWED_CLEAN_SQLITE_DEPENDENCY_VARIANTS,
            REVIEWED_SQLITE_LIFECYCLE_DEPENDENCY_VARIANTS,
            REVIEWED_RETIRED_REVIEW_DEPENDENCY_VARIANTS,
            REVIEWED_PRODUCT_INTAKE_DEPENDENCY_VARIANTS,
            REVIEWED_INCIDENT_ORDER_DEPENDENCY_VARIANTS,
            REVIEWED_ORIGINAL_GAP_DEPENDENCY_VARIANTS,
            REVIEWED_SOURCE_INTEGRATION_DEPENDENCY_VARIANTS,
            REVIEWED_SOURCE_READER_DEPENDENCY_VARIANTS,
            REVIEWED_FROZEN_INPUT_DEPENDENCY_VARIANTS,
            REVIEWED_BROKER_CUSTODY_DEPENDENCY_VARIANTS,
            REVIEWED_VOTE_METADATA_DEPENDENCY_VARIANTS,
            REVIEWED_PRE_ENTRY_OBSERVER_DEPENDENCY_VARIANTS,
            REVIEWED_STOP_INDEXED_VOTE_DEPENDENCY_VARIANTS,
            REVIEWED_STOP_FORWARD_STREAM_DEPENDENCY_VARIANTS,
            REVIEWED_STOP_SHARED_POSITION_DEPENDENCY_VARIANTS,
            REVIEWED_CALENDAR_PHYSICAL_DEPENDENCY_VARIANTS,
            REVIEWED_ASSEMBLER_BUDGET_DEPENDENCY_VARIANTS,
            REVIEWED_NATIVE_EMPTY_DEPENDENCY_VARIANTS,
            REVIEWED_COMPLETED_EMPTY_DEPENDENCY_VARIANTS,
            REVIEWED_COMPLETED_OFFLINE_DEPENDENCY_VARIANTS,
            REVIEWED_AUXILIARY_DATA_ROOT_DEPENDENCY_VARIANTS,
            REVIEWED_LEGACY_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS,
            REVIEWED_ARCHIVE_AUTHORITY_DEPENDENCY_VARIANTS,
            REVIEWED_POSTCLOSE_READER_DEPENDENCY_VARIANTS,
            REVIEWED_LATE_COST_DEPENDENCY_VARIANTS,
            REVIEWED_PREFIX_PRODUCER_DEPENDENCY_VARIANTS,
            REVIEWED_COMPLETION_CONSUMER_DEPENDENCY_VARIANTS,
            REVIEWED_COMPLETION_CENSUS_DEPENDENCY_VARIANTS,
            REVIEWED_AVG_DOWN_INPUT_DEPENDENCY_VARIANTS,
            REVIEWED_CLEANUP_DEPENDENCY_VARIANTS,
            REVIEWED_QUANTITY_EXCLUSIONS_DEPENDENCY_VARIANTS,
            REVIEWED_HISTORY_SEGMENT_DEPENDENCY_VARIANTS,
            REVIEWED_STARTUP_RETRY_DEPENDENCY_VARIANTS,
            REVIEWED_TRAILING_REUSE_DEPENDENCY_VARIANTS,
            REVIEWED_PARTIAL_CLOCK_DEPENDENCY_VARIANTS,
            REVIEWED_CAUSAL_QUANTITY_DEPENDENCY_VARIANTS,
            REVIEWED_PRESERVED_SNAPSHOT_DEPENDENCY_VARIANTS,
            REVIEWED_SNAPSHOT_METADATA_DEPENDENCY_VARIANTS,
            REVIEWED_ARTIFACT_SOURCE_DEPENDENCY_VARIANTS,
            REVIEWED_PRIOR_SNAPSHOT_IO_DEPENDENCY_VARIANTS,
            REVIEWED_SCANNER_HISTORY_DEPENDENCY_VARIANTS,
            REVIEWED_AUXILIARY_HISTORY_DEPENDENCY_VARIANTS,
            REVIEWED_PARTIAL_SELL_OBSERVER_DEPENDENCY_VARIANTS,
            REVIEWED_STOPPED_PREOPEN_DEPENDENCY_VARIANTS,
            REVIEWED_DELAY_PARENT_VERIFICATION_DEPENDENCY_VARIANTS,
            REVIEWED_STARTUP_READONLY_DEPENDENCY_VARIANTS,
        ):
            variant = variants.get((trigger, trigger_sha))
            if not variant:
                continue
            selector = variant["selector_path"]
            path = root / selector
            if (
                variants
                in (
                    REVIEWED_CLEAN_SQLITE_DEPENDENCY_VARIANTS,
                    REVIEWED_SQLITE_LIFECYCLE_DEPENDENCY_VARIANTS,
                    REVIEWED_TRAILING_REUSE_DEPENDENCY_VARIANTS,
                    REVIEWED_ORIGINAL_GAP_DEPENDENCY_VARIANTS,
                )
                and not path.exists()
                and not path.is_symlink()
            ):
                try:
                    revision_bytes(commit, selector)
                except ValueError as exc:
                    if str(exc) == "entry_consumer_code_source_missing":
                        # A verified predecessor predates this new selector.
                        # A candidate whose Git tree owns it must retain it.
                        continue
                    raise
                raise ValueError(
                    "entry_consumer_reviewed_dependency_missing:" + selector
                )
            if (
                variants
                in (
                    REVIEWED_AUXILIARY_HISTORY_DEPENDENCY_VARIANTS,
                    REVIEWED_STOPPED_PREOPEN_DEPENDENCY_VARIANTS,
                )
                and not path.exists()
                and not path.is_symlink()
            ):
                # Earlier immutable preparations predate this selector. Their
                # complete historical dependency generation still verifies.
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(
                    "entry_consumer_reviewed_dependency_missing:" + selector
                )
            selector_sha = hashlib.sha256(candidate_bytes(selector)).hexdigest()
            if (
                variants is REVIEWED_CLEANUP_DEPENDENCY_VARIANTS
                and selector_sha != variant["selector_sha256"]
            ):
                if (
                    prepared_owner_present
                    and REVIEWED_PREPARED_OWNER_HASHES.get(selector) == selector_sha
                ):
                    # This historical selector no longer describes the exact
                    # reviewed current generation, which is checked below.
                    continue
                raise ValueError(
                    "entry_consumer_reviewed_dependency_unreviewed:" + selector
                )
            if selector_sha == variant["selector_sha256"]:
                additional = variant.get("additional_selector_path")
                if (
                    additional
                    and hashlib.sha256(candidate_bytes(additional)).hexdigest()
                    != variant["additional_selector_sha256"]
                ):
                    continue
                dependencies = variant["dependencies"]
                extensions = variant["contract_extensions"].get(
                    (origin, expected), extensions
                )
                break
        if cleanup_present:
            dependencies = {**dependencies, **REVIEWED_RETIRED_REVIEW_HASHES}
        if role_latency_present:
            dependencies = {**dependencies, **REVIEWED_ROLE_LATENCY_HASHES}
        if delay_shutdown_present:
            dependencies = {
                **dependencies,
                **REVIEWED_STARTUP_BUDGET_HASHES,
                **REVIEWED_DELAY_SHUTDOWN_HASHES,
            }
        if routed_reuse_present:
            dependencies = {
                **dependencies,
                **REVIEWED_STARTUP_BUDGET_HASHES,
                **REVIEWED_DELAY_SHUTDOWN_HASHES,
                **REVIEWED_ROUTED_REUSE_HASHES,
            }
        if source_epoch_present:
            dependencies = {
                **dependencies,
                **REVIEWED_STARTUP_BUDGET_HASHES,
                **REVIEWED_DELAY_SHUTDOWN_HASHES,
                **REVIEWED_ROUTED_REUSE_HASHES,
                **REVIEWED_SOURCE_EPOCH_HASHES,
            }
        if closed_observer_present:
            dependencies = {**dependencies, **REVIEWED_CLOSED_OBSERVER_HASHES}
        if postclose_repair_present:
            dependencies = {**dependencies, **REVIEWED_POSTCLOSE_REPAIR_HASHES}
        if logical_pipeline_present:
            dependencies = {**dependencies, **REVIEWED_LOGICAL_PIPELINE_HASHES}
        if historical_resolution_present:
            dependencies = {**dependencies, **REVIEWED_HISTORICAL_RESOLUTION_HASHES}
        if finalization_health_present:
            dependencies = {**dependencies, **REVIEWED_FINALIZATION_HEALTH_HASHES}
        if native_invalidation_present:
            dependencies = {**dependencies, **REVIEWED_NATIVE_INVALIDATION_HASHES}
        if fixed_wait_present:
            dependencies = {**dependencies, **REVIEWED_FIXED_WAIT_HASHES}
        if entry_receipt_present:
            dependencies = {**dependencies, **REVIEWED_ENTRY_RECEIPT_HASHES}
        if buy_identity_present:
            dependencies = {**dependencies, **REVIEWED_BUY_IDENTITY_HASHES}
        if collector_close_present:
            dependencies = {**dependencies, **REVIEWED_COLLECTOR_CLOSE_HASHES}
        if first_transition_present:
            dependencies = {
                **dependencies,
                **REVIEWED_COLLECTOR_FIRST_TRANSITION_HASHES,
            }
        if delay_machine_parent_present:
            dependencies = {**dependencies, **REVIEWED_DELAY_MACHINE_PARENT_HASHES}
            extensions = {
                name: REVIEWED_DELAY_MACHINE_PARENT_HASHES.get(
                    repository_name(name), sha
                )
                for name, sha in extensions.items()
            }
        if quantity_capture_present:
            dependencies = {**dependencies, **REVIEWED_QUANTITY_CAPTURE_HASHES}
        if quantity_stage_present:
            dependencies = {**dependencies, **REVIEWED_QUANTITY_STAGE_HASHES}
        if nonfixed_capacity_present:
            dependencies = {**dependencies, **REVIEWED_NONFIXED_CAPACITY_HASHES}
            extensions = {
                name: REVIEWED_NONFIXED_CAPACITY_HASHES.get(repository_name(name), sha)
                for name, sha in extensions.items()
            }
        if holding_input_present:
            dependencies = {
                **{repository_name(name): sha for name, sha in dependencies.items()},
                **REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES,
            }
            extensions = {
                name: REVIEWED_HOLDING_INPUT_DEPENDENCY_HASHES.get(
                    repository_name(name), sha
                )
                for name, sha in extensions.items()
            }
        if post_sell_source_present:
            dependencies = {**dependencies, **REVIEWED_POST_SELL_SOURCE_HASHES}
            extensions = {
                name: REVIEWED_POST_SELL_SOURCE_HASHES.get(repository_name(name), sha)
                for name, sha in extensions.items()
            }
        if operator_market_present:
            operator_variants = (
                entry_cost_variants
                if entry_cost_present
                else (
                    REVIEWED_POSTCLOSE_RECOVERY_DEPENDENCY_VARIANTS
                    if postclose_recovery_present
                    else (
                        REVIEWED_P5_ANCESTRY_DEPENDENCY_VARIANTS
                        if p5_ancestry_present
                        else REVIEWED_OPERATOR_MARKET_DEPENDENCY_VARIANTS
                    )
                )
            )
            operator_variant = operator_variants.get((trigger, trigger_sha))
            if operator_variant is None:
                raise ValueError(
                    "entry_consumer_operator_market_generation_mixed:" + trigger
                )
            dependencies = {**dependencies, **operator_variant["dependencies"]}
            extensions = {
                name: REVIEWED_OPERATOR_MARKET_HASHES.get(repository_name(name), sha)
                for name, sha in extensions.items()
            }
            if postclose_recovery_present:
                extensions = {
                    name: REVIEWED_POSTCLOSE_RECOVERY_HASHES.get(
                        repository_name(name), sha
                    )
                    for name, sha in extensions.items()
                }
        if entry_cost_present:
            variant = entry_cost_variants.get((trigger, trigger_sha))
            if variant is None:
                raise ValueError(
                    "entry_consumer_entry_cost_generation_mixed:" + trigger
                )
            dependencies = {**dependencies, **variant["dependencies"]}
            extensions = {
                name: entry_cost_hashes.get(repository_name(name), sha)
                for name, sha in extensions.items()
            }
        dependencies_by_trigger[trigger] = (trigger_sha, dependencies)
    for key, name in paths.items():
        after = candidate_bytes(name)
        runtime_hashes[os.path.normpath(name)] = hashlib.sha256(after).hexdigest()
        if name in extensions:
            if hashlib.sha256(after).hexdigest() != extensions[
                name
            ] or after != revision_bytes(commit, name):
                raise ValueError("entry_consumer_contract_extension_unreviewed:" + name)
            changed.append(name)
            continue
        before = revision_bytes(origin, name)
        if after != revision_bytes(commit, name):
            raise ValueError("entry_consumer_dirty_release")
        original_raw = revision_raw(origin, name)
        original_hashes[key] = hashlib.sha256(original_raw).hexdigest()
        if before == after:
            if original_raw != physical_candidates[repository_name(name)]:
                changed.append(name)
            continue
        pair = (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest())
        if (
            pair in REVIEWED_OPERATOR_MARKET_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_POST_SELL_SOURCE_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_HOLDING_INPUT_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_NONFIXED_CAPACITY_PAIRS.get(repository_name(name), ())
            or pair
            in REVIEWED_DELAY_MACHINE_PARENT_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_QUANTITY_STAGE_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_QUANTITY_CAPTURE_PAIRS.get(repository_name(name), ())
            or pair
            in REVIEWED_COLLECTOR_FIRST_TRANSITION_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_COLLECTOR_CLOSE_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_BUY_IDENTITY_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_ENTRY_RECEIPT_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_FIXED_WAIT_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_NATIVE_INVALIDATION_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_FINALIZATION_HEALTH_PAIRS.get(repository_name(name), ())
            or pair
            in REVIEWED_HISTORICAL_RESOLUTION_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_LOGICAL_PIPELINE_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_POSTCLOSE_REPAIR_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_CLOSED_OBSERVER_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_SOURCE_EPOCH_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_ROUTED_REUSE_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_DELAY_SHUTDOWN_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_STARTUP_BUDGET_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_ROLE_LATENCY_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_DELAY_CLEANUP_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_VOTE_METADATA_PAIRS.get(name, ())
            or pair in REVIEWED_PRE_ENTRY_OBSERVER_PAIRS.get(name, ())
            or pair in REVIEWED_STOP_INDEXED_VOTE_PAIRS.get(name, ())
            or pair in REVIEWED_STOP_FORWARD_STREAM_PAIRS.get(name, ())
            or pair in REVIEWED_STOP_SHARED_POSITION_PAIRS.get(name, ())
            or pair in REVIEWED_CALENDAR_PHYSICAL_PAIRS.get(name, ())
            or pair in REVIEWED_ASSEMBLER_BUDGET_PAIRS.get(name, ())
            or pair in REVIEWED_NATIVE_EMPTY_PAIRS.get(name, ())
            or pair in REVIEWED_COMPLETED_EMPTY_PAIRS.get(name, ())
            or pair in REVIEWED_COMPLETED_OFFLINE_PAIRS.get(name, ())
            or pair in REVIEWED_AUXILIARY_DATA_ROOT_PAIRS.get(name, ())
            or pair in REVIEWED_LEGACY_ARCHIVE_AUTHORITY_PAIRS.get(name, ())
            or pair in REVIEWED_ARCHIVE_AUTHORITY_PAIRS.get(name, ())
            or pair in REVIEWED_POSTCLOSE_READER_PAIRS.get(name, ())
            or pair in REVIEWED_LATE_COST_PAIRS.get(name, ())
            or pair in REVIEWED_PREFIX_PRODUCER_PAIRS.get(name, ())
            or pair in REVIEWED_COMPLETION_CONSUMER_PAIRS.get(name, ())
            or pair in REVIEWED_COMPLETION_CENSUS_PAIRS.get(name, ())
            or pair in REVIEWED_CLEANUP_PAIRS.get(name, ())
            or pair in REVIEWED_HISTORY_SEGMENT_PAIRS.get(name, ())
            or pair in REVIEWED_STARTUP_RETRY_PAIRS.get(name, ())
            or pair in REVIEWED_TRAILING_REUSE_PAIRS.get(name, ())
            or pair in REVIEWED_PARTIAL_CLOCK_PAIRS.get(name, ())
            or pair in REVIEWED_CAUSAL_QUANTITY_PAIRS.get(name, ())
            or pair in REVIEWED_PRESERVED_SNAPSHOT_PAIRS.get(name, ())
            or pair in REVIEWED_SNAPSHOT_METADATA_PAIRS.get(name, ())
            or pair in REVIEWED_ARTIFACT_SOURCE_PAIRS.get(name, ())
            or pair in REVIEWED_PRIOR_SNAPSHOT_IO_PAIRS.get(name, ())
            or pair in REVIEWED_SCANNER_HISTORY_OBSERVER_PAIRS.get(name, ())
            or pair in REVIEWED_SYNC_PROVIDER_OBSERVER_PAIRS.get(name, ())
            or pair in REVIEWED_PARTIAL_SELL_RESEARCH_SOURCE_PAIRS.get(name, ())
            or pair == REVIEWED_AUXILIARY_HISTORY_SOURCES.get(name)
        ):
            changed.append(name)
            continue
        if (
            pair in REVIEWED_ENTRY_COST_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_POSTCLOSE_RECOVERY_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_SOURCE_INTEGRATION_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_SOURCE_READER_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_FROZEN_INPUT_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_BROKER_CUSTODY_PAIRS.get(repository_name(name), ())
            or pair in REVIEWED_AVG_DOWN_INPUT_SOURCES.get(repository_name(name), ())
            or pair
            in (
                REVIEWED_DELAY_PARENT_VERIFICATION_SOURCES.get(repository_name(name)),
                REVIEWED_RESEARCH_BUDGET_INTEGRATION_SOURCES.get(repository_name(name)),
                REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES.get(
                    repository_name(name)
                ),
                REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES.get(name),
                REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES.get(name),
                REVIEWED_QUANTITY_RESEARCH_COST_SOURCES.get(name),
                REVIEWED_DELAY_RESEARCH_SOURCES.get(name),
                REVIEWED_POST_AUX_GUARD_SOURCES.get(name),
                REVIEWED_AUXILIARY_PRODUCTION_INPUT_SOURCES.get(name),
                REVIEWED_NONFIXED_QUOTE_DELIVERY_SOURCES.get(name),
                REVIEWED_CURSOR_ASOF_SOURCES.get(name),
                REVIEWED_NONFIXED_CONTINUITY_SOURCES.get(name),
                REVIEWED_DELAY_SITUATION_SOURCES.get(name),
                REVIEWED_LONG4_SOURCE_RETENTION_SOURCES.get(name),
                REVIEWED_PROBE_PARTIAL_INTEGRATION_SOURCES.get(name),
                REVIEWED_SOURCE_GAP_CROSSING_SOURCES.get(name),
                REVIEWED_ENTRY_CONSUMER_SOURCES.get(name),
                REVIEWED_ENTRY_LATENCY_SOURCES.get(name),
                REVIEWED_ENTRY_BOUNDARY_SOURCES.get(name),
                REVIEWED_ENTRY_RESPONSE_SOURCES.get(name),
                REVIEWED_ENTRY_STORAGE_SOURCES.get(name),
                REVIEWED_JOINT_CONSUMER_SOURCES.get(name),
                REVIEWED_REST_REDUCTION_SOURCES.get(name),
                REVIEWED_IO_OBSERVER_SOURCES.get(name),
                REVIEWED_IO_DIGEST_SOURCES.get(name),
                REVIEWED_STOP_CONSUMER_SOURCES.get(name),
                REVIEWED_NONFIXED_SUBMIT_SOURCES.get(name),
                REVIEWED_ENTRY_PROJECTION_DELIVERY_SOURCES.get(name),
                REVIEWED_ENTRY_PROJECTION_MOUNT_SOURCES.get(name),
                REVIEWED_STARTUP_OBSERVER_SOURCES.get(name),
                REVIEWED_OBSERVER_HEALTH_SOURCES.get(name),
                REVIEWED_SUBMISSION_TIMEOUT_SOURCES.get(name),
                REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES.get(name),
                REVIEWED_PREMARKET_OBSERVER_SOURCES.get(name),
                REVIEWED_ACTIVE_OBSERVER_SOURCES.get(name),
                REVIEWED_CURRENT_OBSERVER_SOURCES.get(name),
                REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES.get(name),
                REVIEWED_OBSERVER_STATE_READER_SOURCES.get(name),
                REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES.get(name),
                REVIEWED_NATIVE_FEATURE_GAP_OBSERVER_SOURCES.get(name),
                REVIEWED_SCOPE_READY_OBSERVER_SOURCES.get(name),
                REVIEWED_HOLDING_CONTEXT_SNAPSHOT_SOURCES.get(name),
                REVIEWED_STOP_VOTE_SNAPSHOT_SOURCES.get(name),
                REVIEWED_ORDERED_PUBLICATION_SOURCES.get(name),
                REVIEWED_OPPORTUNITY_CUSTODY_SOURCES.get(name),
                REVIEWED_ENTRY_RECEIPT_IDENTITY_SOURCES.get(name),
                REVIEWED_ASYNC_SESSION_BOUNDARY_SOURCES.get(name),
                REVIEWED_TERMINAL_CLOCK_CUSTODY_SOURCES.get(name),
                REVIEWED_NATIVE_ARM_COMPLETION_SOURCES.get(name),
                REVIEWED_CARRIED_SOURCE_BINDING_SOURCES.get(name),
                REVIEWED_HPSP_SOURCE_RECOVERY_SOURCES.get(name),
                REVIEWED_HOLDING_CONTRACT_SOURCES.get(name),
                REVIEWED_POSTCLOSE_READ_SOURCES.get(name),
                REVIEWED_CARRIED_VOTE_PREFIX_SOURCES.get(name),
                REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES.get(name),
                REVIEWED_PREASSESSMENT_OBSERVER_SOURCES.get(name),
            )
        ):
            changed.append(name)
            continue
        if name not in allowed:
            raise ValueError("entry_consumer_producer_changed:" + name)

        def projection(raw):
            tree = ast.parse(raw)
            tree.body = [
                node
                for node in tree.body
                if not (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name in allowed[name]
                )
            ]
            return ast.dump(tree, include_attributes=False)

        if projection(before) != projection(after):
            raise ValueError("entry_consumer_unreviewed_change:" + name)
        changed.append(name)
    for trigger, (trigger_sha, dependencies) in dependencies_by_trigger.items():
        # The selected trigger is re-read in the contract loop and remains Git
        # bound there; its dependency generation cannot change during intake.
        if runtime_hashes.get(trigger) != trigger_sha:
            raise ValueError("entry_consumer_reviewed_trigger_changed:" + trigger)
        for name, expected_sha in dependencies.items():
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("entry_consumer_reviewed_dependency_missing:" + name)
            raw = candidate_bytes(name)
            if hashlib.sha256(raw).hexdigest() != expected_sha:
                raise ValueError(
                    "entry_consumer_reviewed_dependency_unreviewed:" + name
                )
            if raw != revision_bytes(commit, name):
                raise ValueError("entry_consumer_reviewed_dependency_dirty:" + name)
    original_digest = hashlib.sha256(
        json.dumps(
            original_hashes,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    if original_digest != expected:
        raise ValueError("entry_consumer_original_code_contract_invalid")
    return changed


def verify_candidate_delay_code(day, root, commit):
    """Reject an incompatible delay consumer before the running Main is drained.

    This does not select the candidate, publish receipts or authorize startup;
    the normal custody and full bootstrap checks still run after selection.
    The ordered caller verifies the incumbent bootstrap first.
    """
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError("entry_consumer_candidate_code_mismatch")
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get("selected_release_sha")
    if not origin or origin != _preopen(day).get("selected_release_commit"):
        raise ValueError("entry_consumer_origin_invalid")
    bound = manifest.get("pre_submit_delay_handoff") or {}
    if bound.get("status") != "verified_initial_timing_policy":
        return dict(status="not_applicable", target_date=day)
    if bound.get("target_date") != day or not bound.get("code_contract_sha256"):
        raise ValueError("entry_consumer_policy_binding_invalid")
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS

    changed = _verify_entry_code_delta(
        root,
        commit,
        origin,
        {name: name for name in CONTRACT_PATHS},
        bound["code_contract_sha256"],
    )
    return dict(
        status="pass",
        target_date=day,
        origin_commit=origin,
        release_commit=commit,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
        actual_pid_consumed=False,
    )


def verify_candidate_stop_code(day, root, commit):
    """Pre-stop source-exact stop-code check; never select/rewrite a policy."""
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError("entry_consumer_candidate_code_mismatch")
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get("selected_release_sha")
    if not origin or origin != _preopen(day).get("selected_release_commit"):
        raise ValueError("entry_consumer_origin_invalid")
    from src.engine.scalping import main_stop_policy as S

    env = manifest.get("env_overrides") or {}
    if not env.get(S.ENV_FILE):
        return dict(status="pass", applicability="not_installed", target_date=day)
    bundle = S.load_bundle(
        env[S.ENV_FILE], env[S.ENV_SHA], day, require_current_code=False
    )
    bound = manifest.get("main_stop_confirmation_receipt") or {}
    if (
        bound.get("policy_sha256") != bundle["policy_sha256"]
        or bound.get("target_date") != day
    ):
        raise ValueError("entry_consumer_policy_binding_invalid")
    if bundle["code_sha256"] == S.implementation_sha():
        changed = []
    else:
        if any(c["status"] == "selected" for c in bundle["cells"].values()):
            raise ValueError("stop_bundle_code_generation_changed")
        changed = _verify_entry_code_delta(
            root,
            commit,
            origin,
            {name: "src/engine/" + name for name in S.implementation_paths()},
            bundle["code_sha256"],
        )
    return dict(
        status="pass",
        target_date=day,
        origin_commit=origin,
        release_commit=commit,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
        actual_pid_consumed=False,
    )


def verify_candidate_holding_vote_code(day, root, commit):
    """Check the original holding-vote code pin before changing selection.

    Only incumbent carry can cross a reviewed code delta. Full source handoff
    and the unchanged policy receipt remain mandatory during preparation.
    """
    _today(day, None)
    root = Path(root).resolve(strict=True)
    if Path(__file__).resolve().parents[3] != root:
        raise ValueError("entry_consumer_candidate_code_mismatch")
    manifest = _read(bootstrap.manifest_path(day))
    origin = manifest.get("selected_release_sha")
    if not origin or origin != _preopen(day).get("selected_release_commit"):
        raise ValueError("entry_consumer_origin_invalid")
    bound = manifest.get("holding_path_vote_policy_receipt") or {}
    from src.engine.scalping import holding_path_vote_policy as V
    from src.engine.scalping.holding_vote_experiment import code_sha, _code_paths

    if not bound.get("allowed_runtime_apply"):
        if (
            bound.get("status") != "baseline_policy_not_published"
            or V.policy_path(DATA_DIR, day).exists()
        ):
            raise ValueError("holding_vote_candidate_policy_not_verified")
        return dict(status="pass", applicability="not_installed", target_date=day)
    bundle = V.load_bundle(DATA_DIR, day, require_current_code=False)
    if (
        bound.get("bundle_sha256") != bundle.get("bundle_sha256")
        or bound.get("target_date") != day
        or bound.get("path") != str(V.policy_path(DATA_DIR, day))
    ):
        raise ValueError("entry_consumer_policy_binding_invalid")
    changed = []
    if (
        bundle.get("schema") == V.SUCCESSOR_SCHEMA
        and bundle.get("code_sha256") != code_sha()
    ):
        if bundle.get("selection_mode") != "incumbent_carry":
            raise ValueError("holding_vote_successor_code_changed")
        changed = _verify_entry_code_delta(
            root,
            commit,
            origin,
            {name: "src/engine/" + name for name in _code_paths()},
            bundle["code_sha256"],
        )
    return dict(
        status="pass",
        target_date=day,
        origin_commit=origin,
        release_commit=commit,
        changed_consumer_paths=changed,
        policy_effect="unchanged",
        actual_pid_consumed=False,
    )


def _checked_bootstrap(day, pid):
    options = {"observer_reuse": True} if _OBSERVER_CUSTODY.get() is not None else {}
    check = bootstrap.verify_bootstrap(day, pid=pid, write=False, **options)
    if check.get("status") != "pass":
        raise ValueError(
            "intraday_bootstrap_invalid:" + ",".join(check.get("findings") or [])
        )
    from src.engine.automation.auxiliary_reader_readiness import verify_auxiliary_reader

    verify_auxiliary_reader(day, data_root=DATA_DIR)
    return check


def prepare(
    day,
    *,
    old_pid,
    previous_root,
    confirm,
    now=None,
    reseal_postclose_source=False,
    previous_stopped=False,
    freeze_operating_checklist=False,
):
    token = _STOPPED_PREPARATION.set(
        (day, int(old_pid), str(Path(previous_root).resolve()))
        if previous_stopped
        else None
    )
    native_token = _NATIVE_PREDECESSOR.set(None)
    try:
        return _prepare(
            day,
            old_pid=old_pid,
            previous_root=previous_root,
            confirm=confirm,
            now=now,
            reseal_postclose_source=reseal_postclose_source,
            previous_stopped=previous_stopped,
            freeze_operating_checklist=freeze_operating_checklist,
        )
    finally:
        _NATIVE_PREDECESSOR.reset(native_token)
        _STOPPED_PREPARATION.reset(token)


def _prepare(
    day,
    *,
    old_pid,
    previous_root,
    confirm,
    now=None,
    reseal_postclose_source=False,
    previous_stopped=False,
    freeze_operating_checklist=False,
):
    current = _today(day, now)
    if confirm != CONFIRM:
        raise ValueError("intraday_handoff_explicit_authority_required")
    root, commit = _selection()
    previous = Path(previous_root).resolve(strict=True)
    managed = (
        DATA_DIR.parent.parent / f"{DATA_DIR.parent.name}-runtime-releases"
    ).resolve()
    if previous.parent != managed or previous == root:
        raise ValueError("intraday_previous_release_invalid")
    old_commit = subprocess.check_output(
        ["git", "-C", str(previous), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(previous),
            "status",
            "--porcelain",
            "--",
            "src",
            "deploy",
            "restart.sh",
        ],
        text=True,
    ).strip()
    original = _preopen(day)
    if previous_stopped and original.get("selected_release_commit") == old_commit:
        selection = _read(DATA_DIR / "runtime/runtime_release_selection.json")
        if (
            selection.get("approved_by") != "user"
            or selection.get("approval_scope") != "ordered_intraday_deploy_and_restart"
            or selection.get("previous_release_root")
            != str(Path(previous_root).resolve())
            or Path("/proc", str(int(old_pid))).exists()
        ):
            raise ValueError("intraday_native_predecessor_not_stopped")
        path = selection.get("native_predecessor_path")
        identity = (_read(path).get("verification") or {}).get("pid_identity") or {}
        if identity.get("pid") != int(old_pid):
            raise ValueError("intraday_native_predecessor_pid_invalid")
        native = _native_predecessor(
            day,
            selection["git_commit"],
            previous_root,
            selection["previous_git_commit"],
            identity,
            path,
            selection.get("native_predecessor_sha256"),
        )
        _NATIVE_PREDECESSOR.set(native)
    native_predecessor = _NATIVE_PREDECESSOR.get()
    if previous_stopped:
        # Explicit recovery of an attested but terminated predecessor. Never
        # fabricate live PID consumption from a historical bootstrap receipt.
        if Path("/proc", str(int(old_pid))).exists():
            raise ValueError("intraday_previous_pid_still_exists")
        previous_consumed_path = (
            Path(native_predecessor["path"])
            if native_predecessor
            else _paths(day, old_commit)[1]
        )
        previous_consumed_sha = _sha(previous_consumed_path)
        old_identity = (
            native_predecessor["identity"]
            if native_predecessor
            else _read(previous_consumed_path).get("pid_identity") or {}
        )
        if old_identity.get("pid") != int(old_pid) or not old_identity.get(
            "start_ticks"
        ):
            raise ValueError("intraday_stopped_identity_unattested")
        if (
            original.get("selected_release_commit") == old_commit
            and not native_predecessor
        ):
            raise ValueError("intraday_stopped_consumed_handoff_required")
    else:
        old_identity = _identity(old_pid)
    # A subsequent same-day handoff may use the preceding verified consumption.
    if original.get("selected_release_commit") != old_commit:
        prior_path, prior_consumed = _paths(day, old_commit)
        prior = _read(prior_path)
        consumed = _read(prior_consumed)
        if (
            prior.get("schema") != "intraday_policy_preserving_release_handoff_v1"
            or prior.get("status") != "prepared_verified"
            or prior.get("authority") != CONFIRM
            or prior.get("target_date") != day
            or prior.get("selected_release_commit") != old_commit
            or prior.get("release_root") != str(previous)
            or _sha(_preopen_path(day)) != prior.get("preopen_sha256")
            or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
            or consumed.get("status") != "pass"
            or consumed.get("target_date") != day
            or consumed.get("selected_release_commit") != old_commit
            or consumed.get("release_root") != str(previous)
            or consumed.get("actual_pid_consumed") is not True
            or consumed.get("pid_identity") != old_identity
            or consumed.get("handoff_sha256") != _sha(prior_path)
        ):
            raise ValueError("intraday_previous_consumption_invalid")
    if dirty or old_identity["cwd"] != str(previous / "src"):
        raise ValueError("intraday_previous_pid_or_release_invalid")
    check = _checked_bootstrap(day, None if previous_stopped else old_pid)
    prepared_index = (
        DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"
    )
    prepared = _read(prepared_index)
    receipt_path = Path(prepared["receipt_path"])
    prepared_root = prepared_index.parent.resolve()
    if receipt_path.resolve().parent.parent != prepared_root or _sha(
        receipt_path
    ) != prepared.get("receipt_sha256"):
        raise ValueError("intraday_original_prepared_invalid")
    frozen = [
        bootstrap.env_path(day),
        bootstrap.manifest_path(day),
        _preopen_path(day),
        prepared_index,
        receipt_path,
    ]
    if native_predecessor:
        frozen.append(previous_consumed_path)
    if original.get("selected_release_commit") != old_commit:
        if (
            consumed.get("manifest_sha256") != check.get("manifest_sha256")
            or prior.get("prepared_receipt_path") != str(receipt_path)
            or prior.get("prepared_receipt_sha256") != _sha(receipt_path)
            or any(
                prior.get("frozen_files", {}).get(str(path)) != _sha(path)
                for path in frozen
            )
        ):
            raise ValueError("intraday_previous_generation_changed")
    reseal = None
    if reseal_postclose_source:
        from src.engine.automation.next_preopen_readiness import _source_receipts

        original_prepared = _read(receipt_path)
        source_day = original_prepared.get("source_date")
        if (
            original_prepared.get("schema") != "next_preopen_readiness_v1"
            or original_prepared.get("status") != "prepared_verified"
            or original_prepared.get("target_date") != day
            or original_prepared.get("actual_pid_consumed") is not False
        ):
            raise ValueError("intraday_original_prepared_contract_invalid")
        # Reuse the exact sealed whole-chain PASS and independently checked
        # live old PID. Re-evaluating the new selector here would require its
        # own consumed receipt before prepare/launch, a circular second-handoff
        # gate. Every source hash and dated policy byte must still match; the
        # launcher/consumers recheck the full contract after the new PID binds.
        controller = _read(
            DATA_DIR
            / "report/postclose_done_controller"
            / f"postclose_done_controller_{source_day}.json"
        )
        strict = (
            _read(controller["verification_attempt_path"])
            if controller.get("verification_attempt_path")
            else {}
        )
        old_checklist = (strict.get("checklist_handoff") or {}).get("path")
        expected = (strict.get("generation_binding") or {}).get("checklist_sha256")
        historical = None
        try:
            old_checklist_sha = _sha(old_checklist) if old_checklist else None
        except FileNotFoundError:
            # A removed executable release can have owned the original docs
            # symlink. Absence permits only the same exact-hash Git/preserved
            # snapshot path below, never a fresh document or relaxed binding.
            old_checklist_sha = None
        if old_checklist and old_checklist_sha != expected:
            relative = "docs/checklists/" + day + "-stage2-todo-checklist.md"
            origin_commit, predecessor = old_commit, None
            if original.get("selected_release_commit") != old_commit:
                inherited = (prior.get("postclose_source_reseal") or {}).get(
                    "historical_checklist"
                )
                if inherited:
                    historical_prior, predecessor = _historical_predecessor(
                        day, old_commit, expected
                    )
                    origin_commit = historical_prior["git_commit"]
            try:
                original_bytes = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        str(previous),
                        "show",
                        origin_commit + ":" + relative,
                    ],
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                # A PREOPEN-generated document may not exist in the earlier
                # release tree. Only the exact strict-bound snapshot below can
                # replace missing Git bytes; current edited docs cannot.
                original_bytes = b""
            original_basis = "original_whole_chain_checklist_generation"
            if hashlib.sha256(original_bytes).hexdigest() != expected:
                # Native postclose writes the checklist after the release was
                # committed. Its strict-bound bytes need not be a Git blob.
                preserved = (
                    DATA_DIR
                    / "runtime/policy_bootstrap/historical_checklists"
                    / (expected + ".md")
                )
                if not preserved.exists() or _sha(preserved) != expected:
                    raise ValueError(
                        "intraday_original_checklist_git_generation_missing"
                    )
                original_bytes = preserved.read_bytes()
                original_basis = "strict_bound_postclose_generated_checklist"
            snapshot = _paths(day, commit)[0].parent / (
                commit + ".historical-checklist.md"
            )
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if snapshot.exists():
                if snapshot.read_bytes() != original_bytes:
                    raise ValueError("intraday_historical_checklist_snapshot_changed")
            else:
                with snapshot.open("xb") as out:
                    out.write(original_bytes)
                    out.flush()
                    os.fsync(out.fileno())
            historical = dict(
                path=str(snapshot),
                sha256=expected,
                git_commit=origin_commit,
                git_path=relative,
                basis=original_basis,
            )
            if predecessor:
                historical["predecessor"] = predecessor
            frozen.append(snapshot)
        source = _source_receipts(
            source_day,
            day,
            generation_only=True,
            **({"checklist_snapshot": Path(historical["path"])} if historical else {}),
        )
        if not source.get("policy_receipts") or source[
            "policy_receipts"
        ] != original_prepared.get("policy_receipts"):
            raise ValueError("intraday_reseal_policy_generation_changed")
        checklist = (
            DATA_DIR.parent / "docs/checklists" / (day + "-stage2-todo-checklist.md")
        )
        operating = (
            _freeze_operating_checklist(day, commit, checklist)
            if freeze_operating_checklist
            else None
        )
        frozen.extend(
            [
                Path(source["controller_path"]),
                Path(source["summary_path"]),
                Path(operating["path"]) if operating else checklist,
            ]
        )
        reseal = dict(
            source_date=source_day,
            target_date=day,
            current_source_receipts=source,
            checklist_path=str(checklist),
            original_controller_sha256=original_prepared.get("controller_sha256"),
            original_summary_sha256=original_prepared.get("summary_sha256"),
            policy_effect="unchanged",
        )
        if historical:
            reseal["historical_checklist"] = historical
        if operating:
            reseal["operating_checklist"] = operating
    # All native source receipts remain independently validated by the launcher.
    hashes = {str(path): _sha(path) for path in frozen}
    if reseal is not None and any(
        hashes[source[key + "_path"]] != source[key + "_sha256"]
        for key in ("controller", "summary")
    ):
        raise ValueError("intraday_postclose_generation_changed_during_prepare")
    if previous_stopped:
        if (
            Path("/proc", str(int(old_pid))).exists()
            or _sha(previous_consumed_path) != previous_consumed_sha
        ):
            raise ValueError("intraday_stopped_predecessor_changed")
    elif _identity(old_pid) != old_identity:
        raise ValueError("intraday_old_pid_changed_during_prepare")
    payload = {
        "schema": "intraday_policy_preserving_release_handoff_v1",
        "status": "prepared_verified",
        "target_date": day,
        "selected_release_commit": commit,
        "release_root": str(root),
        "previous_release_root": str(previous),
        "previous_release_commit": old_commit,
        "old_pid_identity": old_identity,
        "prepared_at": current.isoformat(),
        "first_launch_before": (current + timedelta(minutes=15)).isoformat(),
        "preopen_sha256": hashes[str(_preopen_path(day))],
        "frozen_files": hashes,
        "prepared_receipt_path": str(receipt_path),
        "prepared_receipt_sha256": _sha(receipt_path),
        "manifest_sha256": check.get("manifest_sha256"),
        "actual_pid_consumed": False,
        "policy_effect": "unchanged",
        "authority": confirm,
    }
    if reseal is not None:
        payload["postclose_source_reseal"] = reseal
    if previous_stopped:
        payload["previous_process_state"] = (
            "stopped_native_preopen_consumption_verified"
            if native_predecessor
            else "stopped_historical_consumption_verified"
        )
        payload["previous_consumption_sha256"] = previous_consumed_sha
        if native_predecessor:
            payload["native_predecessor_path"] = str(previous_consumed_path)
    path, _ = _paths(day, commit)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A receipt is immutable. Repeating preparation cannot silently replace it.
    content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    with path.open("x", encoding="utf-8") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    return verify(day, commit, now=current)


def verify(day, commit, *, now=None):
    return _verify_handoff(day, commit, now=now)


def _freeze_operating_checklist(day, commit, checklist):
    import stat

    with os.fdopen(
        os.open(checklist, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024 * 1024:
            raise ValueError("intraday_operating_checklist_invalid")
        content = stream.read(2 * 1024 * 1024 + 1)
        after = checklist.lstat()
        identity = lambda s: (
            s.st_dev,
            s.st_ino,
            s.st_size,
            s.st_mtime_ns,
            s.st_ctime_ns,
        )
        if len(content) != before.st_size or identity(before) != identity(after):
            raise ValueError("intraday_operating_checklist_changed_during_read")
    path = _paths(day, commit)[0].parent / (commit + ".operating-checklist.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return dict(
        path=str(path),
        sha256=hashlib.sha256(content).hexdigest(),
        source_path=str(checklist),
        target_date=day,
        role="launch_document_snapshot",
    )


def _verify_handoff(day, commit, *, now=None, historical_observer=False):
    """Keep launch verification strict; historical observation uses sealed sources."""
    findings = []
    payload = {}
    try:
        if historical_observer:
            current = (now or datetime.now(KST)).astimezone(KST)
            if (
                day > current.date().isoformat()
                or datetime.fromisoformat(day).date().isoformat() != day
            ):
                raise ValueError("intraday_observer_source_scope_mismatch")
        else:
            current = _today(day, now)
        # Read-only consumers may run from their own reviewed immutable
        # report release. Prepare/consume keep the selected-root requirement.
        root, selected = _selection(require_selected_cwd=False)
        path, consumed_path = _paths(day, commit)
        payload = _read(path)
        if (
            selected != commit
            or payload.get("schema") != "intraday_policy_preserving_release_handoff_v1"
            or payload.get("status") != "prepared_verified"
            or payload.get("authority") != CONFIRM
            or payload.get("target_date") != day
            or payload.get("selected_release_commit") != commit
            or payload.get("release_root") != str(root)
            or payload.get("actual_pid_consumed") is not False
        ):
            raise ValueError("intraday_handoff_identity_invalid")
        _preopen(day)
        native_predecessor = None
        if payload.get("previous_process_state"):
            if (
                payload["previous_process_state"]
                == "stopped_native_preopen_consumption_verified"
            ):
                native_predecessor = _native_predecessor(
                    day,
                    commit,
                    payload["previous_release_root"],
                    payload["previous_release_commit"],
                    payload["old_pid_identity"],
                    payload.get("native_predecessor_path"),
                    payload.get("previous_consumption_sha256"),
                )
            else:
                predecessor = _paths(day, payload["previous_release_commit"])[1]
                if (
                    payload["previous_process_state"]
                    != "stopped_historical_consumption_verified"
                    or _sha(predecessor) != payload.get("previous_consumption_sha256")
                    or _read(predecessor).get("pid_identity")
                    != payload.get("old_pid_identity")
                ):
                    raise ValueError("intraday_stopped_predecessor_changed")
        frozen = payload["frozen_files"]
        required = {
            str(bootstrap.env_path(day)),
            str(bootstrap.manifest_path(day)),
            str(_preopen_path(day)),
            str(DATA_DIR / "runtime/policy_bootstrap/prepared" / day / "latest.json"),
            payload["prepared_receipt_path"],
        }
        if native_predecessor:
            required.add(native_predecessor["path"])
        reseal = payload.get("postclose_source_reseal")
        if reseal is not None:
            prepared_receipt = _read(payload["prepared_receipt_path"])
            source = reseal["current_source_receipts"]
            if (
                reseal.get("target_date") != day
                or reseal.get("source_date") != prepared_receipt.get("source_date")
                or reseal.get("policy_effect") != "unchanged"
                or source.get("policy_receipts")
                != prepared_receipt.get("policy_receipts")
                or reseal.get("checklist_path")
                != str(
                    DATA_DIR.parent
                    / "docs/checklists"
                    / (day + "-stage2-todo-checklist.md")
                )
                or source.get("controller_path")
                != str(
                    DATA_DIR
                    / "report/postclose_done_controller"
                    / ("postclose_done_controller_" + reseal["source_date"] + ".json")
                )
                or source.get("summary_path")
                != str(
                    DATA_DIR
                    / "report/runtime_approval_summary"
                    / ("runtime_approval_summary_" + reseal["source_date"] + ".json")
                )
            ):
                raise ValueError("intraday_postclose_reseal_identity_invalid")
            if any(
                frozen.get(source[key + "_path"]) != source.get(key + "_sha256")
                for key in ("controller", "summary")
            ):
                raise ValueError("intraday_postclose_reseal_hash_invalid")
            snapshot = reseal.get("historical_checklist")
            if snapshot:
                expected_path = _paths(day, commit)[0].parent / (
                    commit + ".historical-checklist.md"
                )
                strict = _read(
                    _read(source["controller_path"])["verification_attempt_path"]
                )
                origin_commit = payload["previous_release_commit"]
                if snapshot.get("predecessor"):
                    inherited, predecessor = _historical_predecessor(
                        day, origin_commit, snapshot["sha256"]
                    )
                    if predecessor != snapshot["predecessor"]:
                        raise ValueError("intraday_historical_predecessor_changed")
                    origin_commit = inherited["git_commit"]
                if (
                    snapshot.get("path") != str(expected_path)
                    or snapshot.get("sha256")
                    != strict["generation_binding"]["checklist_sha256"]
                    or frozen.get(str(expected_path)) != snapshot["sha256"]
                    or snapshot.get("git_commit") != origin_commit
                    or snapshot.get("git_path")
                    != "docs/checklists/" + day + "-stage2-todo-checklist.md"
                ):
                    raise ValueError("intraday_historical_checklist_binding_invalid")
                required.add(str(expected_path))
            operating = reseal.get("operating_checklist")
            if operating is not None:
                operating_path = path.parent / (commit + ".operating-checklist.md")
                if (
                    operating.get("path") != str(operating_path)
                    or operating_path.is_symlink()
                    or operating.get("source_path") != reseal["checklist_path"]
                    or operating.get("target_date") != day
                    or operating.get("role") != "launch_document_snapshot"
                    or frozen.get(str(operating_path)) != operating.get("sha256")
                ):
                    raise ValueError("intraday_operating_checklist_binding_invalid")
                required.add(str(operating_path))
            else:
                required.add(reseal["checklist_path"])
            required.update([source["controller_path"], source["summary_path"]])
        historical_document = None
        if historical_observer:
            # Only an already-consumed historical handoff may disregard edits
            # to the operational checklist. Its sealed snapshot and all other
            # sources remain required. Public verify/consume/activation never
            # take this branch, and the observer binds the live PID separately.
            if (
                not reseal
                or not (
                    reseal.get("historical_checklist")
                    or reseal.get("operating_checklist")
                )
                or not consumed_path.exists()
            ):
                raise ValueError(
                    "intraday_observer_consumed_historical_handoff_required"
                )
            historical_document = (
                reseal["checklist_path"]
                if not reseal.get("operating_checklist")
                else None
            )
        if set(frozen) != required or any(
            _sha(name) != sha
            for name, sha in frozen.items()
            if name != historical_document
        ):
            raise ValueError("intraday_preserved_generation_changed")
        start = datetime.fromisoformat(payload["prepared_at"])
        deadline = datetime.fromisoformat(payload["first_launch_before"])
        if (
            start.tzinfo is None
            or deadline.tzinfo is None
            or start > current
            or deadline != start + timedelta(minutes=15)
        ):
            raise ValueError("intraday_handoff_clock_invalid")
        consumed = None
        if consumed_path.exists():
            consumed = _read(consumed_path)
            if (
                consumed.get("handoff_sha256") != _sha(path)
                or consumed.get("target_date") != day
                or consumed.get("selected_release_commit") != commit
                or consumed.get("actual_pid_consumed") is not True
                or consumed.get("release_root") != str(root)
            ):
                raise ValueError("intraday_consumption_invalid")
        elif current > deadline:
            review = _PREDECESSOR_REVIEW.get() or {}
            observation = review.get("prepared_observation") or {}
            if (
                review.get("day") != day
                or review.get("root") != root
                or review.get("commit") != commit
                or observation.get("original_first_launch_before")
                != payload["first_launch_before"]
                or observation.get("runtime_effect") is not False
                or observation.get("actual_pid_consumed") is not False
                or observation.get("allowed_runtime_apply") is not False
                or not observation.get("source_hashes")
                or any(
                    _sha(path) != sha
                    for path, sha in observation["source_hashes"].items()
                )
            ):
                raise ValueError("intraday_first_launch_window_expired")
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        findings.append(str(exc))
    return {
        "status": "pass" if not findings else "fail",
        "target_date": day,
        "findings": findings,
        "basis": "intraday_policy_preserving_handoff",
        "handoff": payload,
        "actual_pid_consumed": False,
    }


def verify_pid_consumption(day, *, pid, now=None):
    """Read-only proof of the selected release's exact live child consumption."""
    try:
        current = _today(day, now)
        root, commit = _selection(require_selected_cwd=False)
        identity = _identity(pid)
        if identity["cwd"] != str(root / "src"):
            raise ValueError("intraday_consumption_pid_root_invalid")
        path, consumed_path = _paths(day, commit)
        frozen = {
            _preopen_path(day): _sha(_preopen_path(day)),
            bootstrap.env_path(day): _sha(bootstrap.env_path(day)),
            bootstrap.manifest_path(day): _sha(bootstrap.manifest_path(day)),
        }
        native = not path.exists()
        if native:
            if _preopen(day).get("selected_release_commit") != commit:
                raise ValueError("intraday_consumption_handoff_missing")
        else:
            frozen.update({path: _sha(path), consumed_path: _sha(consumed_path)})
            check = _verify_consumed_handoff(day, commit, now=current)
            if check["status"] != "pass":
                return check
            consumed = _read(consumed_path)
            if (
                consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
                or consumed.get("status") != "pass"
                or consumed.get("actual_pid_consumed") is not True
                or consumed.get("target_date") != day
                or consumed.get("selected_release_commit") != commit
                or consumed.get("release_root") != str(root)
                or consumed.get("handoff_sha256") != frozen[path]
                or consumed.get("pid_identity") != identity
            ):
                raise ValueError("intraday_consumption_current_pid_not_bound")
        checked = _checked_bootstrap(day, pid)
        manifest_sha = checked.get("manifest_sha256")
        if not manifest_sha or (
            not native and consumed.get("manifest_sha256") != manifest_sha
        ):
            raise ValueError("intraday_consumption_manifest_mismatch")
        if (
            any(_sha(p) != sha for p, sha in frozen.items())
            or (native and path.exists())
            or _identity(pid) != identity
            or _selection(require_selected_cwd=False) != (root, commit)
        ):
            raise ValueError("intraday_consumption_generation_changed")
        return dict(
            schema="intraday_pid_consumption_verification_v1",
            status="pass",
            findings=[],
            target_date=day,
            selected_release_commit=commit,
            release_root=str(root),
            basis="native_preopen" if native else "intraday_policy_preserving_handoff",
            pid_identity=identity,
            actual_pid_consumed=True,
            manifest_sha256=manifest_sha,
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        return dict(
            status="fail",
            findings=[str(exc)],
            target_date=day,
            actual_pid_consumed=False,
        )


def _verify_consumed_handoff(day, commit, *, now=None):
    """Existing live policy custody; never a launch/consume/activation gate."""
    try:
        root, selected = _selection(require_selected_cwd=False)
        path, consumed_path = _paths(day, commit)
        handoff_sha, consumed_sha = _sha(path), _sha(consumed_path)
        consumed = _read(consumed_path)
        identity = consumed.get("pid_identity") or {}
        if (
            selected != commit
            or consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
            or consumed.get("status") != "pass"
            or consumed.get("actual_pid_consumed") is not True
            or consumed.get("target_date") != day
            or consumed.get("selected_release_commit") != commit
            or consumed.get("release_root") != str(root)
            or consumed.get("handoff_sha256") != handoff_sha
            or identity.get("cwd") != str(root / "src")
            or _identity(identity["pid"]) != identity
        ):
            raise ValueError("intraday_consumed_live_identity_invalid")
        historical = bool(
            (_read(path).get("postclose_source_reseal") or {}).get(
                "historical_checklist"
            )
        )
        result = _verify_handoff(day, commit, now=now, historical_observer=historical)
        if consumed.get("manifest_sha256") != result.get("handoff", {}).get(
            "manifest_sha256"
        ):
            raise ValueError("intraday_consumed_manifest_changed")
        if (
            _sha(path) != handoff_sha
            or _sha(consumed_path) != consumed_sha
            or _identity(identity["pid"]) != identity
            or _selection(require_selected_cwd=False) != (root, commit)
        ):
            raise ValueError("intraday_consumed_generation_changed")
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return dict(
            status="fail",
            findings=[str(exc)],
            target_date=day,
            actual_pid_consumed=False,
        )


@contextmanager
def predecessor_review(day, *, pid):
    """Read-only exact live predecessor scope for a clean candidate validator."""
    from src.engine.infrastructure import runtime_release_router as router

    root, commit = _selection(require_selected_cwd=False)
    candidate = Path(__file__).resolve().parents[3]
    candidate_commit = router.git(candidate, "rev-parse", "HEAD")
    router.validate_release(
        DATA_DIR.parent,
        dict(
            schema="runtime_release_selection_v1",
            workspace=str(DATA_DIR.parent),
            release_root=str(candidate),
            git_commit=candidate_commit,
        ),
    )
    if root == candidate:
        raise ValueError("intraday_predecessor_candidate_already_selected")
    identity = _identity(pid)
    review = dict(
        day=day,
        root=root,
        commit=commit,
        code_root=candidate,
        code_commit=candidate_commit,
        identity=identity,
    )
    token = _PREDECESSOR_REVIEW.set(review)
    try:
        yield review
        if _identity(pid) != identity or _selection(require_selected_cwd=False) != (
            root,
            commit,
        ):
            raise ValueError("intraday_predecessor_review_generation_changed")
    finally:
        _PREDECESSOR_REVIEW.reset(token)


def verify_predecessor_consumption(day, *, pid):
    """Fully revalidate the live predecessor without selecting or consuming code."""
    with predecessor_review(day, pid=pid) as review:
        result = verify_pid_consumption(day, pid=pid)
        if result.get("status") == "pass":
            result.update(
                verification_code_root=str(review["code_root"]),
                verification_code_commit=review["code_commit"],
                candidate_pid_consumed=False,
                runtime_effect=False,
            )
        return result


def consume(day, *, pid, now=None):
    if (_PREDECESSOR_REVIEW.get() or {}).get("prepared_observation") is not None:
        raise ValueError("intraday_preparation_review_not_launch_authority")
    _, commit = _selection()
    path, consumed_path = _paths(day, commit)
    if not path.exists():
        return {
            "status": "pass",
            "basis": "native_preopen",
            "actual_pid_consumed": False,
        }
    check = verify(day, commit, now=now)
    if check["status"] != "pass":
        return check
    identity = _identity(pid)
    if identity["cwd"] != str(Path(check["handoff"]["release_root"]) / "src"):
        raise ValueError("intraday_new_pid_root_invalid")
    verified = _checked_bootstrap(day, pid)
    if _identity(pid) != identity:
        raise ValueError("intraday_new_pid_changed_during_verify")
    payload = {
        "schema": "intraday_policy_preserving_consumption_v1",
        "status": "pass",
        "target_date": day,
        "selected_release_commit": commit,
        "release_root": check["handoff"]["release_root"],
        "handoff_sha256": _sha(path),
        "pid_identity": identity,
        "actual_pid_consumed": True,
        "manifest_sha256": verified.get("manifest_sha256"),
        "verified_at": (now or datetime.now(KST)).isoformat(),
    }
    bootstrap._publish(
        consumed_path, json.dumps(payload, sort_keys=True, indent=2) + "\n"
    )
    return payload


def historical_checklist_for_observer(project, source_date, *, now=None):
    """Resolve a consumed, same-day handoff for historical generation observers.

    This receipt cannot publish a new finalization or whole-chain completion.
    The caller must still check every other source and the original DONE hashes.
    """
    try:
        return _historical_checklist_for_observer(project, source_date, now=now)
    except (OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        raise ValueError(
            "intraday_observer_receipt_unavailable:" + type(exc).__name__
        ) from exc


def _historical_checklist_for_observer(project, source_date, *, now=None):
    current = now or datetime.now(KST)
    day = current.astimezone(KST).date().isoformat()
    if (Path(project) / "data").resolve() != DATA_DIR.resolve():
        raise ValueError("intraday_observer_data_root_mismatch")
    root, commit = _selection(require_selected_cwd=False)
    closed = None
    if not _paths(day, commit)[0].exists():
        closed = closed_consumption_observation(now=current)
        day = closed["target_date"]
    handoff_path, consumed_path = _paths(day, commit)
    handoff_sha = _sha(handoff_path)
    check = _verify_handoff(day, commit, now=current, historical_observer=True)
    if check["status"] != "pass":
        raise ValueError(
            "intraday_observer_handoff_invalid:" + ",".join(check["findings"])
        )
    preserved = check["handoff"]
    reseal = preserved.get("postclose_source_reseal") or {}
    historical = (
        reseal.get("historical_checklist") or reseal.get("operating_checklist") or {}
    )
    if (
        reseal.get("source_date") != source_date
        or reseal.get("target_date") != day
        or not historical
        or reseal.get("policy_effect") != "unchanged"
    ):
        raise ValueError("intraday_observer_source_scope_mismatch")
    # A launch snapshot can already be the original strict-bound document.
    # It needs no second historical copy, but must match that exact generation.
    if not reseal.get("historical_checklist"):
        controller = _read(reseal["current_source_receipts"]["controller_path"])
        strict = _read(controller["verification_attempt_path"])
        if (
            historical.get("sha256") != strict["generation_binding"]["checklist_sha256"]
            or _sha(historical["path"]) != historical["sha256"]
        ):
            raise ValueError("intraday_observer_strict_checklist_binding_invalid")
    consumed_sha = _sha(consumed_path)
    consumed = _read(consumed_path)
    identity = consumed.get("pid_identity") or {}
    if (
        consumed.get("schema") != "intraday_policy_preserving_consumption_v1"
        or consumed.get("status") != "pass"
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("handoff_sha256") != handoff_sha
        or consumed.get("target_date") != day
        or consumed.get("selected_release_commit") != commit
        or consumed.get("release_root") != str(root)
        or identity.get("cwd") != str(root / "src")
    ):
        raise ValueError("intraday_observer_current_pid_not_bound")
    try:
        live = _identity(identity["pid"])
    except FileNotFoundError:
        closed = closed_consumption_observation(day, now=current)
        live = closed["pid_identity"]
    if live != identity:
        raise ValueError("intraday_observer_current_pid_not_bound")
    token = _OBSERVER_CUSTODY.set(closed or (day, commit))
    try:
        bootstrap_check = _checked_bootstrap(day, None if closed else identity["pid"])
    finally:
        _OBSERVER_CUSTODY.reset(token)
    if (
        consumed.get("manifest_sha256") != bootstrap_check.get("manifest_sha256")
        or (
            closed_consumption_observation(day, now=current) != closed
            if closed
            else _identity(identity["pid"]) != identity
        )
        or _sha(handoff_path) != handoff_sha
        or _sha(consumed_path) != consumed_sha
        or _selection(require_selected_cwd=False) != (root, commit)
    ):
        raise ValueError("intraday_observer_pid_generation_changed")
    return dict(
        schema="intraday_historical_checklist_observer_v1",
        basis="consumed_intraday_preserved_historical_generation",
        source_date=source_date,
        target_date=day,
        release_commit=commit,
        path=historical["path"],
        sha256=historical["sha256"],
        handoff_path=str(handoff_path),
        handoff_sha256=handoff_sha,
        consumed_path=str(consumed_path),
        consumed_sha256=consumed_sha,
        delay_observer_validation=bootstrap_check.get("delay_observer_validation"),
        pid_identity=identity,
        pid_state="closed" if closed else "live",
        closed_consumption=closed,
        runtime_effect=False,
        new_finalization_claimed=False,
    )


def activate_main_v2(day, *, pid, confirm, now=None):
    """Apply an approved Main policy only after the reviewed code PID binds."""
    current = _today(day, now)
    if confirm != "APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION":
        raise ValueError("intraday_main_policy_explicit_authority_required")
    root, commit = _selection()
    identity = _identity(pid)
    if identity["cwd"] != str(root / "src"):
        raise ValueError("intraday_main_policy_pid_release_mismatch")
    check = verify(day, commit, now=current)
    _, consumed_path = _paths(day, commit)
    consumed = _read(consumed_path)
    if (
        check["status"] != "pass"
        or consumed.get("status") != "pass"
        or consumed.get("pid_identity") != identity
        or consumed.get("actual_pid_consumed") is not True
        or consumed.get("selected_release_commit") != commit
    ):
        raise ValueError("intraday_main_policy_code_consumption_missing")
    verified = _checked_bootstrap(day, pid)
    evidence = {
        "schema": "intraday_main_policy_code_pid_v1",
        "target_date": day,
        "release_commit": commit,
        "pid_identity": identity,
        "consumed_path": str(consumed_path),
        "consumed_sha256": _sha(consumed_path),
        "manifest_sha256": verified["manifest_sha256"],
        "verified_at": current.isoformat(),
        "custody_and_order_paths": "existing_native_main_guards_unchanged",
    }
    if _identity(pid) != identity:
        raise ValueError("intraday_main_policy_pid_changed")
    from src.engine.scalping.continuous_reversal_policy_v2 import activate

    candidate = (
        DATA_DIR / "runtime/mechanistic_entry_policy/candidates" / f"policy_{day}.json"
    )
    if candidate.is_file() and json.loads(candidate.read_text())["continuous_reversal"][
        "schema"
    ] in {"continuous_reversal_policy_v5", "continuous_reversal_policy_v6"}:
        # v5 is issued as next_session and consumed by the PREOPEN path. Do not
        # reinterpret it with the older intraday activation contract.
        raise ValueError("operating_v5_requires_next_session_activation")
    if (
        candidate.is_file()
        and json.loads(candidate.read_text())["continuous_reversal"]["schema"]
        == "continuous_reversal_policy_v3"
    ):
        from src.engine.scalping.continuous_reversal_policy_v3 import activate
    if (
        candidate.is_file()
        and json.loads(candidate.read_text())["continuous_reversal"]["schema"]
        == "continuous_reversal_policy_v4"
    ):
        from src.engine.scalping.continuous_reversal_policy_v4 import activate
    receipt = activate(DATA_DIR, day, now=current, intraday_evidence=evidence)
    return dict(status="pass", activation=receipt, actual_policy_pid_consumption=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--verify-predecessor", action="store_true")
    group.add_argument("--consume", action="store_true")
    group.add_argument("--activate-main-v2", action="store_true")
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--old-pid", type=int)
    parser.add_argument(
        "--validation-session",
        help="internal transition digest scope; no verdict reuse",
    )
    parser.add_argument("--pid", type=int)
    parser.add_argument("--previous-root")
    parser.add_argument("--confirm")
    parser.add_argument("--reseal-postclose-source", action="store_true")
    parser.add_argument("--previous-stopped", action="store_true")
    parser.add_argument("--freeze-operating-checklist", action="store_true")
    args = parser.parse_args(argv)
    if args.validation_session and args.activate_main_v2:
        parser.error("validation session cannot wrap policy activation")
    from src.engine.infrastructure.validation_digest_session import (
        transition_session,
        ValidationDeferred,
    )

    session = None
    try:
        with transition_session(
            DATA_DIR, args.target_date, args.validation_session, args.pid
        ) as session:
            if args.prepare:
                result = prepare(
                    args.target_date,
                    old_pid=args.old_pid,
                    previous_root=args.previous_root,
                    confirm=args.confirm,
                    reseal_postclose_source=args.reseal_postclose_source,
                    previous_stopped=args.previous_stopped,
                    freeze_operating_checklist=args.freeze_operating_checklist,
                )
            elif args.activate_main_v2:
                result = activate_main_v2(
                    args.target_date, pid=args.pid, confirm=args.confirm
                )
            elif args.consume:
                result = consume(args.target_date, pid=args.pid)
            elif args.verify_predecessor:
                result = verify_predecessor_consumption(args.target_date, pid=args.pid)
            elif args.pid is not None:
                result = verify_pid_consumption(args.target_date, pid=args.pid)
            else:
                result = verify(
                    args.target_date, _selection(require_selected_cwd=False)[1]
                )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
        ValidationDeferred,
    ) as exc:
        result = {"status": "fail", "findings": [str(exc)]}
    if session is not None:
        result["validation_io"] = session.stats
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    # Nested policy readers import the canonical module. Running prepare on a
    # second __main__ copy would give them different ContextVar instances.
    from src.engine.automation.intraday_release_handoff import main as canonical_main

    raise SystemExit(canonical_main())
