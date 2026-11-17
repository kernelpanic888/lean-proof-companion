"""Local CLI. Lean checks require macOS; model generation is optional."""
import argparse
import dataclasses
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from . import __version__
from .core import CORE, LeanWorker, atomic, read_result


def parser():
    p=argparse.ArgumentParser(description='Keep the statement fixed. Ask a model for a proof. Check it with Lean.')
    p.add_argument('--version',action='version',version=__version__)
    commands=p.add_subparsers(dest='command',required=True)
    doctor=commands.add_parser('doctor',help='Check the local Lean and isolation environment')
    doctor.add_argument('--project',type=Path,default=CORE)
    for name in ['verify','prove']:
        c=commands.add_parser(name,help='Check a saved proof' if name=='verify' else 'Generate and check up to three attempts')
        c.add_argument('--project',type=Path,default=CORE,help='Trusted Lake package; use its toolchain and imports')
        c.add_argument('--source',type=Path,required=True,help='Trusted Lean source with reference or placeholder bodies')
        c.add_argument('--name',required=True,help='Exact fully qualified theorem name')
        c.add_argument('--runs',type=Path,default=Path('runs'))
        if name=='verify':c.add_argument('--proof',type=Path,required=True,help='One Lean proof term, e.g. by ...')
        else:
            c.add_argument('--model',type=Path,required=True,help='Local MLX model directory')
            c.add_argument('--adapter',type=Path,help='Optional local LoRA adapter directory')
            c.add_argument('--attempts',type=int,choices=[1,2,3],default=3)
    replay=commands.add_parser('replay',help='Validate saved evidence hashes; does not rerun Lean')
    replay.add_argument('directory',type=Path)
    test=commands.add_parser('selftest',help='Run model-free Lean and negative-control regressions')
    test.add_argument('--project',type=Path,default=CORE)
    test.add_argument('--runs',type=Path,default=Path('runs/selftest'))
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.command=='doctor':
            report={'python':sys.version.split()[0],'platform':platform.system(),'version':__version__,
                    'sandbox_available':Path('/usr/bin/sandbox-exec').is_file()}
            worker=LeanWorker(args.project)
            report.update(lean=worker.version,project=str(worker.package))
            # Probe process execution as well as the existence of the executable.
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:worker.parse('theorem probe : True := by trivial',tmp)
            report['status']='PASS';print(json.dumps(report,indent=2));return 0
        if args.command=='replay':
            print(json.dumps(read_result(args.directory),ensure_ascii=False,indent=2));return 0
        if args.command=='selftest':
            from .selftest import run
            return run(args.project,args.runs)
        worker=LeanWorker(args.project)
        args.runs.mkdir(parents=True,exist_ok=True)
        tasks=worker.tasks(args.source.read_text(),args.runs/('parse-'+str(time.time_ns())),origin=str(args.source))
        selected=[t for t in tasks if t.name==args.name]
        if len(selected)!=1:raise ValueError('Expected exactly one target; available: '+', '.join(t.name for t in tasks))
        task=selected[0]
        if args.command=='verify':
            result=worker.verify(task,args.proof.read_text(),args.runs)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if result['accepted'] else 2 if result['status']=='INFRA_ERROR' else 1
        from .pipeline import MLXGenerator,freeze_model,run_task
        if not args.model.is_dir() or (args.adapter and not args.adapter.is_dir()):raise ValueError('model/adapter directory missing')
        manifest_file=args.runs/('model-'+str(time.time_ns())+'.json')
        manifest=freeze_model(args.model,args.adapter,manifest_file)
        generator=MLXGenerator(args.model,args.adapter)
        report=run_task(task,worker,generator,args.runs,'lora' if args.adapter else 'base',manifest,attempts=args.attempts)
        destination=args.runs/('evaluation-'+str(time.time_ns())+'.json')
        atomic(destination,report);print(json.dumps({'report':str(destination),**report},ensure_ascii=False,indent=2))
        if any(a['status']=='INFRA_ERROR' for a in report['attempts']):return 2
        return 0 if report['accepted'] else 1
    except (OSError,ValueError,RuntimeError,ImportError,subprocess.SubprocessError) as error:
        print(json.dumps({'status':'INFRA_ERROR','accepted':False,'reason':str(error)}),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
