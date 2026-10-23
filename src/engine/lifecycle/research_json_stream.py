"""Stream a producer-sealed legacy JSON projection without a resident census.

This lifecycle adapter understands JSON structure, not broker/API semantics.
Only the original producer's byte-bound dependency receipt grants provenance.
Large timelines become content-addressed normalized events in a private root.
"""
import hashlib
import json
from pathlib import Path
from contextlib import nullcontext, contextmanager
from .research_input_budget import Claim
from . import research_storage as storage
from src.engine.scalping.universal_trailing_replay import decode_quote, ObservationCoverage


@contextmanager
def hashed_text_source(path):
    """Hash original physical bytes during the consumer's sole semantic read."""
    import io
    import gzip
    digest = hashlib.sha256()

    class HashingRaw(io.RawIOBase):
        def readable(self):
            return True

        def readinto(self, target):
            size = raw.readinto(target)
            if size:
                digest.update(memoryview(target)[:size])
            return size

    with Path(path).open('rb', buffering=0) as raw, io.BufferedReader(HashingRaw()) as physical:
        decoded = gzip.GzipFile(fileobj=physical) if Path(path).suffix == '.gz' else physical
        with io.TextIOWrapper(decoded, encoding='utf-8', errors='replace') as text:
            yield text, digest

TRADE_FIELDS=frozenset(('id','record_id','strategy','stock_code','code','status',
    'main_automatic_management_allowed','first_buy_at_epoch','buy_fill_quantity','buy_filled_qty','buy_fill_amount',
    'trailing_replay_cost_model','actual_cost_reconciliation','entry_quote_route','entry_quote_item',
    'trailing_observation_source_gap','holding_ai_required','holding_vote_source','holding_ai_policy_sha256','trailing_entry_context','trailing_situation_pin',
    'rec_date','completion_observed_date','entry_mode','terminal_population_scope',
    'prior_entry_snapshot_receipt','prior_fill_snapshot_receipts','sell_quantity_conserved',
    'terminal_profit_rate_reconciled','realized_pnl_krw_source','realized_pnl_krw',
    'broker_actual_cost_observed','broker_actual_fees_taxes_krw','profit_rate',
    'strict_completion_status','strict_completion_reasons','exact_sell_fill_time',
    'position_residual_qty','terminal_decision_authority','sell_time_forbidden_for_intraday_horizon'))


