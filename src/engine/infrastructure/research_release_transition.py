"""Durable CAS publication set for reviewed research/release handoffs.

Prepared bytes and original bytes are immutable snapshots. Existing release
set/selection locks precede family locks. Unknown successor writes are never
rolled back. This module has no order, restart or policy-selection authority.
"""
from contextlib import contextmanager,ExitStack
from contextvars import ContextVar
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import re

from src.engine.lifecycle.research_admission import start_ticks

SCHEMA='research_release_transition_v1'
ENV='KORSTOCKSCAN_RESEARCH_RELEASE_TRANSITION'
_OWNED=ContextVar('research_release_transition',default=None)
_JOURNAL=ContextVar('research_release_write_journal',default=None)


def journal_json(path,value,**formatting):
    if _JOURNAL.get() is None:return False
    return journal_write(path,json.dumps(value,**formatting).encode('utf-8'))


def journal_active():return _JOURNAL.get() is not None


def journal_write(path,raw):
    """Explicit metadata writers participate only in the owning transition.

    There is no global rename interception or environment-only delegation.
    Source, broker, journal and other unlisted paths cannot be written here.
    """
    transaction=_JOURNAL.get()
    if transaction is None:return False
    candidate=Path(path).resolve()
    # Disposable research scratch/cache is not a committed pointer. Its owner
    # deletes it; recording it would make every successful cleanup look like
    # a later unknown writer. Durable family/report leaves remain journaled.
    if candidate.is_relative_to(transaction.data) and any(part.startswith('.') for part in candidate.relative_to(transaction.data).parts):
        return False
    transaction.write(path,raw)
    return True


def sha(raw):return hashlib.sha256(raw).hexdigest() if raw is not None else None


def _write(path,raw):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('transition_path_invalid')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        if path.exists():os.fchmod(fd,path.stat().st_mode & 0o777)
        with os.fdopen(fd,'wb') as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
        descriptor=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    finally:Path(name).unlink(missing_ok=True)


def _read(path):
    if path.exists() and path.stat().st_size>4*1024*1024:raise ValueError('transition_pointer_budget_invalid')
    return path.read_bytes() if path.exists() else None


def _record(path):
    value=json.loads(_read(path))
    expected=sha(json.dumps({k:v for k,v in value.items() if k!='manifest_sha256'},sort_keys=True,separators=(',',':')).encode())
    if value.get('schema')!=SCHEMA or value.get('manifest_sha256')!=expected:
        raise ValueError('transition_record_invalid')
    return value


def assert_readable(data_root):
    path=Path(data_root).resolve()/'runtime/research_release_transition/current.json'
    if not path.exists():return
    value=_record(path)
    if value.get('state')!='publishing':return
    if _OWNED.get()==value.get('transition_id'):return
    try:
        proof=json.loads(os.environ.get(ENV,'{}'));pid=proof['parent_pid'];fd=proof['fd']
        if (proof['transition_id']!=value['transition_id'] or pid!=os.getppid()
            or start_ticks(pid)!=proof['parent_start_ticks'] or pid!=value['owner_pid']
            or Path(proof['lock_path'])!=Path(data_root).resolve()/'runtime/runtime_release_set.lock'):
            raise ValueError('transition_reader_owner_invalid')
        actual=os.fstat(fd);original=Path(f'/proc/{pid}/fd/{fd}').stat();disk=Path(proof['lock_path']).stat()
        if (actual.st_dev,actual.st_ino)!=(original.st_dev,original.st_ino) or (actual.st_dev,actual.st_ino)!=(disk.st_dev,disk.st_ino):
            raise ValueError('transition_reader_fd_invalid')
        with Path(proof['lock_path']).open('a+b') as probe:
            try:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:return
        raise ValueError('transition_reader_lock_not_held')
    except (ValueError,OSError,KeyError,TypeError):
        raise ValueError('research_release_transition_incomplete') from None


