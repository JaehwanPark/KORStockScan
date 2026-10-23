"""Canonical listing-source preparation shared by Main startup and EOD.

Infrastructure owns scheduling and persistence; pure venue contracts own row
validation. This module never imports the EOD feature/model/report pipeline.
"""
from __future__ import annotations

from datetime import date, datetime
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from zoneinfo import ZoneInfo

from src.database.models import SecurityMarketEligibilityDaily
from src.trading.market.aftermarket_eligibility import resolve_symbol_venue_eligibility

KST = ZoneInfo("Asia/Seoul")
MAX_DAILY_ATTEMPTS = 3
RETRY_INTERVAL_SECONDS = 300.0

# Operator removal from listing/collection masters on 2026-10-23. Preserve
# dated source receipts; this does not reclassify broker data or custody.
REMOVED_MASTER_SYMBOLS = frozenset({'179880', '266690', '468670', '486510'})


def master_symbol_removed(code: object) -> bool:
    return str(code or '').strip().upper().removeprefix('A').split('_', 1)[0] in REMOVED_MASTER_SYMBOLS


def store_market_eligibility_rows(
    session,
    *,
    trade_date: date,
    source_rows: dict[str, dict],
) -> dict:
    quality_counts: dict[str, int] = {}
    excluded = []
    for code, source_snapshot in sorted((source_rows or {}).items()):
        if master_symbol_removed(code):
            excluded.append(code)
            continue
        resolved = resolve_symbol_venue_eligibility(
            code,
            trade_date,
            source_snapshot,
        )
        session.merge(
            SecurityMarketEligibilityDaily(
                trade_date=trade_date,
                stock_code=resolved.stock_code,
                krx_regular_eligible=resolved.krx_regular_eligible,
                nxt_eligible=resolved.nxt_eligible,
                krx_aftermarket_eligible=resolved.krx_aftermarket_eligible,
                eligible_venues_json=list(resolved.eligible_venues),
                audit_info=resolved.audit_info,
                stock_state=resolved.stock_state,
                order_warning=resolved.order_warning,
                market_code=resolved.market_code,
                source_api_id=resolved.source_api_id,
                source_revision=resolved.source_revision,
                observed_at_kst=resolved.observed_at_kst,
                payload_sha256=resolved.payload_sha256,
                quality_state=resolved.quality_state,
                blocked_reasons_json=list(resolved.blockers),
            )
        )
        quality_counts[resolved.quality_state] = (
            quality_counts.get(resolved.quality_state, 0) + 1
        )
    return {
        "stored_count": int(sum(quality_counts.values())),
        "quality_counts": quality_counts,
        **({'operator_removed_master_codes': excluded} if excluded else {}),
    }