def resident_completed_rows(trades,output_root):
    """The census writer projects its resident rows before discarding them.

    This is the same structural projection as completed_rows, with no source
    file serialization/readback. Timelines and complete fill sets become
    independently verified immutable trees at their native production time.
    """
    from src.engine.scalping.holding_path_vote_replay import compact_signal
    for original in trades:
        if not isinstance(original,dict):
            raise ValueError('research_native_completed_row_invalid')
        body={};quotes=None;signals=[];signal_bytes=0
        coverage=ObservationCoverage()
        def bounded(value,limit):
            try:
                raw=storage.encoded(value)
            except ValueError:
                # Legacy native snapshot JSON can contain IEEE nonfinite
                # diagnostic values. Preserve them as missing, never as zero
                # or observed fees/PnL; original bytes remain in provenance.
                import math
                def missing(item):
                    if isinstance(item,float) and not math.isfinite(item):return None
                    if isinstance(item,dict):return {key:missing(child) for key,child in item.items()}
                    if isinstance(item,list):return [missing(child) for child in item]
                    return item
                value=missing(value);raw=storage.encoded(value)
                body['native_nonfinite_normalization']='missing_not_zero'
            if len(raw)>limit:
                body['projection_source_gap']='normalized_field_unbounded'
                return None
            return value
        for key,value in original.items():
            if key=='timeline':
                def events():
                    nonlocal signal_bytes
                    for event in value:
                        event=bounded(event,2*1024*1024)
                        if event is None:
                            yield dict(kind='SOURCE_GAP',known_at=None,reason='normalized_event_unbounded')
                            continue
                        if not isinstance(event,dict):
                            raise ValueError('research_legacy_timeline_invalid')
                        coverage.observe(event)
                        if event.get('stage')=='holding_path_signal_snapshot':
                            signal=compact_signal(event);signal_bytes+=len(storage.encoded(signal))
                            if signal_bytes<=1024*1024:signals.append(signal)
                            else:
                                signals.clear();body['holding_path_projection_gap']='signal_projection_capacity_exceeded'
                        if event.get('stage')!='scalp_trailing_input_transition':continue
                        fields=event.get('fields') or {};quote=fields.get('universal_trailing_quote')
                        try:quote=decode_quote(quote)
                        except (ValueError,TypeError):
                            body['trailing_observation_source_gap']='trailing_quote_encoding_invalid'
                            quote=None
                        coverage.quote(quote)
                        if isinstance(quote,dict) and quote.get('kind')=='QUOTE':
                            if body.get('holding_vote_source') is None:
                                body['holding_vote_source']=quote.get('holding_vote_source')
                            yield quote
                        for name in ('trailing_entry_context','trailing_situation_pin'):
                            context=fields.get(name)
                            if isinstance(context,str):context=json.loads(context)
                            if context is not None and body.get(name) is None:body[name]=context
                quotes=storage.write_tree(output_root,events());body['timeline']=[]
            elif key in ('buy_fill_legs','sell_fill_legs'):
                body[key+'_ref']=storage.write_tree(output_root,
                    (bounded(leg,storage.RECORD_BYTES) for leg in value))
            elif key in TRADE_FIELDS:
                body[key]=bounded(value,storage.RECORD_BYTES)
        if coverage.gap():body['trailing_observation_source_gap']=coverage.gap()
        body['holding_path_signal_snapshots_ref']=storage.write_tree(output_root,signals)
        yield body,quotes or storage.write_tree(output_root,[])


