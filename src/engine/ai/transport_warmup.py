"""Main-only bounded provider diagnostics, outside decision and tuning ledgers."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime
import logging
import threading
import time


class TransportWarmup:
    """One diagnostic worker; live calls never wait on this executor or lock."""

    def __init__(self, clients, *, allowed, busy, record, interval_sec=240,
                 clock=time.monotonic):
        self.clients = tuple(clients)
        self.allowed = allowed
        self.busy = busy
        self.record = record
        self.interval_sec = max(120, float(interval_sec))
        self.clock = clock
        self.last_activity = {}
        self.lock = threading.Lock()
        self.lifecycle_lock = threading.Lock()
        self.tick_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='ai-warmup-http')
        self.pending = None
        self.thread = None
        self.deadline_sec = 5.0

    def note_activity(self, client):
        with self.lock:
            self.last_activity[id(client)] = self.clock()

    def tick(self):
        if not self.tick_lock.acquire(blocking=False):
            return
        try:
            self._tick()
        finally:
            self.tick_lock.release()

    def _deferred_status(self):
        if self.stop_event.is_set():
            return 'stopped'
        if not self.allowed():
            return 'deferred_session'
        if self.busy():
            return 'deferred_live_priority'
        return None

    def _request(self, client, deadline, provider_started):
        # SDK resource lookup can be lazy and slow; include it in the wall budget.
        status = self._deferred_status()
        if status:
            return {'status': status}
        create = client.responses.create
        status = self._deferred_status()
        if status:
            return {'status': status}
        remaining = deadline - self.clock()
        if remaining <= 0:
            return {'status': 'deadline_expired_before_provider'}
        provider_started.set()
        response = create(
            model='gpt-5.4-nano',
            instructions='This is a transport warmup diagnostic. Return only OK. Never make a trading decision.',
            input='Return OK.', store=False, max_output_tokens=16,
            reasoning={'effort': 'none'}, timeout=remaining,
            metadata={'endpoint_name': 'transport_warmup_diagnostic', 'order_authority': 'none'},
        )
        usage = getattr(response, 'usage', None)
        return {
            'status': 'completed' if response.status == 'completed' and response.output_text.strip() == 'OK' else 'unexpected_response',
            'input_tokens': getattr(usage, 'input_tokens', None),
            'output_tokens': getattr(usage, 'output_tokens', None),
        }

    def _tick(self):
        if self.stop_event.is_set() or not self.allowed() or self.busy():
            return
        if self.pending is not None and not self.pending.done():
            return  # A late diagnostic cannot enqueue a new provider request.
        for index, client in enumerate(self.clients):
            if self.stop_event.is_set() or self.busy() or not self.allowed():
                return
            with self.lock:
                last = self.last_activity.get(id(client), float('-inf'))
                if self.clock() - last < self.interval_sec:
                    continue
                # Charge cadence at admission, including failed attempts.
                self.last_activity[id(client)] = self.clock()
            started = self.clock()
            deadline = started + self.deadline_sec
            provider_started = threading.Event()
            receipt = {
                'schema': 'ai_transport_warmup_v1', 'at': datetime.now().astimezone().isoformat(),
                'key_index': index, 'model': 'gpt-5.4-nano', 'interval_sec': self.interval_sec,
                'decision_authority': 'transport_diagnostic_only', 'runtime_effect': False,
                'actual_order_submitted': False, 'tuning_input_allowed': False,
                'metric_role': 'source_quality_gate', 'window_policy': 'current_main_pid_day',
                'sample_floor': 'one_exact_diagnostic_receipt',
                'primary_decision_metric': 'diagnostic_roundtrip_ms',
                'source_quality_gate': 'exact_model_key_index_pid_source_root',
                'forbidden_uses': ['trading_verdict', 'tuning_input', 'policy_selection',
                                   'realized_pnl', 'live_latency_recovery_claim'],
            }
            self.pending = None
            try:
                with self.lifecycle_lock:
                    if self.stop_event.is_set():
                        return
                    self.pending = self.executor.submit(
                        self._request, client, deadline, provider_started)
                receipt.update(self.pending.result(timeout=max(0, deadline-self.clock())))
            except TimeoutError:
                receipt.update(status='timeout', cancelled=self.pending.cancel() if self.pending is not None else False)
            except Exception as exc:
                receipt.update(status='error', error_type=type(exc).__name__)
            receipt['elapsed_ms'] = round((self.clock()-started)*1000, 3)
            receipt['provider_call_started_at_receipt'] = provider_started.is_set()
            # No response text, credential, order state, cache or failure-state mutation.
            self.record(receipt)
            if self.pending is not None and not self.pending.done():
                return

    def start(self):
        def run():
            while not self.stop_event.is_set():
                try:
                    self.tick()
                except Exception as exc:
                    # Diagnostic storage/lifecycle failure must not stop Main.
                    logging.getLogger(__name__).warning(
                        'AI warmup diagnostic failed: %s', type(exc).__name__)
                self.stop_event.wait(10)
        with self.lifecycle_lock:
            if self.thread is not None or self.stop_event.is_set():
                return
            self.thread = threading.Thread(target=run, daemon=True, name='main-ai-warmup')
            try:
                self.thread.start()
            except Exception:
                self.thread = None
                raise

    def stop(self):
        with self.lifecycle_lock:
            self.stop_event.set()
            self.executor.shutdown(wait=False, cancel_futures=True)
