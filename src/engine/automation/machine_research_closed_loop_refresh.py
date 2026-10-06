"""Resume the existing nightly episode research publication fixed point.

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
            "candidates/episode_*.json",
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
            "low_price_two_leg_expanded_candidate_research.py",
            "low_price_two_leg_tuning.py",
        )
    ]
    paths.append(engine / "automation" / "low_price_two_leg_auto_expansion_policy.py")
    paths += [
        engine.parent / "trading" / name
        for name in (
            "market/comparison_cost.py",
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
    path = Path(path)
    path.stat()
    if "widget" in path.name or "widget" in path.parent.name:
        raise ValueError("retired_family_dependency")
    if path.parent.name in {"low_price_two_leg_expanded_candidate_research", "low_price_two_leg_tuning"}:
        from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import read_report
        return read_report(path)
    return loop.read_object(path, limit=32 * 1024 * 1024)


def read_studies(day, *, report_root=DATA_DIR / "report", families=("episode",)):
    if not families or set(families) != {"episode"}:
        raise ValueError("research_family_retired_or_unknown")
    path = (Path(report_root) / "low_price_two_leg_expanded_candidate_research" /
            f"low_price_two_leg_expanded_candidate_research_{day}.json").resolve()
    try:
        value = _read_report_dependency(path)
        if (str(value.get("end_date") or value.get("target_date")) != day.isoformat()
            or value.get("closed_loop_contract") != loop.SCHEMA
            or any(value.get(k) is not v for k, v in loop.AUTHORITY.items())):
            raise ValueError("exact_study_contract_invalid")
        return {"episode": value}, {"episode": path}, []
    except (FileNotFoundError, ValueError):
        return {}, {"episode": path}, ["episode"]


def lifecycle_counts(studies):
    counts, mapping = {}, []
    for family, report in studies.items():
        results = report.get("profiles") or {}
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


def _study_source_generations(report):
    from src.engine.monitoring.research_source_facts import generation, source_integrity
    sources = {}
    for result in (report.get("profiles") or {}).values():
        for name, expected in (result.get("execution_feasibility") or {}).get("source_generations", {}).items():
            if name in sources and list(sources[name]) != list(expected):
                raise ValueError("episode_study_source_generation_conflict")
            source_integrity(name)
            if list(generation(Path(name).lstat())) != list(expected):
                raise ValueError("episode_study_source_changed")
            sources[name] = expected
    return sources


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


def _refresh(day, *, directory=loop.DIRECTORY, report_root=DATA_DIR / "report",
             publish=True, collect_costs=False, source_wait_seconds=0, allocation_only=False):
    """Refresh surviving episode evidence under the existing writer and allocator."""
    if collect_costs:
        raise ValueError("widget_cost_recovery_permanently_retired_episode_costs_owned_by_native_tuning")
    started = clock.monotonic()
    publication = _publication_contract(day)
    destination = report_path(report_root, day)
    with loop.research_scope(directory), loop.writer_lock(Path(directory) / "refresh", blocking=False):
        studies, paths, missing = read_studies(day, report_root=report_root)
        if missing:
            body = dict(schema=loop.SCHEMA, target_date=str(day), status="waiting",
                        semantic_disposition="required_completed_study_missing", missing_families=missing,
                        active_families=["episode"], **loop.AUTHORITY)
            loop.atomic_write(destination, body)
            return body
        try:
            previous = loop.read_object(destination, limit=16 * 1024 * 1024)
        except FileNotFoundError:
            previous = {}
        if (previous.get("allocation_only") is allocation_only
            and previous.get("exact_cost_recovery_requested") is collect_costs
            and previous.get("publication_requested") is publish
            and validate_current_receipt(previous, day, publication_contract=publication)):
            return previous
        from src.engine.monitoring.research_allocation_snapshot import write_snapshot
        from src.engine.monitoring.research_version_outcomes import episode_feedback
        from src.engine.monitoring.research_cache_storage import capacity_receipt
        allocator = loop.load_allocator(day, directory=directory)
        if allocator is None or allocator.get("source_quality_status") != "PASS":
            write_snapshot(day, directory=directory, report_root=report_root)
        report, path = studies["episode"], paths["episode"]
        source_generations = _study_source_generations(report)
        publications = {}
        if publish:
            receipt = _publish_episode(day, report, path, publication,
                                       directory=directory, report_root=report_root)
            folder = Path(receipt["policy_path"]).parent
            manifest = loop.read_object(folder / f"research_publication_{publication['effective_date']}.json")
            publications["episode"] = dict(directory=str(folder), effective_date=publication["effective_date"],
                                            generation_sha256=manifest["generation_sha256"],
                                            policy_path=receipt["policy_path"], profile_count=receipt["profile_count"])
        else:
            loop.write_joint_inputs(report, family="episode", directory=directory)
            report["joint_allocation_gate"] = loop.combined_joint_gate(
                report, family="episode", source_date=day, directory=directory)
        gate = report["joint_allocation_gate"]
        dependency_paths = {str(path), *dependency_catalog(directory),
                            str((Path(directory) / f"allocator_{day}.json").resolve()),
                            *gate.get("capital_source_dependencies", [])}
        feedback_path = Path(report_root) / "low_price_two_leg_tuning" / f"low_price_two_leg_tuning_{day}.json"
        dependency_paths.add(str(feedback_path.resolve()))
        snapshot = loop.load_allocator(day, directory=directory) or {}
        dependency_paths.update(str((Path(directory) / relative).resolve()) for relative in (
            "native_cash.json", "native_inventory.json", f"opening_capacity/capacity_source_{day}.json",
            f"capacity_source_{day}.json", f"native_capacity/{day}/native_cash.json",
            f"native_capacity/{day}/native_inventory.json"))
        for key in ("owner_policy_path", "native_acquisition_path", "native_cash_path", "native_inventory_path"):
            if snapshot.get(key):
                dependency_paths.add(str(Path(snapshot[key]).resolve()))
        stage_source = (snapshot.get("constraints") or {}).get("same_stage_source_path")
        if stage_source:
            dependency_paths.add(str(Path(stage_source).resolve()))
        _study_source_generations(report)
        dependencies = {name: loop.digest(_read_report_dependency(Path(name), source_date=day))
                        if Path(name).exists() else None for name in sorted(dependency_paths)}
        counts, mapping = lifecycle_counts(studies)
        body = dict(schema=loop.SCHEMA, target_date=str(day), status="complete", active_families=["episode"],
                    storage_capacity=capacity_receipt(directory, day, report_root), code_sources=code_contract(),
                    research_directory=str(Path(directory).resolve()), dependency_catalog=dependency_catalog(directory),
                    dependency_sha256=loop.digest(dependencies), dependency_sources=dependencies,
                    source_generations=source_generations,
                    exact_cost_recovery_requested=collect_costs, publication_requested=publish,
                    allocation_only=allocation_only, publication_contract=publication,
                    execution_mode="completed_study_fixed_point_no_grid_replay", compute_replayed=False,
                    phase_metrics=dict(source_wait_seconds=source_wait_seconds,
                                       compute_seconds=clock.monotonic()-started, outcome_recovery_seconds=0),
                    lifecycle_counts=counts, parent_child_mapping=mapping, publications=publications,
                    joint_allocation_gate=gate, policy_version_feedback={"episode": episode_feedback(day, report_root=report_root)},
                    consumer_acceptance="waiting_exact_next_date_natural_PREOPEN",
                    economic_acceptance="waiting_mature_exact_cost_outcomes",
                    semantic_disposition="prospective_or_allocation_evidence_pending" if any(
                        item["selection_disposition"] != "selected" for item in mapping) else "selected_next_date",
                    **loop.AUTHORITY)
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
        and value.get("active_families") == ["episode"]
        and not set(value.get("publications") or {}).difference({"episode"})
        and value.get("target_date") == str(day)
        and value.get("status") == "complete"
        and value.get("receipt_sha256") == loop.digest(body)
        and (bool(value.get("publications")) or value.get("allocation_only") is True)
        and all(
            item.get("unaccounted_count") == 0
            for item in value.get("lifecycle_counts", {}).values()
        )
    )


def refresh_family(day, family, *, directory=loop.DIRECTORY, report_root=DATA_DIR / "report"):
    if family != "episode":
        raise ValueError("research_family_retired_or_unknown")
    studies, paths, missing = read_studies(day, report_root=report_root)
    if missing:
        return dict(status="waiting", missing_families=missing)
    publication = _publication_contract(day)
    with loop.research_scope(directory), loop.writer_lock(Path(directory) / "refresh", blocking=False):
        return _publish_episode(day, studies[family], paths[family], publication,
                                directory=directory, report_root=report_root)


def _publish_episode(day, report, path, publication, *, directory, report_root):
    from src.engine.monitoring.research_version_outcomes import episode_feedback
    from src.engine.monitoring import low_price_two_leg_expanded_candidate_research as study
    from src.engine.automation import low_price_two_leg_auto_expansion_policy as policy
    _study_source_generations(report)
    report["policy_version_feedback"] = episode_feedback(day, report_root=report_root)
    loop.write_joint_inputs(report, family="episode", directory=directory)
    report["joint_allocation_gate"] = loop.combined_joint_gate(
        report, family="episode", source_date=day, directory=directory)
    study.write_report(report, path.parent)
    folder = Path(directory).parent / "low_price_two_leg_auto_expansion"
    _study_source_generations(report)
    value = policy.build_policy(publication_date=date.fromisoformat(publication["publication_date"]),
                               source_date=day, report_dir=path.parent, policy_dir=folder)
    effective = date.fromisoformat(value["effective_date"])
    child = policy.policy_path(effective, policy_dir=folder)
    policy.preserve_source_snapshot(value, policy_dir=folder)
    manifest = loop.publication_transaction(
        folder, effective_date=effective, files={child.name: value},
        expected_generation=loop.future_publication_parent(folder, effective))
    policy.load_policy(effective, policy_dir=folder)
    value = loop.read_object(child, limit=32 * 1024 * 1024)
    receipt = dict(schema="family_policy_refresh_v2", target_date=str(day), family="episode",
                   status="complete", publication_contract=publication, policy_path=str(child.resolve()),
                   policy_sha256=loop.digest(value), source_path=str(path),
                   source_sha256=loop.digest(_read_report_dependency(path)),
                   directory=str(folder.resolve()), effective_date=str(effective),
                   generation_sha256=manifest["generation_sha256"],
                   profile_count=len(value.get("profiles") or {}),
                   allocation_disposition=report["joint_allocation_gate"].get("status"), **loop.AUTHORITY)
    receipt["receipt_sha256"] = loop.digest(receipt)
    loop.atomic_write(Path(report_root) / REPORT_TYPE / f"episode_policy_refresh_{day}.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--source-wait-sec", type=int, default=900)
    parser.add_argument("--source-poll-sec", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--family", choices=("episode", "allocation", "legacy"), default="legacy")
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
    if args.family == "episode":
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
            collect_costs=False,
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
