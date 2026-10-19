"""Stream a producer-sealed legacy JSON projection without a resident census.

This lifecycle adapter understands JSON structure, not broker/API semantics.
Only the original producer's byte-bound dependency receipt grants provenance.
Large timelines become content-addressed normalized events in a private root.
"""
import json
from pathlib import Path
from .research_input_budget import Claim
from . import research_storage as storage

TRADE_FIELDS=frozenset(('id','record_id','strategy','stock_code','code','status',
    'main_automatic_management_allowed','first_buy_at_epoch','buy_fill_quantity','buy_filled_qty','buy_fill_amount',
    'trailing_replay_cost_model','actual_cost_reconciliation','entry_quote_route','entry_quote_item',
    'holding_ai_required','holding_vote_source','holding_ai_policy_sha256','trailing_entry_context','trailing_situation_pin',
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
                        if event.get('stage')=='holding_path_signal_snapshot':
                            signal=compact_signal(event);signal_bytes+=len(storage.encoded(signal))
                            if signal_bytes<=1024*1024:signals.append(signal)
                            else:
                                signals.clear();body['holding_path_projection_gap']='signal_projection_capacity_exceeded'
                        if event.get('stage')!='scalp_trailing_input_transition':continue
                        fields=event.get('fields') or {};quote=fields.get('universal_trailing_quote')
                        if isinstance(quote,str):quote=json.loads(quote)
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
        body['holding_path_signal_snapshots_ref']=storage.write_tree(output_root,signals)
        yield body,quotes or storage.write_tree(output_root,[])


class Reader:
    def __init__(self,handle):
        self.handle=handle;self.buffer='';self.offset=0;self.eof=False
        self.decoder=json.JSONDecoder()
    def fill(self):
        self.buffer=self.buffer[self.offset:];self.offset=0
        text=self.handle.read(65536);self.buffer+=text;self.eof=not text
        return bool(text)
    def peek(self):
        while self.offset==len(self.buffer):
            if not self.fill():return ''
        return self.buffer[self.offset]
    def spaces(self):
        while self.peek() and self.peek().isspace():self.offset+=1
    def take(self,expected):
        self.spaces()
        if self.peek()!=expected:raise ValueError('research_legacy_json_structure_invalid')
        self.offset+=1
    def value(self,limit=2*1024*1024):
        self.spaces()
        with Claim(limit*8):
            while True:
                try:
                    value,end=self.decoder.raw_decode(self.buffer,self.offset)
                    # A number at a chunk boundary may have more digits.
                    if end==len(self.buffer) and not self.eof and isinstance(value,(int,float)):
                        if self.fill():continue
                    if len(self.buffer[self.offset:end].encode('utf-8'))>limit:
                        raise ValueError('research_legacy_json_field_partition_required')
                    self.offset=end;return value
                except json.JSONDecodeError:
                    if len(self.buffer)-self.offset>limit:
                        raise ValueError('research_legacy_json_field_partition_required')
                    if not self.fill():raise ValueError('research_legacy_json_incomplete') from None
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
    def fields(self,visit):
        self.take('{');first=True;seen=set()
        while True:
            self.spaces()
            if self.peek()=='}':self.offset+=1;return
            if not first:self.take(',')
            key=self.value(1024)
            if not isinstance(key,str) or key in seen:raise ValueError('research_legacy_json_field_invalid')
            seen.add(key)
            if len(seen)>256:raise ValueError('research_legacy_json_field_budget_invalid')
            self.take(':');yield from visit(key,self);first=False
    def target(self,pointer,project):
        found=[False]
        def visit(key,reader):
            if key!=pointer[0]:reader.skip();return
            found[0]=True
            if len(pointer)==1:yield from reader.array(project)
            else:yield from reader.target(pointer[1:],project)
        yield from self.fields(visit)
        if not found[0]:raise ValueError('research_legacy_json_target_missing')


def completed_rows(path,output_root):
    """Yield original trade metadata and a separate complete quote path ref."""
    def trade(reader):
        body={};reference=None
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
                        if isinstance(quote,str):quote=json.loads(quote)
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
        body['holding_path_signal_snapshots_ref']=storage.write_tree(output_root,signals)
        return body,reference or storage.write_tree(output_root,[])
    import gzip
    from .snapshot_archive import logical_path
    logical = logical_path(path)
    path = logical if logical.exists() else Path(str(logical)+'.gz')
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        reader=Reader(handle)
        yield from reader.target(('sections','completed_trade_projection'),trade)
        reader.spaces()
        if reader.peek():raise ValueError('research_legacy_json_trailing_content')