class RuntimeMarketEligibilitySource:
    """One complete listing read per Main process/KST day, outside entry work.

    Failed reads retain canonical UNKNOWN/CONFLICT rows and retry on a later
    scheduler tick, at most three times per date. A restart starts a new source
    observation; no previous-date or previous-process completion is assumed.
    """

    def __init__(self, receipt_dir, *, now=None, monotonic=None, calendar=None,
                 token=None, fetch=None, log=None):
        self.receipt_dir = Path(receipt_dir)
        self._now = now or (lambda: datetime.now(KST))
        self._monotonic = monotonic or time.monotonic
        self._calendar = calendar
        self._token = token
        self._fetch = fetch
        self._log = log
        self._lock = threading.Lock()
        self._day = None
        self._open = False
        self._attempts = 0
        self._next_attempt = 0.0
        self._complete = False
        self._result = None

    def _write_receipt(self, result):
        directory = self.receipt_dir / result['target_date']
        directory.mkdir(parents=True, exist_ok=True)
        # Preserve every attempt; the filename includes process start identity.
        try:
            start = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
        except (OSError, IndexError):
            start = 'unknown'
        path = directory / f"{os.getpid()}-{start}-{self._attempts}.json"
        raw = (json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode()
        with path.open('xb') as out:
            out.write(raw)
        fd, name = tempfile.mkstemp(prefix='.latest-', dir=directory)
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(raw)
            os.replace(name, directory / 'latest.json')
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def tick(self, db):
        if not self._lock.acquire(blocking=False):
            return {'status': 'in_progress'}
        try:
            return self._tick_locked(db)
        finally:
            self._lock.release()

    def _tick_locked(self, db):
        from src.utils import kiwoom_utils
        from src.utils.logger import log_info

        now = self._now()
        if now.tzinfo is None:
            raise ValueError('market_eligibility_current_clock_must_be_aware')
        now = now.astimezone(KST)
        day = now.date()
        if day != self._day:
            self._day = day
            self._open = (self._calendar(day) if self._calendar is not None
                          else kiwoom_utils.is_trading_day()[0])
            self._attempts, self._next_attempt = 0, 0.0
            self._complete, self._result = False, None
        if not self._open:
            return {'status': 'not_trading_day', 'target_date': day.isoformat()}
        if self._complete:
            return {**self._result, 'cache_hit': True}
        if self._attempts >= MAX_DAILY_ATTEMPTS or self._monotonic() < self._next_attempt:
            return {**(self._result or {}), 'retry_deferred': True}
        self._attempts += 1
        self._next_attempt = self._monotonic() + RETRY_INTERVAL_SECONDS
        result = dict(schema='runtime_market_eligibility_source_v1',
                      target_date=day.isoformat(), observed_at_kst=now.isoformat(),
                      pid=os.getpid(), attempt=self._attempts,
                      source_api_id='ka10099', source_scope='all_kospi_kosdaq_listings',
                      authority='venue_listing_source_only', actual_order_submitted=False,
                      cache_hit=False)
        try:
            token = (self._token or kiwoom_utils.get_kiwoom_token)()
            if not token:
                raise ValueError('market_eligibility_token_unavailable')
            rows, source = (self._fetch or kiwoom_utils.get_stock_eligibility_map_ka10099)(
                token, None, mrkt_tps=('0', '10'), trade_date=day,
                observed_at_kst=now, runtime_prepare=True)
            # Preserve each normalized source row and payload hash before EOD
            # or a later attempt can merge a newer value into the daily table.
            result.update(source=source, source_rows=rows)
            if self._now().astimezone(KST).date() != day:
                raise ValueError('market_eligibility_source_date_changed')
            with db.get_session() as session:
                if source.get('complete') is True and rows:
                    # A full same-day refresh is a new listing snapshot. Do not
                    # leave an omitted old ka10099 row as current NXT authority.
                    prior = session.query(SecurityMarketEligibilityDaily).filter(
                        SecurityMarketEligibilityDaily.trade_date == day,
                        SecurityMarketEligibilityDaily.source_api_id == 'ka10099').all()
                    missing = [row for row in prior if row.stock_code not in rows
                               and row.stock_code.isdigit() and len(row.stock_code) == 6]
                    superseded = {}
                    for row in missing:
                        old = {column.name: getattr(row, column.name)
                               for column in row.__table__.columns}
                        superseded[row.stock_code] = {
                            key: value.isoformat() if isinstance(value, (date, datetime)) else value
                            for key, value in old.items()}
                        rows[row.stock_code] = dict(
                            stock_code=row.stock_code, trade_date=day.isoformat(),
                            krx_regular_eligible=None, nxt_eligible=None,
                            krx_aftermarket_eligible=None, eligible_venues_json=[],
                            source_api_id='ka10099', source_revision=source.get('eligibility_source_revision'),
                            observed_at_kst=now.isoformat(), payload_sha256=None,
                            quality_state='UNKNOWN', complete=True,
                            blocked_reasons=['official_source_row_missing', 'krx_aftermarket_eligibility_unknown'])
                    result['superseded_missing_rows'] = superseded
                storage = store_market_eligibility_rows(session, trade_date=day, source_rows=rows)
            complete = source.get('complete') is True and bool(rows)
            result.update(status='pass' if complete else 'partial',
                          reason='source_complete' if complete else 'source_incomplete_or_empty',
                          source=source, **storage)
        except Exception as exc:
            result.update(status='fail', reason=type(exc).__name__)
        try:
            self._write_receipt(result)
        except (OSError, ValueError, TypeError) as exc:
            result.update(status='fail', receipt_error=type(exc).__name__)
        self._result = result
        self._complete = result['status'] == 'pass'
        (self._log or log_info)(
            '[MARKET_ELIGIBILITY_SOURCE] '
            f"date={day} attempt={self._attempts} status={result['status']} "
            f"reason={result.get('reason')} stored={result.get('stored_count', 0)}")
        return dict(result)

