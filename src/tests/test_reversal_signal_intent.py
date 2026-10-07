"""Durable Main signal claims retain one parent with the existing split legs."""
from concurrent.futures import ThreadPoolExecutor
import json
import pytest
from src.engine.scalping.initial_quantity_bundle_state import reserve_reversal_signal


def test_competing_provider_requests_have_one_durable_winner(tmp_path):
    def reserve(i):
        try:
            reserve_reversal_signal(tmp_path,signal_id='day:SOR:005930:epoch:42',stage='provider_request',
                                    identity=str(i),binding={'phase':'CONFIRMED_UPTICK'})
            return True
        except ValueError:return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve,range(16)))==1
    journal=json.loads(next(tmp_path.glob('*.json')).read_text())
    assert len(journal['stages'])==1
    # New process/generation cannot request another answer on the same tick.
    with pytest.raises(ValueError,match='already_reserved'):
        reserve_reversal_signal(tmp_path,signal_id='day:SOR:005930:epoch:42',stage='provider_request',
                                identity='new-generation',binding={'phase':'FIRST_UPTICK'})


def test_parent_retry_keeps_identity_and_rejects_new_parent(tmp_path):
    kw=dict(signal_id='signal',stage='parent_entry',identity='attempt-one',binding={'target_id':'target','code':'005930'})
    one=reserve_reversal_signal(tmp_path,**kw)
    assert reserve_reversal_signal(tmp_path,**kw)==one
    with pytest.raises(ValueError,match='already_reserved'):
        reserve_reversal_signal(tmp_path,**dict(kw,identity='attempt-two'))
