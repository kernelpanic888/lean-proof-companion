"""Immutable tasks and isolated Lean verification. No decision reads candidate stdout."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, json, os, subprocess, uuid, time, platform, shutil, signal

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT
TOOL = Path(__file__).with_name('LeanTool.lean')
STANDARD = {'propext','Classical.choice','Quot.sound'}


def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()


def atomic(path, value):
    path=Path(path);tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)


def walk(node):
    yield node
    for child in node.get('children',[]):yield from walk(child)


@dataclass(frozen=True)
class TaskSpec:
    name: str
    context: str
    header: str
    closing: str = ''
    package: str = 'core'
    origin: str = 'user'
    reference: str = ''

    @property
    def task_id(self):
        data=asdict(self);data.pop('reference');return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

    def render(self, proof):return self.context+'\n'+self.header+' := '+proof+'\n'+self.closing


class LeanWorker:
    def __init__(self, package=CORE):
        self.package=Path(package).resolve()
        if platform.system() != 'Darwin' or not Path('/usr/bin/sandbox-exec').is_file():
            raise RuntimeError('Verification requires macOS sandbox-exec; no unisolated fallback is provided')
        lake=shutil.which('lake') or str(Path.home()/'.elan/bin/lake')
        self.prefix=Path(subprocess.check_output([str(lake),'env','lean','--print-prefix'],cwd=self.package,text=True).strip())
        self.lean=self.prefix/'bin/lean'
        self.env=os.environ.copy()
        self.env['LEAN_PATH']=subprocess.check_output([str(lake),'env','printenv','LEAN_PATH'],cwd=self.package,text=True).strip()
        self.version=subprocess.check_output([str(self.lean),'--version'],text=True).strip()

    def call(self, mode, args, writable, extra_path=None, timeout=120):
        writable=Path(writable).resolve();writable.mkdir(parents=True,exist_ok=True)
        profile=writable/'worker.sb'
        profile.write_text('(version 1) (deny default) (allow file-read*) (allow process*) (allow sysctl-read) (allow mach-lookup) (deny network*) (allow file-write* (subpath '+json.dumps(str(writable))+'))')
        cmd=['/usr/bin/sandbox-exec','-f',str(profile),str(self.lean),'--run',str(TOOL),mode,*map(str,args)]
        env=self.env.copy()
        if extra_path:env['LEAN_PATH']=str(extra_path)+os.pathsep+env['LEAN_PATH']
        try:
            p=subprocess.Popen(cmd,cwd=self.package,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            try:
                stdout,stderr=p.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL)
                stdout,stderr=p.communicate()
                (writable/'stdout.log').write_text(stdout);(writable/'stderr.log').write_text(stderr+'\nTIMEOUT')
                return 124
            finally:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            (writable/'stdout.log').write_text(stdout);(writable/'stderr.log').write_text(stderr)
            return p.returncode
        except OSError as error:
            (writable/'stderr.log').write_text(str(error));return 125

    def parse(self, source, directory):
        directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
        inp=directory/'input.lean';inp.write_text(source);result=directory/'parse.json'
        code=self.call('parse',[inp,result],directory)
        if code or not result.exists():raise RuntimeError((directory/'stderr.log').read_text())
        return json.loads(result.read_text())

    def tasks(self, source, directory, origin='user'):
        parsed=self.parse(source,directory)
        if parsed['errors']:raise ValueError(parsed['diagnostics'])
        raw=source.encode();tasks=[]
        for cmd in parsed['commands']:
            tree=cmd['syntax'];nodes=list(walk(tree))
            theorem=next((n for n in nodes if n['kind']=='Lean.Parser.Command.theorem'),None)
            if theorem is None:continue
            value=next((n for n in theorem['children'] if n['kind']=='Lean.Parser.Command.declValSimple'),None)
            ident=next((n for n in theorem['children'] if n['kind']=='Lean.Parser.Command.declId'),None)
            if not value or not ident:raise ValueError('unsupported theorem body')
            name=next(n['text'] for n in walk(ident) if n['kind']=='ident')
            ns=cmd['namespace'];name=name if ns=='[anonymous]' else ns+'.'+name
            start=tree['start'];cut=value['start'];end=tree['end']
            reference=raw[cut+2:end].decode().strip()
            tasks.append(TaskSpec(name,raw[:start].decode(),raw[start:cut].decode().rstrip(),
                                  ''.join('end'+(' '+s if s else '')+'\n' for s in cmd['scopes']),origin=origin,reference=reference))
        if not tasks:raise ValueError('empty audit: no theorem targets')
        if len({t.name for t in tasks})!=len(tasks):raise ValueError('duplicate target names')
        return tasks

    def verify(self, task, proof, runs, raw=None, generation=None):
        root=Path(runs).resolve();root.mkdir(parents=True,exist_ok=True)
        run=root/(time.strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex);run.mkdir()
        atomic(run/'task.json',asdict(task));(run/'raw.txt').write_text(proof if raw is None else raw)
        (run/'proof.txt').write_text(proof);atomic(run/'generation.json',generation or {})
        source=run/'Candidate.lean';source.write_text(task.render(proof))
        expected=run/'Expected.lean';expected.write_text(task.render('by\n  sorry'))
        result={'schema_version':2,'run_id':run.name,'task_id':task.task_id,'status':'INFRA_ERROR',
                'accepted':False,'checker_sha256':digest(TOOL),'lean_version':self.version,'task_name':task.name,'axioms':[]}
        try:
            parse_dir=run/'term';parse_dir.mkdir();term=parse_dir/'term.txt';term.write_text(proof)
            term_result=parse_dir/'term.json'
            code=self.call('term',[term,term_result],parse_dir)
            if code or not term_result.exists():raise RuntimeError('term parser unavailable')
            parsed=json.loads(term_result.read_text())
            if not parsed['ok']:result.update(status='REJECTED',reason=parsed.get('error','invalid term'))
            else:
                nodes=list(walk(parsed['syntax']))
                banned=[n['kind'] for n in nodes if any(x in n['kind'].lower() for x in ['runtac','run_tac','sorry','admit'])]
                if banned:result.update(status='REJECTED',reason='forbidden proof syntax: '+str(banned))
                else:
                    comp=run/'compile';comp.mkdir();meta=comp/'compile.json';olean=comp/'Candidate.olean'
                    code=self.call('compile',[source,olean,meta],comp)
                    if not meta.exists():raise RuntimeError('compiler unavailable: '+(comp/'stderr.log').read_text())
                    diagnostics=json.loads(meta.read_text());result['diagnostics']=diagnostics
                    if code or diagnostics['errors'] or not olean.exists():result.update(status='REJECTED',reason='compile failed')
                    else:
                        # A separate inspector cannot be influenced by candidate messages.
                        audit=run/'inspection';audit.mkdir();audit_file=audit/'audit.json'
                        before=digest(olean)
                        code=self.call('inspect',['Candidate',task.name,expected,audit_file],audit,extra_path=comp)
                        if code or not audit_file.exists():raise RuntimeError('inspector unavailable: '+(audit/'stderr.log').read_text())
                        inspected=json.loads(audit_file.read_text());result['inspection']=inspected;result['axioms']=inspected['axioms']
                        if before!=digest(olean):raise RuntimeError('artifact changed during inspection')
                        if not inspected['same_type'] or not inspected['is_theorem']:result.update(status='REJECTED',reason='type mismatch')
                        elif 'sorryAx' in inspected['axioms']:result.update(status='REJECTED',reason='placeholder dependency')
                        else:
                            warnings=[x for x in diagnostics['diagnostics'] if x['severity']=='warning']
                            result['kernel_valid']=True;result['warnings']=warnings
                            result['status']='CONDITIONAL' if set(inspected['axioms'])-STANDARD else 'VERIFIED_STANDARD'
                            result['accepted']=result['status']=='VERIFIED_STANDARD' and not warnings
                            if warnings:result['reason']='warnings rejected by strict policy'
        except Exception as error:result.update(status='INFRA_ERROR',reason=str(error))
        files=[p for p in run.rglob('*') if p.is_file()]
        result['files']={str(p.relative_to(run)):digest(p) for p in files}
        atomic(run/'result.json',result);atomic(run/'seal.json',{'result_sha256':digest(run/'result.json')});atomic(root/'latest.json',{'run_id':run.name,'result_sha256':digest(run/'result.json')})
        return {**result,'directory':str(run)}


def read_result(directory):
    directory=Path(directory)
    seal=json.loads((directory/'seal.json').read_text())
    if digest(directory/'result.json')!=seal['result_sha256']:raise ValueError('corrupt result')
    result=json.loads((directory/'result.json').read_text())
    for rel,sha in result['files'].items():
        path=(directory/rel).resolve()
        if not path.is_relative_to(directory.resolve()):raise ValueError('unsafe evidence path')
        if digest(path)!=sha:raise ValueError('corrupt evidence: '+rel)
    return result
