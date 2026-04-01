"""Utilities for scale-in bookkeeping and history persistence."""

from datetime import datetime

from sqlalchemy import desc

from src.database.models import HoldingAddHistory
from src.utils.logger import log_error


def record_add_history_event(
    db,
    *,
    recommendation_id,
    stock_code,
    stock_name=None,
    strategy=None,
    add_type=None,
    event_type,
    event_time=None,
    order_no=None,
    request_qty=0,
    executed_qty=0,
    request_price=None,
    executed_price=None,
    prev_buy_price=None,
    new_buy_price=None,
    prev_buy_qty=0,
    new_buy_qty=0,
    add_count_after=0,
    reason=None,
    note=None,
):
    if not db or not recommendation_id or not stock_code or not event_type:
        return False

    try:
        with db.get_session() as session:
            session.add(
                HoldingAddHistory(
                    recommendation_id=int(recommendation_id),
                    stock_code=str(stock_code)[:10],
                    stock_name=stock_name,
                    strategy=strategy,
                    add_type=add_type,
                    event_type=event_type,
                    event_time=event_time or datetime.now(),
                    order_no=order_no,
                    request_qty=int(request_qty or 0),
                    executed_qty=int(executed_qty or 0),
                    request_price=float(request_price) if request_price is not None else None,
                    executed_price=float(executed_price) if executed_price is not None else None,
                    prev_buy_price=float(prev_buy_price) if prev_buy_price is not None else None,
                    new_buy_price=float(new_buy_price) if new_buy_price is not None else None,
                    prev_buy_qty=int(prev_buy_qty or 0),
                    new_buy_qty=int(new_buy_qty or 0),
                    add_count_after=int(add_count_after or 0),
                    reason=reason,
                    note=note,
                )
            )
        return True
    except Exception as e:
        log_error(
            f"[ADD_HISTORY] event persist failed "
            f"(recommendation_id={recommendation_id}, event_type={event_type}): {e}"
        )
        return False


def find_latest_open_add_order_no(db, recommendation_id):
    """
    가장 최근에 열린 add 주문번호를 찾습니다.
    RECONCILED/CANCELLED/EXECUTED 연결용 보조 헬퍼입니다.
    """
    if not db or not recommendation_id:
        return None

    try:
        with db.get_session() as session:
            sent_rows = (
                session.query(HoldingAddHistory)
                .filter(
                    HoldingAddHistory.recommendation_id == int(recommendation_id),
                    HoldingAddHistory.event_type == 'ORDER_SENT',
                    HoldingAddHistory.order_no.isnot(None),
                )
                .order_by(desc(HoldingAddHistory.event_time), desc(HoldingAddHistory.id))
                .all()
            )

            for sent in sent_rows:
                closed = (
                    session.query(HoldingAddHistory.id)
                    .filter(
                        HoldingAddHistory.recommendation_id == int(recommendation_id),
                        HoldingAddHistory.order_no == sent.order_no,
                        HoldingAddHistory.event_type.in_(('EXECUTED', 'CANCELLED', 'RECONCILED')),
                    )
                    .first()
                )
                if not closed:
                    return sent.order_no

            latest_any = (
                session.query(HoldingAddHistory.order_no)
                .filter(
                    HoldingAddHistory.recommendation_id == int(recommendation_id),
                    HoldingAddHistory.order_no.isnot(None),
                )
                .order_by(desc(HoldingAddHistory.event_time), desc(HoldingAddHistory.id))
                .first()
            )
            return latest_any[0] if latest_any else None
    except Exception as e:
        log_error(
            f"[ADD_HISTORY] open order lookup failed (recommendation_id={recommendation_id}): {e}"
        )
        return None
