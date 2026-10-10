"""External whole-population trailing cohort and numeric metrics.

Each input is an already source-bound minimal replay result. Every candidate
shares one transitive common cohort and one chronological purged split.
Partition-local means/winners have no selection authority.
"""
from datetime import datetime
import json
import math
from zoneinfo import ZoneInfo

from src.engine.lifecycle import research_storage as storage
from src.engine.scalping.universal_trailing_replay import _cohort_day, SLIPPAGE_BPS
from src.engine.scalping.pre_submit_delay_initial_policy import number, digest

EVIDENCE = ('actual_completed','actual_entry_alternative_exit','enter_pass_opportunity_cf')


def aggregate(partitions, *, output_root):
    with storage.index(output_root) as db:
        aliases=None
        for part in partitions():
            if aliases is None: aliases=part['candidate_aliases']
            if aliases!=part['candidate_aliases']: raise ValueError('universal_candidate_generation_changed_between_partitions')
            for identity,context in part['population_context'].items():
                value={'context':context,'outcomes':part['minimal_results'][identity],
                       'common':identity in part['common_ids']}
                value=storage.compact_outcomes(output_root,value)
                storage.put(db,identity,value,content_sha=digest(storage.logical_value(value)))
        if aliases is None: return {'status':'valid_empty','strata':{},'allowed_runtime_apply':False}
        db.execute('CREATE TABLE outcomes(id TEXT,candidate TEXT,body TEXT,PRIMARY KEY(id,candidate)) WITHOUT ROWID')
        from src.engine.lifecycle.research_input_budget import Claim
        for identity,value,_ in storage.records(db):
            with Claim(4096*len(aliases)):
                value=storage.expand_outcomes(output_root,value)
                if set(value['outcomes'])!=set(aliases.values()):
                    raise ValueError('universal_candidate_population_incomplete')
                for candidate,body in value['outcomes'].items():
                    db.execute('INSERT INTO outcomes VALUES (?,?,?)',(identity,candidate,storage.encoded(body).decode()))
        db.execute('CREATE TABLE cohort (id TEXT PRIMARY KEY,evidence TEXT,entry REAL,end REAL,day TEXT,'
                   'verified INTEGER,split TEXT) WITHOUT ROWID')
        for identity,row,_ in storage.records(db):
            if not row['common']: continue
            context=row['context']; evidence=context['evidence_kind']
            if evidence not in EVIDENCE: raise ValueError('universal_population_evidence_invalid')
            day,verified=_cohort_day(context,evidence)
            db.execute('INSERT INTO cohort VALUES (?,?,?,?,?,?,?)',(identity,evidence,context['entry_at'],
                context['observation_end_at'],day,int(verified),'train'))
        db.execute('CREATE INDEX cohort_membership ON cohort(evidence,split,entry,id)')
        strata={}
        for evidence in EVIDENCE:
            days=[d for d, in db.execute('SELECT DISTINCT day FROM cohort WHERE evidence=? ORDER BY day',(evidence,))]
            split=max(1,min(len(days)-1,int(len(days)*.7))) if len(days)>1 else len(days)
            train_days,holdout_days=days[:split],days[split:]
            if holdout_days:
                db.execute("UPDATE cohort SET split='holdout' WHERE evidence=? AND day>=?",(evidence,holdout_days[0]))
                cutoff=db.execute("SELECT min(entry) FROM cohort WHERE evidence=? AND split='holdout'",(evidence,)).fetchone()[0]
                db.execute("UPDATE cohort SET split='purged' WHERE evidence=? AND split='train' AND end>=?",(evidence,cutoff))
            def ids(cohort=None):
                condition='evidence=?'+(' AND split=?' if cohort else '')
                args=(evidence,cohort) if cohort else (evidence,)
                return storage.write_tree(output_root,(i for i, in db.execute(
                    'SELECT id FROM cohort WHERE '+condition+' ORDER BY entry,id',args)))
            qualified=ids();train,held,purged=ids('train'),ids('holdout'),ids('purged')
            verified=not bool(db.execute('SELECT 1 FROM cohort WHERE evidence=? AND verified=0 LIMIT 1',(evidence,)).fetchone())
            metrics={}
            for name,candidate in aliases.items():
                metrics[name]={}
                for cohort,cohort_ref in (('train',train),('holdout',held)):
                    def deltas():
                        for identity,body,candidate_body,parent_body in db.execute(
                            'SELECT c.id,r.body,o.body,p.body FROM cohort c JOIN records r ON r.id=c.id '
                            'JOIN outcomes o ON o.id=c.id AND o.candidate=? '
                            'JOIN outcomes p ON p.id=c.id AND p.candidate=? '
                            'WHERE c.evidence=? AND c.split=? ORDER BY c.entry,c.id',
                            (candidate,aliases['incumbent'],evidence,cohort)):
                            context=json.loads(body)['context']
                            amount=number(context['buy_basis_krw'])
                            if amount is None or amount<=0:
                                raise ValueError('universal_notional_unverified')
                            row,base=json.loads(candidate_body),json.loads(parent_body)
                            reference=max(base['modeled_net_pnl_krw'],row['actual_pnl_krw']) if evidence=='actual_completed' else base['modeled_net_pnl_krw']
                            yield (identity,(row['modeled_net_pnl_krw']-reference)/amount*100,
                                   [(v-reference)/amount*100 for v in row['slippage_net_pnl_krw']])
                    count=cohort_ref['count']
                    mean=math.fsum(v for _,v,_ in deltas())/count if count else None
                    worst=min((v for _,v,_ in deltas()),default=None)
                    adverse=storage.write_tree(output_root,(i for i,v,_ in deltas() if v<0))
                    stress={str(bps):math.fsum(v[n] for _,_,v in deltas())/count if count else None
                            for n,bps in enumerate(SLIPPAGE_BPS)}
                    metrics[name][cohort]={'n':count,'paired_ev_pct':mean,'worst_paired_delta_pct':worst,
                                           'worsened_ids_ref':adverse,'slippage_ev_pct':stress}
            strata[evidence]={'common_ids_ref':qualified,'train_ids_ref':train,'holdout_ids_ref':held,'purged_ids_ref':purged,
                'train_days':train_days,'holdout_days':holdout_days,'metrics':metrics,'completion_date_verified':verified,
                'existing_selector_sample_floor_met':evidence=='actual_completed' and verified and len(days)>=7
                    and train['count']>=30 and held['count']>=10 and len(holdout_days)>=2,
                'candidate_review_required':True,'allowed_runtime_apply':False}
        common=storage.write_tree(output_root,(i for i, in db.execute('SELECT id FROM cohort ORDER BY id')))
        population=storage.write_tree(output_root,(i for i,_,_ in storage.records(db)))
        conflicts=storage.write_tree(output_root,({'identity':i,'reason':'global_population_conflict'}
                                                  for i,_,_ in storage.records(db,conflicts=True)))
        return {'status':'evaluated' if common['count'] else 'source_gap','common_ids_ref':common,'population_ids_ref':population,
            'conflicts_ref':conflicts,'strata':strata,'storage_schema':'main_trailing_sharded_evaluation_v2',
            'decision_authority':'research_only_existing_selector_review_required','allowed_runtime_apply':False}
