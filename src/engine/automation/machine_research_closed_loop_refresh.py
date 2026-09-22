"""Resume the existing nightly widget/episode research publication fixed point.

Uses completed studies only. It never regenerates grids, subscribes symbols,
changes an allocator or submits orders. Future study windows remain waiting.
"""

from __future__ import annotations
import argparse
import os
from datetime import date, datetime, time
from pathlib import Path
import time as clock
from zoneinfo import ZoneInfo
from src.engine.monitoring import research_closed_loop as loop
from src.utils.constants import DATA_DIR

REPORT_TYPE = "machine_research_closed_loop"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
EFFECTIVE_DATE = "2026-09-17"


def dependency_catalog(directory):
    root = Path(directory)
    return sorted(
        str(path.resolve())
        for pattern in (
            "widget_outcomes_*.json",
            "candidates/*.json",
            "joint_bundles/*.json",
        )
        for path in root.glob(pattern)
    )


def code_contract():
    engine = Path(__file__).resolve().parents[1]
    paths = [Path(__file__), *engine.joinpath("monitoring").glob("research_*.py")]
    paths += [
        engine.joinpath("monitoring", name)
        for name in (
            "episode_prospective_research.py",
            "low_price_two_leg_entry_spot_research.py",
            "policy_research_economics.py",
            "widget_comparison_cost.py",
            "widget_symbol_runtime_policy.py",
            "widget_symbol_signal_policy_research.py",
            "low_price_two_leg_expanded_candidate_research.py",
            "low_price_two_leg_tuning.py",
        )
    ]
    paths.append(engine / "automation" / "low_price_two_leg_auto_expansion_policy.py")
    paths += [
        engine.parent / "trading" / name
        for name in (
            "widget_auto_trade/policy.py",
            "widget_auto_trade/engine.py",
            "low_price_two_leg/auto_expansion_service.py",
            "low_price_two_leg/machine.py",
            "low_price_two_leg/profiles.py",
            "order/regular_two_leg_machine.py",
            "order/symbol_owner_policy_auto_apply.py",
            "order/symbol_owner_policy_apply.py",
        )
    ]

    return {
        str(path.relative_to(engine.parent)): __import__("hashlib")
        .sha256(path.read_bytes())
        .hexdigest()
        for path in sorted(paths)
        if path.name != "research_scale_benchmark.py"
    }


def report_path(report_root, day):
    return Path(report_root) / REPORT_TYPE / f"{REPORT_TYPE}_{day}.json"


def _read_report_dependency(path, *, source_date=None):
    path.stat()  # Preserve missing dependency semantics of the stable reader.
    if path.name == "widget_signal_auto_trade_state.json":
        if source_date is None:
            raise ValueError("native_widget_dependency_date_required")
        from src.engine.monitoring.research_version_outcomes import native_widget_order_projection
        return native_widget_order_projection(
            loop.read_object(path, limit=16 * 1024 * 1024), source_date=source_date)
    if path.parent.name in {
        "widget_symbol_signal_policy_research",
        "low_price_two_leg_expanded_candidate_research",
        "low_price_two_leg_tuning",
    }:
        from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import (
            read_report,
        )

        return read_report(path)
    return loop.read_object(path, limit=32 * 1024 * 1024)


def read_studies(day, *, report_root=DATA_DIR / "report", families=("widget", "episode")):
    paths = {
        "widget": Path(report_root)
        / "widget_symbol_signal_policy_research"
        / f"widget_symbol_signal_policy_research_{day}.json",
        "episode": Path(report_root)
        / "low_price_two_leg_expanded_candidate_research"
        / f"low_price_two_leg_expanded_candidate_research_{day}.json",
    }
    paths = {family: path.resolve() for family, path in paths.items() if family in families}
    studies, missing = {}, []
    for family, path in paths.items():
        try:
            value = _read_report_dependency(path)
            if (
                str(value.get("end_date") or value.get("target_date"))
                != day.isoformat()
                or value.get("closed_loop_contract") != loop.SCHEMA
                or any(value.get(k) is not v for k, v in loop.AUTHORITY.items())
            ):
                raise ValueError("exact_study_contract_invalid")
            if family == "widget":
                from src.engine.monitoring.widget_symbol_signal_policy_research import assert_completed_source_waiting
                assert_completed_source_waiting(path, day, value)
            studies[family] = value
        except (FileNotFoundError, ValueError):
            missing.append(family)
    return studies, paths, missing


