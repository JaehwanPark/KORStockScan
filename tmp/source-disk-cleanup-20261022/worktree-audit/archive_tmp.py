"""Archive explicitly enumerated closed test and publication scratch trees."""
from pathlib import Path
from decimal import Decimal
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tarfile
import time

from src.engine.infrastructure.log_retention import (
    DocumentReferenceError, DocumentReferences, document_references,
)

O=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('worktree_guards',O/'execute_worktrees.py')
E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
M=E.M; W=M.W
STORE=W.parent/'KORStockScan-storage-archives/source-disk-cleanup-20261022'
PRIVILEGED_ARCHIVE_ROOTS=set()


def write_access(root,rows):
    parents={root}|{root/name for name,row in rows.items() if row['kind']=='directory'}
    protected=[p for p in parents if not os.access(p,os.W_OK|os.X_OK,effective_ids=True)]
    assert not protected or (root in PRIVILEGED_ARCHIVE_ROOTS and
        root==W/'tmp/disk-cleanup-20261002'),'unwritable_parent_preserved'


def unlink_archived(root,path,row):
    try:path.unlink()
    except PermissionError:privileged_unlink(root,path,row)


def privileged_unlink(root,path,row,*,verify_only=False):
    assert root in PRIVILEGED_ARCHIVE_ROOTS and root==W/'tmp/disk-cleanup-20261002'
    # This one closed, archived fixture has a root-owned archives directory.
    # Elevate one inode-checked unlink only, with no recursive or chmod path.
    code="""import json,os,stat,sys
from pathlib import Path
d=json.load(sys.stdin);root=Path(d['root']);p=Path(d['path'])
assert root==Path('/home/ubuntu/KORStockScan/tmp/disk-cleanup-20261002')
assert p.is_relative_to(root) and p!=root and root.resolve()==root
assert '..' not in p.parts and p.parent.resolve()==p.parent
assert not any(q.is_symlink() for q in p.parents if q==root or root in q.parents)
fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 s=os.stat(p.name,dir_fd=fd,follow_symlinks=False)
 actual=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink]
 assert actual==d['stat'] and not stat.S_ISDIR(s.st_mode)
 if not d.get('verify_only'):os.unlink(p.name,dir_fd=fd)
finally:os.close(fd)
"""
    subprocess.run(['sudo','-n','/usr/bin/python3','-I','-c',code],
        input=json.dumps(dict(root=str(root),path=str(path),stat=row['stat'],verify_only=verify_only)),
        text=True,capture_output=True,check=True)


def inventory(root,expected=None):
    assert root.is_dir() and not root.is_symlink() and root.resolve()==root
    result={};device=root.stat().st_dev
    def fail(error):raise error
    for parent,dirs,names in os.walk(root,followlinks=False,onerror=fail):
        assert '.git' not in dirs+names,'nested_git_preserved'
        for name in dirs+names:
            p=Path(parent)/name;s=p.lstat();rel=str(p.relative_to(root))
            assert s.st_dev==device,'nested_filesystem_preserved'
            row={'stat':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink],
                 'allocated':s.st_blocks*512,'mode':stat.S_IMODE(s.st_mode),'mtime_ns':s.st_mtime_ns}
            if stat.S_ISLNK(s.st_mode):row.update(kind='link',target=os.readlink(p))
            elif stat.S_ISDIR(s.st_mode):row.update(kind='directory')
            elif stat.S_ISREG(s.st_mode):
                assert s.st_nlink==1,'hardlink_preserved'
                prior=(expected or {}).get(rel,{})
                digest=prior.get('sha256') if prior.get('stat')==row['stat'] else None
                row.update(kind='file',bytes=s.st_size,sha256=digest or M.A.digest(p))
            elif stat.S_ISFIFO(s.st_mode):row.update(kind='fifo')
            else:raise ValueError('special_file_preserved:'+rel)
            assert p.lstat().st_mtime_ns==s.st_mtime_ns and p.lstat().st_ctime_ns==s.st_ctime_ns,'changed_during_inventory'
            result[rel]=row
        dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
    return result


def has_mount(root):
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        target=Path(line.split()[4].replace('\\040',' '))
        if target==root or root in target.parents:return True
    return False


def external_refs(root,refs):
    return [r for r in refs if not (r['kind']=='workspace_symlink_target' and Path(r['source']).is_relative_to(root))]


