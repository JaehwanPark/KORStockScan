from __future__ import annotations  # 💡 이 줄을 파일 맨 위에 추가하세요!

import threading
from typing import Callable, Dict, List
from src.utils.logger import log_error


class EventBus:
    _instance = None
    _lock = threading.Lock()  # 싱글톤 생성 시의 스레드 안전성 보장

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers: Dict[str, List[Callable]] = {}
                cls._instance._sub_lock = (
                    threading.Lock()
                )  # 구독/발행 시의 스레드 안전성 보장
                print("전역 EventBus(싱글톤) 인스턴스가 생성되었습니다.")
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable):
        """특정 이벤트(event_type)에 대해 반응할 함수(callback)를 등록합니다."""
        with self._sub_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove a previously registered subscriber callback."""
        with self._sub_lock:
            callbacks = self._subscribers.get(event_type)
            if not callbacks:
                return

            try:
                callbacks.remove(callback)
            except ValueError:
                return

            if not callbacks:
                self._subscribers.pop(event_type, None)

    def publish(self, event_type: str, payload: dict = None):
        """이벤트를 발생시키고, 구독 중인 모든 콜백 함수에 데이터를 전달합니다."""
        if payload is None:
            payload = {}

        with self._sub_lock:
            callbacks = self._subscribers.get(event_type, []).copy()

        if not callbacks:
            return  # 구독자가 없으면 조용히 넘어감

        # 💡 각 콜백을 순차적으로 실행 (Subscriber 측에서 무거운 로직은 비동기/스레드로 분리해야 함)
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                log_error(
                    f"[EventBus] '{event_type}' 이벤트 처리 중 에러 발생 ({callback.__name__}): {e}"
                )