class Reader:
    def __init__(self,handle,expected_generation=None,*,max_bytes=None,budgeted=True):
        self.max_bytes=max_bytes;self.budgeted=budgeted;self.read_bytes=0
        self.expected_generation=expected_generation;self.source_sha=hashlib.sha256();self.source_size=0
        self.handle=handle;self.buffer='';self.offset=0;self.eof=False
        self.decoder=json.JSONDecoder()
    def fill(self,size=65536):
        self.buffer=self.buffer[self.offset:];self.offset=0
        text=self.handle.read(size)
        if self.max_bytes is not None:
            self.read_bytes+=len(text.encode('utf-8'))
            if self.read_bytes>self.max_bytes:
                raise ValueError('research_json_source_size_exceeded')
        if self.expected_generation is not None:
            raw=text.encode('utf-8');self.source_sha.update(raw);self.source_size+=len(raw)
        self.buffer+=text;self.eof=not text
        return bool(text)
    def peek(self):
        while self.offset==len(self.buffer):
            if not self.fill():return ''
        return self.buffer[self.offset]
    def spaces(self):
        while self.peek() and self.peek() in ' \r\n\t':self.offset+=1
    def take(self,expected):
        self.spaces()
        if self.peek()!=expected:raise ValueError('research_legacy_json_structure_invalid')
        self.offset+=1
    def value(self,limit=2*1024*1024):
        self.spaces()
        with Claim(limit*8) if self.budgeted else nullcontext():
            while True:
                try:
                    value,end=self.decoder.raw_decode(self.buffer,self.offset)
                    # A number at a chunk boundary may have more digits.
                    if not self.eof and isinstance(value,(int,float)) and not isinstance(value,bool):
                        tail=self.buffer[end:]
                        incomplete=(not tail or (tail[0] in '.eE' and
                            not any(char in tail for char in ',]} \r\n\t')))
                        if incomplete and self.fill():continue
                    if len(self.buffer[self.offset:end].encode('utf-8'))>limit:
                        raise ValueError('research_legacy_json_field_partition_required')
                    self.offset=end;return value
                except json.JSONDecodeError:
                    if len(self.buffer)-self.offset>limit:
                        raise ValueError('research_legacy_json_field_partition_required')
                    remaining=len(self.buffer)-self.offset
                    # Geometric refill avoids quadratic re-decoding of a large
                    # single row while keeping the caller's field/source cap.
                    size=min(max(65536,remaining),max(1,limit-remaining+1))
                    if not self.fill(size):raise ValueError('research_legacy_json_incomplete') from None
    def skip(self):
        """Drain irrelevant fields from a receipt-verified producer object."""
        self.spaces();start=self.peek()
        if start not in '{[':
            if start=='"':
                self.offset+=1;escaped=False
                while True:
                    char=self.peek()
                    if not char:raise ValueError('research_legacy_json_incomplete')
                    self.offset+=1
                    if escaped:escaped=False
                    elif char=='\\':escaped=True
                    elif char=='"':return
            while self.peek() and self.peek() not in ',]} \r\n\t':self.offset+=1
            return
        levels=[];quoted=False;escaped=False
        while True:
            char=self.peek()
            if not char:raise ValueError('research_legacy_json_incomplete')
            self.offset+=1
            if quoted:
                if escaped:escaped=False
                elif char=='\\':escaped=True
                elif char=='"':quoted=False
            elif char=='"':quoted=True
            elif char in '{[':levels.append(char)
            elif char in '}]':
                if not levels or (levels.pop(),char) not in (('{','}'),('[',']')):
                    raise ValueError('research_legacy_json_structure_invalid')
                if not levels:return
    def array(self,project):
        self.take('[');first=True
        while True:
            self.spaces()
            if self.peek()==']':self.offset+=1;return
            if not first:self.take(',')
            yield project(self);first=False
    def fields(self,visit,*,max_fields=256):
        self.take('{');first=True;seen=set()
        while True:
            self.spaces()
            if self.peek()=='}':self.offset+=1;return
            if not first:self.take(',')
            key=self.value(1024)
            if not isinstance(key,str) or key in seen:raise ValueError('research_legacy_json_field_invalid')
            seen.add(key)
            if max_fields is not None and len(seen)>max_fields:raise ValueError('research_legacy_json_field_budget_invalid')
            self.take(':');yield from visit(key,self);first=False
    def finish(self):
        self.spaces()
        if self.peek():raise ValueError('research_json_trailing_data')

    def string_stream(self):
        """Decode one JSON string in bounded chunks for a nested native JSON owner."""
        self.take('"')
        def chunks():
            chunk=[]
            escapes={'"':'"', '\\':'\\', '/':'/', 'b':'\b', 'f':'\f', 'n':'\n', 'r':'\r', 't':'\t'}
            while True:
                char=self.peek()
                if not char or ord(char)<32:raise ValueError('research_json_string_invalid')
                self.offset+=1
                if char=='"':
                    if chunk:yield ''.join(chunk)
                    return
                if char=='\\':
                    escape=self.peek();self.offset+=1
                    if escape=='u':
                        digits=''
                        for _ in range(4):
                            digit=self.peek()
                            if not digit or digit not in '0123456789abcdefABCDEF':raise ValueError('research_json_escape_invalid')
                            self.offset+=1;digits+=digit
                        char=chr(int(digits,16))
                    elif escape in escapes:char=escapes[escape]
                    else:raise ValueError('research_json_escape_invalid')
                chunk.append(char)
                if len(chunk)>=8192:
                    yield ''.join(chunk);chunk=[]
        class Stream:
            def __init__(self):self.parts=chunks();self.pending='';self.done=False
            def read(self,size):
                result=[];remaining=size
                while remaining:
                    if not self.pending:
                        if self.done:break
                        self.pending=next(self.parts,'')
                        if not self.pending:self.done=True;break
                    result.append(self.pending[:remaining])
                    used=min(remaining,len(self.pending));remaining-=used;self.pending=self.pending[used:]
                return ''.join(result)
        return Stream()

    def discard(self):
        """Validate unused JSON without retaining its arrays or strings."""
        # Most discarded rows are small: let the C decoder validate a bounded
        # value rather than walking each scalar/string character in Python.
        try:
            self.value(65536)
            return
        except ValueError as exc:
            if str(exc) != 'research_legacy_json_field_partition_required':raise
        self.spaces();char=self.peek()
        if char=='{':
            def field(key,r):
                r.discard()
                return ()
            for _ in self.fields(field,max_fields=None):pass
        elif char=='[':
            for _ in self.array(lambda r:r.discard()):pass
        elif char=='"':
            self.offset+=1
            while True:
                char=self.peek()
                if not char or ord(char)<32:raise ValueError('research_json_string_invalid')
                self.offset+=1
                if char=='"':return
                if char=='\\':
                    escape=self.peek();self.offset+=1
                    if not escape or escape not in '"\\/bfnrtu':raise ValueError('research_json_escape_invalid')
                    if escape=='u':
                        for _ in range(4):
                            digit=self.peek()
                            if not digit or digit not in '0123456789abcdefABCDEF':raise ValueError('research_json_escape_invalid')
                            self.offset+=1
        else:self.value()

    def target(self,pointer,project):
        found=[False]
        def visit(key,reader):
            if key!=pointer[0]:reader.skip();return
            found[0]=True
            if len(pointer)==1:yield from reader.array(project)
            else:yield from reader.target(pointer[1:],project)
        yield from self.fields(visit)
        if not found[0]:raise ValueError('research_legacy_json_target_missing')


