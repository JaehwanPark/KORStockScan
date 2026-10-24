"""Bounded REG/REMOVE evidence. Caller holds the WS manager state lock.

The official minimal response has no request identity or ordering guarantee.
Only the first response to the sole ever-sent request of its kind/connection
can be attributed. Eviction, timeout and duplicate replies never reset counts.
"""

from collections import deque
from copy import deepcopy


class ControlReceipts:
    def __init__(self):
        self.requests = deque(maxlen=128)
        self.responses = deque(maxlen=128)
        self.epoch = None
        self.counts = {}
        self.response_counts = {}

    def begin(self, packet, *, epoch, now, leases):
        if epoch != self.epoch:
            self.epoch = epoch
            self.counts = {}
            self.response_counts = {}
        kind = packet["trnm"]
        self.counts[kind] = self.counts.get(kind, 0) + 1
        items = sorted(
            {i for row in packet.get("data", ()) for i in row.get("item", ())}
        )
        row = dict(
            local_request_id=f"{epoch}:{kind}:{self.counts[kind]}",
            transport_epoch=epoch,
            trnm=kind,
            group=packet.get("grp_no"),
            items=items,
            realtime_types=sorted(
                {t for r in packet.get("data", ()) for t in r.get("type", ())}
            ),
            lease_ids={i: leases.get(i, {}).get("lease_id") for i in items},
            started_epoch=now,
            send_state="sending",
            broker_ack_observed=None,
            broker_result="unobserved",
        )
        self.requests.append(row)
        return row

    def finish(self, row, *, now, error=None):
        row.update(send_state="uncertain" if error else "sent", send_finished_epoch=now)
        if error:
            row["send_error_type"] = type(error).__name__

    def receive(self, frame, *, epoch, now):
        kind = frame["trnm"]
        if self.epoch is None or epoch > self.epoch:
            self.epoch, self.counts, self.response_counts = epoch, {}, {}
        same = epoch == self.epoch
        count = self.response_counts.get(kind, 0) + 1 if same else None
        if same:
            self.response_counts[kind] = count
        code = frame.get("return_code")
        valid = type(code) is int or (
            isinstance(code, str) and code.isascii() and code.isdigit()
        )
        result = (
            "success"
            if valid and int(code) == 0
            else "rejected" if valid else "invalid_response"
        )
        candidates = [
            r
            for r in self.requests
            if r["transport_epoch"] == epoch and r["trnm"] == kind
        ]
        unique = (
            same
            and self.counts.get(kind) == 1
            and count == 1
            and len(candidates) == 1
            and now >= candidates[0]["started_epoch"]
            and valid
        )
        row = dict(
            trnm=kind,
            transport_epoch=epoch,
            received_epoch=now,
            return_code=code if valid else None,
            raw_return_code=str(code)[:64],
            return_msg=str(frame.get("return_msg") or "")[:512],
            broker_result=result,
            attribution="sole_connection_request" if unique else "unknown",
            local_request_id=candidates[0]["local_request_id"] if unique else None,
            connection_request_count=self.counts.get(kind) if same else None,
            connection_response_count=count,
        )
        self.responses.append(row)
        if unique:
            candidates[0].update(
                broker_ack_observed=True, broker_result=result, response=deepcopy(row)
            )
        return deepcopy(row)

    def projection(self, *, item, epoch, lease_id=None, kind="REG"):
        matches = [
            r
            for r in self.requests
            if r["transport_epoch"] == epoch
            and r["trnm"] == kind
            and item in r["items"]
            and (lease_id is None or r["lease_ids"].get(item) == lease_id)
        ]
        request = matches[-1] if matches else None
        responses = [
            r
            for r in self.responses
            if r["transport_epoch"] == epoch
            and r["trnm"] == kind
            and (request is None or r["received_epoch"] >= request["started_epoch"])
        ]
        return deepcopy(
            dict(
                schema="ws_control_evidence_v1",
                request=request,
                broker_ack_observed=(
                    request.get("broker_ack_observed") if request else None
                ),
                broker_result=(
                    request.get("broker_result", "unobserved")
                    if request
                    else "unobserved"
                ),
                connection_responses=responses[-4:],
                attribution="request_identity_or_unknown",
                response_scope="connection_not_item_unless_bound",
                order_authority=False,
            )
        )

    def snapshot(self):
        """Keep connection evidence after REMOVE has discarded the item registry."""
        return deepcopy(
            dict(
                schema="ws_connection_control_evidence_v1",
                transport_epoch=self.epoch,
                request_counts=self.counts,
                response_counts=self.response_counts,
                requests=list(self.requests)[-16:],
                responses=list(self.responses)[-16:],
                retained_request_limit=16,
                retained_response_limit=16,
                attribution="request_identity_or_unknown",
                order_authority=False,
            )
        )
