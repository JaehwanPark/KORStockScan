"""Validate oversized mixed events with bounded memory before scope isolation.

Only declared entry-plan stages are disjoint from stop inputs. The entire JSON
record is checked; a stage-looking substring or an incomplete record is never
an exclusion receipt. This adapter does not collect or alter source data.
"""
import re

from src.engine.lifecycle.research_json_stream import Reader

# _emit_scalp_entry_adm_snapshot is the native entry diagnostic owner;
# its complete fields object is still validated and checked for stop inputs.
DISJOINT_STAGES = frozenset({"entry_ai_economic_plan_observed", "entry_ai_economic_source_gap",
                            "scalp_entry_action_decision_snapshot"})
STOP_FIELDS = frozenset({"main_stop_source", "main_stop_handoff_source", "main_stop_release_source"})
SPOOL_LIMIT = 128 * 1024 * 1024
ACTIVE_KEY_BYTES_LIMIT = 64 * 1024
_SPECIAL = re.compile(r'["\\\x00-\x1f]')
_PRIMITIVE_END = re.compile(r'[,}\] \r\n\t]')
_HEX = frozenset("0123456789abcdefABCDEF")


class ProjectionReader(Reader):
    def __init__(self, handle, checkpoint):
        super().__init__(handle)
        self.checkpoint = checkpoint
        self.active_key_bytes = 0

    def fill(self):
        self.checkpoint()
        return super().fill()

    def spaces(self):
        # str.isspace() also accepts non-JSON whitespace such as NBSP/VT.
        # Exclusion requires a valid complete JSON record, not lenient syntax.
        while self.peek() and self.peek() in ' \r\n\t':
            self.offset += 1

    def fields(self, visit):
        """Bound native wide entry fields by bytes as well as object keys.

        The shared lifecycle reader's 256-key projection cap predates these
        producer snapshots (455-497 keys). Keep a strict shared memory budget
        across this object and every nested skipped object.
        """
        self.take('{')
        first, seen, held_key_bytes = True, set(), 0
        try:
            while True:
                self.spaces()
                if self.peek() == '}':
                    self.offset += 1
                    return
                if not first:
                    self.take(',')
                key = self.value(1024)
                if not isinstance(key, str) or key in seen or len(seen) >= 1024:
                    raise ValueError('stop_projection_object_key')
                size = len(key.encode('utf-8'))
                if self.active_key_bytes + size > ACTIVE_KEY_BYTES_LIMIT:
                    raise ValueError('stop_projection_active_key_budget')
                seen.add(key)
                self.active_key_bytes += size
                held_key_bytes += size
                self.take(':')
                yield from visit(key, self)
                first = False
        finally:
            self.active_key_bytes -= held_key_bytes

    def string(self):
        self.take('"')
        while True:
            if not self.peek():
                raise ValueError("stop_projection_incomplete_string")
            found = _SPECIAL.search(self.buffer, self.offset)
            if found is None:
                self.offset = len(self.buffer)
                continue
            self.offset = found.start() + 1
            char = found.group()
            if char == '"':
                return
            if char != '\\':
                raise ValueError("stop_projection_string_control")
            escaped = self.peek()
            if not escaped:
                raise ValueError("stop_projection_incomplete_escape")
            self.offset += 1
            if escaped == 'u':
                for _ in range(4):
                    if self.peek() not in _HEX:
                        raise ValueError("stop_projection_unicode_escape")
                    self.offset += 1
            elif escaped not in '"\\/bfnrt':
                raise ValueError("stop_projection_invalid_escape")

    def primitive(self):
        # raw_decode may accept the integer prefix of a number when a refill
        # ends after '.'/'e'. Collect the bounded complete token first.
        token = ''
        while self.peek():
            found = _PRIMITIVE_END.search(self.buffer, self.offset)
            end = found.start() if found else len(self.buffer)
            fragment = self.buffer[self.offset:end]
            if len(token) + len(fragment) > 4096:
                raise ValueError('stop_projection_primitive_budget')
            token += fragment
            self.offset = end
            if found:
                break
        value, end = self.decoder.raw_decode(token)
        if end != len(token) or isinstance(value, (dict, list, str)):
            raise ValueError('stop_projection_primitive')
        if isinstance(value, float):
            import math
            if not math.isfinite(value):
                raise ValueError('stop_projection_nonfinite')

    def checked_skip(self, depth=0):
        if depth > 64:
            raise ValueError("stop_projection_depth")
        self.spaces()
        char = self.peek()
        if char == '"':
            self.string()
            return
        if char == '{':
            self.offset += 1
            first, seen, held_key_bytes = True, set(), 0
            try:
                while True:
                    self.spaces()
                    if self.peek() == '}':
                        self.offset += 1
                        return
                    if not first:
                        self.take(',')
                    key = self.value(4096)
                    if not isinstance(key, str) or key in seen or len(seen) >= 1024:
                        raise ValueError("stop_projection_object_key")
                    size = len(key.encode('utf-8'))
                    if self.active_key_bytes + size > ACTIVE_KEY_BYTES_LIMIT:
                        raise ValueError("stop_projection_active_key_budget")
                    seen.add(key)
                    self.active_key_bytes += size
                    held_key_bytes += size
                    self.take(':')
                    self.checked_skip(depth + 1)
                    first = False
            finally:
                self.active_key_bytes -= held_key_bytes
        elif char == '[':
            self.offset += 1
            first = True
            while True:
                self.spaces()
                if self.peek() == ']':
                    self.offset += 1
                    return
                if not first:
                    self.take(',')
                self.checked_skip(depth + 1)
                first = False
        else:
            self.primitive()


def classify_disjoint_event(handle, *, checkpoint=lambda: None):
    """Return a proven disjoint stage, or None; malformed JSON raises."""
    reader = ProjectionReader(handle, checkpoint)
    stage, stop_field_present = None, False

    def field(key, stream):
        nonlocal stop_field_present
        if key in STOP_FIELDS:
            stop_field_present = True
        stream.checked_skip()
        return iter(())

    def top(key, stream):
        nonlocal stage, stop_field_present
        if key in STOP_FIELDS:
            stop_field_present = True
        if key == 'stage':
            stage = stream.value(4096)
            if not isinstance(stage, str):
                raise ValueError("stop_projection_stage")
        elif key == 'fields':
            yield from stream.fields(field)
        else:
            stream.checked_skip()

    for _ in reader.fields(top):
        pass
    reader.spaces()
    if reader.peek():
        raise ValueError("stop_projection_trailing_data")
    return stage if stage in DISJOINT_STAGES and not stop_field_present else None