def completed_rows(path,output_root,*,expected_generation=None):
    """Yield original trade metadata and a separate complete quote path ref."""
    def trade(reader):
        body={};reference=None
        coverage=ObservationCoverage()
        signals=[];signal_bytes=0
        def bounded(r,limit):
            try:return r.value(limit)
            except ValueError as exc:
                if str(exc)!='research_legacy_json_field_partition_required':raise
                # The complete object boundary is drained; the identifiable
                # trade remains visible as a gap instead of losing later rows.
                r.skip();body['projection_source_gap']='normalized_field_unbounded'
                return None
        def field(key,r):
            nonlocal reference,signal_bytes
            if key=='timeline':
                def projected():
                    nonlocal signal_bytes
                    for event in r.array(lambda r:bounded(r,2*1024*1024)):
                        if event is None:
                            yield dict(kind='SOURCE_GAP',known_at=None,reason='normalized_event_unbounded')
                            continue
                        if not isinstance(event,dict):raise ValueError('research_legacy_timeline_invalid')
                        coverage.observe(event)
                        if event.get('stage')=='holding_path_signal_snapshot':
                            from src.engine.scalping.holding_path_vote_replay import compact_signal
                            signal=compact_signal(event)
                            signal_bytes+=len(storage.encoded(signal))
                            if signal_bytes<=1024*1024:
                                signals.append(signal)
                            else:
                                signals.clear()
                                body['holding_path_projection_gap']='signal_projection_capacity_exceeded'
                        if event.get('stage')!='scalp_trailing_input_transition':continue
                        fields=event.get('fields') or {};quote=fields.get('universal_trailing_quote')
                        try:quote=decode_quote(quote)
                        except (ValueError,TypeError):
                            body['trailing_observation_source_gap']='trailing_quote_encoding_invalid'
                            quote=None
                        coverage.quote(quote)
                        if isinstance(quote,dict) and quote.get('kind')=='QUOTE':
                            if body.get('holding_vote_source') is None:body['holding_vote_source']=quote.get('holding_vote_source')
                            yield quote
                        for name in ('trailing_entry_context','trailing_situation_pin'):
                            context=fields.get(name)
                            if isinstance(context,str):context=json.loads(context)
                            if context is not None and body.get(name) is None:body[name]=context
                reference=storage.write_tree(output_root,projected())
                body['timeline']=[]
            elif key in ('buy_fill_legs','sell_fill_legs'):
                # Keep the original complete fill population outside one
                # resident trade. The assembler consumes every leg causally.
                body[key+'_ref']=storage.write_tree(output_root,r.array(lambda r:bounded(r,storage.RECORD_BYTES)))
            elif key in TRADE_FIELDS:body[key]=bounded(r,storage.RECORD_BYTES)
            else:r.skip()
            return iter(())
        for _ in reader.fields(field):pass
        if coverage.gap():body['trailing_observation_source_gap']=coverage.gap()
        body['holding_path_signal_snapshots_ref']=storage.write_tree(output_root,signals)
        return body,reference or storage.write_tree(output_root,[])
    import gzip
    from .snapshot_archive import logical_path
    logical = logical_path(path)
    path = logical if logical.exists() else Path(str(logical)+'.gz')
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8',newline='') as handle:
        reader=Reader(handle,expected_generation)
        yield from reader.target(('sections','completed_trade_projection'),trade)
        reader.spaces()
        if reader.peek():raise ValueError('research_legacy_json_trailing_content')
        if expected_generation is not None and (
                reader.source_size!=expected_generation.get('size')
                or reader.source_sha.hexdigest()!=expected_generation.get('sha256')):
            raise ValueError('research_legacy_json_logical_generation_changed')


