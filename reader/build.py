"""Build local and public profiles from one reader source. No network required."""
from pathlib import Path
import json
root=Path(__file__).resolve().parent
css=(root/'reader.css').read_text().replace('__BG__','url("'+(root/'research/author-background.txt').read_text().strip()+'")')
data=json.loads((root/'research/reader-data.json').read_text())
shared=(root/'model.js').read_text()+'\n'+(root/'reader.js').read_text()
public_chat="document.getElementById('chat-state').textContent='Локальный сервис не подключён. Запусти start-reader.sh на своём Mac и открой локальный ридер с чатом.'; document.getElementById('chat-reset').disabled=true;"
for name,chat in [('index.html',(root/'local_chat.js').read_text()),('public-reader.html',public_chat)]:
 page=(root/'template.html').read_text().replace('__CSS__',css).replace('__JS__',shared+'\n'+chat).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
 assert not any(x in page for x in ['__CSS__','__JS__','__DATA__','__BG__'])
 (root/'dist').mkdir(exist_ok=True)
 (root/'dist'/name).write_text(page)
 print(root/'dist'/name)
