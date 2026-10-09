"""Advisory research outbox; no Main Telegram manager or strategy imports.

Sending requires a sealed eligible winner, current parent and verified night.
An ambiguous delivery is durable and is never automatically retransmitted.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import time
from urllib import error, parse, request

from src.engine.scalping import market_weakness_research as R


def valid_message_id(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def advisory_eligible(c):
    values = [
        c.get("delta_raw_win_rate"),
        c.get("empirical_lower_5pct_delta"),
        c.get("worst_outcome_U_delta"),
    ]
    values += (
        list(c.get("delayed_common_range_delta", {}).values())
        + c.get("leave_date_delta", [])
        + c.get("leave_episode_delta", [])
    )
    return bool(
        c.get("status") == "eligible_advisory"
        and c.get("scope_winner") is True
        and c.get("comparison_complete") is True
        and c.get("excluded_opportunities", 0) > 0
        and c.get("bootstrap_valid_iterations") == 1000
        and c.get("leave_date_delta")
        and c.get("leave_episode_delta")
        and set(c.get("delayed_common_range_delta", {})) == {"60", "180"}
        and all(R.number(v) is not None and R.number(v) > 0 for v in values)
    )


def recommendation_id(candidate):
    return R.digest(
        dict(
            admin_scope="configured_admin_only",
            scope=candidate["scope"],
            adjustment=candidate["definition"],
        )
    )


def preview(candidate, transition="recommendation"):
    d, s = candidate["definition"], candidate["scope"]
    if transition != "recommendation":
        label = "오류 정정" if transition == "correction" else "추천 철회"
        return f"Main 약세 대응 연구 — {label} / 자동 적용 없음\n후보 ID {recommendation_id(candidate)}\n현재 근거로 이 추천을 유지하지 않습니다. 실제 정책 변경 없음."
    b, c = candidate["baseline"], candidate["candidate"]
    dates = candidate["source_dates"]
    period = f"{dates[0]}~{dates[-1]} ({len(dates)}일)"
    counts = candidate.get("join_counts", {})
    total = counts.get("rows", 0)
    grades = {
        g: dict(
            count=counts.get("join_" + g, 0),
            ratio=counts.get("join_" + g, 0) / total if total else None,
        )
        for g in ("A", "B", "C", "U")
    }
    lower = candidate.get("empirical_lower_5pct_delta")
    return "\n".join(
        [
            "Main 약세 대응 연구 — 조정 후보 발견 / 자동 적용 없음",
            f"대상: {s.get('listing_market')} {s.get('symbol')} / {s.get('session')} / {s.get('route')}",
            f"범위: 실제 보조 PASS 이후 제출 제외 CF / {s.get('decision_origin')}",
            f"약세 조건: 해당 시장 지수 <= {d['weakness_index_max_pct']:+.3f}%",
            f"검토할 조정: {d['axis']} {d['before']} → < {d['after']:.4f} {d['unit']} 시 이번 기회 보류",
            f"누적 비교: {period}; 약세 구간 {candidate['episode_count']}개",
            f"W/F/U: {b['W']}/{b['F']}/{b['U']} → {c['W']}/{c['F']}/{c['U']}",
            f"raw 승률: {b['raw_win_rate']*100:.2f}% → {c['raw_win_rate']*100:.2f}% (Δ {candidate['delta_raw_win_rate']*100:+.2f}%p)",
            f"경험적 하위 5% Δ {lower*100:+.2f}%p; 통계적 95% 보장이 아님",
            f"제외/추가 {candidate['excluded_opportunities']}/{candidate['added_opportunities']}, 놓친 W {candidate['missed_W']}, 제거한 F {candidate['removed_F']}",
            f"근거 품질: {json.dumps(grades,ensure_ascii=True)}",
            "근사 연결 연구 추정; 60/180초 공통 연결·U·날짜/구간 제외 민감도 확인. 실제 체결/수익 보장이 아님.",
            f"기계 parent {d['parent_hash']}; 보조 component {d['auxiliary_hash']}",
            f"근거 세대 {candidate['generation']}; 후보 ID {recommendation_id(candidate)}",
        ]
    )


def current_parent_matches(data_root, candidate):
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective

    try:
        bundle = load_effective(
            data_root=Path(data_root),
            target_date=datetime.now(R.KST).date().isoformat(),
        )
    except (ValueError, OSError, TypeError):
        return False
    if not bundle:
        return False
    d = candidate["definition"]
    family = bundle.get("continuous_reversal", {})
    scope = d.get("policy_scope")
    if (
        scope
        and d.get("scope_parent_machine_payload_sha256")
        and d.get("auxiliary_binding")
    ):
        key, route = scope.rsplit("|", 1)
        machine = (
            family.get("machine_cells", {})
            .get(key, {})
            .get("routes", {})
            .get(route, {})
        )
        auxiliary = (
            family.get("auxiliary_cells", {})
            .get(key, {})
            .get("routes", {})
            .get(route, {})
        )
        if machine.get("payload_sha256") != d[
            "scope_parent_machine_payload_sha256"
        ] or machine.get("payload_sha256") != R.digest(machine.get("payload")):
            return False
        payload = auxiliary.get("payload", {})
        if auxiliary.get("payload_sha256") != R.digest(payload):
            return False
        binding = payload.get("binding", {})
        projected = {k: binding.get(k) for k in d["auxiliary_binding"]}
        return projected == d["auxiliary_binding"] and R.digest(projected) == d.get(
            "auxiliary_hash"
        )
    expected = d.get("auxiliary_hash")
    return bool(
        bundle.get("bundle_sha256") == d.get("parent_hash")
        and expected
        and expected == R.digest(family.get("auxiliary_cells", {}))
    )


def configured_transport(message):
    """Load only existing administrator settings after all eligibility gates."""
    from src.utils.constants import CONFIG_PATH, DEV_PATH

    p = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with p.open() as f:
            config = json.load(f)
        token, admin = str(config.get("TELEGRAM_TOKEN") or ""), str(
            config.get("ADMIN_ID") or ""
        )
    except (OSError, ValueError):
        return dict(status="failed_definite", reason="notification_config_missing")
    if not token or not admin:
        return dict(status="failed_definite", reason="notification_config_missing")
    packet = parse.urlencode(dict(chat_id=admin, text=message)).encode()
    try:
        with request.urlopen(
            request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage", data=packet
            ),
            timeout=10,
        ) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            return dict(
                status="delivery_uncertain", reason="notification_response_size_invalid"
            )
        result = json.loads(raw)
        if result.get("ok") is True and valid_message_id(
            (result.get("result") or {}).get("message_id")
        ):
            return dict(status="sent", message_id=result["result"]["message_id"])
        return dict(status="failed_definite", reason="notification_rejected")
    except error.HTTPError as exc:
        if exc.code == 429:
            try:
                body = json.loads(exc.read(65536))
                delay = body.get("parameters", {}).get("retry_after")
            except (ValueError, OSError):
                delay = None
            return dict(
                status="failed_definite",
                reason="notification_rate_limit",
                retry_after=delay,
            )
        return dict(
            status="failed_definite" if 400 <= exc.code < 500 else "delivery_uncertain",
            reason="notification_http_failure",
        )
    except (OSError, ValueError, TypeError):
        return dict(
            status="delivery_uncertain", reason="notification_delivery_unobservable"
        )


def reconcile(
    root,
    comparison,
    *,
    send_enabled=False,
    data_root=None,
    gate=lambda: False,
    transport=configured_transport,
    parent_matches=current_parent_matches,
    source_matches=lambda: False,
    now=time.time,
):
    from src.engine.automation.main_market_weakness_research import (
        atomic,
        read_json,
        lock,
        check_seal,
    )

    root = Path(root)
    check_seal(comparison)
    if comparison.get("schema") != R.VERSION + ":comparison" or any(
        comparison.get(k) != v for k, v in R.AUTH.items()
    ):
        raise ValueError("notification_comparison_authority_invalid")
    with lock(root / "outbox/outbox.lock"):
        path = root / "outbox/state.json"
        state = read_json(
            path, dict(schema=R.VERSION + ":outbox", recommendations={}, events={})
        )
        for event in state["events"].values():
            if event.get("status") == "sending":
                event.update(
                    status="delivery_uncertain",
                    reason="sending_without_terminal_receipt",
                )
                state["recommendations"][event["recommendation_id"]][
                    "status"
                ] = "delivery_uncertain"
        atomic(path, state)
        candidates = comparison.get("comparisons", [])
        winners = {recommendation_id(c): c for c in candidates if advisory_eligible(c)}
        current_scopes = {c["scope_key"] for c in candidates}
        winning_scopes = {c["scope_key"] for c in winners.values()}
        for rid, rec in state["recommendations"].items():
            if (
                rec.get("status") != "sent"
                or rid in winners
                or rec["candidate"]["scope_key"] in winning_scopes
            ):
                continue
            scope = rec["candidate"]["scope_key"]
            source_invalid = scope not in current_scopes or any(
                c["scope_key"] == scope and c["status"] == "source_gap"
                for c in candidates
            )
            transition = "correction" if source_invalid else "withdrawal"
            prior = rec.get("sent_event")
            previous = state["events"].get(prior, {})
            if previous.get("status") != "sent" or not valid_message_id(
                previous.get("message_id")
            ):
                continue
            key = R.digest([rid, transition, prior])
            state["events"].setdefault(
                key,
                dict(
                    recommendation_id=rid,
                    transition=transition,
                    previous_sent_event=prior,
                    status="prepared",
                    candidate=rec["candidate"],
                    invalidation_reason=(
                        "source_invalidated"
                        if source_invalid
                        else "new_observations_not_eligible"
                    ),
                ),
            )
        for rid, c in winners.items():
            rec = state["recommendations"].get(rid)
            if rec and rec.get("status") in {
                "sent",
                "withdrawn",
                "superseded",
                "delivery_uncertain",
            }:
                continue
            key = R.digest([rid, "recommendation"])
            state["events"].setdefault(
                key,
                dict(
                    recommendation_id=rid,
                    transition="recommendation",
                    status="prepared",
                    candidate=c,
                ),
            )
            state["recommendations"].setdefault(
                rid, dict(status="prepared", candidate=c)
            )
            state["events"][key]["candidate"] = c
            if state["events"][key]["status"] == "suppressed":
                state["events"][key]["status"] = "prepared"
        atomic(path, state)
        dispositions = []
        sent_count = 0
        for key, event in state["events"].items():
            if event["status"] not in {"prepared", "failed_definite"}:
                continue
            c = event["candidate"]
            rid = event["recommendation_id"]
            if event["transition"] == "recommendation":
                if rid not in winners:
                    event.update(
                        status="suppressed", reason="candidate_no_longer_eligible"
                    )
                    continue
                if not parent_matches(data_root, c):
                    event["reason"] = "stale_parent"
                    dispositions.append(
                        dict(
                            event_id=key,
                            status="notification_blocked",
                            reason="stale_parent",
                        )
                    )
                    continue
            else:
                prior = state["events"].get(event.get("previous_sent_event"), {})
                if rid in winners:
                    event.update(
                        status="suppressed", reason="invalidation_no_longer_current"
                    )
                    continue
                if (
                    prior.get("status") != "sent"
                    or not valid_message_id(prior.get("message_id"))
                    or not event.get("invalidation_reason")
                ):
                    event.update(
                        status="suppressed", reason="correction_binding_invalid"
                    )
                    continue
            if not send_enabled:
                dispositions.append(
                    dict(
                        event_id=key,
                        status="preview_only",
                        message=preview(c, event["transition"]),
                    )
                )
                continue
            if (
                not gate()
                or not source_matches()
                or sent_count >= 3
                or now() < event.get("retry_at", 0)
            ):
                dispositions.append(
                    dict(event_id=key, status="deferred_resource_or_window")
                )
                continue
            if event.get("definite_failures", 0) >= 3:
                dispositions.append(
                    dict(
                        event_id=key,
                        status="notification_blocked",
                        reason="bounded_retry_exhausted",
                    )
                )
                continue
            event.update(status="sending", claimed_at=now())
            atomic(
                path, state
            )  # Durable atomic claim before a possibly ambiguous send.
            if (
                not gate()
                or not source_matches()
                or (
                    event["transition"] == "recommendation"
                    and not parent_matches(data_root, c)
                )
            ):
                event.update(
                    status="prepared",
                    reason="source_parent_or_window_changed_before_send",
                )
                atomic(path, state)
                dispositions.append(
                    dict(event_id=key, status="deferred_resource_or_window")
                )
                continue
            message = preview(c, event["transition"])
            old_sent = [
                r["sent_event"]
                for r in state["recommendations"].values()
                if r.get("status") == "sent"
                and r["candidate"]["scope_key"] == c["scope_key"]
            ]
            if old_sent and event["transition"] == "recommendation":
                message += (
                    "\n같은 범위의 이전 안내를 이 후보로 대체합니다: "
                    + ",".join(old_sent)
                )
            try:
                result = transport(message)
            except (OSError, ValueError, TypeError):
                result = dict(
                    status="delivery_uncertain",
                    reason="transport_terminal_unobservable",
                )
            if result.get("status") not in {
                "sent",
                "failed_definite",
                "delivery_uncertain",
            }:
                result = dict(
                    status="delivery_uncertain", reason="transport_terminal_invalid"
                )
            if result.get("status") == "sent" and not valid_message_id(
                result.get("message_id")
            ):
                result = dict(status="delivery_uncertain", reason="message_id_absent")
            event.update(result, finished_at=now())
            sent_count += 1
            if result["status"] == "failed_definite":
                event["definite_failures"] = event.get("definite_failures", 0) + 1
                delay = R.number(result.get("retry_after"))
                event["retry_at"] = now() + max(0, delay or 0)
            elif result["status"] == "sent":
                rec = state["recommendations"][rid]
                if event["transition"] == "recommendation":
                    rec.update(status="sent", sent_event=key, candidate=c)
                    for old_id, old in state["recommendations"].items():
                        if (
                            old_id != rid
                            and old.get("status") == "sent"
                            and old["candidate"]["scope_key"] == c["scope_key"]
                        ):
                            old.update(status="superseded", superseded_by=rid)
                else:
                    rec.update(status="withdrawn", withdrawal_event=key)
            elif result["status"] == "delivery_uncertain":
                state["recommendations"][rid]["status"] = "delivery_uncertain"
            atomic(path, state)
            dispositions.append(dict(event_id=key, status=event["status"]))
        atomic(path, state)
        statuses = {d["status"] for d in dispositions}
        if any(
            e.get("status") == "delivery_uncertain" for e in state["events"].values()
        ):
            status = "delivery_uncertain"
        elif "notification_blocked" in statuses or "failed_definite" in statuses:
            status = "notification_blocked"
        elif "deferred_resource_or_window" in statuses:
            status = "deferred_resource_or_window"
        elif "preview_only" in statuses:
            status = "preview_only"
        else:
            status = "completed" if winners else "not_eligible"
        return dict(
            status=status,
            comparison_sha256=comparison["artifact_content_sha256"],
            eligible_candidates=len(winners),
            dispositions=dispositions,
            **R.AUTH,
        )