def lifecycle_counts(studies):
    counts, mapping = {}, []
    for family, report in studies.items():
        results = report.get("symbols" if family == "widget" else "profiles") or {}
        dispositions = {}
        for native, result in results.items():
            revision = result.get("candidate_revision") or {}
            decision = str(result.get("decision") or "")
            if revision:
                window = (result.get("prospective_window") or {}).get("status")
                disposition = (
                    "research_blocked"
                    if window == "source_gap"
                    else "pending_prospective_validation"
                    if window == "waiting"
                    else "executable_validated"
                    if (result.get("execution_feasibility") or {}).get("status")
                    == "pass"
                    else "proxy_only"
                )
            else:
                disposition = (
                    "research_blocked" if "quarantin" in decision else "proxy_only"
                )
            dispositions[disposition] = dispositions.get(disposition, 0) + 1
            mapping.append(
                dict(
                    family=family,
                    native_research_id=native,
                    parent_revision_sha256=revision.get("revision_sha256"),
                    disposition=disposition,
                    decision=decision,
                    selection_disposition="allocation_blocked"
                    if report.get("joint_allocation_gate", {}).get("status") != "pass"
                    else "selected"
                    if "holdout_pass" in decision
                    else "hold_sample",
                )
            )
        counts[family] = dict(
            input_count=len(results),
            dispositions=dispositions,
            unaccounted_count=len(results) - sum(dispositions.values()),
        )
    return counts, mapping


def _publication_contract(day):
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    publication = date.fromisoformat(os.environ.get("POSTCLOSE_POLICY_PUBLICATION_DATE") or str(day))
    if not day <= publication <= datetime.now(ZoneInfo("Asia/Seoul")).date():
        raise ValueError("research_publication_date_invalid")
    effective = _next_krx_trading_day(publication.isoformat())
    requested = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE")
    if requested and requested != effective:
        raise ValueError("research_effective_date_mismatch")
    return dict(source_date=str(day), publication_date=str(publication), effective_date=effective)