def check(root,expected=None):
    # A verified tar is not a readable replacement for a cited file/directory.
    if document_references(W, {str(root)}):
        raise DocumentReferenceError('document_reference_preserved:'+str(root))
    allowed_roots=json.loads((O/'allowed-tmp-roots.json').read_text())
    allowed=str(root) in allowed_roots
    closure=allowed_roots.get(str(root))
    if closure:
        assert M.A.digest(Path(closure['path']))==closure['sha256'],'closure_changed'
        assert json.loads(Path(closure['path']).read_text())['status']==closure.get('expected_status','passed'),'run_not_closed'
        if closure.get('expected_phase'): assert json.loads(Path(closure['path']).read_text())['phase']==closure['expected_phase'],'run_not_terminal'
    assert allowed and root.resolve()==root and not has_mount(root),'root_boundary_invalid'
    code=E.G.FD_CODE.replace("startswith('/home/ubuntu/KORStockScan/tmp/')", "startswith(('/home/ubuntu/KORStockScan','/tmp/pytest-of-ubuntu'))")
    state=json.loads(subprocess.run(['sudo','-n','/usr/bin/python3','-c',code],check=True,capture_output=True,text=True).stdout)
    assert not state['errors'],'process_census_incomplete'
    assert not any(Path(p)==root or root in Path(p).parents for p in state['paths']),'active_process_preserved'
    rows=inventory(root,expected);opened={tuple(x) for x in state['inodes']}
    assert not any(tuple(r['stat'][:2]) in opened for r in rows.values()),'open_inode_preserved'
    pins=E.G.pin_values()
    identities={str(root),root.name}
    if root.is_relative_to(W):identities.add(str(root.relative_to(W)))
    for name,row in rows.items():
        p=root/name;identities.update((str(p),p.name,row.get('sha256','')))
        if p.is_relative_to(W):identities.add(str(p.relative_to(W)))
    assert not pins & identities,'explicit_pin_preserved'
    assert all(r['mtime_ns']<(time.time()-(60 if closure else 3600))*1e9 for r in rows.values() if r['kind']=='file'),'recent_writer_preserved'
    write_access(root,rows)
    if expected is not None:assert rows==expected,'changed_since_archive'
    return rows


def delete_verified(root,rows):
    """Delete exact archived entries; never sweep files created after verification."""
    # Archive and resume callers, including subset deletion, converge here.
    documents = DocumentReferences(W)
    documents.require_unreferenced({str(root)})
    with documents.watch_changes():
        return _delete_verified(root,rows,documents)


def _delete_verified(root,rows,documents):
    write_access(root,rows)
    deleted=[]
    for name,row in rows.items():
        if row['kind']=='directory':continue
        p=root/name
        assert not any(a.is_symlink() for a in p.parents if a==root or root in a.parents),'new_symlink_parent'
        s=p.lstat()
        actual=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink]
        assert actual==row['stat'],'entry_changed_before_unlink'
        documents.assert_unchanged()
        unlink_archived(root,p,row);deleted.append(name)
        documents.assert_unchanged()
    for name,row in sorted(rows.items(),key=lambda pair:len(Path(pair[0]).parts),reverse=True):
        if row['kind']!='directory':continue
        p=root/name;s=p.lstat()
        assert stat.S_ISDIR(s.st_mode) and [s.st_dev,s.st_ino]==row['stat'][:2],'directory_replaced'
        documents.assert_unchanged()
        try:p.rmdir()
        except PermissionError:
            # Closed OS-isolation fixtures can contain root-owned empty directories.
            # Only rmdir is elevated: no chmod, recursive removal or file deletion.
            if not any(p.iterdir()):
                subprocess.run(['sudo','-n','/usr/bin/rmdir','--',str(p)],check=True,capture_output=True)
        except OSError as e:
            if e.errno not in (39,):raise
        documents.assert_unchanged()
    documents.assert_unchanged()
    try:root.rmdir()
    except OSError as e:
        if e.errno not in (39,):raise
    documents.assert_unchanged()
    return deleted


def verify(path,rows):
    seen=set();proc=subprocess.Popen(['zstd','-q','-dc',str(path)],stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=proc.stdout,mode='r|') as tar:
            for m in tar:
                assert m.name in rows and m.name not in seen,'unexpected_member'
                r=rows[m.name]
                assert m.mode==r['mode'],'mode_mismatch'
                assert int(Decimal(m.pax_headers['mtime'])*1000000000)==r['mtime_ns'],'mtime_mismatch'
                if r['kind']=='file':
                    assert m.isfile() and m.size==r['bytes'],'file_type_or_size_mismatch'
                    h=hashlib.sha256();n=0
                    with tar.extractfile(m) as f:
                        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk);n+=len(chunk)
                    assert n==r['bytes'] and h.hexdigest()==r['sha256'],'member_hash_mismatch'
                elif r['kind']=='link':assert m.issym() and m.linkname==r['target'],'link_mismatch'
                elif r['kind']=='fifo':assert m.isfifo(),'fifo_mismatch'
                else:assert m.isdir(),'directory_mismatch'
                seen.add(m.name)
        for _ in iter(lambda:proc.stdout.read(1048576),b''):pass
        proc.stdout.close();assert proc.wait()==0,'zstd_integrity_failed'
        assert seen==set(rows),'missing_member'
    except BaseException:
        proc.stdout.close()
        if proc.poll() is None:proc.terminate()
        proc.wait();raise


