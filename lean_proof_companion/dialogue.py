"""Local dialogue, deliberately separate from proof acceptance."""
from pathlib import Path
import hashlib,json,time,uuid
from .core import ROOT,atomic

SYSTEM = '''Ты — локальный диалоговый помощник Lean Proof Companion. Отвечай по-русски, ясно и кратко, если пользователь не попросил иначе. Не придумывай ссылки и результаты запусков. Твои ответы сами по себе НЕ проверены Lean. Не называй предложенный код доказанным, пока пользователь не получил отдельный результат проверяющего инструмента. Уточняй неоднозначные условия. Для задачи о занятой категории правило задаётся спецификацией: record возвращает none для занятой ячейки, иначе помечает её занятой. Это авторское правило спецификации, а не встроенное ограничение Lean или универсальный закон уникальности. Не путай игровую категорию с теорией категорий. Если нужен короткий пример Lean, используй точную малую модель: def record (used : Bool) : Option Bool := if used then none else some true. None означает отказ перехода, some true — успешное новое состояние. Не выдумывай другое значение Option для этой модели. Ты — Qwen для диалога; отдельный DeepSeek-Prover предлагает доказательства, Lean проверяет. Не утверждай, что можешь выполнять команды или читать файлы: у тебя нет таких инструментов.'''


def local_config():
    file=ROOT/'.local-dialog.json'
    return json.loads(file.read_text()) if file.is_file() else {}


def repetitive(text):
    """Detect periodic garbage; do not present this as a semantic verifier."""
    tail=text[-1200:]
    for size in range(12,161):
        if len(tail)>=size*4 and tail[-size:]*4==tail[-size*4:]:return True
    return False


class Dialogue:
    def __init__(self,model_path,runs):
        self.path=Path(model_path).expanduser().resolve()
        if not (self.path/'config.json').is_file():raise ValueError('Диалоговая модель не установлена: '+str(self.path))
        from mlx_lm import load
        self.model,self.tokenizer=load(str(self.path),trust_remote_code=False)
        self.tokenizer.apply_chat_template([{'role':'user','content':'probe'}],tokenize=False,add_generation_prompt=True)
        self.runs=Path(runs);self.runs.mkdir(parents=True,exist_ok=True)
        self.identity={'directory':self.path.name,'config_sha256':hashlib.sha256((self.path/'config.json').read_bytes()).hexdigest()}
        manifest=self.path/'.lpc-model-manifest.json'
        if manifest.is_file():
            self.identity.update(revision=json.loads(manifest.read_text()).get('revision'),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())

    def ask(self,question,history=None,max_tokens=512):
        if not isinstance(question,str) or not question.strip() or len(question)>8000:raise ValueError('Вопрос должен содержать от 1 до 8000 символов')
        if not 32<=max_tokens<=1024:raise ValueError('Лимит ответа: от 32 до 1024 токенов')
        history=history or []
        if not isinstance(history,list) or len(history)>12:raise ValueError('Слишком длинная история; начни новый диалог')
        messages=[{'role':'system','content':SYSTEM}]
        for item in history:
            if not isinstance(item,dict) or item.get('role') not in ('user','assistant') or not isinstance(item.get('content'),str):raise ValueError('Недопустимая история диалога')
            if len(item['content'])>8000:raise ValueError('Сообщение истории слишком длинное')
            messages.append({'role':item['role'],'content':item['content']})
        messages.append({'role':'user','content':question.strip()})
        rendered=self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        tokens=self.tokenizer.encode(rendered,add_special_tokens=False)
        if len(tokens)+max_tokens>8192:raise ValueError('Контекст переполнен; начни новый диалог')
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler,make_logits_processors
        import mlx.core as mx
        mx.random.seed(42);parts=[];last=None;reason='stop';start=time.monotonic()
        stream=stream_generate(self.model,self.tokenizer,prompt=tokens,max_tokens=max_tokens,sampler=make_sampler(temp=0.3,top_p=0.9),logits_processors=make_logits_processors(repetition_penalty=1.08,repetition_context_size=128))
        try:
            for response in stream:
                parts.append(response.text);last=response
                if repetitive(''.join(parts)):reason='repetition';break
        finally:stream.close()
        text=''.join(parts).strip();count=getattr(last,'generation_tokens',0)
        if reason!='repetition':reason=getattr(last,'finish_reason',None) or ('length' if count>=max_tokens else 'stop')
        result={'schema_version':1,'run_id':uuid.uuid4().hex,'model':self.identity,'mode':'dialogue','question':question,'history':history,'raw':text,'answer':text if reason!='repetition' else 'Ответ зациклился и остановлен. Попробуй уточнить вопрос или начать новый диалог.',
                'generation_tokens':count,'finish_reason':reason,'elapsed_sec':time.monotonic()-start,'lean_status':'NOT_RUN','accepted':False,'sampler':{'temperature':0.3,'top_p':0.9,'repetition_penalty':1.08,'seed':42}}
        directory=self.runs/result['run_id'];directory.mkdir(exist_ok=False)
        atomic(directory/'result.json',result);(directory/'prompt.txt').write_text(rendered)
        return result