def _refresh(
    day,
    *,
    directory=loop.DIRECTORY,
    report_root=DATA_DIR / "report",
    publish=True,
    collect_costs=False,
    source_wait_seconds=0,
    allocation_only=False,
):
    started = clock.monotonic()
    publication_contract = _publication_contract(day)
    destination = report_path(report_root, day)
    with (
        loop.research_scope(directory),
        loop.writer_lock(Path(directory) / "refresh", blocking=False),
    ):
        studies, paths, missing = read_studies(day, report_root=report_root)
        if missing:
            body = dict(
                schema=loop.SCHEMA,
                target_date=day.isoformat(),
                status="waiting",
                semantic_disposition="required_completed_study_missing",
                missing_families=missing,
                **loop.AUTHORITY,
            )
            loop.atomic_write(destination, body)
            return body
        from src.engine.monitoring.research_allocation_snapshot import write_snapshot

        # Preserve an already frozen exact-date snapshot; do not replace a
        # verified native generation with missing/current next-day balances.
        snapshot = loop.load_allocator(day, directory=directory)
        if snapshot is None or snapshot.get("source_quality_status") != "PASS":
            snapshot = write_snapshot(day, directory=directory, report_root=report_root)
        try:
            previous = loop.read_object(destination, limit=16 * 1024 * 1024)
        except FileNotFoundError:
            previous = {}
        if (
            previous.get("allocation_only", False) is allocation_only
            and previous.get("exact_cost_recovery_requested") is collect_costs
            and validate_current_receipt(
                previous, day, publication_contract=publication_contract
            )
            and previous.get("publication_requested") is publish
        ):
            return previous
        from src.engine.monitoring.research_version_outcomes import (
            collect_widget_outcomes,
            outcome_feedback,
            episode_feedback,
        )

        loader = None
        if collect_costs:
            # Existing adapter/rate limiter, no auth mutation or publisher call.
            from src.utils import kiwoom_utils
            from src.engine.monitoring.low_price_two_leg_tuning import (
                load_realized_pnl_ka10073,
            )

            def loader(native_day, symbol):
                token = kiwoom_utils.get_cached_kiwoom_token()
                if not token:
                    raise ValueError("shared_native_token_missing")
                return load_realized_pnl_ka10073(token, native_day, symbol)

        cost_started = clock.monotonic()
        outcomes = collect_widget_outcomes(
            day,
            state_path=DATA_DIR / "runtime" / "widget_signal_auto_trade_state.json",
            directory=directory,
            loader=loader,
            decision_path=Path(report_root)
            / "widget_signal_auto_trade_events"
            / f"research_decisions_{day}.json",
        )
        cost_seconds = clock.monotonic() - cost_started
        feedback = outcome_feedback(day, directory=directory)
        studies["widget"]["policy_version_feedback"] = feedback
        studies["episode"]["policy_version_feedback"] = episode_feedback(
            day, report_root=report_root
        )
        for family, report in studies.items():
            loop.write_joint_inputs(report, family=family, directory=directory)
        freeze_issue = None
        try:
            loop.freeze_joint_bundle(
                [loop.joint_inputs(report, family=family) for family, report in studies.items()],
                directory=directory,
            )
        except ValueError as exc:
            freeze_issue = str(exc)
        for family, report in studies.items():
            report["joint_bundle_freeze_issue"] = freeze_issue
            # Reconstruct the same canonical gate as the policy consumers.
            # Do not invent a different gate that cannot be hash-validated.
            report["joint_allocation_gate"] = loop.combined_joint_gate(
                report, family=family, source_date=day, directory=directory
            )
        code_sources = code_contract()
        code = loop.digest(code_sources)
        state_path = DATA_DIR / "runtime" / "widget_signal_auto_trade_state.json"
        try:
            state_hash = loop.digest(
                _read_report_dependency(state_path, source_date=day)
            )
        except FileNotFoundError:
            state_hash = None
        if state_hash != outcomes.get("native_state_order_projection_sha256"):
            raise ValueError("native_widget_orders_changed_during_refresh")
        inputs = loop.digest(
            dict(
                studies=studies,
                allocator=snapshot,
                code=code,
                native_widget_state_sha256=state_hash,
                exact_cost_recovery_requested=collect_costs,
                allocation_only=allocation_only,
                publication_contract=publication_contract,
            )
        )
        try:
            previous = loop.read_object(destination, limit=16 * 1024 * 1024)
        except FileNotFoundError:
            previous = {}
        # A cached complete receipt still verifies its publication targets.
        if (
            previous.get("status") == "complete"
            and previous.get("dependency_sha256") == inputs
            and validate_current_receipt(
                previous, day, publication_contract=publication_contract
            )
        ):
            if publish:
                for family, publication in previous["publications"].items():
                    folder = Path(publication["directory"])
                    manifest = loop.read_object(
                        folder
                        / f"research_publication_{publication['effective_date']}.json"
                    )
                    if (
                        manifest["generation_sha256"]
                        != publication["generation_sha256"]
                    ):
                        raise ValueError("closed_loop_publication_changed")
                    for name in manifest["files"]:
                        loop.verify_publication(
                            folder,
                            effective_date=date.fromisoformat(
                                publication["effective_date"]
                            ),
                            name=name,
                            value=loop.read_object(
                                folder / name, limit=32 * 1024 * 1024
                            ),
                        )
            return previous
        loop.atomic_write(
            destination,
            dict(
                schema=loop.SCHEMA,
                target_date=day.isoformat(),
                status="running",
                dependency_sha256=inputs,
                **loop.AUTHORITY,
            ),
        )
        from src.engine.monitoring import widget_symbol_signal_policy_research as widget
        from src.engine.monitoring import (
            low_price_two_leg_expanded_candidate_research as episode,
        )
        from src.engine.monitoring import widget_symbol_runtime_policy as widget_policy
        from src.engine.automation import (
            low_price_two_leg_auto_expansion_policy as episode_policy,
        )

        if not allocation_only:
            widget.write_report(studies["widget"], output_dir=paths["widget"].parent)
            episode.write_report(studies["episode"], paths["episode"].parent)
        publications = {}
        if publish and not allocation_only:
            core, _, _ = widget_policy.write_outputs(
                studies["widget"],
                evidence_report_path=paths["widget"],
                policy_dir=Path(directory).parent / "widget_symbol_runtime_policy",
                apply_report_dir=Path(report_root)
                / "widget_symbol_runtime_policy_apply",
            )
            policy = episode_policy.build_policy(
                publication_date=date.fromisoformat(os.environ["POSTCLOSE_POLICY_PUBLICATION_DATE"]) if os.environ.get("POSTCLOSE_POLICY_PUBLICATION_DATE") else None,
                source_date=day,
                report_dir=paths["episode"].parent,
                policy_dir=Path(directory).parent / "low_price_two_leg_auto_expansion",
            )
            effective = date.fromisoformat(policy["effective_date"])
            child = episode_policy.policy_path(
                effective,
                policy_dir=Path(directory).parent / "low_price_two_leg_auto_expansion",
            )
            episode_policy.preserve_source_snapshot(policy, policy_dir=child.parent)
            loop.publication_transaction(
                child.parent,
                effective_date=effective,
                files={child.name: policy},
                expected_generation=loop.future_publication_parent(
                    child.parent, effective
                ),
            )
            episode_policy.load_policy(effective, policy_dir=child.parent)
            for family, path in [("widget", core), ("episode", child)]:
                payload = loop.read_object(path, limit=32 * 1024 * 1024)
                manifest = loop.read_object(
                    path.parent
                    / f"research_publication_{payload['effective_date']}.json"
                )
                publications[family] = dict(
                    directory=str(path.parent.resolve()),
                    effective_date=payload["effective_date"],
                    generation_sha256=manifest["generation_sha256"],
                    profile_count=len(
                        payload.get("symbols", payload.get("profiles", {}))
                    ),
                )
        counts, mapping = lifecycle_counts(studies)
        dependency_paths = set(paths.values())
        dependency_paths.add(state_path)
        dependency_paths.add(
            Path(report_root)
            / "low_price_two_leg_tuning"
            / f"low_price_two_leg_tuning_{day}.json"
        )
        dependency_paths.update(Path(path) for path in dependency_catalog(directory))
        for report in studies.values():
            dependency_paths.update(Path(path) for path in
                report.get("joint_allocation_gate", {}).get("capital_source_dependencies", []))
        dependency_paths.update(
            Path(directory) / name
            for name in (
                f"allocator_{day}.json",
                f"opening_capacity/capacity_source_{day}.json",
                f"capacity_source_{day}.json",
                f"native_capacity/{day}/native_cash.json",
                f"native_capacity/{day}/native_inventory.json",
                f"widget_outcomes_{day}.json",
            )
        )
        for name in (
            "owner_policy_path",
            "native_acquisition_path",
            "native_cash_path",
            "native_inventory_path",
        ):
            if snapshot.get(name):
                dependency_paths.add(Path(snapshot[name]))
        stage_path = (snapshot.get("constraints") or {}).get("same_stage_source_path")
        if stage_path:
            dependency_paths.add(Path(stage_path))
        dependency_sources = {}
        for path in sorted(dependency_paths):
            try:
                dependency_sources[str(path.resolve())] = loop.digest(
                    _read_report_dependency(path, source_date=day)
                )
            except FileNotFoundError:
                dependency_sources[str(path.resolve())] = None
        if dependency_sources.get(str(state_path.resolve())) != state_hash:
            raise ValueError("native_widget_orders_changed_during_refresh")
        from src.engine.monitoring.research_cache_storage import capacity_receipt
        body = dict(
            storage_capacity=capacity_receipt(directory, day, report_root),
            schema=loop.SCHEMA,
            target_date=day.isoformat(),
            status="complete",
            dependency_sha256=inputs,
            code_sources=code_sources,
            research_directory=str(Path(directory).resolve()),
            dependency_catalog=dependency_catalog(directory),
            source_generations={
                path: generation
                for report in studies.values()
                for result in (
                    report.get("symbols") or report.get("profiles") or {}
                ).values()
                for path, generation in (result.get("execution_feasibility") or {})
                .get("source_generations", {})
                .items()
            },
            exact_cost_recovery_requested=collect_costs,
            publication_requested=publish,
            allocation_only=allocation_only,
            publication_contract=publication_contract,
            dependency_sources=dependency_sources,
            execution_mode="completed_study_fixed_point_no_grid_replay",
            compute_replayed=False,
            phase_metrics=dict(
                source_wait_seconds=source_wait_seconds,
                compute_seconds=clock.monotonic() - started - cost_seconds,
                outcome_recovery_seconds=cost_seconds,
            ),
            lifecycle_counts=counts,
            parent_child_mapping=mapping,
            publications=publications,
            joint_allocation_gate=studies["widget"]["joint_allocation_gate"],
            semantic_disposition="prospective_or_allocation_evidence_pending"
            if any(item["selection_disposition"] != "selected" for item in mapping)
            else "selected_next_date",
            widget_actual_outcome_status=outcomes["status"],
            policy_version_feedback={
                "widget": feedback,
                "episode": episode_feedback(day, report_root=report_root),
            },
            consumer_acceptance="waiting_exact_next_date_natural_PREOPEN",
            economic_acceptance="waiting_mature_exact_cost_outcomes",
            **loop.AUTHORITY,
        )
        body["receipt_sha256"] = loop.digest(body)
        loop.atomic_write(destination, body)
        return body


