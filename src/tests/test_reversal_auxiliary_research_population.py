from collections import defaultdict
from src.engine.scalping import reversal_auxiliary_research_population as R


def test_reuse_only_exact_unchanged_branch_membership():
    bid=next(iter(R.C.OLD.DEFINITIONS));extra=next(iter(R.C.NEW_DEFINITIONS))
    old={'scopes':{'same':[bid],'changed':[bid]}}
    new={'scopes':{'same':[bid],'changed':[bid,extra]}}
    assert R.unchanged_scopes(old,new)=={'same'}


def test_reservoir_is_bounded_and_win_fail_blind():
    first=defaultdict(dict);second=defaultdict(dict)
    for i in range(100):
        p=dict(opportunity_key=str(i),scope='scope',outcome={'status':'WIN'})
        R.select(first,p,None,seed='fixed',limit=6)
        p['outcome']={'status':'FAIL_STOP'}
        R.select(second,p,None,seed='fixed',limit=6)
    assert len(first['scope'])==6
    assert set(first['scope'])==set(second['scope'])
