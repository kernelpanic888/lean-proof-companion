"""One TaskSpec renders every prompt and every candidate check."""
import dataclasses, hashlib, json, time
from pathlib import Path
from .core import TaskSpec, LeanWorker, atomic, digest


def extract_proof(raw, task, worker, directory):
    text=raw
    if text.lstrip().startswith('```'):
        lines=text.strip().splitlines();text='\n'.join(lines[1:])
        if text.rstrip().endswith('```'):text=text.rstrip()[:-3].rstrip()
    elif '```' in text:
        # CoT prose may precede exactly one final code fence.
        chunks=text.split('```')
        if len(chunks)!=3:raise ValueError('ambiguous code fences')
        text=chunks[1]
        if text.startswith(('lean4\n','lean\n')):text=text.split('\n',1)[1]
    if text.lstrip().startswith(('theorem ','lemma ')):
        tasks=worker.tasks(task.context+'\n'+text+'\n'+task.closing,directory)
        candidate=tasks[-1]
        if ' '.join(candidate.header.split())!=' '.join(task.header.split()):raise ValueError('changed theorem header')
        return candidate.reference
    if text.lstrip().startswith('by'):
        return text
    # The prompt already supplies `by\n`; only normalize the omitted initial indent.
    lines=text.splitlines()
    if lines and lines[0] and not lines[0].startswith((' ','\t')):lines[0]='  '+lines[0]
    return 'by\n'+'\n'.join(lines)


def run_task(task, worker, generator, runs, mode, model_manifest, attempts=3):
    outcomes=[];feedback=''
    for i,budget in enumerate([512,1024,1024][:attempts]):
        prompt='Complete the following Lean proof. Return only its body after `by`.\n\n'+task.context+'\n'+task.header+' := by\n'
        if feedback:prompt+='\nPrevious candidate and Lean diagnostics:\n'+feedback+'\nReturn a corrected proof body. Do not change the statement.\n'
        raw,meta=generator(prompt,budget)
        tmp=Path(runs)/('extract-'+str(time.time_ns()));tmp.mkdir(parents=True)
        try:
            proof=extract_proof(raw,task,worker,tmp)
            result=worker.verify(task,proof,runs,raw=raw,generation={**meta,'prompt':prompt,'mode':mode,'budget':budget,'attempt':i+1,'model_manifest':model_manifest})
        except ValueError as error:
            result=worker.verify(task,'INVALID_EXTRACTION',runs,raw=raw,generation={**meta,'prompt':prompt,'mode':mode,'budget':budget,'attempt':i+1,'extraction_error':str(error),'model_manifest':model_manifest})
            result['extraction_error']=str(error)
        outcomes.append(result)
        if result['accepted'] or result['status']=='INFRA_ERROR':break
        feedback=raw+'\n'+json.dumps(result.get('diagnostics',{}),ensure_ascii=False)+'\n'+result.get('reason','')
    return {'task_id':task.task_id,'name':task.name,'first_attempt_pass':outcomes[0]['accepted'],
            'repaired_pass':any(x['accepted'] for x in outcomes[1:]),'accepted':any(x['accepted'] for x in outcomes),
            'attempts':outcomes,'mode':mode}


class MLXGenerator:
    def __init__(self, model_path, adapter_path=None):
        from mlx_lm import load
        self.model,self.tokenizer=load(str(model_path),adapter_path=str(adapter_path) if adapter_path else None)
    def __call__(self,prompt,budget):
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler
        rendered=self.tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=False,add_generation_prompt=True)
        start=time.monotonic();chunks=[];last=None
        for response in stream_generate(self.model,self.tokenizer,prompt=rendered,max_tokens=budget,sampler=make_sampler(temp=0.0)):
            chunks.append(response.text);last=response
        return ''.join(chunks),{'sampler':{'temperature':0.0},'elapsed_sec':time.monotonic()-start,'generation_tokens':getattr(last,'generation_tokens',0),
                              'finish_reason':getattr(last,'finish_reason',None) or ('length' if getattr(last,'generation_tokens',0)>=budget else 'stop')}


def freeze_model(model_path, adapter_path, destination):
    paths={'model':Path(model_path)}
    if adapter_path:paths['adapter']=Path(adapter_path)
    files={label+'/'+str(p.relative_to(folder)):digest(p) for label,folder in paths.items()
           for p in sorted(folder.rglob('*')) if p.is_file()}
    if not files:raise ValueError('no local model files to freeze')
    manifest={'files':files,'frozen_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    atomic(destination,manifest)
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