def refresh(
    day, *, directory=loop.DIRECTORY, report_root=DATA_DIR / "report", **kwargs
):
    try:
        return _refresh(day, directory=directory, report_root=report_root, **kwargs)
    except BlockingIOError:
        return dict(status="waiting", semantic_disposition="existing_writer_running")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        loop.atomic_write(
            report_path(report_root, day),
            dict(
                schema=loop.SCHEMA,
                target_date=str(day),
                status="failed",
                reason=type(exc).__name__,
                failure=str(exc)[:512],
                **loop.AUTHORITY,
            ),
        )
        raise


def validate_current_receipt(value, day, *, publication_contract=None):
    if publication_contract is not None and value.get("publication_contract") != publication_contract:
        return False
    if not validate_receipt(value, day):
        return False
    try:
        if not value.get("dependency_sources"):
            return False
        if value.get("code_sources") != code_contract():
            return False
        if value.get("dependency_catalog") != dependency_catalog(
            value["research_directory"]
        ):
            return False
        from src.engine.monitoring.research_source_facts import (
            generation,
            source_integrity,
        )

        for name, expected in value.get("source_generations", {}).items():
            source_integrity(name)
            if list(generation(Path(name).lstat())) != list(expected):
                return False
        for name, expected in value["dependency_sources"].items():
            path = Path(name)
            if expected is None:
                if os.path.lexists(path):
                    return False
                continue
            if loop.digest(_read_report_dependency(path, source_date=date.fromisoformat(str(day)))) != expected:
                return False
        for publication in value["publications"].values():
            if publication["effective_date"] != (value.get("publication_contract") or {}).get("effective_date"):
                return False
            folder = Path(publication["directory"])
            effective = date.fromisoformat(publication["effective_date"])
            manifest = loop.read_object(
                folder / f"research_publication_{effective}.json"
            )
            if manifest["generation_sha256"] != publication["generation_sha256"]:
                return False
            for name in manifest["files"]:
                loop.verify_publication(
                    folder,
                    effective_date=effective,
                    name=name,
                    value=loop.read_object(folder / name, limit=32 * 1024 * 1024),
                )
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def validate_receipt(value, day):
    body = {k: v for k, v in value.items() if k != "receipt_sha256"}
    return (
        value.get("schema") == loop.SCHEMA
        and value.get("target_date") == str(day)
        and value.get("status") == "complete"
        and value.get("receipt_sha256") == loop.digest(body)
        and (bool(value.get("publications")) or value.get("allocation_only") is True)
        and all(
            item.get("unaccounted_count") == 0
            for item in value.get("lifecycle_counts", {}).values()
        )
    )


