"""Exact amendment receipt reconciliation, using the existing owned adapter.

Official reference: Kiwoom-Securities/Kiwoom-REST-API
234560d213acd8871ae344b5481aecd2f30287fa, inspected 2026-09-10 KST:
packaged spec kt10002/kt00007/ka10075, specs.py, core/client.py, PRD/MOCK
Postman. kiwoom_docs is absent at this revision. No guessed status aliases.
"""

from .adaptive_exit.broker import _count, _number, _hash, TARGET_RATCHET_FAMILY


def reconcile_amendment(adapter, intent, *, price):
    """ACK is identity only. Dated + current proof releases one commitment.

    Missing ACK identity stays unresolved; no symbol-only/manual-order adoption
    and no retry. Reads use the original shared pacing/continuation transport.
    """
    if (
        intent.get("authority_policy_id") != TARGET_RATCHET_FAMILY
        or intent.get("authority_policy_hash") != adapter.policy_hash
    ):
        raise ValueError("amendment_policy_binding_invalid")
    if intent.get("amendment_receipt_sha256"):
        return intent
    if intent.get("action") != "AMEND" or intent.get("state") != "ORDER_BOUND":
        raise ValueError("amendment_ack_identity_unresolved")
    parent_no, child_no = _number(intent["original_order_no"]), _number(
        intent["broker_order_no"]
    )
    day = intent["order_date"]
    from datetime import datetime
    from .adaptive_exit.broker import KST

    if datetime.fromtimestamp(adapter.now_ms() / 1000, KST).date().isoformat() != day:
        raise ValueError("amendment_cross_date_requires_owner_recovery")
    started = adapter.now_ms()
    dated, dh = adapter._pages(
        "kt00007",
        {
            "ord_dt": day.replace("-", ""),
            "qry_tp": "1",
            "stk_bond_tp": "1",
            "sell_tp": "1",
            "stk_cd": adapter.symbol,
            "fr_ord_no": "",
            "dmst_stex_tp": "%",
        },
        "acnt_ord_cntr_prps_dtl",
    )
    current, ch = adapter._pages(
        "ka10075",
        {
            "all_stk_tp": "1",
            "trde_tp": "1",
            "stk_cd": adapter.symbol,
            "stex_tp": "0",
        },
        "oso",
    )

    def row_values(row, live=False):
        if str(row.get("stk_cd", "")) not in {adapter.symbol, "A" + adapter.symbol}:
            raise ValueError("amendment_symbol_conflict")
        route = intent["route"]
        if live:
            if row.get("sor_yn") != ("Y" if route == "SOR" else "N") or row.get(
                "stex_tp"
            ) not in (
                {"0", "1", "2"} if route == "SOR" else {{"KRX": "1", "NXT": "2"}[route]}
            ):
                raise ValueError("amendment_live_route_conflict")
        elif row.get("dmst_stex_tp") not in (
            {"KRX", "NXT", "SOR"} if route == "SOR" else {route}
        ):
            raise ValueError("amendment_dated_route_conflict")
        q, f, r = (
            _count(row.get(k))
            for k in ("ord_qty", "cntr_qty", "oso_qty" if live else "ord_remnq")
        )
        if q <= 0 or f + r > q:
            raise ValueError("amendment_quantity_conflict")
        return q, f, r

    parents = [r for r in dated if r.get("ord_no") == parent_no]
    children = [r for r in dated if r.get("ord_no") == child_no]
    if not parents or not children:
        raise ValueError("amendment_dated_receipt_pending")
    parent_values = {row_values(r) for r in parents}
    child_values = {row_values(r) for r in children}
    if len(parent_values) != 1 or len(child_values) != 1:
        raise ValueError("amendment_duplicate_receipt_conflict")
    pq, pf, pr = parent_values.pop()
    cq, cf, cr = child_values.pop()
    if (
        pr != 0
        or pq != intent["quantity"]
        or pf + cq != pq
        or cf + cr != cq
        or any(
            r.get("ori_ord") != parent_no
            or _count(r.get("ord_uv")) != price
            or _count(r.get("cnfm_qty")) != cq
            for r in children
        )
    ):
        raise ValueError("amendment_confirmation_pending_or_conflicting")
    for row in dated + current:
        parent = row.get("ori_ord", row.get("orig_ord_no"))
        if parent in {parent_no, child_no} and row.get("ord_no") != child_no:
            raise ValueError("amendment_unexpected_successor")
    if any(r.get("ord_no") == parent_no for r in current):
        raise ValueError("amendment_parent_still_current")
    open_child = [r for r in current if r.get("ord_no") == child_no]
    if cr:
        if not open_child or any(
            row_values(r, True) != (cq, cf, cr)
            or r.get("orig_ord_no") != parent_no
            or _count(r.get("ord_pric")) != price
            for r in open_child
        ):
            raise ValueError("amendment_current_receipt_pending_or_conflicting")
    elif open_child:
        raise ValueError("amendment_terminal_current_conflict")
    if not 0 <= adapter.now_ms() - started <= 2000:
        raise ValueError("amendment_reconciliation_stale")
    return adapter.registry.reconcile_sell_amendment(
        context=adapter.context,
        intent_id=intent["intent_id"],
        parent_filled_qty=pf,
        child_quantity=cq,
        child_filled_qty=cf,
        child_remaining_qty=cr,
        receipt_sha256=_hash({"dated": dh, "current": ch}),
    )
