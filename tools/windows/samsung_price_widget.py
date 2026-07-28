"""Small Windows widget that shows Samsung Electronics' 10-second price delta.

The widget only calls the KORStockScan AWS read-only quote endpoint.  It never
stores a Kiwoom app key, secret key, or bearer token, and it cannot issue a
token, submit an order, or control the trading bot.
"""

from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

APP_NAME = "SamsungPriceWidget"
POLL_INTERVAL_MS = 10_000
WINDOW_SIZE = "190x170"
ACCESS_KEY_HEADER = "X-KORStockScan-Widget-Key"
CHART_WIDTH = 174
CHART_HEIGHT = 46


def default_config_path() -> Path:
    app_data = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or "."
    return Path(app_data) / "KORStockScan" / APP_NAME / "config.json"


@dataclass(frozen=True)
class WidgetSettings:
    endpoint_url: str
    access_key: str


def load_settings(config_path: Path | None = None) -> WidgetSettings:
    path = config_path or default_config_path()
    payload: dict = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        pass

    endpoint_url = str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_URL")
        or payload.get("endpoint_url")
        or ""
    ).strip()
    access_key = str(
        os.getenv("KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY")
        or payload.get("access_key")
        or ""
    ).strip()
    return WidgetSettings(endpoint_url=endpoint_url, access_key=access_key)


def validate_settings(settings: WidgetSettings) -> str | None:
    if not settings.endpoint_url or not settings.access_key:
        return "설정 필요"
    if not settings.endpoint_url.lower().startswith("https://"):
        return "HTTPS URL 필요"
    return None


@dataclass(frozen=True)
class Quote:
    current_price: int
    day_low_delta: int | None
    day_low_delta_pct: float | None
    minute_trend: str
    minute_chart: tuple[tuple[str, int], ...]
    market_venue: str
    market_session: str