def refresh_family(day, family, *, directory=loop.DIRECTORY, report_root=DATA_DIR / 'report'):
    """Publish one family's completed study; allocation retains its own writer."""
    studies, paths, missing = read_studies(day, report_root=report_root, families=(family,))
    destination = Path(report_root) / REPORT_TYPE / f'{family}_policy_refresh_{day}.json'
    if missing:
        return dict(status='waiting', missing_families=missing)
    publication = _publication_contract(day)
    with loop.research_scope(directory), loop.writer_lock(Path(directory) / 'refresh', blocking=False):
        report = studies[family]
        from src.engine.monitoring.research_version_outcomes import outcome_feedback, episode_feedback
        report['policy_version_feedback'] = outcome_feedback(day, directory=directory) if family == 'widget' else episode_feedback(day, report_root=report_root)
        loop.write_joint_inputs(report, family=family, directory=directory)
        report['joint_allocation_gate'] = loop.combined_joint_gate(report, family=family, source_date=day, directory=directory)
        if family == 'widget':
            from src.engine.monitoring import widget_symbol_signal_policy_research as study
            from src.engine.monitoring import widget_symbol_runtime_policy as policy
            study.write_report(report, output_dir=paths[family].parent)
            child, _, _ = policy.write_outputs(report, evidence_report_path=paths[family],
                policy_dir=Path(directory).parent / 'widget_symbol_runtime_policy',
                apply_report_dir=Path(report_root) / 'widget_symbol_runtime_policy_apply')
        else:
            from src.engine.monitoring import low_price_two_leg_expanded_candidate_research as study
            from src.engine.automation import low_price_two_leg_auto_expansion_policy as policy
            study.write_report(report, paths[family].parent)
            folder = Path(directory).parent / 'low_price_two_leg_auto_expansion'
            value = policy.build_policy(publication_date=date.fromisoformat(publication['publication_date']),
                source_date=day, report_dir=paths[family].parent, policy_dir=folder)
            effective = date.fromisoformat(value['effective_date'])
            child = policy.policy_path(effective, policy_dir=folder)
            policy.preserve_source_snapshot(value, policy_dir=folder)
            loop.publication_transaction(folder, effective_date=effective, files={child.name:value},
                expected_generation=loop.future_publication_parent(folder, effective))
            policy.load_policy(effective, policy_dir=folder)
        value = loop.read_object(child, limit=32 * 1024 * 1024)
        receipt = dict(schema='family_policy_refresh_v2', target_date=str(day), family=family, status='complete',
            publication_contract=publication, policy_path=str(child.resolve()), policy_sha256=loop.digest(value),
            source_path=str(paths[family]), source_sha256=loop.digest(_read_report_dependency(paths[family])),
            allocation_disposition=report['joint_allocation_gate'].get('status'), **loop.AUTHORITY)
        receipt['receipt_sha256'] = loop.digest(receipt)
        loop.atomic_write(destination, receipt)
        return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--source-wait-sec", type=int, default=900)
    parser.add_argument("--source-poll-sec", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--collect-costs", action="store_true")
    parser.add_argument("--family", choices=("widget", "episode", "allocation", "legacy"), default="legacy")
    args = parser.parse_args(argv)
    day = date.fromisoformat(args.source_date)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    if (
        day > now.date()
        or (args.family in {"legacy", "allocation"} and day == now.date()
        and now.time().replace(tzinfo=None) < time(20, 5))
    ):
        print("machine_research_closed_loop_not_yet_due")
        return 75
    if not args.write:
        studies, _, missing = read_studies(day)
        print(loop.digest(studies), missing)
        return 75 if missing else 0
    if args.family in {"widget", "episode"}:
        try:
            result = refresh_family(day, args.family)
        except BlockingIOError:
            print('family_publication_writer_busy')
            return 75
        print(result["status"])
        return 0 if result["status"] == "complete" else 75
    import signal

    def interrupted(signum, frame):
        raise InterruptedError("research_refresh_terminated")

    signal.signal(signal.SIGTERM, interrupted)
    begin = clock.monotonic()
    while True:
        result = refresh(
            day,
            collect_costs=args.collect_costs,
            publish=args.family != "allocation", allocation_only=args.family == "allocation",
            source_wait_seconds=clock.monotonic() - begin,
        )
        if result["status"] == "complete":
            break
        if clock.monotonic() - begin >= args.source_wait_sec:
            return 75
        clock.sleep(min(30, max(1, args.source_poll_sec)))
    print(result["status"], result["semantic_disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
