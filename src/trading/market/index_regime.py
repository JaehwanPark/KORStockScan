"""Validated twenty trading-date index closes; no provider or order authority."""
from datetime import datetime
import math


def index_regime(rows, *, base_date, scale=1.0):
    if not isinstance(rows, list) or len(rows) < 20:
        raise ValueError('index_twenty_dates_missing')
    selected = rows[:20]
    dates, closes = [], []
    for row in selected:
        day = str(row['dt'])
        datetime.strptime(day, '%Y%m%d')
        value = abs(float(str(row['cur_prc']).replace(',', ''))) / scale
        if not math.isfinite(value) or value <= 0 or day > base_date:
            raise ValueError('index_close_or_date_invalid')
        dates.append(day)
        closes.append(value)
    if len(set(dates)) != 20 or dates != sorted(dates, reverse=True):
        raise ValueError('index_trading_date_order_invalid')
    if dates[0] != base_date:
        raise ValueError('index_base_date_not_covered')
    return dict(regime='BULL' if closes[0] >= sum(closes)/20 else 'BEAR',
                latest_date=dates[0], valid_dates=20, current_close=closes[0],
                ma20=sum(closes)/20, source_quality='valid')
