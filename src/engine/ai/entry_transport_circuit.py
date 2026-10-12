"""Entry deadline circuit; recovery consumes one new normal request only.

The AI engine owns provider admission and its common fail-closed switch. This
small state machine cannot call a provider, reset that switch, or renew a signal.
"""
from __future__ import annotations

import threading
import time
import uuid


class EntryTransportCircuit:
    BACKOFF_SECONDS = (30, 60, 120, 240, 300)

    def __init__(self, threshold=5, *, clock=time.monotonic, owner='entry_transport_deadline'):
        self.threshold = threshold
        self.clock = clock
        self.owner = owner
        self._lock = threading.Lock()
        self.state = 'CLOSED'
        self.generation = 0
        self.failures = 0
        self.recovery_failures = 0
        self.next_probe = 0.0
        self.lease = None
        self.reason = None
        self.not_evaluated = 0
        self.futures = []
        self.last_failed_identity = None

    def admit(self, identity, *, eligible, deadline_remaining, common_disabled=False):
        with self._lock:
            self.futures = [f for f in self.futures if not f.done()]
            allowed = not common_disabled and deadline_remaining > 0
            if self.state != 'CLOSED':
                allowed = (allowed and self.state == 'OPEN' and eligible and bool(identity)
                    and identity != self.last_failed_identity and self.clock() >= self.next_probe
                    and not self.futures)
            if not allowed:
                self.not_evaluated += 1
                return None
            ticket = dict(generation=self.generation, token=uuid.uuid4().hex,
                          identity=identity, recovery=self.state == 'OPEN')
            if ticket['recovery']:
                self.state = 'HALF_OPEN'
                self.lease = ticket
            return ticket

    def _current(self, ticket):
        return bool(ticket and ticket['generation'] == self.generation
                    and (not ticket['recovery'] or ticket == self.lease))

    def failed(self, ticket, *, future=None, reason='entry_transport_deadline', retry_after_seconds=0):
        with self._lock:
            if not self._current(ticket):
                return False
            if future is not None and not future.done() and future not in self.futures:
                self.futures.append(future)
            self.failures += 1
            self.reason = reason
            self.last_failed_identity = ticket['identity']
            if ticket['recovery'] or self.failures >= self.threshold:
                if ticket['recovery']:
                    self.recovery_failures += 1
                self.generation += 1
                self.state = 'OPEN'
                self.lease = None
                delay = self.BACKOFF_SECONDS[min(self.recovery_failures, len(self.BACKOFF_SECONDS)-1)]
                self.next_probe = self.clock() + max(delay, retry_after_seconds)
            return True

    def succeeded(self, ticket, *, deadline_remaining, valid_response):
        with self._lock:
            if not self._current(ticket) or deadline_remaining <= 0 or not valid_response:
                return False
            self.state = 'CLOSED'
            self.generation += 1  # Late callbacks cannot close a successor circuit.
            self.failures = self.recovery_failures = 0
            self.lease = None
            self.reason = None
            self.next_probe = 0.0
            return True

    def abandon(self, ticket):
        with self._lock:
            if self._current(ticket) and ticket['recovery']:
                self.state = 'OPEN'
                self.lease = None
                self.generation += 1
                self.next_probe = self.clock() + self.BACKOFF_SECONDS[min(self.recovery_failures, 4)]

    def ordinary_success(self):
        """A normal response resets failures only before a circuit has opened."""
        with self._lock:
            if self.state == 'CLOSED':
                self.failures = self.recovery_failures = 0
                self.generation += 1

    def snapshot(self):
        with self._lock:
            return dict(schema='entry_transport_circuit_v1', state=self.state,
                generation=self.generation, consecutive_failures=self.failures,
                failure_threshold=self.threshold, reason=self.reason,
                recovery_wait_seconds=max(0, self.next_probe-self.clock()),
                recovery_lease_active=self.lease is not None,
                not_evaluated_count=self.not_evaluated,
                unsettled_future_count=sum(not f.done() for f in self.futures),
                failure_owner=self.owner, decision_authority='none')