class Transition:
    def __init__(self,workspace,identity):
        if not isinstance(identity,str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}',identity):
            raise ValueError('transition_identity_invalid')
        self.workspace=Path(workspace).resolve();self.data=self.workspace/'data'
        self.directory=self.data/'runtime/research_release_transition'/identity
        self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'transition.json';self.current=self.directory.parent/'current.json'
        self.value={'schema':SCHEMA,'transition_id':identity,'state':'prepared','entries':[],'written':[]}
        if self.path.exists():self.value=_record(self.path)
    def _save(self):
        if self.current.exists():
            previous=_record(self.current)
            if previous.get('state')=='publishing' and previous.get('transition_id')!=self.value['transition_id']:
                raise ValueError('transition_other_publication_incomplete')
        self.value.pop('manifest_sha256',None)
        self.value['manifest_sha256']=sha(json.dumps(self.value,sort_keys=True,separators=(',',':')).encode())
        raw=json.dumps(self.value,sort_keys=True,separators=(',',':')).encode();_write(self.path,raw);_write(self.current,raw)
    def add(self,path,raw):
        if self.value['state']!='prepared':raise ValueError('transition_not_prepared')
        path=Path(path).resolve()
        if not any(path.is_relative_to(self.workspace/prefix) for prefix in (
            'data/runtime','data/threshold_cycle','data/report','data/pipeline_event_summaries','docs/checklists')):
            raise ValueError('transition_pointer_outside_workspace')
        if any(e['path']==str(path) for e in self.value['entries']):raise ValueError('transition_duplicate_pointer')
        if raw is not None and (not isinstance(raw,bytes) or len(raw)>4*1024*1024):raise ValueError('transition_pointer_budget_invalid')
        before=_read(path);entry={'path':str(path),'before_sha256':sha(before),'after_sha256':sha(raw)}
        for kind,body in [('before',before),('after',raw)]:
            if body is not None:
                name=kind+'-'+sha(body)+'.bytes';_write(self.directory/name,body);entry[kind+'_snapshot']=name
        self.value['entries'].append(entry);self._save()
    def write(self,path,raw):
        """Seal both versions before a native producer's metadata mutation."""
        if _OWNED.get()!=self.value['transition_id'] or self.value['state']!='publishing':
            raise ValueError('transition_owner_required')
        path=Path(path).resolve()
        if not any(path.is_relative_to(self.workspace/p) for p in (
                'data/runtime','data/threshold_cycle','data/report','data/pipeline_event_summaries','docs/checklists')):
            raise ValueError('transition_pointer_outside_workspace')
        if raw is not None and (not isinstance(raw,bytes) or len(raw)>4*1024*1024):
            raise ValueError('transition_pointer_budget_invalid')
        current=_read(path);generation=sha(current)
        entry=next((e for e in self.value['entries'] if e['path']==str(path)),None)
        if entry is None:
            entry=dict(path=str(path),before_sha256=generation,accepted_sha256=[generation])
            if current is not None:
                name='before-'+generation+'.bytes';_write(self.directory/name,current);entry['before_snapshot']=name
            self.value['entries'].append(entry)
        elif generation not in entry.get('accepted_sha256',[entry['before_sha256'],entry['after_sha256']]):
            raise ValueError('transition_pointer_cas_changed')
        entry['after_sha256']=sha(raw)
        if raw is not None:
            name='after-'+sha(raw)+'.bytes';_write(self.directory/name,raw);entry['after_snapshot']=name
        else:entry.pop('after_snapshot',None)
        accepted=entry.setdefault('accepted_sha256',[entry['before_sha256']])
        if entry['after_sha256'] not in accepted:accepted.append(entry['after_sha256'])
        self.value['pending_pointer']=str(path);self._save()
        if raw is None:path.unlink(missing_ok=True)
        else:_write(path,raw)
        fault=getattr(self,'fault',None)
        if fault:fault(path,'after_rename')
        if str(path) not in self.value['written']:self.value['written'].append(str(path))
        self.value.pop('pending_pointer',None);self._save()
        if fault:fault(path,'after_record')
    def execute(self,steps,*,verify,fault=None):
        """Run real summary/checklist/strict/PREOPEN writers under one journal.

        Expensive source replay precedes this window. A failure leaves durable
        publishing state so consumers refuse mixed generations until this
        exact owner resumes or restores the complete set with CAS.
        """
        if _OWNED.get()!=self.value['transition_id']:raise ValueError('transition_owner_required')
        if self.value['state'] not in ('prepared','publishing'):raise ValueError('transition_not_publishable')
        for entry in self.value['entries']:
            if sha(_read(Path(entry['path']))) not in entry.get('accepted_sha256',
                    [entry['before_sha256'],entry['after_sha256']]):
                raise ValueError('transition_pointer_cas_changed')
        self.value['state']='publishing';self._save();self.fault=fault
        token=_JOURNAL.set(self)
        try:
            for step in steps:step()
            verify()
            for entry in self.value['entries']:
                if sha(_read(Path(entry['path'])))!=entry['after_sha256']:
                    raise ValueError('transition_final_pointer_changed')
            self.value['state']='verified';self._save()
        finally:
            _JOURNAL.reset(token);self.fault=None
    @contextmanager
    def owner(self,*,family_locks=()):
        with ExitStack() as stack:
            handles=[]
            for path in [self.data/'runtime/runtime_release_set.lock',self.data/'runtime/runtime_release_selection.lock',*map(Path,family_locks)]:
                if path.is_symlink() or any(p.is_symlink() for p in path.parents):raise ValueError('transition_lock_path_invalid')
                path.parent.mkdir(parents=True,exist_ok=True);handle=stack.enter_context(path.open('a+b'))
                try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:raise ValueError('transition_existing_writer') from None
                handles.append(handle)
            current=_record(self.current) if self.current.exists() else {}
            if current.get('state')=='publishing' and current.get('transition_id')!=self.value['transition_id']:
                raise ValueError('transition_other_publication_incomplete')
            self.value.update(owner_pid=os.getpid(),owner_start_ticks=start_ticks(os.getpid()))
            self._save();token=_OWNED.set(self.value['transition_id']);self.handles=handles
            try:yield self
            finally:_OWNED.reset(token);self.handles=[]
    def environment(self):
        return {ENV:json.dumps({'transition_id':self.value['transition_id'],'parent_pid':os.getpid(),
            'parent_start_ticks':start_ticks(os.getpid()),'fd':self.handles[0].fileno(),
            'lock_path':str((self.data/'runtime/runtime_release_set.lock').resolve())})}
    @property
    def pass_fds(self):return (self.handles[0].fileno(),)
    def publish(self,*,verify,fault=None):
        if _OWNED.get()!=self.value['transition_id']:raise ValueError('transition_owner_required')
        if self.value['state'] not in ('prepared','publishing'):raise ValueError('transition_not_publishable')
        self.value['state']='publishing';self._save()
        for entry in self.value['entries']:
            path=Path(entry['path']);current=sha(_read(path))
            if current==entry['after_sha256']:
                # Recovery may find a completed rename whose progress update
                # was interrupted. Prepared successor bytes prove ownership.
                if str(path) not in self.value['written']:self.value['written'].append(str(path));self._save()
                continue
            if current!=entry['before_sha256']:raise ValueError('transition_pointer_cas_changed')
            raw=(self.directory/entry['after_snapshot']).read_bytes() if entry.get('after_snapshot') else None
            if sha(raw)!=entry['after_sha256']:raise ValueError('transition_snapshot_changed')
            self.value['pending_pointer']=str(path);self._save()
            if raw is None:path.unlink(missing_ok=True)
            else:_write(path,raw)
            if fault:fault(path,'after_rename')
            self.value['written'].append(str(path));self.value.pop('pending_pointer',None);self._save()
            if fault:fault(path,'after_record')
        verify()
        for entry in self.value['entries']:
            if sha(_read(Path(entry['path'])))!=entry['after_sha256']:raise ValueError('transition_final_pointer_changed')
        self.value['state']='verified';self._save()
    def rollback(self,*,verify_before):
        if _OWNED.get()!=self.value['transition_id']:raise ValueError('transition_owner_required')
        # Validate the complete set before the first restoration; never restore
        # only release while leaving an unknown/newer policy successor behind.
        for entry in self.value['entries']:
            if sha(_read(Path(entry['path']))) not in entry.get('accepted_sha256',
                    [entry['before_sha256'],entry['after_sha256']]):
                raise ValueError('transition_rollback_cas_changed')
        for entry in reversed(self.value['entries']):
            path=Path(entry['path']);raw=(self.directory/entry['before_snapshot']).read_bytes() if entry.get('before_snapshot') else None
            if sha(raw)!=entry['before_sha256']:raise ValueError('transition_snapshot_changed')
            if raw is None:path.unlink(missing_ok=True)
            else:_write(path,raw)
        verify_before();self.value['state']='rolled_back';self._save()
