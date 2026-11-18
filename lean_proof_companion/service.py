"""Loopback-only reader and chat service. Models have no execution tools."""
import concurrent.futures,gc,json,secrets,subprocess,threading,time,webbrowser,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .core import ROOT,CORE,LeanWorker,atomic
from .dialogue import Dialogue,local_config

class Service:
    def __init__(self,model,project,runs,prover_model=None,adapter=None):
        self.model=Path(model);self.project=Path(project);self.runs=Path(runs)
        self.prover_model=prover_model;self.adapter=adapter
        self.executor=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='local-model')
        self.dialogue=None;self.lean=None;self.error=None;self.lean_error=None;self.busy=threading.Lock()
        self.ready=self.executor.submit(self.initialize)
    def initialize(self):
        try:
            self.dialogue=Dialogue(self.model,self.runs/'dialogue')
            probe=self.dialogue.ask('Ответь одним словом: готов.',max_tokens=32)
            if 'готов' not in probe['answer'].lower() or probe['finish_reason']=='repetition':raise RuntimeError('Диалоговая модель не прошла стартовую проверку')
        except Exception as e:self.dialogue=None;self.error=str(e)
        try:
            self.lean=LeanWorker(self.project)
            probe=self.lean.parse('theorem probe : True := by trivial',self.runs/'lean-startup')
            if probe.get('errors'):raise RuntimeError('Lean startup probe failed')
        except Exception as e:self.lean=None;self.lean_error=str(e)
    def health(self):
        return {'status':'loading' if not self.ready.done() else 'error' if self.error else 'ready','model':self.model.name,'model_ready':self.dialogue is not None,'lean_ready':self.lean is not None,'lean_version':self.lean.version if self.lean else None,'deepseek_configured':bool(self.prover_model and Path(self.prover_model).is_dir()),'error':self.error,'lean_error':self.lean_error,'busy':self.busy.locked()}
    def task(self,data):
        if not self.lean:raise ValueError('Lean не готов: '+str(self.lean_error))
        source=data.get('source');name=data.get('name')
        if not isinstance(source,str) or len(source)>64000 or not isinstance(name,str):raise ValueError('Нужны исходная Lean-задача и имя теоремы')
        folder=self.runs/('parse-'+secrets.token_hex(12))
        tasks=self.lean.tasks(source,folder,origin='reader-local-user')
        found=[t for t in tasks if t.name==name]
        if len(found)!=1:raise ValueError('Точная цель не найдена: '+name)
        return found[0]
    def action(self,route,data):
        if route=='/api/chat':
            if self.dialogue is None:self.dialogue=Dialogue(self.model,self.runs/'dialogue')
            return self.dialogue.ask(data.get('question'),data.get('history'),data.get('max_tokens',512))
        task=self.task(data)
        if route=='/api/verify':
            proof=data.get('proof')
            if not isinstance(proof,str) or len(proof)>32000:raise ValueError('Нужно тело доказательства')
            return self.lean.verify(task,proof,self.runs/'proofs')
        if route=='/api/prove':
            if not self.prover_model:raise ValueError('DeepSeek не настроен')
            # Never keep both model families resident during proof generation.
            self.dialogue=None;gc.collect()
            import mlx.core as mx
            mx.clear_cache()
            from .pipeline import MLXGenerator,run_task,freeze_model
            folder=self.runs/('generation-'+secrets.token_hex(12));folder.mkdir(parents=True)
            manifest=freeze_model(self.prover_model,self.adapter,folder/'model-manifest.json')
            generator=MLXGenerator(self.prover_model,self.adapter)
            try:result=run_task(task,self.lean,generator,folder,'lora' if self.adapter else 'base',manifest,attempts=3)
            finally:del generator;gc.collect();mx.clear_cache()
            result['statement']=task.header
            result['proof']=Path(result['attempts'][-1]['directory'],'proof.txt').read_text()
            return result
        raise ValueError('Unknown route')


def serve(args):
    os.environ.setdefault('HF_HUB_OFFLINE','1')
    config=local_config();model=args.model or config.get('chat_model')
    if not model:raise ValueError('Укажи --model или настрой .local-dialog.json')
    reader=ROOT/'reader/dist/index.html'
    if not reader.is_file():raise ValueError('Ридер не собран: python3.11 reader/build.py')
    service=Service(model,args.project,args.runs,config.get('prover_model'),config.get('adapter'))
    token=secrets.token_urlsafe(32);origin='http://127.0.0.1:'+str(args.port)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def allowed_host(self):return self.headers.get('Host')=='127.0.0.1:'+str(args.port)
        def response(self,code,value,content_type='application/json; charset=utf-8'):
            raw=value.encode() if isinstance(value,str) else json.dumps(value,ensure_ascii=False).encode()
            self.send_response(code);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if not self.allowed_host():self.response(403,{'error':'Invalid Host'});return
            if self.path in ('/','/index.html'):
                page=reader.read_text().replace('</head>','<meta name="lpc-session" content="'+token+'"></head>')
                self.response(200,page,'text/html; charset=utf-8');return
            if self.path=='/api/health':self.response(200,service.health());return
            self.response(404,{'error':'Not found'})
        def do_POST(self):
            if not self.allowed_host() or self.headers.get('Origin')!=origin or not secrets.compare_digest(self.headers.get('X-LPC-Session',''),token):self.response(403,{'error':'Local session required'});return
            if self.path not in ('/api/chat','/api/verify','/api/prove'):self.response(404,{'error':'Not found'});return
            try:size=int(self.headers.get('Content-Length','0'))
            except ValueError:self.response(400,{'error':'Invalid length'});return
            if size<1 or size>150000:self.response(413,{'error':'Request too large'});return
            if not service.ready.done():self.response(503,{'error':'Модель загружается'});return
            if service.error:self.response(503,{'error':service.error});return
            if not service.busy.acquire(blocking=False):self.response(429,{'error':'Предыдущая операция ещё выполняется'});return
            try:
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict):raise ValueError('Expected object')
                future=service.executor.submit(service.action,self.path,data)
                # A request disconnect never enables concurrent model execution.
                future.add_done_callback(lambda _:service.busy.release())
                result=future.result()
                self.response(200,result)
            except (ValueError,TypeError,json.JSONDecodeError) as e:
                if 'future' not in locals():service.busy.release()
                self.response(400,{'error':str(e),'accepted':False})
            except Exception as e:
                if 'future' not in locals():service.busy.release()
                self.response(500,{'error':str(e),'accepted':False})
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('Ридер с локальным чатом: '+origin,flush=True)
    if not args.no_open:webbrowser.open(origin+'/#chat')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();service.executor.shutdown(wait=True)