def selected_object(handle, selection):
    """Project named JSON fields while validating every discarded value."""
    reader=Reader(handle,budgeted=False)
    def project(r,fields):
        result={}
        def field(key,child):
            if key not in fields:child.discard()
            elif fields[key] is None:result[key]=child.value(1024*1024*1024)
            else:result[key]=project(child,fields[key])
            return ()
        for _ in r.fields(field,max_fields=None):pass
        return result
    value=project(reader,selection);reader.finish()
    return value


def sealed_sorted_object_projection(handle, fields):
    """Verify a native sorted-JSON content hash while retaining selected fields.

    The producer's complete canonical object, excluding its root sha256, is
    hashed incrementally. Containers never become resident; scalar and selected
    fields keep the existing 64 KiB bound. This is not a new source receipt.
    """
    reader=Reader(handle);digest=hashlib.sha256();projection={};declared=None
    def encoded(value):
        return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii')
    def value(r,depth=0,root=False):
        nonlocal declared
        if depth>64:raise ValueError('research_json_depth_invalid')
        r.spaces();char=r.peek()
        if char=='{':
            digest.update(b'{');previous=None;count=0
            def field(key,child):
                nonlocal previous,count,declared
                if previous is not None and key<=previous:raise ValueError('research_json_canonical_key_order_invalid')
                previous=key
                if root and key=='sha256':declared=child.value(1024);return ()
                if count:digest.update(b',')
                count+=1;digest.update(encoded(key)+b':')
                if root and key in fields:
                    projection[key]=child.value(65536);digest.update(encoded(projection[key]))
                else:value(child,depth+1)
                return ()
            # Runtime rule snapshots use the existing pipeline's 4096-key
            # contract, rather than the small research object's default256.
            for _ in r.fields(field,max_fields=4096):pass
            digest.update(b'}')
        elif char=='[':
            digest.update(b'[');first=True
            def item(child):
                nonlocal first
                if not first:digest.update(b',')
                first=False;value(child,depth+1)
            for _ in r.array(item):pass
            digest.update(b']')
        else:digest.update(encoded(r.value(65536)))
    reader.spaces()
    if reader.peek()!='{':raise ValueError('research_json_sealed_object_required')
    value(reader,root=True);reader.finish()
    if not isinstance(declared,str) or digest.hexdigest()!=declared:
        return None
    return {**projection,'sha256':declared}