def archive(root,rows,path):
    temp=path.with_name(path.name+'.partial')
    with temp.open('xb') as out:
        proc=subprocess.Popen(['nice','-n','15','zstd','-q','-T2','-6','-c'],stdin=subprocess.PIPE,stdout=out)
        try:
            with tarfile.open(fileobj=proc.stdin,mode='w|',format=tarfile.PAX_FORMAT) as tar:
                for name in sorted(rows):
                    p=root/name;info=tar.gettarinfo(str(p),arcname=name)
                    info.pax_headers['mtime']=str(Decimal(rows[name]['mtime_ns'])/1000000000)
                    if rows[name]['kind']=='file':
                        with p.open('rb') as f:tar.addfile(info,f)
                    else:tar.addfile(info)
            proc.stdin.close();assert proc.wait()==0,'compression_failed'
        except BaseException:
            if proc.poll() is None:proc.terminate()
            proc.wait();raise
        out.flush();os.fsync(out.fileno())
    verify(temp,rows);assert not path.exists();temp.rename(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def apply():
    assert not (O/'tmp-archive-result.json').exists(),'already_started'
    STORE.mkdir(parents=True,exist_ok=False)
    base=W/'tmp/nonfixed-quote-deployment-20261017'
    roots=[base/n for n in ('isolated-policy','first-probe-policy','isolated-tmp','isolated-report-mounts')]
    roots+=sorted(base.glob('private-report-attempts-*'))
    roots+=sorted(p for p in Path('/tmp/pytest-of-ubuntu').glob('pytest-*') if not p.is_symlink())
    refs=M.refs({str(p) for p in roots});E.save('tmp-archive-references.json',refs)
    result={'status':'running','removed':[],'skipped':[],'selection':refs['selection']}
    E.save('tmp-archive-result.json',result)
    for index,root in enumerate(roots):
        reasons=external_refs(root,refs['references'].get(str(root),[]))
        if reasons:
            result['skipped'].append({'root':str(root),'reason':'current_reference','references':reasons});continue
        try:rows=check(root)
        except (OSError,ValueError,AssertionError) as e:
            result['skipped'].append({'root':str(root),'reason':str(e)});continue
        print(json.dumps({'archiving':str(root),'files':sum(r['kind']=='file' for r in rows.values()),
                          'GiB':sum(r['allocated'] for r in rows.values())/2**30}),flush=True)
        target=STORE/(str(index)+'-'+root.name+'.tar.zst')
        archive(root,rows,target)
        manifest={'schema':'closed_scratch_archive_v1','original_root':str(root),'archive':str(target),
            'archive_sha256':M.A.digest(target),'members':rows,'restore_command':['tar','--zstd','--keep-old-files','-xf',str(target),'-C',str(root)],
            'restore_requires_original_root_directory':True,'all_member_hashes_verified':True}
        mp=target.with_name(target.name+'.manifest.json')
        with mp.open('x') as f:json.dump(manifest,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        current=M.refs({str(root)})
        reasons=external_refs(root,current['references'].get(str(root),[]))
        if reasons:
            result['skipped'].append({'root':str(root),'reason':'new_reference_after_archive','references':reasons});continue
        try:check(root,rows)
        except (OSError,ValueError,AssertionError) as e:
            result['skipped'].append({'root':str(root),'reason':str(e)});continue
        assert M.A.digest(target)==manifest['archive_sha256'],'archive_changed'
        record={'root':str(root),'archive':str(target),'manifest':str(mp),'archive_sha256':manifest['archive_sha256'],
                'files':sum(r['kind']=='file' for r in rows.values()),'allocated_bytes':M.C.inventory(root)['allocated_bytes'],
                'archive_allocated_bytes':target.stat().st_blocks*512,'logical_bytes':sum(r.get('bytes',0) for r in rows.values())}
        with (O/'tmp-deletion-journal.jsonl').open('a') as f:
            f.write(json.dumps({'event':'verified_archive_delete_intent',**record})+'\n');f.flush();os.fsync(f.fileno())
            deleted=delete_verified(root,rows)
            record['root_removed']=not root.exists()
            record['archived_entries_unlinked']=len(deleted)
            f.write(json.dumps({'event':'removed',**record})+'\n');f.flush();os.fsync(f.fileno())
        result['removed'].append(record);E.save('tmp-archive-result.json',result)
        print(json.dumps({'removed':str(root),'MiB_archive':target.stat().st_size/2**20}),flush=True)
    # Remove only a dangling pytest alias into a tree removed by this run.
    link=Path('/tmp/pytest-of-ubuntu/pytest-current')
    if link.is_symlink() and os.readlink(link) in {r['root'] for r in result['removed']} and not link.exists():link.unlink()
    result.update(status='passed',closed_at=time.time());E.save('tmp-archive-result.json',result)


if __name__=='__main__':apply()
