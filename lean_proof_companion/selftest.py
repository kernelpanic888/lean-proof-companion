"""End-to-end negative controls; no model or network required."""
import json
import subprocess
from pathlib import Path
from .core import LeanWorker, TaskSpec, read_result, atomic
from .pipeline import extract_proof, run_task


def run(project,runs):
    w=LeanWorker(project);out=Path(runs).resolve();out.mkdir(parents=True,exist_ok=True)
    checks={};evidence=[]
    t=TaskSpec('fixed','','theorem fixed (n : Nat) : n = n')
    first=w.verify(t,'by\n  rfl',out);assert first['accepted'],first
    evidence.append(first['directory']);checks['valid_proof']=True
    second=w.verify(t,'by\n  exact True.intro',out)
    assert second['status']=='REJECTED',second
    checks['wrong_proof_rejected']=True
    for name,proof in [('sorry','by sorry'),('admit','by admit'),('extra_command','by rfl\ntheorem extra : True := by trivial')]:
        result=w.verify(t,proof,out);assert result['status']=='REJECTED',result
        checks[name+'_rejected']=True
    try:extract_proof('theorem fixed : True := by trivial',t,w,out/'changed')
    except ValueError:checks['changed_statement_rejected']=True
    else:raise AssertionError('changed statement accepted')
    ax=TaskSpec('derived','axiom assumption : False\n','theorem derived : False')
    conditional=w.verify(ax,'by exact assumption',out)
    assert conditional['status']=='CONDITIONAL' and not conditional['accepted'],conditional
    assert 'assumption' in conditional['axioms'];checks['user_axiom_conditional']=True
    traced=w.verify(ax,'by\n  trace "does not depend on any axioms"\n  exact assumption',out)
    assert traced['status']=='CONDITIONAL' and 'assumption' in traced['axioms'],traced
    checks['stdout_cannot_forge_audit']=True
    evidence.append(traced['directory'])
    read_result(first['directory']);checks['separate_runs']=first['directory']!=second['directory']
    f=Path(first['directory'])/'raw.txt';original=f.read_bytes();f.write_text('tampered')
    try:read_result(first['directory'])
    except ValueError:checks['tamper_detected']=True
    else:raise AssertionError('corrupt evidence accepted')
    finally:f.write_bytes(original)
    read_result(first['directory'])
    answers=iter([('  exact True.intro',{'finish_reason':'stop'}),('  rfl',{'finish_reason':'stop'})]);prompts=[]
    def fixture(prompt,budget):prompts.append(prompt);return next(answers)
    repaired=run_task(t,w,fixture,out,'fixture','no-model')
    assert not repaired['first_attempt_pass'] and repaired['repaired_pass']
    assert 'Lean diagnostics' in prompts[1];checks['repair_feedback']=True
    parsed=w.tasks('namespace Outer\nsection\nvariable (n : Nat)\ntheorem a : (let x := n; x) = n := by rfl\nend\ndef middle : Nat := 4\ntheorem b : middle = 4 := by rfl\nend Outer\n',out/'syntax')
    assert [x.name for x in parsed]==['Outer.a','Outer.b']
    for task in parsed:
        r=w.verify(task,task.reference,out);assert r['accepted'],r
    checks['scope_let_and_intermediate_context']=True
    try:w.tasks('def x := 1',out/'empty')
    except ValueError:checks['empty_target_rejected']=True
    else:raise AssertionError('empty targets accepted')
    # Exercise the OS write boundary directly with a trusted probe command.
    sentinel=out/'outside-worker.txt'
    w.parse('theorem probe : True := by trivial',out/'write-probe')
    probe=subprocess.run(['/usr/bin/sandbox-exec','-f',str(out/'write-probe/worker.sb'),'/usr/bin/touch',str(sentinel)],capture_output=True,text=True)
    assert probe.returncode!=0 and not sentinel.exists(),probe
    atomic(out/'write-probe/probe.json',{'returncode':probe.returncode,'external_write_denied':True})
    checks['sandbox_external_write_denied']=True
    # A successful compiler with no independent audit must fail closed.
    original_call=w.call
    for audit_mode in ['missing','empty']:
        def broken_audit(mode,args,writable,**kwargs):
            if mode=='inspect':
                if audit_mode=='empty':Path(args[-1]).write_text('{}')
                return 0
            return original_call(mode,args,writable,**kwargs)
        w.call=broken_audit
        missing=w.verify(t,'by rfl',out)
        w.call=original_call
        assert missing['status']=='INFRA_ERROR' and not missing['accepted'],missing
        checks[audit_mode+'_audit_fails_closed']=True
    report={'status':'PASS' ,'checks':checks,'lean_version':w.version,'evidence':evidence,
            'model_generation':'NOT_RUN','training':'NOT_RUN','hostile_input_security':'NOT_AUDITED'}
    atomic(out/'selftest-report.json',report);print(json.dumps(report,indent=2));return 0