def parse_quote_payload(payload: object) -> Quote:
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError("quote_unavailable")
    value = payload.get("current_price")
    try:
        price = abs(int(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_price") from exc
    if price <= 0:
        raise ValueError("invalid_price")
    low_delta = payload.get("day_low_delta")
    try:
        low_delta = int(low_delta) if low_delta is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_day_low_delta") from exc
    low_delta_pct = payload.get("day_low_delta_pct")
    try:
        low_delta_pct = float(low_delta_pct) if low_delta_pct is not None else None
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_day_low_delta_pct") from exc
    trend = str(payload.get("minute_trend") or "unavailable")
    if trend not in {"up", "down", "flat", "unavailable"}:
        raise ValueError("invalid_minute_trend")
    market_venue = str(payload.get("market_venue") or "KRX").strip().upper()
    if market_venue not in {"KRX", "NXT"}:
        raise ValueError("invalid_market_venue")
    market_session = str(payload.get("market_session") or "unknown").strip()
    raw_chart = payload.get("minute_chart", [])
    if not isinstance(raw_chart, list):
        raise ValueError("invalid_minute_chart")
    minute_chart: list[tuple[str, int]] = []
    for row in raw_chart[-20:]:
        if not isinstance(row, dict):
            raise ValueError("invalid_minute_chart")
        time_kst = str(row.get("time_kst") or "").strip()
        try:
            close = abs(int(row.get("close")))
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_minute_chart") from exc
        if len(time_kst) != 5 or time_kst[2] != ":" or close <= 0:
            raise ValueError("invalid_minute_chart")
        minute_chart.append((time_kst, close))
    return Quote(
        current_price=price,
        day_low_delta=low_delta,
        day_low_delta_pct=low_delta_pct,
        minute_trend=trend,
        minute_chart=tuple(minute_chart),
        market_venue=market_venue,
        market_session=market_session,
    )


def fetch_current_price(settings: WidgetSettings, *, timeout_sec: int = 10) -> Quote:
    request = Request(
        settings.endpoint_url,
        headers={ACCESS_KEY_HEADER: settings.access_key, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except (URLError, OSError, ValueError) as exc:
        raise RuntimeError("연결 실패") from exc
    return parse_quote_payload(payload)


class SamsungPriceWidget:
    def __init__(self, root: tk.Tk, settings: WidgetSettings) -> None:
        self.root = root
        self.settings = settings
        self.previous_price: int | None = None
        self.inflight = False

        root.title("삼성전자 10초")
        root.geometry(WINDOW_SIZE)
        root.minsize(190, 170)
        root.maxsize(190, 170)
        root.attributes("-topmost", True)
        root.configure(bg="#1e2430")
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        frame = tk.Frame(root, bg="#1e2430", padx=8, pady=6)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="삼성전자 005930 · 10초 갱신",
            fg="#dfe7f3",
            bg="#1e2430",
            font=("Malgun Gothic", 8, "bold"),
            anchor="w",
        ).pack(fill="x")
        self.price_label = tk.Label(
            frame,
            text="—",
            fg="#ffffff",
            bg="#1e2430",
            font=("Segoe UI", 18, "bold"),
            anchor="w",
        )
        self.price_label.pack(fill="x", pady=(2, 0))
        self.low_label = tk.Label(
            frame,
            text="오늘 저가 대비: —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.low_label.pack(fill="x")
        self.trend_label = tk.Label(
            frame,
            text="1분봉: —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.trend_label.pack(fill="x")
        self.delta_label = tk.Label(
            frame,
            text="직전: —",
            fg="#aab7c8",
            bg="#1e2430",
            font=("Malgun Gothic", 8),
            anchor="w",
        )
        self.delta_label.pack(fill="x")
        self.chart_canvas = tk.Canvas(
            frame,
            width=CHART_WIDTH,
            height=CHART_HEIGHT,
            bg="#151a22",
            highlightthickness=0,
        )
        self.chart_canvas.pack(fill="x", pady=(2, 0))
        self.status_label = tk.Label(
            frame,
            text="초기화 중",
            fg="#8fa2b7",
            bg="#1e2430",
            font=("Malgun Gothic", 7),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(7, 0))

    def start(self) -> None:
        problem = validate_settings(self.settings)
        if problem:
            self.status_label.configure(text=problem, fg="#ffb86c")
            return
        self._refresh()

    def _refresh(self) -> None:
        if self.inflight:
            self.root.after(POLL_INTERVAL_MS, self._refresh)
            return
        self.inflight = True
        threading.Thread(target=self._fetch_worker, daemon=True).start()

    def _fetch_worker(self) -> None:
        try:
            quote = fetch_current_price(self.settings)
        except Exception as exc:  # keep the last successful price visible
            self.root.after(0, lambda: self._apply_error(str(exc)))
        else:
            self.root.after(0, lambda: self._apply_quote(quote))

    def _apply_quote(self, quote: Quote) -> None:
        current_price = quote.current_price
        previous = self.previous_price
        self.previous_price = current_price
        self.price_label.configure(text=f"{current_price:,}원")
        if quote.day_low_delta is None or quote.day_low_delta_pct is None:
            self.low_label.configure(text="오늘 저가 대비: —", fg="#aab7c8")
        else:
            self.low_label.configure(
                text=(
                    f"오늘 저가 대비: +{quote.day_low_delta:,}원 "
                    f"(+{quote.day_low_delta_pct:.2f}%)"
                ),
                fg="#ff6b6b" if quote.day_low_delta > 0 else "#aab7c8",
            )
        trend_text, trend_color = {
            "up": ("1분봉: ▲ 상승", "#ff6b6b"),
            "down": ("1분봉: ▼ 하락", "#5ca9ff"),
            "flat": ("1분봉: ─ 보합", "#aab7c8"),
            "unavailable": ("1분봉: 데이터 대기", "#aab7c8"),
        }[quote.minute_trend]
        self.trend_label.configure(text=trend_text, fg=trend_color)
        self._draw_minute_chart(quote.minute_chart)
        if previous is None:
            self.delta_label.configure(text="직전: —", fg="#aab7c8")
        else:
            delta = current_price - previous
            color = "#ff6b6b" if delta > 0 else "#5ca9ff" if delta < 0 else "#aab7c8"
            sign = "+" if delta > 0 else ""
            self.delta_label.configure(text=f"직전: {sign}{delta:,}원", fg=color)
        self.status_label.configure(
            text=(
                f"갱신 {datetime.now().strftime('%H:%M:%S')} · "
                f"{quote.market_venue} · AWS 공유 토큰"
            ),
            fg="#8fa2b7",
        )
        self._finish_cycle()

    def _draw_minute_chart(self, minute_chart: tuple[tuple[str, int], ...]) -> None:
        canvas = self.chart_canvas
        canvas.delete("all")
        if len(minute_chart) < 2:
            canvas.create_text(
                5,
                CHART_HEIGHT // 2,
                text="20분 차트 데이터 대기",
                fill="#8fa2b7",
                font=("Malgun Gothic", 8),
                anchor="w",
            )
            return

        prices = [close for _, close in minute_chart]
        minimum, maximum = min(prices), max(prices)
        left, right, top, bottom = 3, CHART_WIDTH - 3, 8, CHART_HEIGHT - 5
        canvas.create_line(
            left, (top + bottom) / 2, right, (top + bottom) / 2, fill="#293342"
        )
        if maximum == minimum:
            y_values = [(top + bottom) / 2] * len(prices)
        else:
            y_values = [
                bottom - ((price - minimum) / (maximum - minimum)) * (bottom - top)
                for price in prices
            ]
        step = (right - left) / (len(prices) - 1)
        points = [
            coordinate
            for index, y_value in enumerate(y_values)
            for coordinate in (left + index * step, y_value)
        ]
        color = "#ff6b6b" if prices[-1] >= prices[0] else "#5ca9ff"
        canvas.create_line(*points, fill=color, width=2, smooth=True)
        canvas.create_oval(
            points[-2] - 2,
            points[-1] - 2,
            points[-2] + 2,
            points[-1] + 2,
            fill=color,
            outline=color,
        )
        canvas.create_text(
            4,
            2,
            text=f"20분 · {minute_chart[0][0]}–{minute_chart[-1][0]}",
            fill="#8fa2b7",
            font=("Segoe UI", 6),
            anchor="nw",
        )

    def _apply_error(self, message: str) -> None:
        self.status_label.configure(text=f"{message} · AWS 토큰 대기", fg="#ffb86c")
        self._finish_cycle()

    def _finish_cycle(self) -> None:
        self.inflight = False
        self.root.after(POLL_INTERVAL_MS, self._refresh)


def main() -> None:
    root = tk.Tk()
    widget = SamsungPriceWidget(root, load_settings())
    widget.start()
    root.mainloop()


if __name__ == "__main__":
    main()
