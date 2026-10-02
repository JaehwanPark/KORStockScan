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
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='ai-warmup-http')
        self.pending = None
        self.thread = None

    def note_activity(self, client):
        with self.lock:
            self.last_activity[id(client)] = self.clock()

    def tick(self):
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
            try:
                self.pending = self.executor.submit(
                    client.responses.create, model='gpt-5.4-nano',
                    instructions='This is a transport warmup diagnostic. Return only OK. Never make a trading decision.',
                    input='Return OK.', store=False, max_output_tokens=16,
                    reasoning={'effort': 'none'}, timeout=5,
                    metadata={'endpoint_name': 'transport_warmup_diagnostic', 'order_authority': 'none'},
                )
                response = self.pending.result(timeout=5)
                usage = getattr(response, 'usage', None)
                receipt.update(status='completed' if response.status == 'completed' and response.output_text.strip() == 'OK' else 'unexpected_response',
                    input_tokens=getattr(usage, 'input_tokens', None),
                    output_tokens=getattr(usage, 'output_tokens', None))
            except TimeoutError:
                receipt.update(status='timeout', cancelled=self.pending.cancel())
            except Exception as exc:
                receipt.update(status='error', error_type=type(exc).__name__)
            receipt['elapsed_ms'] = round((self.clock()-started)*1000, 3)
            # No response text, credential, order state, cache or failure-state mutation.
            self.record(receipt)
            if self.pending is not None and not self.pending.done():
                return

    def start(self):
        if self.thread is not None:
            return
        def run():
            while not self.stop_event.is_set():
                try:
                    self.tick()
                except Exception as exc:
                    # Diagnostic storage/lifecycle failure must not stop Main.
                    logging.getLogger(__name__).warning(
                        'AI warmup diagnostic failed: %s', type(exc).__name__)
                self.stop_event.wait(10)
        self.thread = threading.Thread(target=run, daemon=True, name='main-ai-warmup')
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.executor.shutdown(wait=False, cancel_futures=True)
