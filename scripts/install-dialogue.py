"""Download an explicitly selected, pinned dialogue model; never touch proof weights."""
from pathlib import Path
import argparse,hashlib,json,sys
from huggingface_hub import snapshot_download
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--prover-model');p.add_argument('--adapter');args=p.parse_args()
root=Path(__file__).resolve().parents[1];target=args.directory.expanduser().resolve()
if args.prover_model and target==Path(args.prover_model).resolve():raise SystemExit('Dialogue and prover directories must differ')
if (target/'config.json').exists() and json.loads((target/'config.json').read_text()).get('model_type')!='qwen3':raise SystemExit('Refusing to overwrite another model')
repo='mlx-community/Qwen3-4B-Instruct-2507-4bit';revision='50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b'
snapshot_download(repo,revision=revision,local_dir=target,allow_patterns=['*.json','*.safetensors','*.model','*.jinja','*.txt','*.md','LICENSE*'],max_workers=3)
manifest={'repo':repo,'revision':revision,'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(target.glob('*')) if f.is_file() and not f.name.startswith('.')}}
(target/'.lpc-model-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
config={'python':sys.executable,'chat_model':str(target),'prover_model':args.prover_model,'adapter':args.adapter}
(root/'.local-dialog.json').write_text(json.dumps(config,indent=2)+'\n')
print('Configured. Run ./start-reader.sh')
