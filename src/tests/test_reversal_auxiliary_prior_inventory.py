"""Prior exposure includes imported, superseded and uncertain attempts."""
import sqlite3
from src.engine.scalping import reversal_auxiliary_research as Q


def test_inventory_reads_both_response_locations_and_keeps_uncertainty(monkeypatch):
    db=sqlite3.connect(':memory:')
    db.executescript('''
      CREATE TABLE strings(id INTEGER,value TEXT);
      CREATE TABLE members(id INTEGER,opportunity INTEGER,request_id INTEGER);
      CREATE TABLE partition_members(partition_id INTEGER,member_id INTEGER);
      CREATE TABLE generation_parts(generation TEXT,partition_id INTEGER);
      CREATE TABLE generations(generation TEXT,descriptor_obj INTEGER);
      CREATE TABLE attempts(attempt TEXT,request_id INTEGER,created REAL,state TEXT,source TEXT,result_obj INTEGER);
      CREATE TABLE attempt_responses(attempt TEXT,result_obj INTEGER);
    ''')
    cases=[('imported',1,1),('response-table',2,None),('uncertain',3,None),
           ('future',4,1),('excluded-generation',5,1),('other-provider',6,3)]
    for i,(key,rid,obj) in enumerate(cases,1):
        db.execute('INSERT INTO strings VALUES(?,?)',(i,key))
        db.execute('INSERT INTO members VALUES(?,?,?)',(i,i,rid))
        db.execute('INSERT INTO partition_members VALUES(?,?)',(i,i))
        db.execute('INSERT INTO generation_parts VALUES(?,?)',('g'+str(i),i))
        db.execute('INSERT INTO generations VALUES(?,?)',('g'+str(i),10))
        db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?)',('a'+str(i),rid,200. if key=='future' else 0.,'reserved' if key=='uncertain' else 'completed','legacy' if key=='imported' else 'provider',obj))
    db.execute('INSERT INTO attempt_responses VALUES(?,?)',('a2',2))
    objects={1:dict(result=dict(provider_provenance=dict(provider='openai',response_id='imported-id',provider_none=False))),
             2:dict(result=dict(provider_provenance=dict(provider='openai',response_id='landed-id',provider_none=False))),
             3:dict(result=dict(provider_provenance=dict(provider='other',response_id='other-id',provider_none=False))),
             10:dict(schema='historical_descriptor')}
    class Store:
        def __init__(self,*args,**kw):assert kw=={'readonly':True};self.db=db
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def get(self,obj):return objects[obj]
    monkeypatch.setattr(Q.S,'Store',Store)
    value=Q.prior_attempt_inventory('/unused',[r[0] for r in cases],before_epoch=100.,exclude_generations=['g5'])
    assert set(value['blocked_source_keys'])=={'imported','response-table','uncertain','other-provider'}
    assert value['classifications']['imported']==['actual_response']
    assert value['classifications']['response-table']==['actual_response']
    assert value['classifications']['other-provider']==['actual_response']
    assert value['classifications']['uncertain']==['uncertain_prior_attempt']
    assert value['unknown_counts_as_exposed'] is True
